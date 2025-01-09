# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from entity import Entity
from utils.collection_utils import object_sum
from utils.time_utils import interpolate

# pylint: disable=too-many-instance-attributes


class Process(Entity):

    # pylint: disable=too-many-instance-attributes, too-many-arguments
    def __init__(self, id_process, data):
        self.id = id_process
        self.lifetime_in_years = data['lifetime_in_years']
        self.energy_demands = data['energy_demands']
        self.feedstock_demands = data['feedstock_demands']
        self.steam_demands = data['steam_demands']
        self._capex_2015_in_euro_per_ton = data['capex_2015_in_euro_per_ton']
        self._capex_2050_in_euro_per_ton = data['capex_2050_in_euro_per_ton']
        self._opex_2015_in_euro_per_ton = data['opex_2015_in_euro_per_ton']
        self._opex_2050_in_euro_per_ton = data['opex_2050_in_euro_per_ton']
        self._interest_rate = data['interest_rate']
        self._depreciation_period = data['depreciation_period']
        self.process_emission_in_ton_co2_per_ton = data['process_emission_in_ton_co2_per_ton']
        self._efficiency_improvement_2015 = data['efficiency_improvement_2015']
        self._efficiency_improvement_2050 = data['efficiency_improvement_2050']
        self._investment_funding_2015 = data['investment_funding_2015']
        self._investment_funding_2050 = data['investment_funding_2050']
        self._investment_flexibility_2015 = data['investment_flexibility_2015']
        self._investment_flexibility_2050 = data['investment_flexibility_2050']

    def accept(self, visitor, year):
        visitor.visit_process(self, year)

    def production_cost_in_euro(
        self,
        year,
        production_in_tons,
        co2_cost_in_euro_per_ton_c02,
        pipeline_cost_scaling,
    ):
        if 15 in self.check_energy_carrier():
            pipeline_cost = pipeline_cost_scaling
        else:
            pipeline_cost = 1

        return pipeline_cost + production_in_tons * (
            self.production_cost_in_euro_per_ton(year)
            + (self.process_emission_in_ton_co2_per_ton + self.energy_emissions_in_ton_co2_per_ton(year))
            * co2_cost_in_euro_per_ton_c02
        )

    def emission_cost_in_euro_per_ton(self, year, co2_cost_in_euro_per_ton_c02):
        return (
            self.process_emission_in_ton_co2_per_ton + self.energy_emissions_in_ton_co2_per_ton(year)
        ) * co2_cost_in_euro_per_ton_c02

    def check_energy_carrier(self):
        energy = [demand.get_energy_carrier_id() for demand in self.energy_demands]
        steam = [demand.get_energy_carrier_id() for demand in self.steam_demands]
        feedstock = [demand.get_energy_carrier_id() for demand in self.feedstock_demands]
        total = energy + steam + feedstock
        return total

    def process_emission_in_tons(self, production_in_tons):
        return production_in_tons * self.process_emission_in_ton_co2_per_ton

    def investment_in_euro(self, year, production_in_tons):
        return (self._capex_in_euro_per_ton(year) - self._investment_funding(year)) * production_in_tons

    def annuity_on_investment(self, year, production_in_tons):
        return self.annuity_on_investment_per_ton(year) * production_in_tons

    def year_of_new_investment(self, year_of_last_reinvestment):
        return self.lifetime_in_years + year_of_last_reinvestment

    def energy_emissions_in_ton_co2_per_ton(self, year):
        energy_emissions = object_sum(
            self.energy_demands,
            lambda demand: demand.energy_carrier_emission_in_ton_co2_per_ton(year),
        )
        steam_emissions = object_sum(self.steam_demands, lambda demand: demand.steam_emission_in_ton_co2_per_ton(year))
        return energy_emissions + steam_emissions

    def production_cost_in_euro_per_ton(self, year):
        return (
            self.annuity_on_investment_per_ton(year)
            + self.opex_in_euro_per_ton(year)
            + (
                self.energy_carrier_cost_in_euro_per_ton(year)
                - self._energy_carrier_subsidies_in_euro_per_ton(year)
                + self._energy_carrier_taxes_in_euro_per_ton(year)
            )
        )

    def energy_demand_in_gj_per_ton(self):
        demand = []
        for energy_demand in self.energy_demands:
            energy_carrier = energy_demand.energy_carrier

        return self.energy_demands

    def steam_demand_in_gj_per_ton(self):
        return self.steam_demands

    def feedstock_demand_in_gj_per_ton(self):
        return self.feedstock_demands

    def energy_and_emission_cost(self, year, co2_cost_in_euro_per_ton_c02):
        return self.energy_carrier_cost_in_euro_per_ton(year) + (
            (self.energy_emissions_in_ton_co2_per_ton(year) + self.process_emission_in_ton_co2_per_ton)
            * co2_cost_in_euro_per_ton_c02
        )

    def energy_cost_per_ton(self, year):
        return object_sum(self.energy_demands, lambda demand: demand.energy_carrier_cost_in_euro_per_ton(year))

    def steam_cost_per_ton(self, year):
        return object_sum(self.steam_demands, lambda demand: demand.steam_cost_in_euro_per_ton(year))

    def feedstock_cost_per_ton(self, year):
        return object_sum(self.feedstock_demands, lambda demand: demand.feedstock_cost_in_euro_per_ton(year))

    def adapt_energy_demands(self, energy_carrier_share):
        new_energy_demands = {}
        for demand in self.energy_demands:
            energy_carrier = demand.energy_carrier
            if energy_carrier in energy_carrier_share:
                new_demand = energy_carrier_share.demand
                new_energy_demands[energy_carrier] = new_demand
            else:
                new_energy_demands[energy_carrier] = demand
        self.energy_demands = new_energy_demands
        return self.energy_demands

    def annuity_on_investment_per_ton(self, year):
        return self._annuity_factor() * (self._capex_in_euro_per_ton(year) - self._investment_funding(year))

    def energy_carrier_cost_in_euro_per_ton(self, year):
        energy_cost = object_sum(self.energy_demands, lambda demand: demand.energy_carrier_cost_in_euro_per_ton(year))
        steam_cost = object_sum(self.steam_demands, lambda demand: demand.steam_cost_in_euro_per_ton(year))
        feedstock_cost = object_sum(self.feedstock_demands, lambda demand: demand.feedstock_cost_in_euro_per_ton(year))
        total_energy_carrier_cost = energy_cost + steam_cost + feedstock_cost
        return total_energy_carrier_cost

    def _annuity_factor(self):
        return (((1 + self._interest_rate) ** self._depreciation_period) * self._interest_rate) / (
            ((1 + self._interest_rate) ** self._depreciation_period) - 1
        )

    def _annuity_on_pipeline_investment(self, pipeline_cost):
        return self._annuity_factor() * pipeline_cost

    def _energy_carrier_subsidies_in_euro_per_ton(self, year):
        energy_subsidies = object_sum(
            self.energy_demands,
            lambda demand: demand.energy_carrier_subsidies_in_euro_per_ton(year),
        )
        steam_subsidies = object_sum(self.steam_demands, lambda demand: demand.steam_subsidies_in_euro_per_ton(year))
        feedstock_subsidies = object_sum(
            self.feedstock_demands,
            lambda demand: demand.feedstock_subsidies_in_euro_per_ton(year),
        )
        total_energy_carrier_subsides = energy_subsidies + steam_subsidies + feedstock_subsidies
        return total_energy_carrier_subsides

    def _energy_carrier_taxes_in_euro_per_ton(self, year):
        energy_taxes = object_sum(self.energy_demands, lambda demand: demand.energy_carrier_taxes_in_euro_per_ton(year))
        steam_taxes = object_sum(self.steam_demands, lambda demand: demand.steam_taxes_in_euro_per_ton(year))
        feedstock_taxes = object_sum(
            self.feedstock_demands,
            lambda demand: demand.feedstock_taxes_in_euro_per_ton(year),
        )
        total_energy_carrier_taxes = energy_taxes + steam_taxes + feedstock_taxes
        return total_energy_carrier_taxes

    def _capex_in_euro_per_ton(self, year):
        return interpolate(year, self._capex_2015_in_euro_per_ton, self._capex_2050_in_euro_per_ton)

    def opex_in_euro_per_ton(self, year):
        return interpolate(year, self._opex_2015_in_euro_per_ton, self._opex_2050_in_euro_per_ton)

    def _efficiency_improvement(self, year):
        return interpolate(year, self._efficiency_improvement_2015, self._efficiency_improvement_2050)

    def _investment_funding(self, year):
        return interpolate(year, self._investment_funding_2015, self._investment_funding_2050)

    def _investment_flexibility(self, year):
        return interpolate(year, self._investment_flexibility_2015, self._investment_flexibility_2050)
