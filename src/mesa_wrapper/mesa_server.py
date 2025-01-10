# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import profile

from mesa_viz_tornado.ModularVisualization import ModularServer
from mesa_viz_tornado.modules import ChartModule

from mesa_wrapper.map_module import MapModule
from mesa_wrapper.mesa_simulation import MesaSimulation


class MesaServer:
    def __init__(self, simulation_mode, time_span, regions, visitors):
        model_params = {
            'simulation_mode': simulation_mode,
            'time_span': time_span,
            'regions': regions,
            'visitors': visitors,
        }
        self._visualization_server = self._create_visualization_server(model_params)

    def run(self):
        os.path.sep = os.sep  # fixes tornado issue

        profile.run(self._visualization_server.launch())

    @staticmethod
    def agent_portrayal(site_agent):
        """Portrayal Method for canvas"""
        site = site_agent.site
        process_ids = site.process_ids
        portrayal = {'radius': '3'}

        # Primary Steel
        blast_furnace = 11
        if blast_furnace in process_ids:
            portrayal['color'] = 'Tomato'

        direct_reduction_ng = 39
        if direct_reduction_ng in process_ids:
            portrayal['color'] = 'Blue'

        direct_reduction_h2 = 38
        if direct_reduction_h2 in process_ids:
            portrayal['color'] = 'Green'

        # Ammonia
        ammonia_smr = 9
        if ammonia_smr in process_ids:
            portrayal['color'] = 'Grey'

        ammonia_h2 = 8
        if ammonia_h2 in process_ids:
            portrayal['color'] = 'Turquoise'

        # Olefins
        steam_cracking = 100
        if steam_cracking in process_ids:
            portrayal['color'] = 'Sienna'

        ethylene_h2 = 44
        if ethylene_h2 in process_ids:
            portrayal['color'] = 'Purple'

        # Methanol
        methanol_smr = 60
        if methanol_smr in process_ids:
            portrayal['color'] = 'Goldenrod'

        methanol_h2 = 59
        if methanol_h2 in process_ids:
            portrayal['color'] = 'Olive'

        return portrayal

    def _create_visualization_server(self, model_params):
        name = 'Technology Diffusion Model'
        model_class = MesaSimulation
        visualization_elements = self._create_visualization_elements()

        return ModularServer(model_class, visualization_elements, name, model_params)

    def _create_visualization_elements(self):
        view = [50, 10]
        zoom = 4
        map_height = 800
        map_width = 500
        map_element = MapModule(self.agent_portrayal, view, zoom, map_height, map_width)
        process_chart = ChartModule(
            [
                {'Label': 'CH4-DRI', 'Color': 'Blue'},
                {'Label': 'H2-DRI', 'Color': 'Green'},
                {'Label': '11', 'Color': 'Red'},
                {'Label': '12', 'Color': 'Black'},
                {'Label': '13', 'Color': 'Yellow'},
                {'Label': 'agent_count', 'Color': 'Purple'},
            ]
        )
        return [map_element, process_chart]
