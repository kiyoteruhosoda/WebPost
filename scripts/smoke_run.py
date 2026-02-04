#!/usr/bin/env python3
"""
Scenario execution script

Usage:
  python scripts/smoke_run.py <scenario-file> [--vars <json>]
  
Example:
  python scripts/smoke_run.py scenarios/fun_navi_reserve.yaml
  python scripts/smoke_run.py scenarios/fun_navi_reserve.yaml --vars '{"facilityID":"001"}'
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from infrastructure.logging.log_setup import setup_console_logging
setup_console_logging(level="INFO")

from application.executor.handler_registry import HandlerRegistry
from application.executor.step_executor import StepExecutor
from application.handlers.http_handler import HttpStepHandler
from application.handlers.scrape_handler import ScrapeStepHandler
from application.handlers.assert_handler import AssertStepHandler
from application.handlers.result_handler import ResultStepHandler
from application.handlers.log_handler import LogStepHandler
from application.services.scenario_input_validator import ScenarioInputValidatorService
from application.services.template_renderer import TemplateRenderer
from application.services.execution_deps import ExecutionDeps
from application.ports.requests_client import RequestsSessionHttpClient
from infrastructure.secrets.env_secret_provider import EnvSecretProvider
from infrastructure.url.base_url_resolver import BaseUrlResolver
from infrastructure.logging.console_logger import ConsoleLogger
from infrastructure.scenario.loader_registry import ScenarioLoaderRegistry
from domain.exceptions import ValidationError
from domain.run import RunContext


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/smoke_run.py <scenario-file> [--vars <json>]")
        print("Example: python scripts/smoke_run.py scenarios/fun_navi_reserve.yaml")
        sys.exit(1)

    scenario_path = sys.argv[1]
    
    # Parse --vars option
    vars_input = {}
    if "--vars" in sys.argv:
        vars_index = sys.argv.index("--vars")
        if vars_index + 1 < len(sys.argv):
            try:
                vars_input = json.loads(sys.argv[vars_index + 1])
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON in --vars: {e}")
                sys.exit(1)
    
    # Load scenario
    registry = ScenarioLoaderRegistry()
    loader = registry.get_loader(Path(scenario_path))
    try:
        scenario = loader.load_from_file(scenario_path)
    except Exception as e:
        print(f"ERROR: Failed to load scenario: {e}")
        sys.exit(1)

    print(f"Scenario: {scenario.meta.name} (v{scenario.meta.version})")
    print(f"Steps: {len(scenario.steps)}")
    
    # Validate required inputs before execution.
    # Reason: Ensure missing inputs fail early in CLI-like runs.
    # Impact: Exits with code 1 when required inputs are absent.
    try:
        ScenarioInputValidatorService.default().validate(scenario, vars_input)
    except ValidationError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Setup execution environment
    renderer = TemplateRenderer()
    http_client = RequestsSessionHttpClient()
    
    # Setup all handlers
    http_handler = HttpStepHandler(http_client, renderer)
    scrape_handler = ScrapeStepHandler()
    assert_handler = AssertStepHandler()
    result_handler = ResultStepHandler(renderer)
    log_handler = LogStepHandler(renderer)
    
    handler_registry = HandlerRegistry([
        http_handler,
        scrape_handler,
        assert_handler,
        result_handler,
        log_handler,
    ])
    
    executor = StepExecutor(handler_registry)
    
    # Setup dependencies
    logger = ConsoleLogger()
    base_url = scenario.defaults.http.base_url if scenario.defaults.http else ""
    url_resolver = BaseUrlResolver(base_url)
    secret_provider = EnvSecretProvider()
    
    deps = ExecutionDeps(
        logger=logger,
        secret_provider=secret_provider,
        url_resolver=url_resolver,
    )

    # Create run context
    ctx = RunContext(vars=vars_input)

    # Execute scenario
    print("\n=== Executing ===\n")
    result = executor.execute(scenario.steps, ctx, deps)
    
    # Display results
    print("\n=== Result ===")
    print(f"Run ID: {ctx.run_id}")
    print(f"Success: {result.ok}")
    if not result.ok:
        print(f"Failed Step: {result.failed_step_id}")
        print(f"Error: {result.error_message}")
    
    if ctx.result:
        print(f"Output: {json.dumps(ctx.result, indent=2, ensure_ascii=False)}")
    
    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
