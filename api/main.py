"""FastAPI アプリケーション - REST API エンドポイント"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Any, Optional, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Body, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.scenario.file_finder import ScenarioFileFinder
from infrastructure.scenario.loader_registry import ScenarioLoaderRegistry
from infrastructure.secrets.env_secret_provider import EnvSecretProvider
from infrastructure.secrets.dict_secret_provider import DictSecretProvider
from infrastructure.logging.console_logger import ConsoleLogger
from infrastructure.logging.composite_logger import CompositeLogger
from infrastructure.logging.run_log_logger import RunLogLogger
from infrastructure.http.http_artifact_saver import HttpArtifactSaver
from infrastructure.idempotency.in_memory_idempotency_store import InMemoryIdempotencyStore
from infrastructure.run.in_memory_run_log_store import InMemoryRunLogStore
from infrastructure.run.in_memory_run_repository import InMemoryRunRepository
from infrastructure.run.in_memory_run_scheduler import InMemoryRunScheduler
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
from domain.run_record import RunRecord, RunStatus


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


class RunAcceptedResponse(BaseModel):
    """Accepted response for async execution"""
    run_id: str = Field(description="Run identifier")
    status: str = Field(description="Run status")
    links: Dict[str, str] = Field(description="Related resources")


class RunStatusResponse(BaseModel):
    """Async run status response"""
    run_id: str = Field(description="Run identifier")
    status: str = Field(description="Run status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Run result")
    error: Optional[str] = Field(default=None, description="Run error")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Update timestamp")


class RunLogEntryResponse(BaseModel):
    """Async run log entry"""
    timestamp: datetime = Field(description="Log timestamp")
    event: str = Field(description="Log event name")
    fields: Dict[str, Any] = Field(description="Log payload")


@dataclass(frozen=True)
class ExecutionOutcome:
    ok: bool
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    error_detail: Optional[ErrorDetailResponse]


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
RUN_REPOSITORY = InMemoryRunRepository()
RUN_LOG_STORE = InMemoryRunLogStore()
RUN_SCHEDULER = InMemoryRunScheduler()
MAX_WAIT_SEC = 30


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


def _build_logger(run_id: str) -> CompositeLogger:
    return CompositeLogger(
        [
            ConsoleLogger(),
            RunLogLogger(run_id=run_id, log_store=RUN_LOG_STORE),
        ]
    )


def _load_scenario(scenario_id: str):
    finder = ScenarioFileFinder(SCENARIOS_DIR)
    scenario_file = finder.find_by_id(scenario_id)

    if scenario_file is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario file not found: {scenario_id}",
        )

    registry = ScenarioLoaderRegistry()
    loader = registry.get_loader(scenario_file)
    return loader.load_from_file(scenario_file)


def _validate_request(scenario, request: RunScenarioRequest) -> None:
    # Reason: Enforce required inputs at the API boundary.
    # Impact: Missing inputs return HTTP 400 instead of runtime failures.
    ScenarioInputValidatorService.default().validate(scenario, request.vars)

    # Reason: Prevent duplicate executions when the same key is supplied.
    # Impact: Requests with a reused idempotency_key return HTTP 409.
    if request.idempotency_key:
        idempotency = IdempotencyService(IDEMPOTENCY_STORE)
        idempotency.register_or_raise(IdempotencyKey(request.idempotency_key))


def _build_execution_components(
    scenario,
    request: RunScenarioRequest,
    logger: CompositeLogger,
    run_id: str,
) -> tuple[StepExecutor, RunContext, ExecutionDeps]:
    resolver = _build_secret_provider_resolver()
    secret_provider = resolver.resolve(request)
    base_url = scenario.defaults.http.base_url if scenario.defaults.http else ""
    url_resolver = BaseUrlResolver(base_url)

    deps = ExecutionDeps(
        logger=logger,
        secret_provider=secret_provider,
        url_resolver=url_resolver,
    )

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
    executor = StepExecutor(registry)

    ctx = RunContext(
        run_id=run_id,
        vars=request.vars,
        state={},
        last=None,
        result={},
    )
    return executor, ctx, deps


def _execute_scenario(
    scenario,
    request: RunScenarioRequest,
    logger: CompositeLogger,
    run_id: str,
) -> ExecutionOutcome:
    ctx: Optional[RunContext] = None
    error_builder = ExecutionErrorBuilder()

    try:
        executor, ctx, deps = _build_execution_components(scenario, request, logger, run_id)
        execution_result = executor.execute(scenario.steps, ctx, deps)
        if not execution_result.ok:
            detail = error_builder.build_from_result(execution_result, ctx)
            return ExecutionOutcome(
                ok=False,
                result=ctx.result,
                error=detail.message,
                error_detail=ErrorDetailResponse(**detail.__dict__),
            )
        return ExecutionOutcome(ok=True, result=ctx.result, error=None, error_detail=None)
    except Exception as exc:
        detail = error_builder.build_from_exception(str(exc), ctx)
        logger.error("scenario_execution_failed", error=str(exc), scenario_id=scenario.meta.id)
        return ExecutionOutcome(
            ok=False,
            result=getattr(ctx, "result", None),
            error=str(exc),
            error_detail=ErrorDetailResponse(**detail.__dict__),
        )


def _create_run_record(scenario_id: str, run_id: str) -> RunRecord:
    now = datetime.now(timezone.utc)
    return RunRecord(
        run_id=run_id,
        scenario_id=scenario_id,
        status=RunStatus.QUEUED,
        created_at=now,
        updated_at=now,
        result=None,
        error=None,
        error_detail=None,
    )


def _build_run_links(run_id: str) -> Dict[str, str]:
    return {
        "self": f"/runs/{run_id}",
        "logs": f"/runs/{run_id}/logs",
    }


def _build_response_from_record(record: RunRecord) -> RunScenarioResponse:
    error_detail = (
        ErrorDetailResponse(**record.error_detail) if record.error_detail else None
    )
    return RunScenarioResponse(
        success=record.status == RunStatus.SUCCEEDED,
        result=record.result,
        error=record.error,
        error_detail=error_detail,
    )


def _execute_async_run(
    scenario_id: str,
    scenario,
    request: RunScenarioRequest,
    run_id: str,
) -> None:
    logger = _build_logger(run_id).bind(run_id=run_id)
    logger.info("run.start", scenario_id=scenario_id)

    try:
        RUN_REPOSITORY.transition_status(run_id, RunStatus.QUEUED, RunStatus.RUNNING)
    except Exception as exc:
        logger.error("run.transition_failed", error=str(exc), run_id=run_id)
        return

    outcome = _execute_scenario(scenario, request, logger, run_id)
    if outcome.ok:
        RUN_REPOSITORY.transition_status(
            run_id,
            RunStatus.RUNNING,
            RunStatus.SUCCEEDED,
            result=outcome.result,
        )
        logger.info("run.end", status=RunStatus.SUCCEEDED.value)
        return

    error_detail = outcome.error_detail.model_dump() if outcome.error_detail else None
    RUN_REPOSITORY.transition_status(
        run_id,
        RunStatus.RUNNING,
        RunStatus.FAILED,
        result=outcome.result,
        error=outcome.error,
        error_detail=error_detail,
    )
    logger.info("run.end", status=RunStatus.FAILED.value)


@app.post("/scenarios/{scenario_id}/runs", response_model=RunScenarioResponse)
def run_scenario(
    scenario_id: str,
    request: RunScenarioRequest = Body(...),
    wait_sec: Optional[int] = Query(default=None, ge=0),
) -> RunScenarioResponse:
    """
    指定されたシナリオを実行する

    Args:
        scenario_id: シナリオID（例: "fun-navi-reserve")
        request: 実行リクエスト（vars, secrets）

    Returns:
        実行結果
    """
    ctx: Optional[RunContext] = None
    logger = ConsoleLogger()

    try:
        if wait_sec is not None and wait_sec > MAX_WAIT_SEC:
            raise HTTPException(
                status_code=400,
                detail=f"wait_sec must be <= {MAX_WAIT_SEC}",
            )

        scenario = _load_scenario(scenario_id)
        _validate_request(scenario, request)

        if wait_sec is None:
            run_id = uuid4().hex
            logger = _build_logger(run_id)
            outcome = _execute_scenario(scenario, request, logger, run_id)
            if not outcome.ok:
                return RunScenarioResponse(
                    success=False,
                    result=outcome.result,
                    error=outcome.error,
                    error_detail=outcome.error_detail,
                )
            return RunScenarioResponse(success=True, result=outcome.result)

        run_id = uuid4().hex
        record = _create_run_record(scenario_id, run_id)
        RUN_REPOSITORY.create(record)

        RUN_SCHEDULER.submit(
            run_id,
            lambda: _execute_async_run(scenario_id, scenario, request, run_id),
        )

        if wait_sec and RUN_SCHEDULER.wait(run_id, wait_sec):
            completed = RUN_REPOSITORY.get(run_id)
            if completed is None:
                raise HTTPException(status_code=404, detail="Run not found")
            return _build_response_from_record(completed)

        accepted = RunAcceptedResponse(
            run_id=run_id,
            status=record.status.value,
            links=_build_run_links(run_id),
        )
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=accepted.model_dump(),
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


@app.get("/runs/{run_id}", response_model=RunStatusResponse)
def get_run_status(run_id: str) -> RunStatusResponse:
    record = RUN_REPOSITORY.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return RunStatusResponse(
        run_id=record.run_id,
        status=record.status.value,
        result=record.result,
        error=record.error,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@app.get("/runs/{run_id}/logs", response_model=List[RunLogEntryResponse])
def get_run_logs(run_id: str) -> List[RunLogEntryResponse]:
    record = RUN_REPOSITORY.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    entries = RUN_LOG_STORE.list(run_id)
    return [
        RunLogEntryResponse(
            timestamp=entry.timestamp,
            event=entry.event,
            fields=entry.fields,
        )
        for entry in entries
    ]
