<!--
© 2024 Fraunhofer-Gesellschaft e.V., München

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# FORECAST-Sites - A technology dffusion model to simulate industry transformation scenarios with high spatial resolution for energy-intensive industry branches

This repository contains the complete model code of the `FORECAST-Sites` modelling approach for technology diffusion scenarios for energy-intensive industries.
The provided model framework is related to the following publication in the journal Scientific Reports:
<a href="https://www.nature.com/articles/s41598-024-78881-7">Scientific Reports - Neuwirth et al. 2024</a></p>
The development of the framework was conducted within the Horzizon Europe project <a href="https://www.transience.eu/">Transience</a> under grent agreement No. 101137606.
Within this repository also a first part of Fraunhofer ISI IndustrialSiteDatabase for European primary steel and basic chemical (high value chemicals (HVC), ammonia, and methanol) is published to directly start exporing scenarios for those industry branches.

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Visualization](#visualization)
7. [Contributing](#contributing)
8. [Badges](#badges)
9. [Contact](#contact)
10. [Notes](#notes)

## Introduction

Welcome to the Technology Diffusion Model in Energy-Intensive Industries repository. This project aims to provide a comprehensive model for studying the diffusion of new technologies within energy-intensive sectors such as steel, cement, and chemical industries. The model helps in understanding how new technologies are adopted over time and their impact on energy consumption and greenhouse gas emissions.

## Features

- **Site-specific investments**: Models the site-specific investments based on techno-economic decisions according to scenario assumptions.
- **Energy demand development**: Shows the spatially highly resolved development and correlation of process adoption and energy usage.
- **Industrial process diffusion**: Evaluates the possible ramp-up of climate-neutral industry processes according to energy price projections and scenario frameworks.
- **Customizable Parameters**: Allows customization for different industries and scenario assumptions, such as energy price projections and different policies.
- **Visualization Tools**: Provides jupyter notebooks for results visualization and analysis by generation graphs and charts for better data interpretation.

## Installation

The installation of the model follows typical Git and Python based schemes.

### Prerequisites

- Python 3.12 or higher
- Nodejs 23.5.0 or higher
- Git
- Python package requirements (see pryproject.toml file)
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
- Activate or deactivate the consideration of hydrogen infrastructure according to plans from the European Hydrogen Backbone initiative
- Select simulation mode: `deterministic` or `monte-carlo`?

3. Configure scenario parameters like CO2-pricing:

- Open the `main.py` file
- Change the values and the interpolation functions between your adjusted start and end year of the simulation accordingly

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
  - Energy carrier and respective shares on energy (`process_energy_carrier_mapping`), steam (`process_steam_mapping`), and feedstock (`process_feedstock_mapping`) demand
  - Energy carrier emission factors and projections in `energy_carrier_emission`
- `scenario information`:
  - Energy carrier price pathways in `energy_carrier_cost`
  - Pipeline/infrastructure information in the file `pipelines.py`

## Visualization

To visualize the results, the model is provided by a live-visualization based on the mesa package on a openstreetmap within an autmatically opened tab in the browser.
All results are saved within the [output](ouput) folder as output.sqlite and intividual excel files.

Some visualization scripts are provided as jupyter notebooks within the [visualization](visualization) folder for results analysis.
The scripts show information like production costs and their cost components, energy demands per energy carrier, development of process shares and their diffusion.

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

TODO: Badge "Checks Python code formatting with ..."

[![web_lint](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_lint.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_lint.yml) Checks JavaScript code formatting with [ESlint](https://eslint.org/)

### Test coverage

[![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/fhg-isi/4bb6f7ce335564341b0181db14bdc98f/raw/forecast-sites_coverage.json)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/coverage.yml) Determines Python test coverage with [pytest-cov](https://github.com/pytest-dev/pytest-cov)

[![web_coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/fhg-isi/4bb6f7ce335564341b0181db14bdc98f/raw/forecast-sites_web_coverage.json)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_coverage.yml) Determines JavaScript test coverage with [jest](https://jestjs.io/)

### License compliance

[![license_check](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/license_check.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/license_check.yml) Checks Python license compatibility with [LicenseCheck](https://github.com/FHPythonUtils/LicenseCheck)

[![web_license_check](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_license_check.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/web_license_check.yml) Checks JavaScript license compatibility with [license-checker](https://github.com/davglass/license-checker)

[![reuse_annotate](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/reuse_annotate.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/reuse_annotate.yml) Creates copyright & license annotations with [reuse](https://git.fsfe.org/reuse/tool)

[![reuse compliance](https://api.reuse.software/badge/github.com/fraunhofer-isi/forecast-sites)](https://api.reuse.software/info/github.com/fraunhofer-isi/forecast-sites) Checks for REUSE compliance with [reuse](https://git.fsfe.org/reuse/tool)

### Dependency updates & security checks

[![renovate](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/renovate.yml/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/renovate.yml) Updates dependencies with [renovate](https://github.com/renovatebot/renovate)

[![CodeQL](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/fraunhofer-isi/forecast-sites/actions/workflows/github-code-scanning/codeql) Discovers vulnerabilities with [CodeQL](https://codeql.github.com/)

## Contact

For any questions or feedback, please contact the project maintainer at Marius.Neuwirth@isi.fraunhofer.de.

## Licenses

This project is free and open source software:

* It is licensed under the GNU Affero General Public License v3 or later (AGPLv3+) - see [LICENSE](./LICENSES/AGPL-3.0-or-later.txt).
* It uses third-party open source modules, see<br>
  * [pyproject.toml](./pyproject.toml)
  * [THIRDPARTY.md](./THIRDPARTY.md)
  * [package.json](./web/package.json)
  * [web/THIRDPARTY.md](./web/THIRDPARTY.md).

## Notes

<p><a href="https://www.isi.fraunhofer.de/en/publishing-notes.html">PUBLISHING NOTES</a></p>

This project has received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No. 101137606.

<img src="https://raw.githubusercontent.com/fraunhofer-isi/.github/refs/heads/main/eu_flag.jpg" alt="eu_flag" width="100px"/>
