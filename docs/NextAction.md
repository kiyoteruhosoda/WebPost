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

* Execute HTTP requests (GET, POST, etc.) to external websites or APIs.
* Store response in `last` for use in subsequent steps.
* Support form data composition with variable merging and template expansion.

### Additional Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `request` | object | required | HTTP request specification (method, URL, headers, form data). |
| `save_as_last` | boolean | optional | Store response in `last` context (default: `true`). Set to `false` for intermediate requests. |

#### request

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `method` | string | optional | HTTP method: `GET`, `POST`, `PUT`, `DELETE`, etc. (default: `GET`). |
| `url` | string | required | Request URL. Relative URLs are resolved against `defaults.http.base_url`. |
| `headers` | object | optional | Request headers. Merged with `defaults.http.headers` (explicit values override defaults). |
| `form_list` | array([string, any]) | optional | Ordered list of form fields as `[name, value]` pairs. Supports template expansion. |
| `merge_from_vars` | string | optional | Variable name containing a dictionary to merge into form data (e.g., hidden inputs from scraping). |

### Use Cases

**1. Simple GET Request**

Fetch a login page or API endpoint.

```yaml
- id: login_get
  type: http
  request:
    method: GET
    url: /login
```

**2. POST with Form Data**

Submit a login form with credentials.

```yaml
- id: login_post
  type: http
  request:
    method: POST
    url: /login
    form_list:
      - [username, "${secrets.USERNAME}"]
      - [password, "${secrets.PASSWORD}"]
      - [remember, "true"]
```

**3. POST with Merged Hidden Inputs**

Merge scraped hidden fields (CSRF tokens) with explicit form data.

```yaml
- id: login_post
  type: http
  request:
    method: POST
    url: /login
    merge_from_vars: login_hidden  # Contains {"csrfToken": "abc123", "sessionId": "xyz"}
    form_list:
      - [username, "${secrets.USERNAME}"]
      - [password, "${secrets.PASSWORD}"]
```

**Result**: Form data becomes `{"csrfToken": "abc123", "sessionId": "xyz", "username": "...", "password": "..."}` (merged fields come first, explicit fields override on collision).

**4. Array Expansion with `[*]`**

Expand arrays into multiple form fields with the same name.

```yaml
- id: reserve_post
  type: http
  request:
    method: POST
    url: /reserve
    form_list:
      - [facilityID, "${vars.facilityID}"]
      - [date, ""]  # Empty placeholder
      - [date, "${vars.dates[*]}"]  # Expands to multiple date fields
```

**Input**: `vars.dates = ["2026-02-10", "2026-02-11"]`

**Result**: Form data includes `date=&date=2026-02-10&date=2026-02-11`

**5. Custom Headers**

Override default headers or add authorization.

```yaml
- id: api_call
  type: http
  request:
    method: POST
    url: /api/v1/resource
    headers:
      Authorization: "Bearer ${vars.token}"
      Content-Type: application/json
```

### form_list Rules

* **Order Preservation**: Items appear in the request in the order specified.
* **Merge Order**: If `merge_from_vars` is used:
  1. Merged variables are added first
  2. Explicit `form_list` entries are added after
  3. Duplicate keys are deduplicated (last value wins)
* **Template Expansion**: All values support `${...}` templates.
* **Array Expansion**: `${vars.field[*]}` expands arrays into multiple fields with the same name.
* **Collision Handling**: When the same key appears multiple times, the last occurrence is used (logged as `collision_keys`).

### Response Context

After execution, the response is stored in `last` (if `save_as_last: true`):

* `${last.status}` - HTTP status code (e.g., `200`, `302`, `404`)
* `${last.text}` - Response body as text
* `${last.url}` - Final URL (after redirects)
* `${last.headers}` - Response headers dictionary

### Error Handling

Use `on_error` rules to handle HTTP failures:

```yaml
- id: login_post
  type: http
  request:
    method: POST
    url: /login
    form_list:
      - [username, "${secrets.USERNAME}"]
      - [password, "${secrets.PASSWORD}"]
  retry:
    max: 2
    backoff_sec: [1, 3]
  on_error:
    - expr: "${last.status}>=500"
      action: retry
    - expr: "${last.status}==401"
      action: goto
      goto_step_id: login_get
    - expr: null
      action: abort
```

---

## 10.3 Type: `scrape`

### Purpose

* Extract values from HTML and store them in `vars` or `state`.

### Additional Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `command` | string | required | Scraping method: `hidden_inputs`, `css`, or `label_next_td`. |
| `save_as` | string | required | Variable name to store the extracted value (e.g., `login_hidden`, `reservationNo`). |
| `save_to` | string | optional | Storage target: `vars` (default) or `state`. Values in `vars` are accessible across steps. |
| `source` | string | optional | HTML source to scrape (default: `last.text` from previous HTTP response). |
| `selector` | string | optional | CSS selector for `css` command (e.g., `div.content > a.link`). |
| `attr` | string | optional | HTML attribute to extract for `css` command (e.g., `href`, `src`, `data-id`). If omitted, extracts text content. |
| `multiple` | boolean | optional | For `css` command: extract all matching elements as a list (default: `false`, extracts first match only). |
| `label` | string | optional | Label text for `label_next_td` command (e.g., `予約番号` to find the label and extract adjacent cell value). |

### Commands

#### `hidden_inputs`

Extracts all hidden input fields from an HTML form and stores them as a dictionary.

**Use Case**: Capture CSRF tokens, session IDs, or form state for subsequent POST requests.

**Fields Required**: `save_as`

**Example**:
```yaml
- id: scrape_login_hidden
  type: scrape
  command: hidden_inputs
  save_as: login_hidden
```

**Behavior**:
- Parses HTML from `source` (default: `last.text`)
- Finds all `<input type="hidden">` elements
- Returns a dictionary: `{"name": "value", ...}`
- Stored in `vars.login_hidden` (accessible as `${vars.login_hidden}`)

**HTML Example**:
```html
<form>
  <input type="hidden" name="csrfToken" value="abc123">
  <input type="hidden" name="sessionId" value="xyz789">
</form>
```

**Result**: `vars.login_hidden = {"csrfToken": "abc123", "sessionId": "xyz789"}`

---

#### `css`

Extracts values using CSS selectors.

**Use Case**: Extract specific elements by class, ID, or structure (links, text, attributes).

**Fields Required**: `save_as`, `selector`

**Optional Fields**: `attr`, `multiple`

**Example 1**: Extract single text value
```yaml
- id: extract_title
  type: scrape
  command: css
  selector: h1.page-title
  save_as: page_title
```

**Example 2**: Extract attribute (e.g., link URL)
```yaml
- id: extract_download_link
  type: scrape
  command: css
  selector: a.download-button
  attr: href
  save_as: download_url
```

**Example 3**: Extract multiple values as a list
```yaml
- id: extract_product_ids
  type: scrape
  command: css
  selector: div.product
  attr: data-product-id
  multiple: true
  save_as: product_ids
```

**Behavior**:
- If `multiple: false` (default): returns first match as string (empty string if no match)
- If `multiple: true`: returns all matches as list (empty list if no match)
- If `attr` is specified: extracts the attribute value
- If `attr` is omitted: extracts text content

---

#### `label_next_td`

Extracts the value from a table cell adjacent to a label.

**Use Case**: Extract structured data from HTML tables where labels and values are in adjacent cells.

**Fields Required**: `save_as`, `label`

**Example**:
```yaml
- id: extract_reservation_no
  type: scrape
  command: label_next_td
  label: 予約番号
  save_as: reservationNo
```

**HTML Example**:
```html
<table>
  <tr>
    <td>予約番号</td>
    <td>12345678901</td>
  </tr>
  <tr>
    <td>予約日時</td>
    <td>2026-02-10 14:00</td>
  </tr>
</table>
```

**Behavior**:
- Searches for a `<td>` or `<th>` containing the exact `label` text
- Extracts the text from the next `<td>` in the same row
- Returns extracted value as string
- Fails if label is not found or next cell is missing

