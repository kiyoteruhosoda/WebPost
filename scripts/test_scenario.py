#!/usr/bin/env python3
"""
Scenario load & execution test script

Usage:
  python scripts/test_scenario.py scenarios/fun_navi_reserve.yaml [--mock]
  
Options:
  --mock    Use mock HTTP client instead of real requests
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.scenario.loader_registry import ScenarioLoaderRegistry
from infrastructure.secrets.env_secret_provider import EnvSecretProvider
from infrastructure.logging.console_logger import ConsoleLogger
from infrastructure.url.base_url_resolver import BaseUrlResolver
from application.executor.step_executor import StepExecutor
from application.executor.handler_registry import HandlerRegistry
from application.handlers.http_handler import HttpStepHandler
from application.handlers.scrape_handler import ScrapeStepHandler
from application.handlers.assert_handler import AssertStepHandler
from application.handlers.result_handler import ResultStepHandler
from application.services.template_renderer import TemplateRenderer
from application.services.execution_deps import ExecutionDeps
from application.ports.requests_client import RequestsSessionHttpClient
from infrastructure.logging.console_logger import ConsoleLogger
from infrastructure.url.base_url_resolver import BaseUrlResolver
from domain.run import RunContext

# Import mock client (conditional import for type checking)
try:
    sys.path.insert(0, str(project_root / "tests"))
    from mock_http_client import MockHttpClient  # type: ignore
except ImportError:
    MockHttpClient = None  # type: ignore


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_scenario.py <scenario-file> [--mock]")
        sys.exit(1)

    scenario_path = sys.argv[1]
    use_mock = "--mock" in sys.argv
    
    print(f"=== Loading scenario: {scenario_path} ===")
    
    # 1) Load scenario
    registry = ScenarioLoaderRegistry()
    loader = registry.get_loader(Path(scenario_path))
    try:
        scenario = loader.load_from_file(scenario_path)
    except Exception as e:
        print(f"ERROR: Failed to load scenario: {e}")
        sys.exit(1)

    print(f"Scenario: {scenario.meta.name} (v{scenario.meta.version})")
    print(f"Steps: {len(scenario.steps)}")
    for i, step in enumerate(scenario.steps):
        print(f"  {i+1}. [{step.id}] {type(step).__name__}")

    # 2) Setup execution environment
    print("\n=== Setting up execution environment ===")
    
    # TemplateRenderer
    renderer = TemplateRenderer()
    
    # HTTP Client (mock or real)
    if use_mock:
        print("Using MOCK HTTP client")
        http_client = MockHttpClient()
    else:
        print("Using REAL HTTP client (requests)")
        http_client = RequestsSessionHttpClient()
    
    # Handlers
    http_handler = HttpStepHandler(http_client, renderer)
    scrape_handler = ScrapeStepHandler()
    assert_handler = AssertStepHandler()
    result_handler = ResultStepHandler(renderer)
    
    # Registry
    registry = HandlerRegistry([
        http_handler,
        scrape_handler,
        assert_handler,
        result_handler,
    ])
    
    # Executor
    executor = StepExecutor(registry)
    
    # Logger
    logger = ConsoleLogger()
    
    # URL Resolver
    base_url = scenario.defaults.http.base_url if scenario.defaults.http else ""
    url_resolver = BaseUrlResolver(base_url)
    
    # 3) Prepare test variables (dummy data)
    print("\n=== Preparing test variables ===")
    vars_input = {
        "mansionGNo": "12345",
        "facilityID": "001",
        "facilityNo": "01",
        "selectDate": "2026-02-10",
        "toNo": "18",
        "roomNo": "101",
        "hiddenUserId": "user001",
        "dates": ["2026/02/02", "2026/04/13"],
        # Optional
        "appliStart": "",
        "eventFlg": "false",
        "eventFacilityNo": "0",
        "rsvNo": "0",
        "spEventFlg": "false",
    }
    
    # Secret Provider - .envファイルから読み込む
    secret_provider = EnvSecretProvider()
    
    print("Variables:", json.dumps(vars_input, indent=2, ensure_ascii=False))
    print("Secrets: loaded from .env file")
    
    # 4) Create RunContext
    ctx = RunContext(
        run_id="test_run_001",
        scenario=scenario,
        vars=vars_input,
    )
    
    # 5) Create ExecutionDeps
    deps = ExecutionDeps(
        logger=logger,
        secret_provider=secret_provider,
        url_resolver=url_resolver,
    )
    
    # 6) Execute
    print("\n=== Executing scenario ===")
    if use_mock:
        print("Using mock responses for stable testing.\n")
    else:
        print("Note: Actual HTTP requests may fail without a running server.")
        print("This test validates scenario loading and step structure.\n")
    
    result = executor.execute(scenario.steps, ctx, deps)
    
    # 7) Display results
    print("\n=== Execution Result ===")
    print(f"Success: {result.ok}")
    if not result.ok:
        print(f"Failed Step: {result.failed_step_id}")
        print(f"Error: {result.error_message}")
    
    if ctx.result:
        print(f"Result: {json.dumps(ctx.result, indent=2, ensure_ascii=False)}")
    
    print("\n=== Context State ===")
    print(f"vars keys: {list(ctx.vars.keys())}")
    print(f"state keys: {list(ctx.state.keys())}")
    
    if result.ok:
        print("\n✅ Scenario execution completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Scenario execution failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
