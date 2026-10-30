# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from demand.demand_factory import DemandFactory
from energy_carrier.energy_carrier_feedstock_demand import EnergyCarrierFeedstockDemand


class EnergyCarrierFeedstockDemandFactory(DemandFactory):
    def __init__(
        self,
        process_energy_carrier_feedstock_demand,
        energy_carriers,
        efficiency_improvement_interpolation_data,
        simulation_options,
    ):
        super().__init__(
            process_energy_carrier_feedstock_demand,
            energy_carriers,
            efficiency_improvement_interpolation_data,
            simulation_options,
        )

    def _demand(self, row):
        id_energy_carrier = row.name
        energy_carrier = self._carriers[id_energy_carrier]

        demand_in_gj_per_process_count = row['demand_in_gj_per_process_count']

        feedstock_demand = EnergyCarrierFeedstockDemand(
            energy_carrier,
            demand_in_gj_per_process_count,
            self._efficiency_improvement_interpolation_data,
            self._simulation_options,
        )
        return feedstock_demand
