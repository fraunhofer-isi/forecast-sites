<!--
© 2024 Fraunhofer-Gesellschaft e.V., München

SPDX-License-Identifier: AGPL-3.0-or-later
-->

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
7. [Contributing](#contributing)
8. [Badges](#badges)
9. [Architecture](#architecture)
10. [Contact](#contact)
11. [Notes](#notes)

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
- **Visualization Tools**: Provides jupyter notebooks for results visualization and analysis by generation graphs and
  charts for better data interpretation.

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

1. Configure the model parameters in the following way:

- Navigate to the [input](input) folder
- Open the [input.sqlite](input\input.sqlite) database
- Manipulate or change the industry site and process information by by navigating through the different tables
    - Techno-economic process information can be seen and changed in the table `product_process_mapping`

2. Configure the modelled products and regions you want to simulate:

- Open the `main.py` file
- Change `id_product` and `id_region` according to your wishes
- Activate or deactivate the consideration of hydrogen infrastructure according to plans from the European Hydrogen
  Backbone initiative
- Select simulation mode: `deterministic` or `monte-carlo`?

3. Configure scenario parameters like CO2-pricing:

- Open the `main.py` file
- Change the values and the interpolation functions between your adjusted start and end year of the simulation
  accordingly

4. Start program

`python src/main.py`

## Configuration

The input.sqlite database and tables allows you to customize several parameters:

- `industry site information`: Add, adjust or delete industry sites with their necessary information on:
    - Geolocation (longitude, latitude) within the `site` table,
    - Production units (production output, age, product, and process) within the `production unit` table.
- `process information`:
    - Capital expenditures (CAPEX) in the table `product_process_mapping`
    - Operational expenditures (OPEX) in the table `product_process_mapping`
    - Specific energy, steam and feedstock consumptions (SEC) in the table `product_process_mapping`
    - Lifetime in the table `product_process_mapping`
    - Optional: efficiency gains over years, process emission factors, etc, in the table `product_process_mapping`
    - Energy carrier and respective shares on energy (`process_energy_carrier_mapping`), steam (
      `process_steam_mapping`), and feedstock (`process_feedstock_mapping`) demand
    - Energy carrier emission factors and projections in `energy_carrier_emission`
- `scenario information`:
    - Energy carrier price pathways in `energy_carrier_cost`
    - Pipeline/infrastructure information in the file `pipelines.py`

## Visualization

To visualize the results, the model is provided by a live-visualization based on the mesa package on a openstreetmap
within an automatically opened tab in the browser.
All results are saved within the [output](ouput) folder as output.sqlite and individual Excel files.

The runtime of the model is generally quite short and depends on the amount of regions, sites, and products modelled.
For modelling primary steel and basic chemicals in entire Europe, the runtime is approximately 10 minutes.

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

[![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/fhg-isi/4bb6f7ce335564341b0181db14bdc98f/raw/forecast-sites_coverage.json)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/coverage.yml)
Determines Python test coverage with [pytest-cov](https://github.com/pytest-dev/pytest-cov)

[![web_coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/fhg-isi/4bb6f7ce335564341b0181db14bdc98f/raw/forecast-sites_web_coverage.json)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_coverage.yml)
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

TODO: clarify/update usage without mesa.

Our class [MesaSimulation](src/mesa_wrapper/mesa_simulation.py) inherits
from [mesa.Model](https://mesa.readthedocs.io/stable/apis/model.html) and implements following
workflow functions:

* `run`: runs the whole simulation by looping over a time span and calling the step function for each step in time.
* `step`: represents a single [step](https://mesa.readthedocs.io/stable/apis/model.html#mesa.model.Model.step) in the
  simulation.

For each step, mesa delegates the actual work to [agents](https://mesa.readthedocs.io/stable/apis/agent.html).
In our case, the agents are instances of the class [SiteAgent](src/mesa_wrapper/site_agent.py). Each SiteAgent wraps
a [Site](src/industrial_site/site.py) and further delegates work to its underlying elements. Also see
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
* [Product](#product)
* [Process](#process)

#### Region

The class [Region](src/region/region.py) represents a geographical region. Each region can have several [Site](#sites)s.
Furthermore, each region knows about region specific properties like energy carrier prices and Co2 cost.

The mesa framework does not consider regions in its original workflow. Our model considers regions while
creating the agents, see function `_create_site_agents` in [MesaSimulation](src/mesa_wrapper/mesa_simulation.py) and
while processing them. Each agent knows what region it belongs to.

#### Site

The class [Site](src/industrial_site/site.py) represents an industrial site. Each site can have
several [ProductionUnit](#production-unit)s.

In order to consider sites in the mesa framework, they are wrapped by the
class [SiteAgent](src/mesa_wrapper/site_agent.py),
implementing mesa- and mesa-geo specific functionality.

#### Production Unit

The class [ProductionUnit](src/industrial_site/production_unit.py) represents a production unit.

Each `ProductionUnit` is responsible to produce one distinct [Product](#product) based on an
associated [Process](#process).

The `Product` and its produced amount are fixed, while the associated `Process` might change over time.

A `ProductionUnit` maps from a `Product` to a currently applied `Process`. It also knows about the previously used
`Process`. 

Furthermore, it has knowledge about the timing of investments.

A `ProductionUnit` is responsible for optimizing the process, see function `optimize_process`. It does not know about
alternative `Process`es itself, but is able to ask its `Product` about them.

#### Product

The class [Product](src/product/product.py) represents a product. Each `Product` knows what [Process](#process)es can be
used to produce it. It is also able to determine the corresponding cost and emission.

#### Process

The class [Process](src/process/process.py) represents a process. Each `Process` includes data related to its energy
demands,
investment lifecycle, cost and emissions.

### Construction

The [factory method pattern](https://en.wikipedia.org/wiki/Factory_method_pattern) is used to separate the construction
logic for the model [Hierarchy](hierarchy) from the model itself. The construction works as follows:

* [main.py](src/main.py) applies a [RegionFactory](src/region/region_factory.py) to create [Region](#region)s. A region
  specific [DataInterface](src/data_interface.py) is passed to the region and its subsequent entities, so that they are
  able to initialize
  themselves with the necessary data from [input.sqlite](input/input.sqlite).
* Each `Region` applies a [SiteFactory](src/industrial_site/site_factory.py) to create corresponding [Site](#site)s,
  including their
  [ProductionUnit](#procution-unit)s based on [ProductionUnitFactory](src/production_unit/production_unit_factory.py).
  The Region also applies an [EnergyCarrierFactory](src/energy_carrier/energy_carrier_factory.py) to create
  `EnergyCarriers`.

* The `ProductionUnitFactory` applies a [ProcessFactory](src/process/process_factory.py) and
  a [ProductFactory](src/product/product_factory.py) to
  create corresponding entities for the initialization of the `ProductionUnit`s.

Once that [Hierarchy](hierarchy) has been created, the `MesaSimulation` creates
a [SiteAgent](src/mesa_wrapper/site_agent.py) for each `Site`. (The `MesaSimulation` itself is created by the
class [MesaServer](src/mesa_wrapper/mesa_server.py).)

### Visitor pattern

The [Visitor](https://en.wikipedia.org/wiki/Visitor_pattern) design pattern allows us to separate our
model [Hierarchy](hierarchy) from its processing. It
enables us to add new operations without touching the existing model classes.

Currently [main.py](src/main.py) creates instances of [TabularResultVisitor](src/visitor/tabular_result_visitor.py) and
[ShapeFileVisitor](src/visitor/shape_file_visitor.py) to process the model results. You can add new visitors by
inheriting from
[Visitor](src/visitor/visitor.py) and implementing its standardized functions (for example `visit_region`).

As part of each simulation step, all the visitors will be passed down the model hierarchy to visit all the elements and
interact with them. Also see the `step` function in [MesaSimulation](src/mesa_wrapper/mesa_simulation.py) and the
`accept` functions
in [Region](src/region/region.py), [Site](src/industrial_site/site.py), and so on.
At the end of the simulation, the `finalize` function of each visitor will be called.

### Data collection

The mesa concept of [DataCollector](https://mesa.readthedocs.io/stable/apis/datacollection.html) and reporters serves
a similar purpose as our [Visitor](#visitor) pattern but differs in its details.

If you are interested in the mesa data collection workflow, you can take the property `agent_count` as en example.
Also see the related methods `_create_data_collector` in [MesasSimulation](src/mesa_wrapper/mesa_simulation.py) and
`_create_visualization_elements` in [MesaServer](src/mesa_wrapper/mesa_server.py).

Also see related visualization classes

* [MapModule](src/mesa_warpper/map_module.py) (custom implementation for leaflet maps) and
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
