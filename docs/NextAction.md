# Scenario TypeCommand Reference (Full, Current Spec)

(Integrated CLI/HTTP support with async runs.)

## 1. Purpose

* Define scenario execution consistently for CLI and HTTP.
* Resolve YAML/YML/JSON scenarios by extension.
* Return machine-readable results and errors.
* Ensure safety (secrets masking) and reproducibility (logs and metadata) for external site automation.

---

## 2. Scope and Assumptions

### 2.1 Scope

* Users of the scenario execution feature (API/CLI users, operators, developers).

### 2.2 Current Behavior

* Scenario files are located under `scenarios/` and resolved by file extension.
* Supported extensions: `.yaml` / `.yml` / `.json`.
* Step specifications live in the Type Reference section only.
* Execution supports both synchronous and asynchronous runs.
* Idempotency keys prevent duplicate executions.

### 2.3 Done (Implemented)

* DONE: Asynchronous runs with `run_id` are available for audit, long execution, and log access.
* DONE: HTTP supports `wait_sec` (bounded waiting) for sync/async coexistence.

---

## 3. Command System (CLI/HTTP)

## 3.1 CLI: `scripts/smoke_run.py`

### Forms

```
python scripts/smoke_run.py run --scenario-file <path> [--vars <json>] [--secrets <json>]
python scripts/smoke_run.py run --scenario-id <id> --api-base-url <url> [--vars <json>] [--secrets <json>] [--wait-sec <sec>]
python scripts/smoke_run.py start --scenario-id <id> --api-base-url <url> [--vars <json>] [--secrets <json>]
python scripts/smoke_run.py wait --run-id <id> --api-base-url <url> [--timeout-sec <sec>]
python scripts/smoke_run.py status --run-id <id> --api-base-url <url>
python scripts/smoke_run.py logs --run-id <id> --api-base-url <url>
```

### Parameters (run)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `--scenario-id` | string | one of | Scenario ID under `scenarios/` (API or local resolution). |
| `--scenario-file` | string | one of | Scenario file path (local execution). |
| `--format` | string | optional | Force extension for `scenario-id` (json/yaml/yml). |
| `--vars` | string(JSON) | optional | Input variables (JSON string). |
| `--secrets` | string(JSON) | optional | Secrets (JSON string). Mutually exclusive with `--secrets-file`/`--secrets-stdin`. |
| `--secrets-file` | string | optional | Secrets from file (JSON). |
| `--secrets-stdin` | flag | optional | Secrets from stdin (JSON). |
| `--secret-ref` | string | optional | `inline` or `env` for API execution. Default: `inline`. |
| `--idempotency-key` | string | optional | Prevent duplicate executions. |
| `--api-base-url` | string | optional | API base URL for HTTP execution. |
| `--wait-sec` | integer | optional | API wait time (sync/async). |

### Parameters (start/wait/status/logs)

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `--scenario-id` | string | required | Scenario ID for API start. |
| `--run-id` | string | required | Run identifier for wait/status/logs. |
| `--api-base-url` | string | required | API base URL. |
| `--timeout-sec` | integer | optional | Wait timeout (default 30). |
| `--interval-sec` | float | optional | Polling interval for wait (default 1.0). |

### Outputs

* Exit code: `0` (success), `1` (failure).
* STDOUT: machine-readable JSON for API calls and local result summary.
* STDERR: detailed error messages on failure.

### Examples

```
python scripts/smoke_run.py run --scenario-file scenarios/fun_navi_reserve.yaml --vars '{"facilityID":"001"}'
python scripts/smoke_run.py run --scenario-id simple_test --api-base-url http://localhost:8000 --wait-sec 30
python scripts/smoke_run.py start --scenario-id simple_test --api-base-url http://localhost:8000
python scripts/smoke_run.py wait --run-id <run_id> --api-base-url http://localhost:8000 --timeout-sec 30
```

### Done (CLI Extensions)

* DONE: `start/wait/status/logs` for async runs.
* DONE: `--wait-sec` and `--timeout-sec` for sync/async coexistence.
* DONE: `--secrets-file`/`--secrets-stdin` to reduce shell history exposure.

---

## 3.2 HTTP: Sync/Async Execution `POST /scenarios/{scenario_id}/runs`

### Purpose

