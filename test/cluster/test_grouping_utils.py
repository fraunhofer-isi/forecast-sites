# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for cluster/grouping_utils.py — group-to-merged-PU logic."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from cluster.grouping_utils import (
    _GROUP_ID_OFFSET,
    _add_optional,
    _assign_groups_to_sites,
    _collect_pus_from_sites,
    _collect_sub_production_units,
    _create_virtual_site_for_group,
    _merge_production_units_in_group,
    _NullSubProductionUnitFactory,
    _sum_minimum_export_data,
    _union_carriers,
    _union_process_maps,
    assign_groups_after_load,
)
from interpolation.interpolation_data import InterpolationData

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_region():
    region = Mock()
    region.id = 1
    region.data_interface = Mock()
    region.sites = []
    return region


def _make_pu(pu_id, sub_pus=None, min_export=None, carriers=None, processes=None):
    """Build a minimal mock ProductionUnit for testing."""
    pu = MagicMock()
    pu.id = pu_id
    pu.sub_production_units = sub_pus or []
    pu._minimum_export_interpolation_data_in_t = min_export or {}
    pu.available_carriers = carriers or []
    pu._original_processes = processes or []
    pu.sector = Mock()
    pu._optimization_factory = Mock()
    return pu


def _make_site(site_id, pus=None):
    site = Mock()
    site.id = site_id
    site.production_units = list(pus or [])
    site.pipeline_context = {'distance_to_closest_h2_pipeline_in_km': None, 'pipeline_cost_scaling_factor': 1}
    site._h2_first_accessible_year = None
    site.geometry = Mock()
    site._processes = []
    site._carriers = []
    return site


# ---------------------------------------------------------------------------
# assign_groups_after_load
# ---------------------------------------------------------------------------


class TestAssignGroupsAfterLoad:
    def test_skip_when_use_groups_false(self, mock_region):
        regions = {1: mock_region}
        assign_groups_after_load(regions, {'use_groups': False})
        mock_region.data_interface.groups_for_region.assert_not_called()

    def test_skip_when_use_groups_missing(self, mock_region):
        regions = {1: mock_region}
        assign_groups_after_load(regions, {})
        mock_region.data_interface.groups_for_region.assert_not_called()

    def test_queries_region_when_enabled(self, mock_region):
        mock_region.data_interface.groups_for_region.return_value = []
        mock_region.data_interface.group_site_memberships.return_value = []
        regions = {1: mock_region}
        assign_groups_after_load(regions, {'use_groups': True})
        mock_region.data_interface.groups_for_region.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# _assign_groups_to_sites
# ---------------------------------------------------------------------------


