# Scenario Command Design

## Purpose
- Provide a consistent command interface to execute scenarios by ID or file path.
- Support YAML/YML/JSON scenario formats via format-specific loaders.
- Return structured results for automation and monitoring.

## Command Surface

### CLI
```
scenario run --scenario-id <id> [--vars <json>] [--secrets <json>] [--format <yaml|yml|json>]
scenario run --scenario-file <path> [--vars <json>] [--secrets <json>]
```

### HTTP
```
POST /scenarios/{scenario_id}/runs
```

## Inputs

### CLI Arguments
- `--scenario-id`: Scenario ID resolved under the scenarios directory.
- `--scenario-file`: Absolute or relative path to a scenario file.
- `--vars`: JSON string for runtime variables.
- `--secrets`: JSON string for secret variables.
- `--format`: Optional override for file format when using `--scenario-id`.

### HTTP Body
```json
{
  "vars": {},
  "secrets": {}
}
```

## Output

### CLI
- Exit code `0` on success, `1` on failure.
- Standard output includes execution summary and scenario metadata.
- Standard error includes error details when execution fails.

### HTTP Response
```json
{
  "success": true,
  "result": {},
  "error": null
}
```

## Format Resolution
- When using `--scenario-id` or HTTP endpoints, the loader is selected by file extension.
- Supported extensions: `.yaml`, `.yml`, `.json`.
- Unsupported extensions must return a format error before execution.

## Execution Flow
1. Resolve the scenario file path (ID or explicit path).
2. Select loader by file extension.
3. Parse scenario into domain objects.
4. Build execution dependencies.
5. Execute steps in order with logging and error handling.
6. Return aggregated results.

## Error Handling
- File not found: return 404 (HTTP) or exit 1 (CLI).
- Unsupported format: return 400 (HTTP) or exit 1 (CLI).
- Execution failure: return `success=false` with error details.

## Logging Requirements
- Each log entry must include a `type` field matching the event name.
- Step start/end must emit `step.start` and `step.end` events.
- Include `run_id` and `step_id` for correlation.