**Result**: `vars.reservationNo = "12345678901"`

---

### General Behavior

* `css` command returns empty string/list when no match is found (not a failure).
* `hidden_inputs` and `label_next_td` fail if required elements are not found.
* All commands default to `source: last.text` (HTML from the previous HTTP response).
* Extracted values are stored in `vars` by default and accessible in subsequent steps via `${vars.save_as}`.

---

## 10.4 Type: `assert`

### Purpose

* Validate conditions based on HTTP responses, scraped values, or execution state.
* Fail the scenario if conditions are not met.
* Support multiple conditions with `all` (AND) or `any` (OR) logic.

### Additional Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `conditions` | array(object) | required | List of conditions to evaluate. |
| `mode` | string | optional | Evaluation mode: `all` (all conditions must pass, default) or `any` (at least one must pass). |
| `fail_fast` | boolean | optional | Stop at first failure (default: `true`). If `false`, evaluates all conditions before failing. |
| `message` | string | optional | Custom failure message (overrides individual condition messages). |

#### conditions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `expr` | string | required | Boolean expression to evaluate. Returns `true` (pass) or `false` (fail). |
| `message` | string | optional | Custom message for this specific condition when it fails. |

### Use Cases

**1. Verify HTTP Status**

Check if login was successful.

```yaml
- id: assert_login_success
  type: assert
  conditions:
    - expr: "${last.status}==200"
      message: "Login failed with status ${last.status}"
```

**2. Multiple Conditions (AND Logic)**

Validate both status and response content.

```yaml
- id: assert_reservation_success
  type: assert
  mode: all
  conditions:
    - expr: "${last.status}==200"
      message: "Unexpected status: ${last.status}"
    - expr: "matches(${vars.reservationNo}, '^[0-9]{11}$')"
      message: "Invalid reservation number format: ${vars.reservationNo}"
```

**3. Any Condition (OR Logic)**

Pass if at least one condition is true.

```yaml
- id: assert_success_or_redirect
  type: assert
  mode: any
  conditions:
    - expr: "${last.status}==200"
    - expr: "${last.status}==302"
  message: "Expected 200 or 302, got ${last.status}"
```

**4. Validate Scraped Data**

Check if extracted value meets requirements.

```yaml
- id: assert_product_price
  type: assert
  conditions:
    - expr: "${vars.price}>0"
      message: "Price must be positive: ${vars.price}"
    - expr: "${vars.price}<10000"
      message: "Price too high: ${vars.price}"
```

**5. Complex Expressions**

Use logical operators and functions.

```yaml
- id: assert_availability
  type: assert
  conditions:
    - expr: "contains(${last.text}, '在庫あり') or contains(${last.text}, 'In Stock')"
      message: "Product not available"
```

### Expression Syntax

Conditions support the following:

* **Comparison Operators**: `==`, `!=`, `<`, `<=`, `>`, `>=`
* **Logical Operators**: `and`, `or`, `not`
* **Template Variables**: `${last.status}`, `${vars.xxx}`, `${state.xxx}`
* **Functions**:
  * `matches(text, pattern)` - Regex matching
  * `contains(text, substring)` - Substring check
  * `len(value)` - Length of string or list

**Examples**:
```python
"${last.status}==200"
"${last.status}>=200 and ${last.status}<300"
"contains(${last.text}, 'Success')"
"matches(${vars.email}, '^[^@]+@[^@]+\\.[^@]+$')"
"len(${vars.items})>0"
```

### Behavior

**Mode: `all` (default)**
* All conditions must evaluate to `true`
* If `fail_fast: true` (default), stops at first failure
* If `fail_fast: false`, evaluates all conditions and reports all failures

**Mode: `any`**
* At least one condition must evaluate to `true`
* If all conditions fail, the step fails
* `fail_fast` is ignored in `any` mode

**Failure**:
* Step fails if conditions are not met
* Error message includes:
  * Custom `message` (if provided)
  * Individual condition messages
  * Failed expression details
* Triggers `on_error` rules (if defined)