class TestAssignGroupsToSites:
    def test_skip_when_no_group_rows(self, mock_region):
        mock_region.data_interface.groups_for_region.return_value = []
        mock_region.data_interface.group_site_memberships.return_value = []
        _assign_groups_to_sites(mock_region, {})
        # No virtual site should have been added
        assert mock_region.sites == []

    def test_skip_when_group_has_no_sites(self, mock_region):
        mock_region.data_interface.groups_for_region.return_value = [{'id_group': 1}]
        mock_region.data_interface.group_site_memberships.return_value = []
        _assign_groups_to_sites(mock_region, {})
        assert mock_region.sites == []

    def test_skip_when_membership_site_not_in_region(self, mock_region):
        mock_region.data_interface.groups_for_region.return_value = [{'id_group': 1}]
        mock_region.data_interface.group_site_memberships.return_value = [
            {'id_group': 1, 'id_site': 999}  # site 999 not in region
        ]
        mock_region.sites = []
        _assign_groups_to_sites(mock_region, {})
        assert mock_region.sites == []

    def test_virtual_site_added_for_group(self, mock_region):
        pu = _make_pu(pu_id=10)
        site = _make_site(site_id=1, pus=[pu])
        mock_region.sites = [site]
        mock_region.data_interface.groups_for_region.return_value = [{'id_group': 1}]
        mock_region.data_interface.group_site_memberships.return_value = [{'id_group': 1, 'id_site': 1}]

        simulation_options = {'start_year': 2025, 'end_year': 2045, 'year_increment': 5}
        with (
            patch('cluster.grouping_utils._merge_production_units_in_group') as mock_merge,
            patch('cluster.grouping_utils._create_virtual_site_for_group') as mock_vsite,
        ):
            mock_merged_pu = Mock()
            mock_merge.return_value = mock_merged_pu
            mock_virtual_site = Mock()
            mock_vsite.return_value = mock_virtual_site

            _assign_groups_to_sites(mock_region, simulation_options)

        # Virtual site should have been appended
        assert mock_virtual_site in mock_region.sites
        mock_merge.assert_called_once_with(1, [pu], simulation_options)
        mock_vsite.assert_called_once_with(1, mock_region, [site], mock_merged_pu)

    def test_original_pus_removed_from_member_sites(self, mock_region):
        pu = _make_pu(pu_id=10)
        site = _make_site(site_id=1, pus=[pu])
        mock_region.sites = [site]
        mock_region.data_interface.groups_for_region.return_value = [{'id_group': 1}]
        mock_region.data_interface.group_site_memberships.return_value = [{'id_group': 1, 'id_site': 1}]

        simulation_options = {'start_year': 2025}
        with (
            patch('cluster.grouping_utils._merge_production_units_in_group') as mock_merge,
            patch('cluster.grouping_utils._create_virtual_site_for_group') as mock_vsite,
        ):
            mock_merge.return_value = Mock()
            mock_vsite.return_value = Mock()
            _assign_groups_to_sites(mock_region, simulation_options)

        # Original site should have its PUs stripped
        assert site.production_units == []

    def test_non_grouped_pus_stay_on_original_site(self, mock_region):
        """PUs not in any group remain on their sites unchanged."""
        grouped_pu = _make_pu(pu_id=10)
        ungrouped_pu = _make_pu(pu_id=20)
        site = _make_site(site_id=1, pus=[grouped_pu, ungrouped_pu])
        _make_site(site_id=2, pus=[ungrouped_pu])
        # Only site 1's first PU is in the group; but both belong to site 1 here
        # More realistic: site 2 is outside the group
        site2 = _make_site(site_id=2, pus=[ungrouped_pu])
        mock_region.sites = [site, site2]
        mock_region.data_interface.groups_for_region.return_value = [{'id_group': 1}]
        mock_region.data_interface.group_site_memberships.return_value = [
            {'id_group': 1, 'id_site': 1}  # only site 1 is in group
        ]

        simulation_options = {'start_year': 2025}
        with (
            patch('cluster.grouping_utils._merge_production_units_in_group') as mock_merge,
            patch('cluster.grouping_utils._create_virtual_site_for_group') as mock_vsite,
        ):
            mock_merge.return_value = Mock()
            mock_vsite.return_value = Mock()
            _assign_groups_to_sites(mock_region, simulation_options)

        # Site 2 (not in group) should retain its PU
        assert ungrouped_pu in site2.production_units

    def test_skip_group_with_no_production_units(self, mock_region):
        """Test that group is skipped when member sites have no production units."""
        site = _make_site(site_id=1, pus=[])  # No PUs
        mock_region.sites = [site]
        mock_region.data_interface.groups_for_region.return_value = [{'id_group': 1}]
        mock_region.data_interface.group_site_memberships.return_value = [{'id_group': 1, 'id_site': 1}]

        simulation_options = {'start_year': 2025}
        with (
            patch('cluster.grouping_utils._merge_production_units_in_group') as mock_merge,
            patch('cluster.grouping_utils._create_virtual_site_for_group') as mock_vsite,
        ):
            _assign_groups_to_sites(mock_region, simulation_options)

        # Should not create virtual site since there are no PUs
        mock_merge.assert_not_called()
        mock_vsite.assert_not_called()


# ---------------------------------------------------------------------------
# _sum_minimum_export_data
# ---------------------------------------------------------------------------


