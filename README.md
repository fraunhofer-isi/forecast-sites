<!-- SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- AI-assisted code generation was used during development. -->

# FORECAST-Sites - A technology diffusion model to simulate industry transformation scenarios with high spatial resolution for energy-intensive industry branches

This repository contains the complete model code of the `FORECAST-Sites` modelling approach for technology diffusion
scenarios for energy-intensive industries.
The provided model framework is related to the following publication in the journal Scientific Reports:
<a href="https://www.nature.com/articles/s41598-024-78881-7">Scientific Reports - Neuwirth et al. 2024</a></p>
The development of the framework was conducted within the Horizon Europe project <a href="https://www.transience.eu/">
Transience</a> under grant agreement No. 101137606.
Within this repository also a first part of Fraunhofer ISI IndustrialSiteDatabase for European primary steel and basic
chemical (high value chemicals (HVC), ammonia, and methanol) is published to directly start exporting scenarios for
those
industry branches.

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Visualization](#visualization)
7. [Output files for energy system modellers](#output-files-for-energy-system-modellers)
8. [Contributing](#contributing)
9. [Badges](#badges)
10. [Architecture](#architecture)
11. [Contact](#contact)
12. [Licenses](#licenses)
13. [Notes](#notes)

## Introduction

Welcome to the Technology Diffusion Model in Energy-Intensive Industries repository. This project aims to provide a
comprehensive model for studying the diffusion of new technologies within energy-intensive sectors such as steel,
cement, and chemical industries. The model helps in understanding how new technologies are adopted over time and their
impact on energy consumption and greenhouse gas emissions.

## Features

- **Site-specific investments**: Models the site-specific investments based on techno-economic decisions according to
  scenario assumptions.
- **Energy demand development**: Shows the spatially highly resolved development and correlation of process adoption and
  energy usage.
- **Industrial process diffusion**: Evaluates the possible ramp-up of climate-neutral industry processes according to
  energy price projections and scenario frameworks.
- **Customizable Parameters**: Allows customization for different industries and scenario assumptions, such as energy
  price projections and different policies.
- **Visualization Tools**: Provides an interactive browser-based map of the modelled sites and a time-series chart of
  process adoption while the simulation runs, plus tabular result files for your own analysis (see
  [Output files for energy system modellers](#output-files-for-energy-system-modellers)).

## Installation

The installation of the model follows typical Git and Python based schemes.

### Prerequisites

- Python 3.12 or higher
- Nodejs 23.5.0 or higher
- Git
- Python package requirements (see pyproject.toml file)
- Node package requirements (see web/package.json)

### Steps

1. Clone the repository:
   `git clone https://github.com/fraunhofer-isi/forecast-sites.git`
2. Navigate to the project directory:
   `cd forecast-sites`
3. Install the required python packages:
   `pip install .[dev]`
4. Install the required nodejs packages:
   
   ```
   cd web
   npm install
   ```

## Usage

1. Provide and configure the model input:

- The repository ships a small **example input set** under `resources/input/por`, covering a single
  refinery site in the Rotterdam area across four scenarios. The shipped defaults in
  [simulation_options.toml](src/simulation_options.toml) already point at it
  (`region_ids = [18]`, `input_mode = "CSV"`), so the model runs on a fresh clone without further
  setup. Use it to verify your installation and as a template for the table layout.
- The input is read either from CSV or from SQLite, selected by `input_mode`. With `"CSV"` the files
  in `csv_input_directory` are imported into `database_path`
  (`./resources/input/input.sqlite`) on every start; that database is generated and therefore not
  part of the repository. With `"SQLITE"` an existing database at `database_path` is used directly.
- To model your own sites, replace or extend the CSV files. `check/check_csv_integrity.py` imports a
  CSV directory and reports foreign key violations, which is the quickest way to validate an edit:

  ```
  python check/check_csv_integrity.py resources/input/por
  ```

- Manipulate or change the industry site and process information by navigating through the different tables
  - Techno-economic process information can be seen and changed in the table `process`

2. Configure the modelled products and regions you want to simulate:

- Open the `src/simulation_options.toml` file
- Change `id_product_filter` and `region_ids` according to your wishes
- Activate or deactivate the consideration of hydrogen infrastructure according to plans from the European Hydrogen
  Backbone initiative
- Select the optimization type: `REGION_MULTI_PERIOD`, `LINEAR_PROGRAMMING` or `COMPARING`

3. Configure scenario parameters like CO2-pricing:

- Open the `src/simulation_options.toml` file
- Change the values and the interpolation functions between your adjusted start and end year of the simulation
  accordingly

4. Start program

`python src/main.py`

## Configuration

The input database and its tables allow you to customize several parameters:

- `industry site information`: Add, adjust or delete industry sites with their necessary information on:
  - Geolocation (longitude, latitude) within the `site` table,
  - Production units within the `production_unit` table, and their installed processes with capacity and
    reinvestment year within the `sub_production_unit` table.
- `process information`, all in the `process` table:
  - Capital expenditures (CAPEX), as `capex_start_year_in_euro_per_process_count` and the matching end year value
  - Operational expenditures (OPEX), likewise as start and end year values
  - Investment funding, as `investment_funding_start_year_in_euro_per_process_count` and its end year value
  - Lifetime (`lifetime_in_years`), depreciation period and life extension factor
  - Optional: efficiency gains over years (`efficiency_improvement_start_year` and its end year value) and the
    non-energy process emission factor
- `process demands and outputs`, each in its own mapping table, all per process count:
  - `process_energy_carrier_energy_demand_in_gj_per_process_count`
  - `process_energy_carrier_feedstock_demand_in_gj_per_process_count`
  - `process_product_feedstock_demand_in_t_per_process_count` and
    `process_by_product_feedstock_demand_in_t_per_process_count`
  - `process_energy_carrier_output_in_gj_per_process_count`,
    `process_product_output_in_t_per_process_count` and
    `process_by_product_output_in_t_per_process_count`
- `scenario information`:
  - Energy carrier prices in `energy_carrier_purchase_price_in_euro_per_gj` and
    `energy_carrier_sell_price_in_euro_per_gj`
  - Energy carrier emission factors in `energy_carrier_emission_in_t_co2_per_gj`
  - Energy carrier availability, minimum use, subsidies and taxes in the correspondingly named tables
  - Product prices and emissions in `product_purchase_price_in_euro_per_t`,
    `product_sell_price_in_euro_per_t` and `product_emission_in_t_co2_per_t`
  - Pipeline/infrastructure information in the file [pipelines.py](src/pipelines/pipelines.py)

### Modelling planned future investments

A plant that is already decided but not yet built is expressed through the
`year_of_last_reinvestment` column of the `sub_production_unit` table. The column accepts any year:

| Value | Meaning |
|---|---|
| a past year | the unit exists and is operating |
| a future year | the unit is planned and becomes available in that year |

Three consequences follow, so no separate "is future" flag is needed:

- **Availability.** The unit counts as available exactly from its reinvestment year onwards
  (`year_of_last_reinvestment <= year`). Before that year it cannot be used.
- **Annuity.** No annuity is charged before the reinvestment year, so a decision taken today does
  not burden today's costs.
- **New investment.** The investment is booked in the reinvestment year itself, on the installed
  capacity `max_process_execution_count`.

A planned unit is also protected from the inactivity cleanup: a unit that has gone unused for more
than four years is normally retired, but a unit whose reinvestment year still lies ahead is kept.

## Visualization

To visualize the results, the model is provided by a live-visualization based on the mesa package on a openstreetmap
within an automatically opened tab in the browser.
All results are saved within a timestamped folder below `results/` (see `rolling_output_directory_prefix` in
`src/simulation_options.toml`) as `output.sqlite` and individual Excel files.

The runtime of the model is generally quite short and depends on the amount of regions, sites, and products modelled.
For modelling primary steel and basic chemicals in entire Europe, the runtime is approximately 10 minutes.

## Output files for energy system modellers

This section explains the files a model run produces and how to use them for coupling with energy system models.

### The output directory

Each run creates a timestamped output directory containing:

- `output.sqlite` — the primary result database,
- one `.xlsx` file per output table,
- `simulation_options.toml` — a copy of the configuration used for the run,
- yearly shape file folders such as `shape_file_2025/` for geographic visualization.

### `output.sqlite` is the primary source

At the start of a run the complete input database is copied into the output directory as
`output.sqlite`. All result tables are then added to that same database. This makes the output
**self-contained**:

- all input assumptions used for the run are preserved,
- all result tables sit next to them,
- and the ID mapping tables needed to interpret the results are already included.

Result tables reference entities by integer IDs (`id_scenario`, `id_region`, `id_site`, `id_sector`,
`id_production_unit`, `id_sub_production_unit`, `id_process`, `id_energy_carrier`, `id_product`,
`id_by_product`). Join them against the corresponding `id_*` tables, which follow a simple
`id` / `name` structure, to recover readable names.

Use `output.sqlite` if you work in Python, R, SQL or Julia, want reproducible extraction, need to
join results with mapping tables, or want to prepare inputs for another model.

### Excel files are a convenience mirror

For every result table an Excel file with the same name is written, for example
`region_energy_carrier_total_demand_in_gj.xlsx`. They are convenient for manual inspection and
sharing, but they contain only the table itself — **not** the ID mappings. For serious model coupling
treat SQLite as the primary source and Excel as a mirror.

### Year column convention

The two sides of the database use different year column names:

| Table kind | Year columns |
|---|---|
| Input tables | `2025`, `2030`, `2040` |
| Output result tables | `Y2025`, `Y2030`, `Y2040` |

### Gross (brutto) vs net (netto) energy demand

This distinction is essential and decides which tables you should read.

| Concept | Table suffix | Meaning |
|---|---|---|
| **Gross / brutto** | `total_demand_in_gj` | Energy required by the modeled industrial processes — internal process demand |
| **Net / netto** | `purchased_amount_in_gj` | Energy purchased from outside the modeled system boundary — external supply requirement |

The two differ because the model may include internal production of carriers, internal conversion
chains, exports, feedstock transformations and multi-step industrial routes.

- Use **gross** demand to understand process-side energy use inside industry.
- Use **net** demand to couple to power, hydrogen, gas or multi-energy system models.

For most coupling to external energy system models, **net demand is the right starting point**.

### Most relevant tables for coupling

| Table | Resolution | Content |
|---|---|---|
| `region_energy_carrier_purchased_amount_in_gj` | scenario, region, carrier | **Net** energy demand — the single most important coupling table |
| `sector_energy_carrier_purchased_amount_in_gj` | scenario, region, sector, carrier | Net energy demand by sector |
| `region_energy_carrier_total_demand_in_gj` | scenario, region, carrier | Gross energy demand |
| `sector_energy_carrier_total_demand_in_gj` | scenario, region, sector, carrier | Gross energy demand by sector |
| `region_direct_emission_in_t_co2` | region | Direct CO2 emissions |
| `sector_direct_emission_in_t_co2` | region, sector | Direct CO2 emissions by sector |
| `region_captured_emission_in_t_co2` | region | Captured CO2 quantities |
| `sector_captured_emission_in_t_co2` | region, sector | Captured CO2 by sector |

Every table listed above also exists as an `.xlsx` file of the same name.

## Contributing

We welcome contributions to enhance the model or add new features. Please follow these steps:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-branch`.
3. Make your changes and commit them: `git commit -am 'Add new feature'`.
4. Push to the branch: `git push origin feature-branch`.
5. Create a Pull Request.

## Badges

Click on some badge to navigate to the corresponding **quality assurance** workflow:

### Formatting & linting

[![lint](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/lint.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/lint.yml)
Checks Python code formatting with [ruff](https://docs.astral.sh/ruff/)

[![naming_conventions](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/naming_conventions.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/naming_conventions.yml)
Checks Python folder and file names to be snake_case.

[![web_lint](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_lint.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_lint.yml)
Checks JavaScript code formatting with [ESlint](https://eslint.org/)

### Test coverage

[![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/fhg-isi/4bb6f7ce335564341b0181db14bdc98f/raw/forecast-sites_test_coverage.json)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/coverage.yml)
Determines Python test coverage with [pytest-cov](https://github.com/pytest-dev/pytest-cov)

[![web_coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/fhg-isi/4bb6f7ce335564341b0181db14bdc98f/raw/forecast-sites_web_coverage.json)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_test_coverage.yml)
Determines JavaScript test coverage with [jest](https://jestjs.io/)

### License compliance

[![license_check](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/license_check.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/license_check.yml)
Checks Python license compatibility with [LicenseCheck](https://github.com/FHPythonUtils/LicenseCheck)

[![web_license_check](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_license_check.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_license_check.yml)
Checks JavaScript license compatibility with [license-checker](https://github.com/davglass/license-checker)

[![reuse_annotate](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/reuse_annotate.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/reuse_annotate.yml)
Creates copyright & license annotations with [reuse](https://git.fsfe.org/reuse/tool)

[![reuse compliance](https://api.reuse.software/badge/github.com/fraunhofer-isi/forecast-sites)](https://api.reuse.software/info/github.com/fraunhofer-isi/forecast-sites)
Checks for REUSE compliance with [reuse](https://git.fsfe.org/reuse/tool)

### Dependency updates & security checks

[![renovate](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/renovate.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/renovate.yml)
Updates dependencies with [renovate](https://github.com/renovatebot/renovate)

[![CodeQL](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/github-code-scanning/codeql)
Discovers vulnerabilities with [CodeQL](https://codeql.github.com/)

## Architecture

This section describes the frameworks and design patterns used in the code.

### Mesa

[mesa](https://github.com/projectmesa/mesa) is a python framework for agent-based
modeling. [mesa-geo](https://mesa-geo.readthedocs.io/stable/index.html)
and [mesa_viz_tornado](https://github.com/projectmesa/mesa-viz-tornado) are related extensions.

The concepts and features of mesa help us to structure the code and visualize results.
See [modeling modules](https://mesa.readthedocs.io/stable/getting_started.html#modeling-modules)
for a description of the Mesa-concepts "model", "agent", and "space" if you are not already familiar with them.

If you do not want to use mesa, you can disable its usage by setting `is_using_mesa` to `False`
in [main.py](src/main.py).

Our class [MesaSimulation](src/mesa_wrapper/mesa_simulation.py) inherits
from [mesa.Model](https://mesa.readthedocs.io/stable/apis/model.html) and implements following
workflow functions:

* `run`: runs the whole simulation by looping over a time span and calling the step function for each step in time.
* `step`: represents a single [step](https://mesa.readthedocs.io/stable/apis/model.html#mesa.model.Model.step) in the
  simulation.

For each step, mesa delegates the actual work to [agents](https://mesa.readthedocs.io/stable/apis/agent.html).
In our case, the agents are instances of the class [SiteAgent](src/mesa_wrapper/site_agent.py). Each SiteAgent wraps
a [Site](src/sites/site.py) and further delegates work to its underlying elements. Also see
the [Hierarchy](#hierarchy)
described below.

Our class [MesaSimulation](src/mesa_wrapper/mesa_simulation.py) also includes a custom implementation of
the [Visitor pattern](#visitor-pattern), separating the hierarchical structure from its post-processing.

If you are interested in the evaluating part of the mesa workflow, see section [Data collection](#data-collection)
below.

### Hierarchy

The `FORECAST-Sites` model consists of a hierarchical structure and its elements are:

* [Region](#region)
* [Site](#site)
* [ProductionUnit](#production-unit)
* [SubProductionUnit](#sub-production-unit)
* [Process](#process)

Carriers are *not* levels of this hierarchy. A `Product`, an `EnergyCarrier` and a `ByProduct` are
referenced by the `Demand` and `Output` objects of a `Process`; see [Carriers](#carriers) below.

#### Region

The class [Region](src/region/region.py) represents a geographical region. Each region can have several [Site](#site)s.
Furthermore, each region knows about region specific properties like energy carrier prices and Co2 cost.

The mesa framework does not consider regions in its original workflow. Our model considers regions while
creating the agents, see function `_create_site_agents` in [MesaSimulation](src/mesa_wrapper/mesa_simulation.py) and
while processing them. Each agent knows what region it belongs to.

#### Site

The class [Site](src/sites/site.py) represents an industrial site. Each site can have
several [ProductionUnit](#production-unit)s.

A site also mediates access to the shared carrier pool that its production units buy from
(`shared_pool_for`). Purchases are deducted from that pool; production does not replenish it.

In order to consider sites in the mesa framework, they are wrapped by the
class [SiteAgent](src/mesa_wrapper/site_agent.py),
implementing mesa- and mesa-geo specific functionality.

#### Production Unit

The class [ProductionUnit](src/production_unit/production_unit.py) represents a production unit. It owns a
list of [SubProductionUnit](#sub-production-unit)s and holds the optimization result for them.

A `ProductionUnit` knows the alternative processes it may run and exposes them as
`available_process_options`. The optimization asks the production unit for those options; it does not
ask a `Product`.

A `ProductionUnit` drives its own optimization in `optimize(year, context)`: it retires sub production
units that have been unused for too long, maps each process option to the sub production unit that
currently runs it, asks the `OptimizationFactory` for an optimization, runs it and applies the
resulting process execution counts. For the multi-period optimization type the result covers several
years at once and is cached, so later years are served from the cache instead of being re-solved.

#### Sub Production Unit

The class [SubProductionUnit](src/sub_production_unit/sub_production_unit.py) represents one installed
process at a production unit, together with its capacity and its reinvestment year.

It carries two separate counts and the distinction is load bearing:
`max_process_execution_count` is the installed capacity and carries the capital costs, while
`process_execution_count` is the actual utilization and carries the operating costs and emissions.

`year_of_last_reinvestment` also expresses *planned future* capacity. Set it to a future year and the
unit only becomes available from that year onwards, with no annuity charged before it.

#### Process

The class [Process](src/processes/process.py) represents a process. Each `Process` includes data related to its energy
demands, investment lifecycle, cost and emissions. Its `Demand` and `Output` objects state how much of
which carrier is consumed or produced per process execution.

A process that is already in place is represented by
[InstalledProcess](src/processes/installed_process.py), which replaces the investment cost with an
age-dependent repair cost.

#### Carriers

A carrier is something a process consumes or produces. There are three kinds, all deriving from
[Carrier](src/carrier/carrier.py):

| Class | Unit | Role |
|---|---|---|
| [Product](src/product/product.py) | t | the modelled output, can be sold |
| [EnergyCarrier](src/energy_carrier/energy_carrier.py) | GJ | energy input, can be subsidized and taxed |
| [ByProduct](src/by_product/by_product.py) | t | secondary output, can be sold |

A carrier knows its own prices and emission factors. It does **not** know which processes use it.

### Construction

The [factory method pattern](https://en.wikipedia.org/wiki/Factory_method_pattern) is used to separate the construction
logic for the model [Hierarchy](#hierarchy) from the model itself. The construction works as follows:

* [main.py](src/main.py) applies a [RegionFactory](src/region/region_factory.py) to create [Region](#region)s. A region
  specific [DataInterface](src/data_layer/data_interface.py) is passed to the region and its subsequent entities, so that they are
  able to initialize themselves with the necessary data from the input database
  (`./resources/input/input.sqlite`, see `database_path` in [simulation_options.toml](src/simulation_options.toml)).
* The `RegionFactory` builds the carriers and the processes up front, via
  [EnergyCarrierFactory](src/energy_carrier/energy_carrier_factory.py),
  [ProductFactory](src/product/product_factory.py), [ByProductFactory](src/by_product/by_product_factory.py) and
  [ProcessFactory](src/processes/process_factory.py). The results are handed down as lookup maps, so the
  lower factories do not construct carriers or processes themselves.
* The `RegionFactory` then applies a [SiteFactory](src/sites/site_factory.py) to create the
  [Site](#site)s.
* The `SiteFactory` creates a [SubProductionUnitFactory](src/sub_production_unit/sub_production_unit_factory.py)
  and a [ProductionUnitFactory](src/production_unit/production_unit_factory.py), which together build the
  [ProductionUnit](#production-unit)s and their [SubProductionUnit](#sub-production-unit)s.

Once that [Hierarchy](#hierarchy) has been created, the `MesaSimulation` creates
a [SiteAgent](src/mesa_wrapper/site_agent.py) for each `Site`. (The `MesaSimulation` itself is created by the
class [MesaServer](src/mesa_wrapper/mesa_server.py).)

### Visitor pattern

The [Visitor](https://en.wikipedia.org/wiki/Visitor_pattern) design pattern allows us to separate our
model [Hierarchy](#hierarchy) from its processing. It
enables us to add new operations without touching the existing model classes.

Currently [main.py](src/main.py) creates instances of
[CollectingResultVisitor](src/result/collecting_result_visitor.py) and
[ShapeFileVisitor](src/result/shape_file_visitor.py) to process the model results. You can add new visitors by
inheriting from
[Visitor](src/result/visitor/visitor.py) and implementing its standardized functions (for example `visit_region`).

As part of each simulation step, all the visitors will be passed down the model hierarchy to visit all the elements and
interact with them. Also see the `step` function in [MesaSimulation](src/mesa_wrapper/mesa_simulation.py) and the
`accept` functions
in [Region](src/region/region.py), [Site](src/sites/site.py), and so on.
At the end of the simulation, the `finalize` function of each visitor will be called.

### Data collection

The mesa concept of [DataCollector](https://mesa.readthedocs.io/stable/apis/datacollection.html) and reporters serves
a similar purpose as our [Visitor](#visitor-pattern) pattern but differs in its details.

If you are interested in the mesa data collection workflow, you can take the property `agent_count` as en example.
Also see the related methods `_create_data_collector` in [MesasSimulation](src/mesa_wrapper/mesa_simulation.py) and
`_create_visualization_elements` in [MesaServer](src/mesa_wrapper/mesa_server.py).

Also see related visualization classes

* [MapModule](src/mesa_wrapper/map_module.py) (custom implementation for leaflet maps) and
* [ChartVisualization](https://github.com/projectmesa/mesa-viz-tornado/blob/main/mesa_viz_tornado/modules/ChartVisualization.py)
  from [mesa-viz-tornado](https://github.com/projectmesa/mesa-viz-tornado).

## Contact

For any questions or feedback, please contact the project maintainer at Marius.Neuwirth@isi.fraunhofer.de.

## Licenses

This project is free and open source software:

* It is licensed under the GNU Affero General Public License v3 or later (AGPLv3+) -
  see [LICENSE](./LICENSES/AGPL-3.0-or-later.txt).
* It uses third-party open source modules, see<br>
  * [pyproject.toml](./pyproject.toml)
  * [THIRDPARTY.md](./THIRDPARTY.md)
  * [package.json](./web/package.json)
  * [web/THIRDPARTY.md](./web/THIRDPARTY.md).

## Notes

<p><a href="https://www.isi.fraunhofer.de/en/publishing-notes.html">PUBLISHING NOTES</a></p>

This project has received funding from the European Union’s Horizon Europe research and innovation programme under grant
agreement No. 101137606.

<img src="https://raw.githubusercontent.com/fraunhofer-isi/.github/refs/heads/main/eu_flag.jpg" alt="eu_flag" width="100px"/>

