"""FastAPI アプリケーション - REST API エンドポイント"""
from pathlib import Path
from typing import Dict, Any, Optional

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
from infrastructure.logging.console_logger import ConsoleLogger
from infrastructure.http.http_artifact_saver import HttpArtifactSaver
from infrastructure.url.base_url_resolver import BaseUrlResolver
from application.ports.requests_client import RequestsSessionHttpClient
from application.services.execution_deps import ExecutionDeps
from application.services.template_renderer import TemplateRenderer
from application.executor.handler_registry import HandlerRegistry
from application.executor.step_executor import StepExecutor
from application.handlers.http_handler import HttpStepHandler
from application.handlers.scrape_handler import ScrapeStepHandler
from application.handlers.assert_handler import AssertStepHandler
from application.handlers.result_handler import ResultStepHandler
from application.handlers.log_handler import LogStepHandler
from domain.run import RunContext


# リクエストモデル
class RunScenarioRequest(BaseModel):
    """シナリオ実行リクエスト"""
    vars: Dict[str, Any] = Field(default_factory=dict, description="入力変数")
    secrets: Dict[str, str] = Field(default_factory=dict, description="シークレット変数")


# レスポンスモデル
class RunScenarioResponse(BaseModel):
    """シナリオ実行レスポンス"""
    success: bool = Field(description="実行成功フラグ")
    result: Optional[Dict[str, Any]] = Field(default=None, description="実行結果")
    error: Optional[str] = Field(default=None, description="エラーメッセージ")


# FastAPIアプリケーション
app = FastAPI(
    title="WebPost Scenario Runner",
    description="シナリオベースのWeb自動化エンジン",
    version="1.0.0"
)

# 設定
SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"
TMP_DIR = Path(__file__).parent.parent / "tmp"


@app.get("/")
def read_root():
    """ヘルスチェック"""
    return {"status": "ok", "service": "webpost"}


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
    
    try:
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
        
        # 3. 実行環境を構築
        # EnvSecretProviderは環境変数から読み込むので、
        # リクエストのsecretsは別の実装が必要
        # ここでは簡易的にdictを持つクラスを作成
        class DictSecretProvider:
            def __init__(self, secrets: Dict[str, str]):
                self._secrets = secrets
            
            def get(self) -> Dict[str, Any]:
                return self._secrets
        
        secret_provider = DictSecretProvider(request.secrets)
        url_resolver = BaseUrlResolver(scenario.defaults.http.base_url)
        
        deps = ExecutionDeps(
            logger=logger,
            secret_provider=secret_provider,
            url_resolver=url_resolver
        )
        
        # 4. ハンドラー登録
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
        
        # 5. 実行
        executor = StepExecutor(registry)
        ctx = RunContext(
            scenario=scenario,
            vars=request.vars,
            state={},
            last=None,
            result={}
        )
        
        executor.execute(scenario.steps, ctx, deps)
        
        # 6. 結果を返す
        return RunScenarioResponse(
            success=True,
            result=ctx.result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("scenario_execution_failed", error=str(e), scenario_id=scenario_id)
        return RunScenarioResponse(
            success=False,
            error=str(e)
        )