class TestSumMinimumExportData:
    def test_single_pu_returns_same_values(self):
        product = Mock()
        interp = InterpolationData(100.0, 200.0, 150.0)
        pu = _make_pu(pu_id=1, min_export={product: interp})
        result = _sum_minimum_export_data([pu])
        assert result[product].value_for_start_year == 100.0
        assert result[product].value_for_end_year == 200.0
        assert result[product].value_for_interim_year == 150.0

    def test_two_pus_same_product_sums(self):
        product = Mock()
        pu1 = _make_pu(pu_id=1, min_export={product: InterpolationData(100.0, 200.0, 150.0)})
        pu2 = _make_pu(pu_id=2, min_export={product: InterpolationData(50.0, 80.0, 60.0)})
        result = _sum_minimum_export_data([pu1, pu2])
        assert result[product].value_for_start_year == 150.0
        assert result[product].value_for_end_year == 280.0
        assert result[product].value_for_interim_year == 210.0

    def test_different_products_combined(self):
        p1, p2 = Mock(), Mock()
        pu1 = _make_pu(pu_id=1, min_export={p1: InterpolationData(100.0, 200.0)})
        pu2 = _make_pu(pu_id=2, min_export={p2: InterpolationData(50.0, 80.0)})
        result = _sum_minimum_export_data([pu1, pu2])
        assert p1 in result
        assert p2 in result
        assert result[p1].value_for_start_year == 100.0
        assert result[p2].value_for_start_year == 50.0

    def test_none_interim_year_stays_none_when_both_none(self):
        product = Mock()
        pu1 = _make_pu(pu_id=1, min_export={product: InterpolationData(100.0, 200.0, None)})
        pu2 = _make_pu(pu_id=2, min_export={product: InterpolationData(50.0, 80.0, None)})
        result = _sum_minimum_export_data([pu1, pu2])
        assert result[product].value_for_interim_year is None

    def test_none_interim_year_added_to_value(self):
        product = Mock()
        pu1 = _make_pu(pu_id=1, min_export={product: InterpolationData(100.0, 200.0, None)})
        pu2 = _make_pu(pu_id=2, min_export={product: InterpolationData(50.0, 80.0, 60.0)})
        result = _sum_minimum_export_data([pu1, pu2])
        assert result[product].value_for_interim_year == 60.0

    def test_empty_pus(self):
        result = _sum_minimum_export_data([_make_pu(pu_id=1)])
        assert result == {}


# ---------------------------------------------------------------------------
# _add_optional
# ---------------------------------------------------------------------------


class TestAddOptional:
    def test_both_values(self):
        assert _add_optional(3.0, 5.0) == 8.0

    def test_both_none(self):
        assert _add_optional(None, None) is None

    def test_first_none(self):
        assert _add_optional(None, 5.0) == 5.0

    def test_second_none(self):
        assert _add_optional(3.0, None) == 3.0


# ---------------------------------------------------------------------------
# _union_carriers
# ---------------------------------------------------------------------------


class TestUnionCarriers:
    def test_no_overlap(self):
        c1, c2 = Mock(), Mock()
        pu1 = _make_pu(pu_id=1, carriers=[c1])
        pu2 = _make_pu(pu_id=2, carriers=[c2])
        result = _union_carriers([pu1, pu2])
        assert c1 in result
        assert c2 in result

    def test_overlap_deduplicated(self):
        c1 = Mock()
        pu1 = _make_pu(pu_id=1, carriers=[c1])
        pu2 = _make_pu(pu_id=2, carriers=[c1])
        result = _union_carriers([pu1, pu2])
        assert len(result) == 1

    def test_empty_carriers(self):
        pu = _make_pu(pu_id=1, carriers=[])
        assert _union_carriers([pu]) == set()


# ---------------------------------------------------------------------------
# _union_process_maps
# ---------------------------------------------------------------------------


class TestUnionProcessMaps:
    def test_merges_processes_by_id(self):
        p1 = Mock()
        p1.id = 101
        p2 = Mock()
        p2.id = 202
        pu1 = _make_pu(pu_id=1, processes=[p1])
        pu2 = _make_pu(pu_id=2, processes=[p2])
        result = _union_process_maps([pu1, pu2])
        assert 101 in result
        assert 202 in result

    def test_duplicate_process_ids_use_last_value(self):
        p = Mock()
        p.id = 101
        pu1 = _make_pu(pu_id=1, processes=[p])
        pu2 = _make_pu(pu_id=2, processes=[p])
        result = _union_process_maps([pu1, pu2])
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _collect_sub_production_units / _collect_pus_from_sites
# ---------------------------------------------------------------------------


