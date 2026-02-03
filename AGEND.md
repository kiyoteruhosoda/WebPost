# AGEND.md (AI Coding Instructions)

## 0. Language Rules
- **AI responses must be written in Japanese**
- All other content must be written in **English**:
  - Source code
  - Comments
  - Exception messages
  - Logs
  - Test names and descriptions
  - Documentation inside the repository

---

## 1. Documentation Style
- This document defines **policies and rules only**
- Do not include background or educational explanations
- Keep each rule concise and directive
- Avoid redundancy and narrative descriptions

---

## 2. Implementation Style (Modern)
- Use **modern, idiomatic Python**
- Prefer current best practices over legacy patterns
- Avoid outdated or verbose constructs
- Write code as if targeting **current production standards**
- Favor clarity, explicitness, and maintainability
- **Actively refactor growing classes and responsibilities**
- **Split large classes or modules to maintain long-term maintainability**

## 2+. Runtime Environment
- All commands must be executed after activating the virtual environment
- Always run:
  source .venv/bin/activate
- Do not assume global Python packages
---

## 3. Premises
- Language: Python 3.x
- Architecture: Domain-Driven Design (DDD)
- Design principle: Polymorphism first
- **Test creation is mandatory**

---

## 4. AI Working Procedure (Mandatory)
1. Decompose change requests into **Purpose / Constraints / Acceptance Criteria**
2. Identify impact scope in order: Domain → Application → Infrastructure → Presentation
3. Decide implementation strategy:
   - Do not solve by increasing `if/elif`
   - Prefer **Interface (Protocol / ABC) + concrete implementations**
4. Apply changes with minimal diff
5. **Add or update tests**
6. Ensure all existing tests and static checks pass

---

## 5. DDD Layering Rules (Mandatory)

### 5.1 Dependency Direction (Strict)
- Domain must not depend on other layers
- Application may depend only on Domain
- Infrastructure may depend on Domain and Application
- Presentation must call Application only (no direct Infrastructure access)

### 5.2 Domain Layer
- Entities / Value Objects / Domain Services / Domain Events
- Business rules and validations
- Abstractions for polymorphic behavior (ABC / Protocol)

### 5.3 Application Layer
- Use cases as orchestration units
- Transaction boundaries if required
- Input / Output DTOs
- Ports (repository interfaces, external service interfaces)

### 5.4 Infrastructure Layer
- Repository implementations
- External API clients
- Database access and configuration
- Persistence details must not leak to Domain or Application

### 5.5 Presentation Layer
- CLI / API / Web I/O
- Mapping between external requests and use case inputs
- Mapping between use case outputs and responses

---

## 6. Polymorphism First Rules

### 6.1 Prohibited
- Feature extension via large `if/elif` or flag-based branching
- Excessive use of `isinstance` (except at boundaries)

### 6.2 Recommended Patterns
- Strategy / State / Factory / Visitor
- Abstract differences in Domain using `abc.ABC` or `typing.Protocol`

Examples:
- Extract abstractions such as `PricingPolicy`, `DiscountRule`,
  `NotificationChannel`, `AuthMethod`
- Extend behavior by adding new implementations, not modifying existing ones

---

## 7. Naming and Coding Rules
- Classes: PascalCase
- Functions / variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Exceptions: names must end with `Error`
- Type hints are mandatory
- `dataclasses` may be used appropriately
  - Avoid overuse in Domain models

---

## 8. Error and Exception Handling
- Domain: rule violations raise Domain-level exceptions
  - e.g. `ValidationError`, `InvariantError`
- Application: use case failures may be aggregated into Application exceptions
- Presentation: convert exceptions into user-facing representations
  - e.g. messages, HTTP status codes
- Do not swallow exceptions
- Logging and conversion must be handled at layer boundaries

---

## 9. Testing Rules (Mandatory)

### 9.1 Required
- Every implementation change must include tests
- Bug fixes must follow:
  - Reproduction test → Fix → Passing test
- Refactoring must preserve behavior with regression tests

### 9.2 Style
- Use `pytest`
- Follow AAA pattern (Arrange / Act / Assert)
- Mock external I/O using `unittest.mock` or equivalent
- Domain tests must be fast and isolated
- Application tests must mock ports and validate use cases
- Infrastructure tests may be integration tests and separated if slow

### 9.3 Coverage Policy
- High coverage for critical domain logic
- Include boundary and exception cases
- Do not inflate coverage with trivial getters/setters

---

## 10. Existing Code Protection (Mandatory)
- Do not break existing public APIs
  - Function signatures
  - Return types
  - Public class attributes
- Behavior changes must include comments explaining:
  - Reason
  - Impact scope
- Do not perform unrelated formatting or large-scale renaming

---

## 11. Change Log (Optional but Recommended)
- For significant changes, record:
  - Purpose
  - Summary of changes
  - Added or updated tests
  - Compatibility impact, if any

---