### Error Handling

```yaml
- id: assert_login_success
  type: assert
  conditions:
    - expr: "${last.status}==200"
  on_error:
    - expr: "${last.status}==401"
      action: goto
      goto_step_id: login_get
    - expr: null
      action: abort
```

---

## 10.5 Type: `result`

### Purpose

* Define the final output of a scenario execution.
* Store extracted or computed values to be returned to the caller (API response or CLI output).
* Support template expansion for dynamic output composition.

### Additional Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `fields` | object | optional | Key-value pairs defining the output structure. Supports templates (`${...}`). |

### Use Cases

**1. Return Scraped Values**

Return reservation information extracted from a website.

```yaml
- id: result
  type: result
  fields:
    reservationNo: "${vars.reservationNo}"
    facilityName: "${vars.facilityName}"
    reservationDate: "${vars.selectDate}"
```

**API Response**:
```json
{
  "success": true,
  "result": {
    "reservationNo": "12345678901",
    "facilityName": "Meeting Room A",
    "reservationDate": "2026-02-10"
  }
}
```

**2. Return Computed Values**

Include both input and output values.

```yaml
- id: result
  type: result
  fields:
    input_facility_id: "${vars.facilityID}"
    input_dates: "${vars.dates}"
    output_reservation_no: "${vars.reservationNo}"
    status: "success"
```

**3. Return HTTP Response Details**

Include HTTP status or final URL for debugging.

```yaml
- id: result
  type: result
  fields:
    reservation_no: "${vars.reservationNo}"
    final_url: "${last.url}"
    http_status: "${last.status}"
```

**4. Return Multiple Items**

Return a list of extracted values.

```yaml
- id: result
  type: result
  fields:
    product_ids: "${vars.product_ids}"  # List from scraping
    total_count: "${vars.total_count}"
```

**5. Static and Dynamic Fields**

Mix static values with template expansion.

```yaml
- id: result
  type: result
  fields:
    status: "completed"
    timestamp: "${state.execution_time}"
    reservation_no: "${vars.reservationNo}"
    api_version: "1.0"
```

### Behavior

* **Execution**: Does not fail unless template expansion fails.
* **Storage**: Values are stored in the run context's `result` field.
* **Output**: Returned in the API response or CLI output under `result` key.
* **Templates**: All values support `${...}` template expansion.
* **Multiple Result Steps**: If multiple `result` steps are executed, the last one wins (overwrites previous results).
* **Secrets**: Do not include `${secrets.xxx}` in result fields (will be masked in logs but returned in output).

### Template Expansion

* `${vars.xxx}` - Input or scraped variables
* `${state.xxx}` - Intermediate state values
* `${last.status}` - HTTP status from last request
* `${last.url}` - Final URL from last request
* `${last.text}` - Response body (not recommended for large responses)

### Best Practices

1. **Place at End**: Typically the last or second-to-last step (before final assertions).
2. **Clear Naming**: Use descriptive field names for API consumers.
3. **Avoid Secrets**: Do not expose sensitive data in results.
4. **Document Output**: Document the expected output structure for API users.
5. **Type Consistency**: Ensure values have consistent types across executions.

### Example Scenario Flow

```yaml
steps:
  - id: login
    type: http
    request:
      method: POST
      url: /login
      form_list:
        - [username, "${secrets.USERNAME}"]
        - [password, "${secrets.PASSWORD}"]
  
  - id: scrape_user_info
    type: scrape
    command: css
    selector: span.user-id
    save_as: user_id
  
  - id: result
    type: result
    fields:
      user_id: "${vars.user_id}"
      login_status: "success"
```

---

## 10.6 Type: `log`

### Purpose

* Emit structured log messages during scenario execution.
* Provide visibility into execution progress and intermediate values.
* Support debugging and auditing with template expansion.

### Additional Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | string | required | Log message text. Supports templates (`${...}`). **Secrets are forbidden**. |
| `level` | string | optional | Log level: `info` (default), `debug`, `error`, `warning`. |
| `fields` | object | optional | Additional structured fields for log context (key-value pairs). |

