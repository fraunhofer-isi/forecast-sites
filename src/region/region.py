# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
import logging

from optimization.optimization_type import OptimizationType
from optimization.region_multi_period_optimization import RegionMultiPeriodOptimization
from region.region_carrier_calculator import RegionCarrierCalculator
from region.region_result_applier import RegionResultApplier
from result.visitor.entity import Entity

# Tolerance for numerical comparisons (small negative values are acceptable)
NEGATIVE_TOLERANCE = -1e-3


class Region(Entity):
    def __init__(
        self,
        id_region,
        data_interface,
        energy_carrier_map,
        sector_map,
        product_map,
        by_product_map,
        process_map,
        site_factory,
        simulation_options,
    ):
        super().__init__(id_region)
        self._data_interface = data_interface

        self._energy_carrier_map = energy_carrier_map
        self._sector_map = sector_map
        self._product_map = product_map
        self._by_product_map = by_product_map
        self._process_map = process_map

        self._carrier_availability = self._initialize_carrier_availability()

        self.sites = site_factory.create_sites(self)

        self._simulation_options = simulation_options
        self._cached_multi_period_result = None
        self._cached_production_units = None

    @property
    def id_scenario(self):
        return self._data_interface.id_scenario

    @property
    def interest_rate(self):
        return self._data_interface.interest_rate

    @property
    def site_data(self):
        site_data = self._data_interface.site_data
        return site_data

    @property
    def sectors(self):
        used_sectors = {sector for site in self.sites for sector in site.sectors}
        return used_sectors

    @property
    def simulation_options(self):
        return self._simulation_options

    @property
    def data_interface(self):
        return self._data_interface

    @property
    def energy_carrier_map(self):
        return self._energy_carrier_map

    @property
    def product_map(self):
        return self._product_map

    @property
    def by_product_map(self):
        return self._by_product_map

    @staticmethod
    def _default_carrier_availability(carrier):
        """Delegate to calculator for default carrier availability (delegates to calculator)."""
        return RegionCarrierCalculator.default_carrier_availability(carrier)

    def accept(self, visitor, year):
        enter_results = visitor.enter_region(self, year)
        child_results = {}
        for site in self.sites:
            child_result = site.accept(visitor, year)
            child_results[site] = child_result
        result = visitor.exit_region(
            self,
            year,
            enter_results,
            child_results,
        )
        return result

    def consume_purchased_carrier_amounts_for_start_year(self, start_year):
        for site in self.sites:
            site.consume_purchased_carrier_amounts_for_start_year(start_year)

    def consume_purchased_carrier_amount(
        self,
        carrier,
        purchased_amount,
        year,
        context,
    ):
        RegionCarrierCalculator.validate_purchased_amount(purchased_amount)
        RegionCarrierCalculator.validate_carrier_known(carrier, self._carrier_availability)

        availability = self._carrier_availability[carrier][str(year)]
        if availability < NEGATIVE_TOLERANCE:
            logging.warning(
                'Carrier availability for carrier %s is negative: %s. This should never happen.', carrier, availability
            )

        if not RegionCarrierCalculator.check_availability_sufficient(availability, purchased_amount):
            simulation_options = context.simulation_options
            start_year = simulation_options['start_year']
            if year == start_year:
                message = (
                    f'Carrier {carrier} not available in sufficient amount {purchased_amount} '
                    f'in region {self} for start year {start_year}.'
                )
                logging.error(message)
            else:
                message = (
                    f'Carrier {carrier} not available in sufficient amount {purchased_amount} in region {self} for year {year}.'
                )
                raise ValueError(message)

        self._carrier_availability[carrier][str(year)] -= purchased_amount

    def co2_cost_in_euro_per_t_co2(self, year):
        return self._data_interface.co2_cost_in_euro_per_t_co2(year)

    def carrier_availability(self, carrier, year):
        if carrier not in self._carrier_availability:
            default_series = self._default_carrier_availability_series(carrier, year)
            self._carrier_availability[carrier] = default_series
        return self._carrier_availability[carrier][str(year)]

    def process_ids_for_site(self, id_site):
        site = self._site(id_site)
        if site is None:
            return []
        return site.used_process_ids

    def optimize(self, year, context):
        optimization_type = context.simulation_options['optimization_type']

        if optimization_type == OptimizationType.REGION_MULTI_PERIOD and self._has_cached_multi_period_result(year):
            self._replay_cached_result(year, context)
            return

        production_units = self._collect_production_units()
        for production_unit in production_units:
            production_unit._remove_inactive_sub_production_units(year)
            production_unit._process_option_mapping = production_unit._process_option_to_sub_production_unit_mapping()

        optimization = RegionMultiPeriodOptimization(year, self, production_units, context)
        result = optimization.optimize()

        self._cached_multi_period_result = result
        self._cached_production_units = production_units
        RegionResultApplier().apply_for_year(year, result, production_units, context)

    def _has_cached_multi_period_result(self, year):
        return self._cached_multi_period_result is not None and self._cached_multi_period_result.has_result_for_year(year)

    def _replay_cached_result(self, year, context):
        production_units = self._cached_production_units
        for production_unit in production_units:
            production_unit._remove_inactive_sub_production_units(year)
            production_unit._process_option_mapping = production_unit._process_option_to_sub_production_unit_mapping()
        RegionResultApplier().apply_for_year(
            year,
            self._cached_multi_period_result,
            production_units,
            context,
        )

    def _collect_production_units(self):
        production_units = []
        for site in self.sites:
            production_units.extend(site.production_units)
        return production_units

    def _site(self, id_site):
        site_for_id = next((site for site in self.sites if site.id == id_site), None)
        return site_for_id

    def _default_carrier_availability_series(self, carrier, year):
        availability = self._default_carrier_availability(carrier)
        availability_series = self._data_interface.annual_value_series(availability, year)
        return availability_series

    def _initialize_carrier_availability(self):
        carrier_availability = {}
        carrier_availability = self._include_energy_carrier_availability(carrier_availability)
        carrier_availability = self._include_product_availability(carrier_availability)
        carrier_availability = self._include_by_product_availability(carrier_availability)
        return carrier_availability

    def _include_energy_carrier_availability(self, carrier_availability):
        for energy_carrier in self._energy_carrier_map.values():
            availability_series = self._data_interface.energy_carrier_availability_series(energy_carrier)
            if availability_series is not None:
                carrier_availability[energy_carrier] = availability_series

        return carrier_availability

    def _include_product_availability(self, carrier_availability):
        for product in self._product_map.values():
            availability_series = self._data_interface.product_availability_series(product)
            if availability_series is not None:
                carrier_availability[product] = availability_series

        return carrier_availability

    def _include_by_product_availability(self, carrier_availability):
        for by_product in self._by_product_map.values():
            availability_series = self._data_interface.by_product_availability_series(by_product)
            if availability_series is not None:
                carrier_availability[by_product] = availability_series

        return carrier_availability
