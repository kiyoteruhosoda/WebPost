#!/usr/bin/env python3
"""
Scenario execution script

Usage:
  python scripts/smoke_run.py run --scenario-file <path> [--vars <json>] [--secrets <json>]
  python scripts/smoke_run.py run --scenario-id <id> --api-base-url <url> [--vars <json>] [--secrets <json>]
  python scripts/smoke_run.py start --scenario-id <id> --api-base-url <url> [--vars <json>] [--secrets <json>]
  python scripts/smoke_run.py wait --run-id <id> --api-base-url <url> [--timeout-sec <sec>]
  python scripts/smoke_run.py status --run-id <id> --api-base-url <url>
  python scripts/smoke_run.py logs --run-id <id> --api-base-url <url>

Examples:
  python scripts/smoke_run.py scenarios/fun_navi_reserve.yaml
  python scripts/smoke_run.py run --scenario-file scenarios/fun_navi_reserve.yaml --vars '{"facilityID":"001"}'
  python scripts/smoke_run.py run --scenario-id simple_test --api-base-url http://localhost:8000
  python scripts/smoke_run.py start --scenario-id simple_test --api-base-url http://localhost:8000
  python scripts/smoke_run.py wait --run-id <run_id> --api-base-url http://localhost:8000 --timeout-sec 30
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests
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
from infrastructure.scenario.file_finder import ScenarioFileFinder
from infrastructure.scenario.loader_registry import ScenarioLoaderRegistry
from infrastructure.secrets.dict_secret_provider import DictSecretProvider
from domain.exceptions import ValidationError
from domain.run import RunContext


SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"
DEFAULT_API_TIMEOUT_SEC = 30


def _parse_json_payload(raw: str, label: str) -> dict:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for {label}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed


def _load_json_file(path: str, label: str) -> dict:
    try:
        content = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Unable to read {label} file: {exc}") from exc
    return _parse_json_payload(content, label)


def _load_json_stdin(label: str) -> dict:
    content = sys.stdin.read()
    if not content.strip():
        return {}
    return _parse_json_payload(content, label)


def _load_optional_payload(args: argparse.Namespace, label: str) -> dict:
    sources = [
        args.secrets is not None,
        args.secrets_file is not None,
        args.secrets_stdin,
    ]
    if sum(sources) > 1:
        raise ValueError(f"Multiple {label} sources provided")
    if args.secrets is not None:
        return _parse_json_payload(args.secrets, label)
    if args.secrets_file is not None:
        return _load_json_file(args.secrets_file, label)
    if args.secrets_stdin:
        return _load_json_stdin(label)
    return {}


def _load_vars_payload(raw: str | None) -> dict:
    if raw is None:
        return {}
    return _parse_json_payload(raw, "vars")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scenario execution helper")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run scenario locally or via API")
    run_parser.add_argument("--scenario-id", type=str)
    run_parser.add_argument("--scenario-file", type=str)
    run_parser.add_argument("--format", type=str, choices=["json", "yaml", "yml"])
    run_parser.add_argument("--vars", type=str)
    run_parser.add_argument("--secrets", type=str)
    run_parser.add_argument("--secrets-file", type=str)
    run_parser.add_argument("--secrets-stdin", action="store_true")
    run_parser.add_argument("--secret-ref", type=str, choices=["inline", "env"], default="inline")
    run_parser.add_argument("--idempotency-key", type=str)
    run_parser.add_argument("--api-base-url", type=str)
    run_parser.add_argument("--wait-sec", type=int)

    start_parser = subparsers.add_parser("start", help="Start scenario via API")
    start_parser.add_argument("--scenario-id", type=str, required=True)
    start_parser.add_argument("--vars", type=str)
    start_parser.add_argument("--secrets", type=str)
    start_parser.add_argument("--secrets-file", type=str)
    start_parser.add_argument("--secrets-stdin", action="store_true")
    start_parser.add_argument("--secret-ref", type=str, choices=["inline", "env"], default="inline")
    start_parser.add_argument("--idempotency-key", type=str)
    start_parser.add_argument("--api-base-url", type=str, required=True)

    wait_parser = subparsers.add_parser("wait", help="Wait for async run completion")
    wait_parser.add_argument("--run-id", type=str, required=True)
    wait_parser.add_argument("--api-base-url", type=str, required=True)
    wait_parser.add_argument("--timeout-sec", type=int, default=DEFAULT_API_TIMEOUT_SEC)
    wait_parser.add_argument("--interval-sec", type=float, default=1.0)

    status_parser = subparsers.add_parser("status", help="Fetch async run status")
    status_parser.add_argument("--run-id", type=str, required=True)
    status_parser.add_argument("--api-base-url", type=str, required=True)

    logs_parser = subparsers.add_parser("logs", help="Fetch async run logs")
    logs_parser.add_argument("--run-id", type=str, required=True)
    logs_parser.add_argument("--api-base-url", type=str, required=True)

    return parser


def _resolve_scenario_path(scenario_id: str, forced_format: str | None) -> Path:
    if forced_format:
        candidate = SCENARIOS_DIR / f"{scenario_id}.{forced_format}"
        if not candidate.exists():
            raise ValueError(f"Scenario file not found: {candidate}")
        return candidate
    finder = ScenarioFileFinder(SCENARIOS_DIR)
    scenario_file = finder.find_by_id(scenario_id)
    if scenario_file is None:
        raise ValueError(f"Scenario file not found: {scenario_id}")
    return scenario_file


def _run_local(args: argparse.Namespace) -> int:
    if args.scenario_file:
        scenario_path = Path(args.scenario_file)
    elif args.scenario_id:
        scenario_path = _resolve_scenario_path(args.scenario_id, args.format)
    else:
        raise ValueError("scenario-file or scenario-id is required for local run")

    vars_input = _load_vars_payload(args.vars)
    secrets_input = _load_optional_payload(args, "secrets")

    registry = ScenarioLoaderRegistry()
    loader = registry.get_loader(Path(scenario_path))
    try:
        scenario = loader.load_from_file(scenario_path)
    except Exception as e:
        raise ValueError(f"Failed to load scenario: {e}") from e

    print(f"Scenario: {scenario.meta.name} (v{scenario.meta.version})")
    print(f"Steps: {len(scenario.steps)}")
    
    # Validate required inputs before execution.
    # Reason: Ensure missing inputs fail early in CLI-like runs.
    # Impact: Exits with code 1 when required inputs are absent.
    try:
        ScenarioInputValidatorService.default().validate(scenario, vars_input)
    except ValidationError as e:
        raise ValueError(str(e)) from e

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
    if secrets_input:
        secret_provider = DictSecretProvider(secrets_input)
    else:
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
    
    return 0 if result.ok else 1


def _build_api_payload(args: argparse.Namespace) -> dict:
    payload = {
        "vars": _load_vars_payload(args.vars),
        "secrets": _load_optional_payload(args, "secrets"),
        "secret_ref": args.secret_ref,
    }
    if args.idempotency_key:
        payload["idempotency_key"] = args.idempotency_key
    return payload


def _post_run_request(
    base_url: str,
    scenario_id: str,
    payload: dict,
    wait_sec: int | None,
) -> requests.Response:
    url = f"{base_url.rstrip('/')}/scenarios/{scenario_id}/runs"
    params = {}
    if wait_sec is not None:
        params["wait_sec"] = wait_sec
    response = requests.post(url, json=payload, params=params, timeout=DEFAULT_API_TIMEOUT_SEC)
    return response


def _run_api(args: argparse.Namespace) -> int:
    if not args.api_base_url:
        raise ValueError("api-base-url is required for API run")
    if not args.scenario_id:
        raise ValueError("scenario-id is required for API run")
    payload = _build_api_payload(args)
    response = _post_run_request(args.api_base_url, args.scenario_id, payload, args.wait_sec)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if response.status_code == 202:
        return 0
    if response.status_code >= 400:
        return 1
    return 0 if data.get("success") else 1


def _start_api(args: argparse.Namespace) -> int:
    payload = _build_api_payload(args)
    response = _post_run_request(args.api_base_url, args.scenario_id, payload, wait_sec=0)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return 0 if response.status_code == 202 else 1


def _get_json(url: str) -> dict:
    response = requests.get(url, timeout=DEFAULT_API_TIMEOUT_SEC)
    response.raise_for_status()
    return response.json()


def _wait_api(args: argparse.Namespace) -> int:
    deadline = time.monotonic() + args.timeout_sec
    status_url = f"{args.api_base_url.rstrip('/')}/runs/{args.run_id}"
    while True:
        data = _get_json(status_url)
        status = data.get("status", "").lower()
        if status in {"succeeded", "failed"}:
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return 0 if status == "succeeded" else 1
        if time.monotonic() >= deadline:
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return 1
        time.sleep(args.interval_sec)


def _status_api(args: argparse.Namespace) -> int:
    url = f"{args.api_base_url.rstrip('/')}/runs/{args.run_id}"
    data = _get_json(url)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def _logs_api(args: argparse.Namespace) -> int:
    url = f"{args.api_base_url.rstrip('/')}/runs/{args.run_id}/logs"
    data = _get_json(url)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def main() -> None:
    parser = _build_parser()
    argv = sys.argv[1:]
    if argv and argv[0] not in {"run", "start", "wait", "status", "logs"}:
        argv = ["run", "--scenario-file", argv[0]] + argv[1:]
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "run":
            if args.scenario_file or args.scenario_id and not args.api_base_url:
                exit_code = _run_local(args)
            else:
                exit_code = _run_api(args)
        elif args.command == "start":
            exit_code = _start_api(args)
        elif args.command == "wait":
            exit_code = _wait_api(args)
        elif args.command == "status":
            exit_code = _status_api(args)
        elif args.command == "logs":
            exit_code = _logs_api(args)
        else:
            raise ValueError(f"Unknown command: {args.command}")
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    except requests.RequestException as exc:
        print(f"ERROR: API request failed: {exc}")
        sys.exit(1)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