### Use Cases

**1. Progress Indicator**

Log execution milestones.

```yaml
- id: log_start
  type: log
  message: "Starting reservation for facility ${vars.facilityID}"
  level: info
```

**2. Debug Values**

Inspect intermediate values during development.

```yaml
- id: log_debug
  type: log
  message: "Scraped reservation number: ${vars.reservationNo}"
  level: debug
```

**3. Structured Logging**

Add context fields for better log analysis.

```yaml
- id: log_reservation
  type: log
  message: "Reservation completed"
  level: info
  fields:
    reservation_no: "${vars.reservationNo}"
    facility_id: "${vars.facilityID}"
    dates: "${vars.dates}"
```

**Output**:
```json
{
  "type": "step.log",
  "level": "info",
  "message": "Reservation completed",
  "reservation_no": "12345678901",
  "facility_id": "001",
  "dates": ["2026-02-10", "2026-02-11"]
}
```

**4. Error Context**

Log errors with relevant context before failing.

```yaml
- id: log_error
  type: log
  message: "Login failed with status ${last.status}"
  level: error
  fields:
    url: "${last.url}"
    status: "${last.status}"
```

**5. Conditional Logging**

Combine with conditional execution (via previous step results).

```yaml
- id: log_retry
  type: log
  message: "Retrying request (attempt ${state.retry_count})"
  level: warning
```

### Template Expansion

Messages and fields support template variables:

* `${vars.xxx}` - Input or scraped variables
* `${state.xxx}` - Intermediate state
* `${last.status}` - HTTP status
* `${last.url}` - Last request URL
* **Forbidden**: `${secrets.xxx}` (will cause step failure)

### Security

**Secret Detection**:
* Templates referencing `${secrets.xxx}` are **rejected** at runtime
* Step fails with error: "Log templates must not reference secrets"
* This prevents accidental secret exposure in logs

**Safe Example**:
```yaml
- id: log_user
  type: log
  message: "Logged in as user ${vars.username}"  # OK: vars, not secrets
```

**Unsafe Example** (will fail):
```yaml
- id: log_credentials
  type: log
  message: "Using password ${secrets.PASSWORD}"  # ERROR: secrets forbidden
```

### Log Levels

| Level | Use Case |
| --- | --- |
| `debug` | Development/troubleshooting, verbose output |
| `info` | Normal execution progress, milestones |
| `warning` | Non-fatal issues, retries |
| `error` | Errors, failures (before abort) |

### Behavior

* **Execution**: Always succeeds unless template expansion fails or secrets are referenced.
* **Output**: Emitted to the configured logger (console, file, or structured log store).
* **Context**: Automatically includes `run_id`, `step_id`, `type` fields.
* **Timing**: Executed at the point where it appears in the step sequence.
* **Non-Blocking**: Does not affect scenario success/failure (unless template error occurs).

### Best Practices

1. **Use Info for Milestones**: Log major progress points at `info` level.
2. **Use Debug Sparingly**: Reserve `debug` for development; disable in production.
3. **Add Structured Fields**: Use `fields` instead of embedding data in message strings.
4. **Never Log Secrets**: Do not reference `${secrets.xxx}` in messages or fields.
5. **Log Before Critical Steps**: Add logs before potentially failing steps for debugging.

### Example Scenario Flow

```yaml
steps:
  - id: log_start
    type: log
    message: "Starting login sequence"
    level: info
  
  - id: login_post
    type: http
    request:
      method: POST
      url: /login
      form_list:
        - [username, "${secrets.USERNAME}"]
        - [password, "${secrets.PASSWORD}"]
  
  - id: log_login_result
    type: log
    message: "Login completed with status ${last.status}"
    level: info
    fields:
      status: "${last.status}"
      final_url: "${last.url}"
  
  - id: scrape_user_id
    type: scrape
    command: css
    selector: span.user-id
    save_as: user_id
  
  - id: log_user_id
    type: log
    message: "Extracted user ID: ${vars.user_id}"
    level: debug
```

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
