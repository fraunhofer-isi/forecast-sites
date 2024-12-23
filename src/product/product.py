# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from entity import Entity


class Product(Entity):

    def __init__(self, product_id, available_processes):
        self.id = product_id
        self.available_processes = available_processes

    def accept(self, visitor, year):
        visitor.visit_product(self, year)

    def virtual_production_cost_per_process_for_comparison(self, year):
        virtual_production_cost = {}
        for process in self.available_processes:
            virtual_production_cost[process.id] = process.production_cost_in_euro_per_ton(year)
        return virtual_production_cost

    def virtual_process_emission_cost_per_process_for_comparison(self, production_in_tons, co2_price_in_euro_per_ton):
        virtual_process_emission_cost = {}
        for process in self.available_processes:
            virtual_process_emission_cost[process.id] = (
                process.process_emission_in_tons(production_in_tons) / production_in_tons
            ) * co2_price_in_euro_per_ton
        return virtual_process_emission_cost

    def virtual_energy_emission_cost_per_process_for_comparison(self, year, co2_price_in_euro_per_ton):
        virtual_energy_emission_cost = {}
        for process in self.available_processes:
            virtual_energy_emission_cost[process.id] = (
                process.energy_emissions_in_ton_co2_per_ton(year) * co2_price_in_euro_per_ton
            )
        return virtual_energy_emission_cost

    def virtual_annuity_per_process(self, year):
        virtual_annuity_per_process = {}
        for process in self.available_processes:
            virtual_annuity_per_process[process.id] = process._annuity_on_investment_per_ton(year)
        return virtual_annuity_per_process

    def virtual_opex_per_process(self, year):
        virtual_opex = {}
        for process in self.available_processes:
            virtual_opex[process.id] = process._opex_in_euro_per_ton(year)
        return virtual_opex
