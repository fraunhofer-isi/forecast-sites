# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from sector.sector import Sector


class SectorFactory:
    def __init__(self, data_interface):
        self._sector_data = data_interface.sector_data

    def create_map(self):
        sector_map = {}
        for _, row in self._sector_data.iterrows():
            id_sector = row['id']
            name = row['name']
            sector_map[id_sector] = Sector(id_sector, name)
        return sector_map
