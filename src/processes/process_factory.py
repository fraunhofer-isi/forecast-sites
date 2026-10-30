# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from by_product.by_product_feedstock_demand_factory import (
    ByProductFeedstockDemandFactory,
)
from by_product.by_product_output_factory import ByProductOutputFactory
from energy_carrier.energy_carrier_energy_demand_factory import (
    EnergyCarrierEnergyDemandFactory,
)
from energy_carrier.energy_carrier_feedstock_demand_factory import (
    EnergyCarrierFeedstockDemandFactory,
)
from energy_carrier.energy_carrier_output_factory import EnergyCarrierOutputFactory
from interpolation.interpolation_data import InterpolationData
from processes.process import Process
from processes.process_data import ProcessData
from product.product_feedstock_demand_factory import ProductFeedstockDemandFactory
from product.product_output_factory import ProductOutputFactory


class ProcessFactory:
    def __init__(
        self,
        data_interface,
        energy_carriers,
        products,
        by_products,
        simulation_options,
    ):
        self._data_interface = data_interface
        self._energy_carriers = energy_carriers
        self._products = products
        self._by_products = by_products
        self._simulation_options = simulation_options

        self._process_data = data_interface.process_data
        self._process_energy_carrier_mapping = data_interface.process_energy_carrier_energy_demand
        self._process_sector_mapping = data_interface.process_sector_mapping.reset_index()

        self._energy_carrier_output_factory = EnergyCarrierOutputFactory(
            data_interface.process_energy_carrier_output, energy_carriers
        )

        self._product_output_factory = ProductOutputFactory(data_interface.process_product_output, products)

        self._by_product_output_factory = ByProductOutputFactory(data_interface.process_by_product_output, by_products)

    def _efficiency_improvement_interpolation_data(self, id_process):
        start_value = self._process_data['efficiency_improvement_start_year'][id_process]
        end_value = self._process_data['efficiency_improvement_end_year'][id_process]
        interpolation_data = InterpolationData(start_value, end_value)
        return interpolation_data

    def create_map(self):
        processes = {}
        for id_process in self._process_data.index:
            process = self._create(id_process)
            processes[id_process] = process
        return processes

    def _create(self, id_process):
        process_entry = self._process_data.loc[id_process]

        demands = self._create_demands(id_process)
        outputs = self._create_outputs(id_process)
        sector_ids = self._sector_ids(id_process)
        process_data = ProcessData(process_entry, demands, outputs, sector_ids)

        process = Process(id_process, process_data)
        return process

    def _create_demands(self, id_process):
        efficiency_improvement_interpolation_data = self._efficiency_improvement_interpolation_data(id_process)

        energy_carrier_energy_demand_factory = EnergyCarrierEnergyDemandFactory(
            self._data_interface.process_energy_carrier_energy_demand,
            self._energy_carriers,
            efficiency_improvement_interpolation_data,
            self._simulation_options,
        )
        energy_demands = energy_carrier_energy_demand_factory.create(id_process)

        energy_carrier_feedstock_demand_factory = EnergyCarrierFeedstockDemandFactory(
            self._data_interface.process_energy_carrier_feedstock_demand,
            self._energy_carriers,
            efficiency_improvement_interpolation_data,
            self._simulation_options,
        )
        feedstock_demands = energy_carrier_feedstock_demand_factory.create(id_process)

        product_feedstock_demand_factory = ProductFeedstockDemandFactory(
            self._data_interface.process_product_feedstock_demand,
            self._products,
            efficiency_improvement_interpolation_data,
            self._simulation_options,
        )

        product_feedstock_demands = product_feedstock_demand_factory.create(id_process)

        by_product_feedstock_demand_factory = ByProductFeedstockDemandFactory(
            self._data_interface.process_by_product_feedstock_demand,
            self._by_products,
            efficiency_improvement_interpolation_data,
            self._simulation_options,
        )

        by_product_feedstock_demands = by_product_feedstock_demand_factory.create(id_process)

        demands = energy_demands + feedstock_demands + by_product_feedstock_demands + product_feedstock_demands

        return demands

    def _create_outputs(self, id_process):
        product_outputs = self._product_output_factory.create(id_process)
        by_product_outputs = self._by_product_output_factory.create(id_process)
        energy_carrier_outputs = self._energy_carrier_output_factory.create(id_process)
        outputs = product_outputs + by_product_outputs + energy_carrier_outputs
        return outputs

    def _sector_ids(self, id_process):
        sector_ids = set()
        process_mapping = self._process_sector_mapping
        filtered_process_mapping = process_mapping[process_mapping['id_process'] == id_process]
        for _, row in filtered_process_mapping.iterrows():
            sector_ids.add(int(row['id_sector']))
        return tuple(sector_ids)