* Execute a scenario over HTTP and return results as JSON.

### Path Parameter

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `scenario_id` | string | required | Scenario ID under `scenarios/`. |

### Request Body (Current)

```json
{
  "vars": {},
  "secrets": {},
  "secret_ref": "inline",
  "idempotency_key": "optional"
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `vars` | object | optional | Input variables. |
| `secrets` | object | optional | Secret values (inline). |
| `secret_ref` | string | optional | `inline` or `env` secret provider. |
| `idempotency_key` | string | optional | Prevent duplicate executions. |

### Query Parameter

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `wait_sec` | integer | optional | Wait time for sync/async coexistence. Max: 30. |

### Response (Sync)

```json
{
  "success": true,
  "result": {},
  "error": null,
  "error_detail": null
}
```

### Response (Async Accepted)

```json
{
  "run_id": "run_20260203_171500_abcd",
  "status": "queued",
  "links": {
    "self": "/runs/run_20260203_171500_abcd",
    "logs": "/runs/run_20260203_171500_abcd/logs"
  }
}
```

### Error Detail

```json
{
  "code": "step_failed",
  "message": "assertion failed: ${last.status}==200",
  "step_id": "assert_login_success",
  "last_status": 500
}
```

### Status Codes

| Code | Condition |
| --- | --- |
| `200` | Synchronous response (success/result/error populated). |
| `202` | Async accepted with `run_id`. |
| `400` | Validation error, unsupported format, or invalid wait_sec. |
| `404` | Scenario file not found. |
| `409` | Idempotency conflict. |

---

## 3.3 HTTP: Async Status/Logs

### Status Lookup

* `GET /runs/{run_id}` returns status/result/error/timestamps.

### Logs

* `GET /runs/{run_id}/logs` returns log entries.
* `run_id` is included in log fields (logger binds run_id for correlation).

---

## 4. Format Resolution Rules

* `scenario-id` resolution selects by extension priority: `.json` → `.yaml` → `.yml`.
* `--format` forces the extension for `scenario-id` in CLI.
* Unsupported extensions fail before execution.

---

## 5. Execution Flow

### 5.1 Synchronous

1. Resolve scenario file (ID or file path).
2. Select loader by extension.
3. Convert scenario to domain objects.
4. Build execution dependencies (logger, secret provider, URL resolver).
5. Execute steps sequentially (`enabled=false` steps are skipped).
6. Aggregate results and return response.

### 5.2 Asynchronous Run

* Create a Run record and transition `queued → running → succeeded/failed`.
* Steps execute sequentially in array order.
* `requests.Session` and execution context are run-scoped.
* `vars/state/last` are isolated per run.

---

## 6. Template Rules

### 6.1 References

* `${vars.xxx}`: input variables
* `${state.xxx}`: intermediate state
* `${last.status}` `${last.text}` `${last.url}`: last HTTP response
* `${secrets.xxx}`: secrets (forbidden in log templates)

### 6.2 Expansion

* `${...}` tokens are evaluated and replaced.
* Lists render as comma-joined strings in templates.
* `${vars.items[*].id}` expands to a list and renders as comma-joined string.

---

## 7. Scenario DSL (Top-Level)

### 7.1 Structure

```json
{
  "meta": {
    "id": "fun_navi_reserve",
    "name": "fun-navi-reserve",
    "description": "Login -> Reserve -> Extract reservation number",
    "version": 1,
    "enabled": true,
    "user_agent": "ScenarioRunner/1.0"
  },
  "inputs": {
    "required": ["mansionGNo", "facilityID", "dates"],
    "optional": ["timeout_sec"]
  },
  "defaults": {
    "http": {
      "base_url": "https://fun-navi.net",
      "timeout_sec": 20,
      "headers": {
        "User-Agent": "ScenarioRunner/1.0"
      }
    }
  },
  "steps": []
}
```

### 7.2 meta

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string/integer | recommended | Scenario identifier. |
| `name` | string | optional | Display name. |
| `description` | string | optional | Description. |
| `version` | integer | optional | Version for operations. |
| `enabled` | boolean | optional | Default `true`. |
| `user_agent` | string | optional | User agent metadata. |

### 7.3 inputs (optional)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `required` | array(string) | optional | Required input keys. |
| `optional` | array(string) | optional | Optional input keys. |

### 7.4 defaults.http (optional)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `base_url` | string | optional | Base URL for relative paths. |
| `timeout_sec` | integer | optional | HTTP timeout. |
| `headers` | object | optional | Default headers. |

---

## 8. Logging

* All log events include a `type` field.
* Steps emit `step.start` and `step.end`.
* Log steps reject templates that reference secrets.

---

## 9. Security and Masking

* `secrets` must not be logged.
* Extracted values may be masked based on operational policy.

---

# 10. Scenario Type Reference (Full)

## 10.1 Common Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | required | Step identifier. |
| `type` | string | required | `http` / `scrape` / `assert` / `result` / `log`. |
| `enabled` | boolean | optional | Default `true`. |
| `retry` | object | optional | Retry policy. |
| `on_error` | array | optional | Error handling rules. |

### retry

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `max` | integer | optional | Max retry count. |
| `backoff_sec` | array(integer) | optional | Backoff seconds. |

* If the backoff array is shorter than retries, the last value is reused.

### on_error

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `expr` | string/null | optional | Condition expression. `null` is fallback. |
| `action` | string | optional | `abort` / `retry` / `goto`. |
| `goto_step_id` | string | optional | Target step for `goto`. |

---

## 10.2 Type: `http`

### Purpose

* Execute HTTP requests and update `last`.

### Additional Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `request` | object | required | HTTP request specification. |
| `save_as_last` | boolean | optional | Keep response in `last` (default true). |

#### request

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `method` | string | optional | Default `GET`. |
| `url` | string | required | Relative or absolute URL. |
| `headers` | object | optional | Headers merged with defaults. |
| `form_list` | array([string, any]) | optional | Ordered form entries. |
| `merge_from_vars` | string | optional | Merge `vars[merge_from_vars]` into form list. |

#### form_list Rules

* Items preserve order.
* Merged `vars` pairs are added first; explicit `form_list` overrides on duplicate keys (last wins).
* Duplicate keys are deduplicated to the last value before the request is sent.

---

## 10.3 Type: `scrape`

### Purpose

* Extract values from HTML and store them in `vars` or `state`.

### Additional Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `command` | string | required | `hidden_inputs` / `css` / `label_next_td`. |
| `save_as` | string | required | Storage key. |
| `save_to` | string | optional | `vars` or `state` (default `vars`). |
| `source` | string | optional | Source selector (default `last.text`). |
| `selector` | string | optional | CSS selector for `css` command. |
| `attr` | string | optional | Attribute name for `css` command. |
| `multiple` | boolean | optional | Collect multiple values (`css`). |
| `label` | string | optional | Label text for `label_next_td`. |

### Behavior

* `css` command returns empty string/list when no match is found (not a failure).
* `hidden_inputs` requires `save_as`.
* `label_next_td` requires `label` and `save_as`.

---

## 10.4 Type: `assert`

### Purpose

* Evaluate conditions and determine success/failure.

### Additional Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `conditions` | array(object) | required | Condition list. |
| `mode` | string | optional | `all` (default) or `any`. |
| `fail_fast` | boolean | optional | Early exit (default true). |
| `message` | string | optional | Override failure message. |

#### conditions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `expr` | string | required | Expression to evaluate. |
| `message` | string | optional | Message for this condition when it fails. |

---

## 10.5 Type: `result`

### Purpose

* Store final output in `result` (API/CLI response payload).

### Additional Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `fields` | object | optional | Output key/value pairs (templates allowed). |

---

## 10.6 Type: `log`

### Purpose

* Emit logs during execution.

### Additional Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | string | required | Log message (templates allowed, secrets forbidden). |
| `level` | string | optional | `info` / `debug` / `error` (lowercase). |
| `fields` | object | optional | Additional structured fields. |

---

## 11. Error Handling

* Scenario not found: CLI exits `1`, HTTP returns `404`.
* Unsupported format: CLI exits `1`, HTTP returns `400`.
* Execution failure: `success=false` and `error`/`error_detail` populated.

---

## 12. Async Order Guarantee

* Steps execute sequentially in array order within a run (no parallel execution).
* `requests.Session` is created per run and discarded on completion.
* `vars/state/last` are run-scoped and isolated across runs.
* A run is not executed twice (status transition guard).
