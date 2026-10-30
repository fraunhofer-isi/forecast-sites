# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from by_product.by_product import ByProduct
from immutable.partial_immutable import PartialImmutable
from processes.process_data_properties import ProcessDataProperties
from processes.process_data_spec import ProcessDataSpec
from processes.process_financial_calculator import ProcessFinancialCalculator
from processes.process_production_consumption_calculator import (
    ProcessProductionConsumptionCalculator,
)
from product.product import Product
from result.visitor.entity import Entity
from utils import collection_utils

if TYPE_CHECKING:
    from demand.demand import Demand
    from output.output import Output


class AbstractProcess(Entity, PartialImmutable):
    """
    Base class for all processes.

    Wraps a data specification object (ProcessDataSpec) and exposes a unified
    interface for both technology templates and installed instances.

    Delegates to specialized calculators for data access, financial calculations,
    and production/consumption flows.
    """

    def __init__(self, id_process: int, process_data: ProcessDataSpec):
        if not isinstance(process_data, ProcessDataSpec):
            msg = 'process_data must implement ProcessDataSpec protocol'
            raise TypeError(msg)
        Entity.__init__(self, id_process)
        self._process_data: ProcessDataSpec = process_data

        # Initialize delegated calculators
        self._data_properties = ProcessDataProperties(process_data)
        self._financial_calc = ProcessFinancialCalculator(process_data.depreciation_period)
        self._prod_cons_calc = ProcessProductionConsumptionCalculator(
            process_data.outputs,
            process_data.demands,
        )

        # The super __init__ method of PartialImmutable needs to be called after setting the class attributes.
        # Otherwise, the attribute(s) could not be set.
        PartialImmutable.__init__(self)

    @property
    def demands(self) -> tuple[Demand]:
        return self._data_properties.demands

    @property
    def outputs(self) -> tuple[Output]:
        return self._data_properties.outputs

    @property
    def carbon_capture_rate(self) -> float:
        return self._data_properties.carbon_capture_rate

    @property
    def is_capture_process(self) -> bool:
        return self._data_properties.is_capture_process

    @property
    def sector_ids(self) -> tuple[int]:
        return self._data_properties.sector_ids

    @property
    def lifetime_in_years(self) -> int:
        return self._data_properties.lifetime_in_years

    @property
    def tech_available_at_year(self) -> int:
        return self._data_properties.tech_available_at_year

    @property
    def depreciation_period(self) -> int:
        return self._data_properties.depreciation_period

    @property
    def life_extension_factor(self) -> float:
        return self._data_properties.life_extension_factor

    @property
    def used_carriers(self) -> list[Any]:
        carriers = self._input_carriers + self.output_carriers
        unique_carriers = collection_utils.unique_list_preserving_order(carriers)
        return unique_carriers

    @property
    def output_carriers(self) -> list[Any]:
        carriers = [output.carrier for output in self.outputs]
        unique_carriers = collection_utils.unique_list_preserving_order(carriers)
        return unique_carriers

    @property
    def output_products(self) -> list[Any]:
        return [output.carrier for output in self.outputs if isinstance(output.carrier, Product)]

    @property
    def output_by_products(self) -> list[Any]:
        return [output.carrier for output in self.outputs if isinstance(output.carrier, ByProduct)]

    @property
    def emission(self):  # type: ignore[override]
        msg = 'Needs to be implemented by inheriting class'
        raise NotImplementedError(msg)

    @property
    def non_energy_direct_process_emission_in_t_co2_per_process_count(self) -> float:
        return self._data_properties.non_energy_direct_process_emission_in_t_co2_per_process_count

    @property
    def capex_interpolation_data_in_euro_per_process_count(self):  # InterpolationData
        return self._data_properties.capex_interpolation_data_in_euro_per_process_count

    @property
    def opex_interpolation_data_in_euro_per_process_count(self):  # InterpolationData
        return self._data_properties.opex_interpolation_data_in_euro_per_process_count

    @property
    def investment_funding_interpolation_data_in_euro_per_process_count(
        self,
    ):  # InterpolationData
        return self._data_properties.investment_funding_interpolation_data_in_euro_per_process_count

    @property
    def efficiency_improvement_interpolation_data(self):  # InterpolationData
        return self._data_properties.efficiency_improvement_interpolation_data

    @property
    def _input_carriers(self) -> list[Any]:
        carriers = [demand.carrier for demand in self.demands]
        unique_carriers = collection_utils.unique_list_preserving_order(carriers)
        return unique_carriers

    def _compound_factor(self, interest_rate):
        return self._financial_calc.compound_factor(interest_rate)

    def _annuity_factor(self, interest_rate) -> float:
        return self._financial_calc.annuity_factor(interest_rate)

    def accept(self, visitor, year):  # return type domain-specific
        enter_results = visitor.enter_process(self, year)
        child_results = {}
        for output in self.outputs:
            child_result = output.accept(visitor, year)
            child_results[output] = child_result
        process_results = visitor.exit_process(self, year, enter_results, child_results)
        return process_results

    def netto_produced_or_consumed_amount_per_process_count(self, year, carrier) -> float:
        return self._prod_cons_calc.netto_produced_or_consumed_amount_per_process_count(year, carrier)

    def production_in_gj(self, carrier, process_execution_count: float) -> float:
        return self._prod_cons_calc.production_in_gj(carrier, process_execution_count)

    def invest_cost_in_euro_per_process_count(
        self,
        current_year: int,
        interest_rate: float,
        simulation_options: dict,
        capex_factor: float = 1.0,
    ) -> float:
        raise NotImplementedError

    def opex_in_euro_per_process_count(self, year: int, simulation_options: dict) -> float:
        raise NotImplementedError

    def _production_in_unit_per_process_count(self, carrier) -> float:
        return self._prod_cons_calc._production_in_unit_per_process_count(carrier)

    def _production_in_t_per_process_count(self, carrier) -> float:
        return self._prod_cons_calc._production_in_t_per_process_count(carrier)

    def _production_in_gj_per_process_count(self, carrier) -> float:
        return self._prod_cons_calc._production_in_gj_per_process_count(carrier)

    def _consumption_in_unit_per_process_count(self, year, carrier) -> float:
        return self._prod_cons_calc._consumption_in_unit_per_process_count(year, carrier)

    def _consumption_in_t_per_process_count(self, year, carrier) -> float:
        return self._prod_cons_calc._consumption_in_t_per_process_count(year, carrier)

    def _consumption_in_gj_per_process_count(self, year, energy_carrier) -> float:
        return self._prod_cons_calc._consumption_in_gj_per_process_count(year, energy_carrier)
