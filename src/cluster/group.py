# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

# cluster/group.py


class Group:
    """
    Minimal data container holding a group's id, region, and member sites.

    A group defines which sites are treated as one merged production unit during
    optimization. All carrier-pool logic, transport costs, and seeding have been
    removed; the merge happens in grouping_utils before optimization runs.
    """

    def __init__(self, id_group, region):
        self._id = id_group
        self._region = region
        self.sites = []

    @property
    def id(self):
        return self._id

    @property
    def region(self):
        return self._region

    def __repr__(self):
        return f'Group(id={self._id})'
