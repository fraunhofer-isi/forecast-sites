# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from processes.process import Process
from utils.time_utils import create_time_span


class InstalledProcess(Process):
    def __init__(
        self,
        process,
        sub_production_unit,
    ):
        self._sub_production_unit = sub_production_unit
        # The super __init__ method needs to be called after setting the class attributes because
        # we inherit from PartialImmutable through Process. Otherwise, the attribute(s) could not be set.
        super().__init__(process.id, process)

    def __repr__(self):
        class_name = type(self).__name__
        return f'{class_name}({self._id}|{self._year_of_last_reinvestment})'

    def is_available_in_year(self, year):
        return self._sub_production_unit.year_of_last_reinvestment <= year

    def available_process_execution_count(self, year):
        if not self.is_available_in_year(year):
            return 0
        return self._sub_production_unit.max_process_execution_count

    @property
    def _year_of_last_reinvestment(self):
        return self._sub_production_unit.year_of_last_reinvestment

    def invest_cost_in_euro_per_process_count(
        self,
        current_year,
        interest_rate,
        simulation_options,
        _capex_factor=1.0,
    ):
        # Age-dependent repair cost. The start year capex factor does not apply here:
        # it penalizes switching to a *new* process, so an already installed process
        # must not be scaled by it.
        total_repair_cost = 0

        planning_years = self._planning_years(current_year, simulation_options)
        for year in planning_years:
            age = self._age(year)
            raw_capex = self.capex_in_euro_per_process_count(year, simulation_options)

            capex_age_factor = self._capex_age_factor(age)
            yearly_repair_cost = capex_age_factor * raw_capex

            # Discount to t=0
            discounted_repair = yearly_repair_cost / (1 + interest_rate) ** (year - current_year)
            total_repair_cost += discounted_repair

        return total_repair_cost

    def annuity_on_investment_in_euro_per_process_count(self, year, interest_rate, simulation_options):
        age = self._age(year)
        if age >= self.depreciation_period:
            return 0
        return super().annuity_on_investment_in_euro_per_process_count(year, interest_rate, simulation_options)

    def _capex_age_factor(self, age):
        """Repair cost factor: zero within lifetime, rising linearly after."""
        if age <= self.lifetime_in_years:
            return 0
        return self.life_extension_factor * (age - self.lifetime_in_years)

    @staticmethod
    def _planning_years(current_year, simulation_options):
        """Generate planning years from current year and simulation options."""
        end_year = current_year + simulation_options['rolling_planning_horizon_in_years']
        planning_year_increment = 1
        return create_time_span(current_year, end_year, planning_year_increment)

    def opex_in_euro_per_process_count(self, year, simulation_options):
        # overrides Process.opex_in_euro_per_process_count
        raw_opex = super().opex_in_euro_per_process_count(year, simulation_options)
        age_factor = self._opex_age_factor(year)
        opex = age_factor * raw_opex
        return opex

    def _opex_age_factor(self, year):
        age = self._age(year)
        age_factor = 1 + age / 10000  # to prevent infeasibility
        return age_factor

    def _age(self, year):
        age = year - self._year_of_last_reinvestment
        return age