class TestCollect:
    def test_collect_sub_pus(self):
        sp1, sp2, sp3 = Mock(), Mock(), Mock()
        pu1 = _make_pu(pu_id=1, sub_pus=[sp1, sp2])
        pu2 = _make_pu(pu_id=2, sub_pus=[sp3])
        result = _collect_sub_production_units([pu1, pu2])
        assert result == [sp1, sp2, sp3]

    def test_collect_pus_from_sites(self):
        pu1 = _make_pu(pu_id=1)
        pu2 = _make_pu(pu_id=2)
        s1 = _make_site(1, [pu1])
        s2 = _make_site(2, [pu2])
        result = _collect_pus_from_sites([s1, s2])
        assert result == [pu1, pu2]


# ---------------------------------------------------------------------------
# _create_virtual_site_for_group
# ---------------------------------------------------------------------------


class TestCreateVirtualSiteForGroup:
    def test_virtual_site_has_correct_id(self, mock_region):
        merged_pu = Mock()
        merged_pu._site = None
        site = _make_site(site_id=5)
        virtual = _create_virtual_site_for_group(3, mock_region, [site], merged_pu)
        assert virtual.id == _GROUP_ID_OFFSET + 3

    def test_virtual_site_holds_merged_pu(self, mock_region):
        merged_pu = Mock()
        merged_pu._site = None
        site = _make_site(site_id=5)
        virtual = _create_virtual_site_for_group(3, mock_region, [site], merged_pu)
        assert virtual.production_units == [merged_pu]

    def test_merged_pu_site_set_to_virtual(self, mock_region):
        merged_pu = MagicMock()
        site = _make_site(site_id=5)
        virtual = _create_virtual_site_for_group(3, mock_region, [site], merged_pu)
        assert merged_pu._site == virtual

    def test_pipeline_context_copied_from_first_site(self, mock_region):
        merged_pu = Mock()
        merged_pu._site = None
        ctx = {'distance_to_closest_h2_pipeline_in_km': 25.0, 'pipeline_cost_scaling_factor': 2}
        site = _make_site(site_id=5)
        site.pipeline_context = ctx
        virtual = _create_virtual_site_for_group(3, mock_region, [site], merged_pu)
        assert virtual.pipeline_context is ctx

    def test_pool_is_region(self, mock_region):
        merged_pu = Mock()
        merged_pu._site = None
        site = _make_site(site_id=5)
        virtual = _create_virtual_site_for_group(3, mock_region, [site], merged_pu)
        assert virtual.pool is mock_region


class TestNullSubProductionUnitFactory:
    def test_returns_empty_list(self):
        factory = _NullSubProductionUnitFactory()
        result = factory.create_for_start_year(999)
        assert result == []


# ---------------------------------------------------------------------------
# _merge_production_units_in_group
# ---------------------------------------------------------------------------


class TestMergeProductionUnitsInGroup:
    def test_merges_pus_correctly(self):
        """Test that _merge_production_units_in_group creates a merged PU."""
        sp1 = Mock()
        sp1._id_production_unit = 10
        sp2 = Mock()
        sp2._id_production_unit = 20
        pu1 = _make_pu(pu_id=10, sub_pus=[sp1], min_export={}, carriers=[], processes=[])
        pu2 = _make_pu(pu_id=20, sub_pus=[sp2], min_export={}, carriers=[], processes=[])

        simulation_options = {'start_year': 2025}

        # This will call the real function - may fail on incomplete mocks
        # but let's try with proper mocks for ProductionUnit constructor
        with patch('cluster.grouping_utils.ProductionUnit') as mock_pu_class:
            mock_merged = Mock()
            mock_merged.optimization_results = None
            mock_merged._extract_pseudo_optimization_results_for_start_year = Mock(return_value=None)
            mock_merged._initialize_sub_production_inactivity = Mock(return_value={})
            mock_pu_class.return_value = mock_merged

            # Call without process map to simplify
            _merge_production_units_in_group(1, [pu1, pu2], simulation_options)

            # Verify it was called
            mock_pu_class.assert_called_once()
