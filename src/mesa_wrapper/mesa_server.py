# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import os
from typing import ClassVar

from mesa import DataCollector
from mesa_viz_tornado.ModularVisualization import ModularServer
from mesa_viz_tornado.modules import ChartModule

from mesa_wrapper.map_module import MapModule
from mesa_wrapper.mesa_simulation import MesaSimulation
from mesa_wrapper.simulation_factory import SimulationFactory
from utils.site_cluster import first_digit


class MesaServer:
    BRANCH_COLORS: ClassVar[dict[int, str]] = {
        1: 'Tomato',
        2: 'Blue',
        3: 'Green',
        4: 'Purple',
        5: 'Goldenrod',
        6: 'Sienna',
        7: 'Orange',
        8: 'Cyan',
        9: 'Magenta',
    }

    def __init__(
        self,
        regions,
        simulation_options,
        visitors,
    ):
        self._simulation_options = simulation_options
        self._model_params = {
            'regions': regions,
            'options': simulation_options,
            'visitors': visitors,
        }

        if not simulation_options.get('headless', False):
            self._visualization_server = self._create_visualization_server(self._model_params)

    def run(self):
        if self._simulation_options.get('headless', False):
            self._run_headless()
        else:
            os.path.sep = os.sep
            self._visualization_server.launch()

    def _run_headless(self):
        simulation = MesaSimulation(
            regions=self._model_params['regions'],
            options=self._model_params['options'],
            visitors=self._model_params['visitors'],
        )
        while simulation.running:
            simulation.step()

    @staticmethod
    def agent_portrayal(site_agent):
        """Portrayal Method for canvas"""
        process_ids = site_agent.used_process_ids

        portrayal = {'radius': '3'}
        portrayal = MesaServer._set_color_for_primary_steel(portrayal, process_ids)
        portrayal = MesaServer._set_color_for_ammonia(portrayal, process_ids)
        portrayal = MesaServer._set_color_for_olefins(portrayal, process_ids)
        portrayal = MesaServer._set_color_for_methanol(portrayal, process_ids)

        # Default color if no process matched any category
        if 'color' not in portrayal:
            portrayal['color'] = 'Grey'

        return portrayal

    @staticmethod
    def _set_color_for_primary_steel(portrayal, process_ids):
        blast_furnace = 11
        if blast_furnace in process_ids:
            portrayal['color'] = 'Tomato'
        direct_reduction_ng = 39

        if direct_reduction_ng in process_ids:
            portrayal['color'] = 'Blue'
        direct_reduction_h2 = 38

        if direct_reduction_h2 in process_ids:
            portrayal['color'] = 'Green'
        return portrayal

    @staticmethod
    def _set_color_for_ammonia(portrayal, process_ids):
        ammonia_smr = 9
        if ammonia_smr in process_ids:
            portrayal['color'] = 'Grey'

        ammonia_h2 = 8
        if ammonia_h2 in process_ids:
            portrayal['color'] = 'Turquoise'
        return portrayal

    @staticmethod
    def _set_color_for_olefins(portrayal, process_ids):
        steam_cracking = 100
        if steam_cracking in process_ids:
            portrayal['color'] = 'Sienna'
        ethylene_h2 = 44
        if ethylene_h2 in process_ids:
            portrayal['color'] = 'Purple'
        return portrayal

    @staticmethod
    def _set_color_for_methanol(portrayal, process_ids):
        methanol_smr = 60
        if methanol_smr in process_ids:
            portrayal['color'] = 'Goldenrod'
        methanol_h2 = 59
        if methanol_h2 in process_ids:
            portrayal['color'] = 'Olive'
        return portrayal

    @staticmethod
    def _create_data_collector():
        branch_reporters = {
            f'Branch {b}': (
                lambda sim, branch=b: sum(1 for a in sim.agents if any(first_digit(pid) == branch for pid in a.used_process_ids))
            )
            for b in range(1, 10)
        }
        return DataCollector(
            model_reporters={
                'agent_count': lambda sim: len(sim.agents),
                **branch_reporters,
            },
            agent_reporters={'process_ids': lambda a: a.used_process_ids},
        )

    def _create_visualization_server(self, model_params):
        name = 'forecast-sites'
        model_class = MesaSimulation

        model_factory = SimulationFactory(model_class)

        visualization_elements = self._create_visualization_elements()

        return ModularServer(
            model_factory,
            visualization_elements,
            name,
            model_params,
        )

    def _create_visualization_elements(self):
        view = [50, 10]
        zoom = 4
        map_height = 800
        map_width = 500
        map_element = MapModule(
            self._simulation_options,
            self.agent_portrayal,
            view,
            zoom,
            map_height,
            map_width,
        )
        process_chart = ChartModule([{'Label': f'Branch {b}', 'Color': color} for b, color in MesaServer.BRANCH_COLORS.items()])

        return [map_element, process_chart]
