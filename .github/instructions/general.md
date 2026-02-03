---
applyTo: '**'
---

# General AI Instructions

## Language
- AI responses must be written in Japanese
- All code, comments, logs, exception messages, tests, and documentation must be written in English

---

## Environment
- Always activate the virtual environment before execution:
  source .venv/bin/activate
- Do not assume globally installed Python packages

---

## Technology
- Language: Python 3.x
- Architecture: Domain-Driven Design (DDD)
- Design principle: Polymorphism first
- Test creation is mandatory

---

## Coding Style (Modern)
- Use modern, idiomatic Python
- Prefer current best practices over legacy patterns
- Avoid outdated or verbose constructs
- Prioritize clarity, explicitness, and maintainability
- Actively refactor growing classes and responsibilities
- Split oversized classes or modules to preserve long-term maintainability

---

## Design Rules
- Do not extend functionality by adding large `if/elif` or flag-based branching
- Prefer abstractions (ABC / Protocol) and concrete implementations
- Extend behavior by adding new implementations, not modifying existing ones
- Avoid excessive use of `isinstance` (except at boundaries)

---

## Layering Rules
- Domain must not depend on other layers
- Application may depend only on Domain
- Infrastructure may depend on Domain and Application
- Presentation must use Application only

---

## Testing
- Every implementation change must include tests
- Use pytest
- Bug fixes must start with a failing reproduction test
- Domain tests should be fast and isolated
- Application tests must mock ports and validate use cases

---

## Restrictions
- Do not break existing public APIs
- Do not perform unrelated refactoring
- Prefer maintainability over preserving oversized structures

## Documentation Restrictions
- Do not create new documentation files unless explicitly requested
- Do not update README or docs as a side effect of code changes
- Do not add explanatory documents for implemented code
