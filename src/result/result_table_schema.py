# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Declares which result tables CollectingResultVisitor produces and how each one is indexed.

This is data, not behavior: each entry pairs a table name with its ResultTableKind, which
TabularVisitor maps to the matching empty-table factory. Keeping the schema declarative makes the
full set of outputs reviewable at a glance and removes the repetition that previously allowed the
same table to be declared twice by accident.

Absolute results hold totals per entity and year. Specific results hold values per process
execution count.
"""

from result.visitor.result_table_kind import ResultTableKind as Kind

ABSOLUTE_RESULT_TABLES = (
    # Carrier purchases
    ('site_energy_carrier_purchased_amount_in_gj', Kind.SITE_ENERGY_CARRIER),
    ('site_product_purchased_amount_in_t', Kind.SITE_PRODUCT),
    ('site_by_product_purchased_amount_in_t', Kind.SITE_BY_PRODUCT),
    ('production_unit_energy_carrier_purchased_amount_in_gj', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('region_energy_carrier_purchased_amount_in_gj', Kind.REGION_ENERGY_CARRIER),
    ('sector_energy_carrier_purchased_amount_in_gj', Kind.SECTOR_ENERGY_CARRIER),
    ('production_unit_product_purchased_amount_in_t', Kind.PRODUCTION_UNIT_PRODUCT),
    ('production_unit_by_product_purchased_amount_in_t', Kind.PRODUCTION_UNIT_BY_PRODUCT),
    # Production
    ('process_energy_carrier_production_in_gj', Kind.ENERGY_CARRIER),
    ('process_product_production_in_t', Kind.PRODUCT),
    ('process_by_product_production_in_t', Kind.BY_PRODUCT),
    # Export
    ('production_unit_energy_carrier_export_in_gj', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_product_export_in_t', Kind.PRODUCTION_UNIT_PRODUCT),
    ('production_unit_by_product_export_in_t', Kind.PRODUCTION_UNIT_BY_PRODUCT),
    # Demand
    ('process_energy_carrier_energy_demand_in_gj', Kind.ENERGY_CARRIER),
    ('process_energy_carrier_feedstock_demand_in_gj', Kind.ENERGY_CARRIER),
    ('process_product_feedstock_demand_in_t', Kind.PRODUCT),
    ('process_by_product_feedstock_demand_in_t', Kind.BY_PRODUCT),
    # Emission, aggregated per production unit
    ('region_upstream_emission_in_t_co2', Kind.REGION),
    ('sector_upstream_emission_in_t_co2', Kind.SECTOR),
    ('region_downstream_emission_in_t_co2', Kind.REGION),
    ('sector_downstream_emission_in_t_co2', Kind.SECTOR),
    ('region_renewably_bound_co2_emission_in_t_co2', Kind.REGION),
    ('sector_renewably_bound_co2_emission_in_t_co2', Kind.SECTOR),
    ('production_unit_energy_carrier_upstream_emission_in_t_co2', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_product_upstream_emission_in_t_co2', Kind.PRODUCTION_UNIT_PRODUCT),
    ('production_unit_product_downstream_emission_in_t_co2', Kind.PRODUCTION_UNIT_PRODUCT),
    ('production_unit_energy_carrier_downstream_emission_in_t_co2', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_by_product_downstream_emission_in_t_co2', Kind.PRODUCTION_UNIT_BY_PRODUCT),
    ('production_unit_by_product_upstream_emission_in_t_co2', Kind.PRODUCTION_UNIT_BY_PRODUCT),
    ('production_unit_energy_carrier_renewably_bound_co2_emission_in_t_co2', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_product_renewably_bound_co2_emission_in_t_co2', Kind.PRODUCTION_UNIT_PRODUCT),
    ('production_unit_by_product_renewably_bound_co2_emission_in_t_co2', Kind.PRODUCTION_UNIT_BY_PRODUCT),
    # Emission, per process
    ('process_execution_count', Kind.BASE),
    ('region_direct_emission_in_t_co2', Kind.REGION),
    ('sector_direct_emission_in_t_co2', Kind.SECTOR),
    ('process_direct_emission_in_t_co2', Kind.BASE),
    ('process_direct_energy_emission_in_t_co2', Kind.BASE),
    ('process_direct_non_energy_emission_in_t_co2', Kind.BASE),
    ('region_captured_emission_in_t_co2', Kind.REGION),
    ('sector_captured_emission_in_t_co2', Kind.SECTOR),
    ('process_captured_emission_in_t_co2', Kind.BASE),
    # Emission, per demand and per production
    ('process_energy_carrier_energy_demand_direct_emission_in_t_co2', Kind.ENERGY_CARRIER),
    ('process_energy_carrier_production_direct_emission_in_t_co2', Kind.ENERGY_CARRIER),
    # Cost, per production unit
    ('production_unit_energy_carrier_purchase_cost_in_euro', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_energy_carrier_taxes_in_euro', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_energy_carrier_subsidies_in_euro', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_product_purchase_cost_in_euro', Kind.PRODUCTION_UNIT_PRODUCT),
    ('production_unit_by_product_purchase_cost_in_euro', Kind.PRODUCTION_UNIT_BY_PRODUCT),
    ('production_unit_energy_carrier_upstream_emission_cost_in_euro', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_product_upstream_emission_cost_in_euro', Kind.PRODUCTION_UNIT_PRODUCT),
    ('production_unit_by_product_upstream_emission_cost_in_euro', Kind.PRODUCTION_UNIT_BY_PRODUCT),
    ('production_unit_energy_carrier_downstream_emission_cost_in_euro', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_product_downstream_emission_cost_in_euro', Kind.PRODUCTION_UNIT_PRODUCT),
    ('production_unit_by_product_downstream_emission_cost_in_euro', Kind.PRODUCTION_UNIT_BY_PRODUCT),
    ('production_unit_energy_carrier_renewably_bound_co2_emission_cost_in_euro', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_product_renewably_bound_co2_emission_cost_in_euro', Kind.PRODUCTION_UNIT_PRODUCT),
    ('production_unit_by_product_renewably_bound_co2_emission_cost_in_euro', Kind.PRODUCTION_UNIT_BY_PRODUCT),
    ('production_unit_overall_emission_budget_used_in_t_co2', Kind.PRODUCTION_UNIT),
    ('production_unit_overall_emission_budget_in_t_co2', Kind.PRODUCTION_UNIT),
    ('production_unit_budget_relevant_emission_in_t_co2', Kind.PRODUCTION_UNIT),
    ('production_unit_energy_carrier_sell_gain_in_euro', Kind.PRODUCTION_UNIT_ENERGY_CARRIER),
    ('production_unit_product_sell_gain_in_euro', Kind.PRODUCTION_UNIT_PRODUCT),
    ('production_unit_by_product_sell_gain_in_euro', Kind.PRODUCTION_UNIT_BY_PRODUCT),
    # Cost, per process
    ('process_production_cost_in_euro', Kind.BASE),
    ('process_direct_emission_cost_in_euro', Kind.BASE),
    ('process_direct_energy_emission_cost_in_euro', Kind.BASE),
    ('process_direct_non_energy_emission_cost_in_euro', Kind.BASE),
    ('process_saving_due_to_captured_emission_in_euro', Kind.BASE),
    ('process_annuity_on_investment_in_euro', Kind.BASE),
    ('process_investment_in_euro', Kind.BASE),  # = capex
    ('process_opex_in_euro', Kind.BASE),
)

SPECIFIC_RESULT_TABLES = (
    # Cost
    ('process_product_production_cost_in_euro_per_process_count', Kind.PRODUCT),
    ('process_by_product_production_cost_in_euro_per_process_count', Kind.BY_PRODUCT),
    ('process_energy_carrier_production_cost_in_euro_per_process_count', Kind.ENERGY_CARRIER),
    ('process_carrier_cost_in_euro_per_process_count', Kind.BASE),
    ('process_energy_carrier_energy_purchase_cost_in_euro_per_process_count', Kind.ENERGY_CARRIER),
    ('process_energy_carrier_feedstock_purchase_cost_in_euro_per_process_count', Kind.ENERGY_CARRIER),
    ('process_product_purchase_cost_in_euro_per_process_count', Kind.PRODUCT),
    ('process_by_product_purchase_cost_in_euro_per_process_count', Kind.BY_PRODUCT),
    ('process_annuity_on_investment_in_euro_per_process_count', Kind.BASE),
    ('process_opex_in_euro_per_process_count', Kind.BASE),
)
