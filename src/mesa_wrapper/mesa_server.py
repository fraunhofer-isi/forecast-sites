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
            "simulation_mode": simulation_mode,
            "time_span": time_span,
            "regions": regions,
            "visitors": visitors,
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
        portrayal = {"radius": "3"}

        # Primary Steel
        if 11 in process_ids:
            portrayal["color"] = "Tomato"
        if 39 in process_ids:
            portrayal["color"] = "Blue"
        if 38 in process_ids:
            portrayal["color"] = "Green"

        # Ammonia
        if 9 in process_ids:
            portrayal["color"] = "Grey"
        if 8 in process_ids:
            portrayal["color"] = "Turquoise"

        # Olefins
        if 100 in process_ids:
            portrayal["color"] = "Sienna"
        if 44 in process_ids:
            portrayal["color"] = "Purple"

        # Methanol
        if 60 in process_ids:
            portrayal["color"] = "Goldenrod"
        if 59 in process_ids:
            portrayal["color"] = "Olive"

        return portrayal

    def _create_visualization_server(self, model_params):
        name = "Technology Diffusion Model"
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
                {"Label": "CH4-DRI", "Color": "Blue"},
                {"Label": "H2-DRI", "Color": "Green"},
                {"Label": "11", "Color": "Red"},
                {"Label": "12", "Color": "Black"},
                {"Label": "13", "Color": "Yellow"},
                {"Label": "agent_count", "Color": "Purple"},
            ]
        )
        return [map_element, process_chart]
