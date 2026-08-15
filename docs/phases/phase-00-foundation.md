# Phase 00 — Project Foundation

Status: **COMPLETED**

## Objective
Establish the coding standards, folder structure, validation rules, test runner, and development environment setup to build a stable codebase for the WealthNest mutual fund aggregator.

## Why this phase exists
Before writing complex PDF parsers or calculations, we must align on clean architecture constraints, choose deterministic typing paradigms (e.g. `Decimal`), and implement linting standards.

## Scope
- Git repository setup
- Test framework installation (`pytest`)
- Development guidelines (formatting via `black`, typing via `mypy`)
- Pydantic models architecture
- Basic configuration structure

## Tasks
- [x] Create project layout
- [x] Configure standard requirements and dev-dependencies
- [x] Set up base Git configuration and `.gitignore`
- [x] Implement pytest framework verification

## Technical Design
We chose to organize the source code inside a `cas-parser/` directory containing Pydantic-based schemas (`app.models`) and logic modules (`app.parser`), keeping unit tests cleanly aligned in `tests/`.

## Input
Developer environment config.

## Output
A working local development loop.

## Validation
Verified using small test dummy runner:
```bash
pytest tests
```

## Tests
- Verification tests ensuring model structures can load Pydantic attributes.

## Known Limitations
None.

## Decisions
- Used Pydantic v2 for parsing and validating JSON structures.
- Enforced python 3.11+ to utilize modern dict/typing optimizations.
- Enforced strict `Decimal` usage for all financial numbers.

## Future Improvements
Continuous integration (CI) workflows for automatic verification testing on Git push.

## Completion Criteria
- Developer can clone repo and run test suite successfully.
- Code style is fully standardized.
