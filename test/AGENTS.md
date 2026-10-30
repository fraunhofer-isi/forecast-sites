<!--
SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
SPDX-License-Identifier: AGPL-3.0-or-later

AI-assisted code generation was used during development.
-->

# Agent Instructions: Tests

Conventions for everything below `test/` and `test_integration/`.
For global rules see [AGENTS.md](../AGENTS.md), for production code see [src/AGENTS.md](../src/AGENTS.md).

## Layout

`test/` mirrors `src/` one to one:

```
src/optimization/comparing_optimization.py
test/optimization/test_comparing_optimization.py
```

| Artifact | Convention |
|---|---|
| File | `test_<module>.py` |
| Class | `Test<SourceClass>` |
| Method | `test_<specific_behavior>` |

`test/` holds isolated unit tests. `test_integration/` holds tests that build real objects from
`test_integration/conftest.py` fixtures. Both suites must stay green:

```bash
pytest test test_integration -q
```

Test coverage is expected to stay at 100 %. Run `pytest --cov` before handing off.

## Project-specific helpers

Use `test_utils`, not `unittest.mock` directly.

### `Mock` from `test_utils.isi_mock`

A `MagicMock` with a shorthand: the first positional argument becomes the `return_value`.

```python
from test_utils.isi_mock import Mock

sut.installed_process.net_capex_in_euro_per_process_count = Mock(20)  # returns 20 when called
```

### `patch` from `test_utils.isi_mock`

`patch` takes the **object**, never a string path. Passing a string raises `KeyError` on purpose,
so that renames are caught by the import instead of failing silently at runtime.

```python
from test_utils.isi_mock import patch

@patch(MesaSimulation._optimize_regions)
@patch(MesaSimulation._create_time_span, [2020, 2021])
def test_step_with_region_scoped_optimization(self): ...
```

Only patch what the tested code path actually reaches. A decorator for a method that is never
called on that path is dead weight and breaks at collection time once the method is renamed or
removed — this is exactly how the suite was broken before the merge cleanup.

### `make_process_data_stub` from `test_utils.process_data_stub`

Builds a `ProcessDataStub` with sensible defaults; pass only what the test cares about.

```python
process = make_process_data_stub(lifetime_in_years=15, depreciation_period=30)
```

Derive expected values from the stub instead of hardcoding them, so changed defaults do not
silently invalidate the assertion:

```python
lifetime = installed_process.lifetime_in_years
factor = installed_process.life_extension_factor
assert installed_process._capex_age_factor(lifetime + 10) == pytest.approx(factor * 10)
```

## Mocking

- Mock **boundaries** (database, file system, external libraries), not internal domain logic.
- Prefer `Mock(spec=TheClass)` so typos in attribute names fail the test instead of passing.
- Build reusable mocks as `@pytest.fixture`, one fixture per concept.
- Over-mocking is a smell: if a test needs five chained mocks to express its setup, the unit under
  test probably has too many collaborators.

## Assertions

- Arrange / Act / Assert, visually separated.
- Floating point: always `pytest.approx` or an explicit tolerance, never `==`.
- Assert **behavior**, not internals. `factory.get('Widget') == process` instead of
  `factory._processes_dict['Widget'] == process`.
- Every test needs at least one assertion. A test without an assertion always passes and is worse
  than no test.
- Use `@pytest.mark.parametrize` instead of copy-pasted near-identical tests.

## Fresh state per test

Never share mutable state across test methods via `setup_method` or class attributes. Use fixtures,
so each test gets a new instance and the suite stays order-independent.

## Error paths

Use `pytest.raises` and assert on the message where the message carries information:

```python
with pytest.raises(ValueError, match='must not be negative'):
    sut.apply(-1)
```

## Pinning intentional behavior

When a behavior is a deliberate modeling decision rather than an obvious truth, say so in the test
name and docstring. Such tests are the specification; the next agent must not "fix" them away.

Current examples in this repository:

- `test_fully_funded_process_stays_penalized_in_start_year` pins that the start year CAPEX factor
  scales the CAPEX *before* the investment funding is deducted.
- The pool delta integration tests pin that production does **not** replenish shared pool
  availability; only purchases are deducted.
- `test_capex_age_factor_*` pin the age-dependent repair cost model for installed processes.

## Known deviation

Many test modules group several `Test*` classes in one file, which violates the global
one-class-per-file rule. This is an accepted pattern for tests; see the open technical debt issue
before changing it wholesale.
