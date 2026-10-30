# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for cluster/group.py — minimal data container."""

from unittest.mock import Mock

import pytest

from cluster.group import Group


@pytest.fixture
def mock_region():
    region = Mock()
    region.id = 1
    return region


class TestGroupConstruction:
    """Group is a data container: id, region, sites."""

    def test_group_holds_id(self):
        group = Group(id_group=42, region=Mock())
        assert group.id == 42

    def test_group_holds_region(self):
        region = Mock()
        group = Group(id_group=1, region=region)
        assert group.region is region

    def test_group_starts_with_empty_sites_list(self):
        group = Group(id_group=1, region=Mock())
        assert group.sites == []

    def test_sites_can_be_appended(self):
        group = Group(id_group=1, region=Mock())
        mock_site = Mock()
        group.sites.append(mock_site)
        assert mock_site in group.sites

    def test_repr_shows_id(self):
        group = Group(id_group=7, region=Mock())
        assert '7' in repr(group)
