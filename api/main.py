"""FastAPI アプリケーション - REST API エンドポイント"""
from pathlib import Path
from typing import Callable, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.scenario.file_finder import ScenarioFileFinder
from infrastructure.scenario.loader_registry import ScenarioLoaderRegistry
from infrastructure.secrets.env_secret_provider import EnvSecretProvider
from infrastructure.secrets.dict_secret_provider import DictSecretProvider
from infrastructure.logging.console_logger import ConsoleLogger
from infrastructure.http.http_artifact_saver import HttpArtifactSaver
from infrastructure.idempotency.in_memory_idempotency_store import InMemoryIdempotencyStore
from infrastructure.url.base_url_resolver import BaseUrlResolver
from application.ports.requests_client import RequestsSessionHttpClient
from application.services.execution_deps import ExecutionDeps, SecretProviderPort
from application.services.template_renderer import TemplateRenderer
from application.executor.handler_registry import HandlerRegistry
from application.executor.step_executor import StepExecutor
from application.handlers.http_handler import HttpStepHandler
from application.handlers.scrape_handler import ScrapeStepHandler
from application.handlers.assert_handler import AssertStepHandler
from application.handlers.result_handler import ResultStepHandler
from application.handlers.log_handler import LogStepHandler
from application.services.scenario_input_validator import ScenarioInputValidatorService
from application.services.idempotency_service import IdempotencyService
from application.services.execution_error_builder import ExecutionErrorBuilder
from application.exceptions import IdempotencyError
from domain.run import RunContext
from domain.exceptions import ValidationError
from domain.ids import IdempotencyKey


# リクエストモデル
class RunScenarioRequest(BaseModel):
    """シナリオ実行リクエスト"""
    vars: Dict[str, Any] = Field(default_factory=dict, description="入力変数")
    secrets: Dict[str, str] = Field(default_factory=dict, description="シークレット変数")
    secret_ref: Optional[str] = Field(
        default=None,
        description="Secret provider reference. Use 'inline' or 'env'.",
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        description="Prevent duplicate executions when provided.",
    )


class ErrorDetailResponse(BaseModel):
    """Structured error detail"""
    code: str = Field(description="Error code")
    message: str = Field(description="Error message")
    step_id: Optional[str] = Field(default=None, description="Failed step id")
    last_status: Optional[int] = Field(default=None, description="Last response status")


class RunScenarioResponse(BaseModel):
    """シナリオ実行レスポンス"""
    success: bool = Field(description="実行成功フラグ")
    result: Optional[Dict[str, Any]] = Field(default=None, description="実行結果")
    error: Optional[str] = Field(default=None, description="エラーメッセージ")
    error_detail: Optional[ErrorDetailResponse] = Field(
        default=None,
        description="Structured error detail",
    )


# FastAPIアプリケーション
app = FastAPI(
    title="WebPost Scenario Runner",
    description="シナリオベースのWeb自動化エンジン",
    version="1.0.0"
)

# 設定
SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"
TMP_DIR = Path(__file__).parent.parent / "tmp"
IDEMPOTENCY_STORE = InMemoryIdempotencyStore()


@app.get("/")
def read_root():
    """ヘルスチェック"""
    return {"status": "ok", "service": "webpost"}


class SecretProviderResolver:
    def __init__(
        self,
        factories: Dict[str, Callable[[RunScenarioRequest], SecretProviderPort]],
        default_key: str,
    ) -> None:
        self._factories = factories
        self._default_key = default_key

    def resolve(self, request: RunScenarioRequest) -> SecretProviderPort:
        key = request.secret_ref or self._default_key
        factory = self._factories.get(key)
        if not factory:
            raise HTTPException(status_code=400, detail=f"Unknown secret_ref: {key}")
        return factory(request)


def _build_secret_provider_resolver() -> SecretProviderResolver:
    return SecretProviderResolver(
        factories={
            "inline": lambda request: DictSecretProvider(request.secrets),
            "env": lambda _request: EnvSecretProvider(),
        },
        default_key="inline",
    )


@app.post("/scenarios/{scenario_id}/runs", response_model=RunScenarioResponse)
def run_scenario(
    scenario_id: str,
    request: RunScenarioRequest = Body(...)
) -> RunScenarioResponse:
    """
    指定されたシナリオを実行する
    
    Args:
        scenario_id: シナリオID（例: "fun-navi-reserve"）
        request: 実行リクエスト（vars, secrets）
    
    Returns:
        実行結果
    """
    logger = ConsoleLogger()
    ctx: Optional[RunContext] = None
    
    try:
        # Reason: Prevent duplicate executions when the same key is supplied.
        # Impact: Requests with a reused idempotency_key return HTTP 409.
        if request.idempotency_key:
            idempotency = IdempotencyService(IDEMPOTENCY_STORE)
            idempotency.register_or_raise(IdempotencyKey(request.idempotency_key))

        # 1. シナリオファイルを探索
        finder = ScenarioFileFinder(SCENARIOS_DIR)
        scenario_file = finder.find_by_id(scenario_id)
        
        if scenario_file is None:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario file not found: {scenario_id}"
            )
        
        # 2. シナリオをロード
        registry = ScenarioLoaderRegistry()
        loader = registry.get_loader(scenario_file)
        scenario = loader.load_from_file(scenario_file)
        
        # 3. 実行前バリデーション
        # Reason: Enforce required inputs at the API boundary.
        # Impact: Missing inputs return HTTP 400 instead of runtime failures.
        ScenarioInputValidatorService.default().validate(scenario, request.vars)

        # 4. 実行環境を構築
        resolver = _build_secret_provider_resolver()
        secret_provider = resolver.resolve(request)
        url_resolver = BaseUrlResolver(scenario.defaults.http.base_url)
        
        deps = ExecutionDeps(
            logger=logger,
            secret_provider=secret_provider,
            url_resolver=url_resolver
        )
        
        # 5. ハンドラー登録
        renderer = TemplateRenderer()
        http_client = RequestsSessionHttpClient()
        
        handlers = [
            HttpStepHandler(http_client, renderer),
            ScrapeStepHandler(),
            AssertStepHandler(),
            ResultStepHandler(renderer),
            LogStepHandler(renderer),
        ]
        registry = HandlerRegistry(handlers)
        
        # 6. 実行
        executor = StepExecutor(registry)
        error_builder = ExecutionErrorBuilder()
        ctx = RunContext(
            scenario=scenario,
            vars=request.vars,
            state={},
            last=None,
            result={}
        )

        execution_result = executor.execute(scenario.steps, ctx, deps)

        if not execution_result.ok:
            # Reason: Provide structured error details for failed executions.
            # Impact: Clients can rely on error_detail for diagnostics.
            detail = error_builder.build_from_result(execution_result, ctx)
            return RunScenarioResponse(
                success=False,
                result=ctx.result,
                error=detail.message,
                error_detail=ErrorDetailResponse(**detail.__dict__),
            )
        
        # 7. 結果を返す
        return RunScenarioResponse(
            success=True,
            result=ctx.result
        )
        
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IdempotencyError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        error_builder = ExecutionErrorBuilder()
        detail = error_builder.build_from_exception(str(e), ctx)
        logger.error("scenario_execution_failed", error=str(e), scenario_id=scenario_id)
        return RunScenarioResponse(
            success=False,
            error=str(e),
            error_detail=ErrorDetailResponse(**detail.__dict__),
        )
