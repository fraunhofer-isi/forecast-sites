# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from enum import StrEnum


class ResultTableKind(StrEnum):
    """
    Index structure of a result table.

    Each kind corresponds to one empty-table factory on TabularVisitor and therefore to one
    combination of index columns. Declaring the kind instead of calling the factory directly keeps
    the table schema readable as data; see result.result_table_schema.
    """

    REGION = 'region'
    REGION_ENERGY_CARRIER = 'region_energy_carrier'
    SECTOR = 'sector'
    SECTOR_ENERGY_CARRIER = 'sector_energy_carrier'
    SITE = 'site'
    SITE_ENERGY_CARRIER = 'site_energy_carrier'
    SITE_PRODUCT = 'site_product'
    SITE_BY_PRODUCT = 'site_by_product'
    PRODUCTION_UNIT = 'production_unit'
    PRODUCTION_UNIT_ENERGY_CARRIER = 'production_unit_energy_carrier'
    PRODUCTION_UNIT_PRODUCT = 'production_unit_product'
    PRODUCTION_UNIT_BY_PRODUCT = 'production_unit_by_product'
    BASE = 'base'
    ENERGY_CARRIER = 'energy_carrier'
    PRODUCT = 'product'
    BY_PRODUCT = 'by_product'
