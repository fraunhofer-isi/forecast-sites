<!--
SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
SPDX-License-Identifier: AGPL-3.0-or-later

AI-assisted code generation was used during development.
-->

# Agent Instructions: Production Code

Conventions for everything below `src/`.
For global rules see [AGENTS.md](../AGENTS.md), for tests see [test/AGENTS.md](../test/AGENTS.md).
The user-facing description of the model lives in [README.md](../README.md#architecture).

## Abstraction levels

The model hierarchy defines the abstraction levels. Higher levels orchestrate, lower levels compute.
Never let a lower level reach back up.

```
Region              scenario and region wide data: carrier availability, prices, CO2 cost
  Site              geographic location, shared carrier pool, H2 accessibility
    ProductionUnit  owns sub production units, holds the optimization result
      SubProductionUnit   one installed process with a reinvestment year
        Process           techno-economic data, cost and emission calculations
          Demand / Output  carrier amounts consumed or produced per process execution
            Carrier        EnergyCarrier, Product, ByProduct
```

Orthogonal to the hierarchy:

| Concern | Location | Level |
|---|---|---|
| Optimization | `src/optimization/` | coordination: builds LP objective and constraints |
| Result collection | `src/result/` | coordination: Visitor pattern over the hierarchy |
| Data access | `src/data_layer/`, `src/input/` | boundary: SQLite and CSV |
| Pure arithmetic | `*_calculator.py` | implementation detail |

**Rule:** a coordination-level module must not perform domain arithmetic. If you find a formula in
`src/optimization/`, it belongs in a calculator or on the domain object.

## Patterns in use

- **Factory** — construction is separated from the model: `RegionFactory`, `SiteFactory`,
  `ProductionUnitFactory`, `ProcessFactory`, `EnergyCarrierFactory`. Entities do not build their own
  children.
- **Visitor** — result processing is separated from the hierarchy. New outputs are added by
  inheriting from `Visitor` and implementing `visit_*` / `enter_*` / `exit_*`, never by adding
  reporting code to domain classes.
- **Calculator objects** — `ProcessFinancialCalculator`, `ProcessEmissionCalculator`,
  `ProcessProductionConsumptionCalculator`, `RegionCarrierCalculator`. Domain objects fetch their
  data and delegate the arithmetic.
- **Adapter at boundaries** — `DataInterface` wraps SQLite. Third-party types must not leak into the
  domain.

## CAPEX and investment funding

This is a load-bearing convention; it was lost once in a merge and silently changed all investment
decisions.

**One source of truth:** `ProcessFinancialCalculator.net_investment(capex, funding, capex_factor)`
returns `max(capex * capex_factor - funding, 0.0)`. Nothing else may compute `capex - funding`.

```
ProcessFinancialCalculator.net_investment            pure arithmetic
  Process.net_capex_in_euro_per_process_count        fetches interpolated capex + funding, delegates
    Process.invest_cost_in_euro_per_process_count    polymorphic entry point
      InstalledProcess.invest_cost_...               age-dependent repair cost, ignores the factor
        three LP objective builders                  pass capex_factor, no arithmetic
```

**The factor scales the CAPEX before the funding is deducted.** `start_year_capex_factor` (default
5.0) is a calibration penalty against unrealistic technology switching in the start year. Deducting
the funding first would yield zero for a fully funded process and silently disable the penalty:

```
capex 1000, funding 1000, factor 5.0
  correct:  max(1000 * 5 - 1000, 0) = 4000
  wrong:    (1000 - 1000) * 5       = 0
```

**No `isinstance` checks for the CAPEX factor.** `InstalledProcess` ignores `capex_factor` itself
(parameter named `_capex_factor`), so callers pass the factor unconditionally. Do not reintroduce
`if not isinstance(process, InstalledProcess)` into the objective builders *to decide the factor*.

The rule is about the factor only. `region_multi_period_optimization._build_objective` legitimately
uses `isinstance(process, InstalledProcess)` to zero the `new_capacity` coefficient, because an
existing plant cannot be newly built. That check is correct; do not remove it.

The two objective builders share the CAPEX and funding arithmetic:

- `region_multi_period_optimization._build_objective` (uses `net_capex_...`, salvage value is based
  on the same net amount)
- `linear_programming_model_builder._invest_process_cost_in_euro_per_process_count`

**The arithmetic is synchronized; the horizon treatment is deliberately not.** Do not "harmonize"
the salvage value across them — see the next section for why.

## Investment horizon: why only the multi-period path has a salvage value

Decided by the domain owner; the reasoning is recorded in `bd show forecast-sites-private-6zj.18`.

| | `REGION_MULTI_PERIOD` | `LINEAR_PROGRAMMING`, `REGION_LINEAR_PROGRAMMING` |
|---|---|---|
| Horizon | one global observation period | rolling, re-solved per step |
| Investment term | `net_capex * discount - salvage` | `net_capex`, full amount |
| Discounting | `1/(1+r)^(year - start year)`; the investment sits in a future period | none needed; the investment falls in the current year, which *is* the discount base |

A salvage value only accrues at the **end of a single global observation period**, and only the
multi-period formulation has one. Deducting salvage inside a rolling horizon would require the
opposite entry as well — writing down residual value when a plant closes early — which the rolling
formulation does not model. Charging the full net CAPEX is therefore the self-consistent choice
there, not an oversight. Apart from the salvage term the two families behave identically.

Accepted consequence: with the shipped defaults (`rolling_planning_horizon_in_years = 1`,
`year_increment = 5`) `_planning_years` yields two years, so a new plant must earn its whole CAPEX
from two years of margin. `start_year_capex_factor` is a separate penalty that applies to the start
year only. Both are intended calibration, not defects.

There is no annuity correction anywhere, and none is wanted.

## The investment funding input

Four deliberate properties, decided by the domain owner; reasoning in
`bd show forecast-sites-private-6zj.19`. None of these is an oversight.

| Property | Behavior |
|---|---|
| Shape over time | **linear**, start-year and end-year value only |
| Unit | **absolute euro per process count**, not a share of the CAPEX |
| Applies to | **new plants only** |
| Negative result | **capped at zero** |

`process_data.investment_funding_interpolation_data_in_euro_per_process_count` is built without an
interim year, so the funding follows a straight line over the whole simulation. Do not "fix" this by
adding one.

For orientation: of the fifteen `InterpolationData(...)` call sites in `src/`, the energy carrier
**subsidies** are the only one that passes a third value for an interim year. CAPEX, OPEX,
investment funding, taxes, minimum use, upstream emissions and efficiency improvement are all plain
two-point lines. So the funding is not an outlier — the subsidies are.

Because the input is an absolute amount, the effective funding rate drifts silently whenever the
CAPEX changes over time. Accepted.

`InstalledProcess.invest_cost_in_euro_per_process_count` returns the age-dependent repair cost and
**ignores the funding**, so funding never subsidizes life extension of existing units.

The capping at zero in `net_investment` is not a defensive guard against bad input — it *is* the
mechanism that enforces "funding never exceeds CAPEX". Do not add input validation for this.

## Cost bases: capacity versus utilization

Capital costs are charged on installed capacity, variable costs on actual utilization. Decided by
the domain owner; reasoning in `bd show forecast-sites-private-6zj.12`.

In `sub_production_unit/sub_production_unit.py`:

| Term | Base |
|---|---|
| `annuity_on_investment_in_euro` | `max_process_execution_count` |
| `new_investment_in_euro` | `max_process_execution_count` |
| `opex_in_euro` | `process_execution_count` |
| direct emissions | `process_execution_count` |
| process production cost | `process_execution_count` |

This is a consistent split, not an inconsistency between two methods.

**Beware when testing:** `sub_production_unit_factory` has a construction path that sets
`max_process_execution_count` equal to `process_execution_count`. A test built through that path
cannot tell this behavior apart from the alternative, so pick a unit where the two differ.

## Downstream CO2 is internalized by the producer

Decided by the domain owner; reasoning in `bd show forecast-sites-private-6zj.11`.

```
emission_adjusted_price = sell_price - downstream_emission * co2_price
```

The producer carries the downstream CO2 cost of sold quantities in the objective function, which
makes a carrier with a high downstream factor less attractive to produce and sell. That price signal
is intended.

**The scope asymmetry is also intended.** The objective function prices downstream CO2
*unconditionally*, while the emission constraint only counts it when `'downstream'` appears in
`emission_constraint_scope`. All four carrier classes declare
`downstream_emission_in_t_co2_per_unit(self, _year, _simulation_options)` with both parameters
unused, so the price side never consults the scope. Removing `'downstream'` from the scope therefore
drops the **constraint** while the **price signal remains**.

Gross terms cancel between the objective and the constraint only because all seven output and demand
implementations use the same formula; the netting is **emergent, not explicit**. If one
implementation loses its `- ds * co2` term, it breaks silently.
`test/processes/test_process_downstream_emission_netting.py` exists to catch that.

## Shared carrier pools

Purchases are deducted from the shared pool; **production does not replenish it**. `Site.pool` is the
`Region`, `Site.shared_pool_for(carrier)` returns it, and `Group` is a minimal data container without
pool logic. Do not add a `provide_produced_carrier_amount` chain back in — that is a different
modeling decision and the integration tests pin the current one.

## ID naming: the Option B pattern

New classes inherit from `Entity` and use its generic `.id`. Where a class needs additional *semantic*
IDs, expose them as properties over private storage rather than as public attributes:

```python
class DataInterface:
    def __init__(self, id_scenario: int, id_region: int) -> None:
        self._id_scenario = id_scenario
        self._id_region = id_region

    @property
    def id_scenario(self) -> int:
        """Explicit semantic access to the scenario ID."""
        return self._id_scenario

    @id_scenario.setter
    def id_scenario(self, value: int) -> None:
        self._id_scenario = value
```

Rules:

- Private name mirrors the property name: `_id_scenario` ↔ `id_scenario`.
- Add the setter whenever existing code assigns the attribute; otherwise the refactoring breaks
  callers.
- Always add type hints and a one-line docstring.
- Do not apply this to classes that already get `.id` from `Entity` and need nothing more.

Why properties over plain attributes: semantic clarity (`id_scenario` says what kind of ID it is),
encapsulation, and a single place to add validation later. The runtime cost is negligible.

## `simulation_options` is immutable; loop variables are explicit parameters

`simulation_options` is global configuration, loaded once in `main()` and read, never written, by
everything downstream. A per-iteration value — one scenario out of `scenario_ids`, one region out of
`region_ids` — is **not** a configuration option and must never be written back into the dict.

`RegionFactory` is the reference pattern:

```python
def create_regions(self):
    region_ids = self._simulation_options['region_ids']   # filter: plural, lives in options
    for id_region in region_ids:
        region = self._create_region(id_region)           # current: singular, explicit parameter

def _create_region(self, id_region):
    data_interface = DataInterface(self._id_scenario, id_region, self._simulation_options)
```

`main()`'s scenario loop mirrors it exactly — `id_scenario` travels as an explicit `int` argument to
`_simulate` and `export_product_route_shares`, never by rebuilding the options dict:

```python
for id_scenario in simulation_options['scenario_ids']:
    _simulate(id_scenario, simulation_options)
    export_product_route_shares(id_scenario, simulation_options)
```

**Do not write** `{**simulation_options, 'id_scenario': id_scenario}`. A prior version of this file
did exactly that, which silently narrowed `id_scenario` from `list[int]` to `int` partway through the
call stack — three modules relied on the override already having happened and would have broken (or
silently returned wrong results, e.g. a shapefile folder suffix of `_scenario_[1]`) if called before
it. See `bd show forecast-sites-private-y80` (decision record) for the full history.

A visitor that is handed the model it is visiting reads state from the model, not from options:
`ShapeFileVisitor._shape_file_path` takes the `region` it already receives in `enter_region` and
reads `region.id_scenario`, exactly like `IndexingVisitor` does. Only code with no model reference —
the top-level scenario loop, the IAMC export path — needs the id injected as a parameter.

## Interpolation

Year-dependent techno-economic values come from `InterpolationData` (start year, end year, optional
interim year) and are resolved through `interpolation.interpolator.interpolate(year, options, data)`.
Never interpolate by hand.

## Boundaries and resources

- All paths in `src/simulation_options.toml` are relative to the **project root**; run commands from
  there.
- Never hardcode absolute or machine-specific paths. CLI helper scripts use `argparse`.
- Never commit generated artifacts (`results/`, `resources/input/input.sqlite`).

## Language

American English for all identifiers, comments, docstrings and log messages. German strings have been
removed from this codebase; do not reintroduce them.

## Known deviations

Three modules exceed the 500 line limit: `result/collecting_result_visitor.py` (705),
`production_unit/production_unit.py` (501) and `optimization/linear_programming_model_builder.py`
(430). `collecting_result_visitor.py` is the dominant offender on every metric at once — it also
holds the two longest functions in the codebase and 40 methods — so it is the one to split first.

These are pre-existing and tracked as technical debt; do not split them opportunistically in the
middle of unrelated work, and re-measure before acting on any number quoted here.
