# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for UpstreamChainBuilder and UpstreamChain classes."""

import unittest

import pandas as pd

from route_analysis.upstream_chain_builder import UpstreamChain, UpstreamChainBuilder


class TestUpstreamChain(unittest.TestCase):
    """Tests for UpstreamChain dataclass."""

    def test_init_default_values(self):
        """Test UpstreamChain initializes with empty collections."""
        chain = UpstreamChain()
        assert len(chain.process_ids) == 0
        assert len(chain.energy_demands) == 0
        assert len(chain.internal_carrier_pool_inputs) == 0
        assert len(chain.purchased_carrier_flows) == 0

    def test_process_ids_is_set(self):
        """Test that process_ids is a set."""
        chain = UpstreamChain()
        assert isinstance(chain.process_ids, set)

    def test_energy_demands_is_list(self):
        """Test that energy_demands is a list."""
        chain = UpstreamChain()
        assert isinstance(chain.energy_demands, list)

    def test_can_add_process_id(self):
        """Test that process_ids can be modified."""
        chain = UpstreamChain()
        chain.process_ids.add(1)
        assert 1 in chain.process_ids
        assert len(chain.process_ids) == 1

    def test_can_append_energy_demand(self):
        """Test that energy demands can be added."""
        chain = UpstreamChain()
        chain.energy_demands.append((1, 2, 100.0, 'GJ'))
        assert len(chain.energy_demands) == 1
        assert chain.energy_demands[0] == (1, 2, 100.0, 'GJ')

    def test_can_append_product_flows(self):
        """Test that product flows can be added."""
        chain = UpstreamChain()
        chain.product_flows.append((1, 2, 3, 50.0))
        assert len(chain.product_flows) == 1

    def test_can_append_carrier_flows(self):
        """Test that carrier flows can be added."""
        chain = UpstreamChain()
        chain.carrier_flows.append((1, 2, 3, 75.0))
        assert len(chain.carrier_flows) == 1

    def test_multiple_energy_demands(self):
        """Test multiple energy demands."""
        chain = UpstreamChain()
        chain.energy_demands.append((1, 2, 100.0, 'GJ'))
        chain.energy_demands.append((3, 4, 50.0, 'GJ'))
        assert len(chain.energy_demands) == 2

    def test_duplicate_process_ids_not_added(self):
        """Test that set doesn't add duplicates."""
        chain = UpstreamChain()
        chain.process_ids.add(1)
        chain.process_ids.add(1)
        assert len(chain.process_ids) == 1

    def test_all_flow_types(self):
        """Test that all flow types can be populated."""
        chain = UpstreamChain()
        chain.process_ids.add(1)
        chain.energy_demands.append((1, 2, 100.0, 'GJ'))
        chain.internal_carrier_pool_inputs.append((1, 2, 50.0))
        chain.purchased_carrier_flows.append((1, 2, 25.0))
        chain.product_flows.append((1, 2, 3, 10.0))
        chain.purchased_product_flows.append((1, 2, 5.0))
        chain.by_product_flows.append((1, 2, 3, 7.0))
        chain.purchased_by_product_flows.append((1, 2, 3.0))
        chain.carrier_flows.append((1, 2, 3, 15.0))
        chain.final_product_outputs.append((1, 2, 20.0))

        assert len(chain.process_ids) == 1
        assert len(chain.energy_demands) == 1
        assert len(chain.internal_carrier_pool_inputs) == 1
        assert len(chain.purchased_carrier_flows) == 1
        assert len(chain.product_flows) == 1
        assert len(chain.purchased_product_flows) == 1
        assert len(chain.by_product_flows) == 1
        assert len(chain.purchased_by_product_flows) == 1
        assert len(chain.carrier_flows) == 1
        assert len(chain.final_product_outputs) == 1


class TestUpstreamChainBuilderConstants(unittest.TestCase):
    """Tests for UpstreamChainBuilder constants and basic properties."""

    def test_max_depth_constant(self):
        """Test MAX_DEPTH constant is set."""
        assert UpstreamChainBuilder.MAX_DEPTH == 10

    def test_default_lhv_constant(self):
        """Test DEFAULT_LHV_GJ_PER_T constant is set."""
        assert UpstreamChainBuilder.DEFAULT_LHV_GJ_PER_T == 40.0

    def test_min_value_constant(self):
        """Test MIN_VALUE constant for filtering insignificant amounts."""
        assert UpstreamChainBuilder.MIN_VALUE == 1e-09

    def test_min_value_very_small(self):
        """Test that MIN_VALUE is actually very small."""
        assert UpstreamChainBuilder.MIN_VALUE < 1e-08


class TestUpstreamChainBuilderInitialization(unittest.TestCase):
    """Tests for UpstreamChainBuilder initialization."""

    def setUp(self):
        """Set up test fixtures."""
        empty_df = pd.DataFrame()
        self.mock_context = {
            'process_product_production_in_t': empty_df,
            'process_by_product_production_in_t': empty_df,
            'process_energy_carrier_production_in_gj': empty_df,
            'process_energy_carrier_energy_demand_in_gj': empty_df,
            'process_energy_carrier_feedstock_demand_in_gj': empty_df,
            'process_product_feedstock_demand_in_t': empty_df,
            'process_by_product_feedstock_demand_in_t': empty_df,
            'production_unit_energy_carrier_purchased_amount_in_gj': empty_df,
            'production_unit_product_purchased_amount_in_t': empty_df,
            'production_unit_by_product_purchased_amount_in_t': empty_df,
        }
        self.lhv_map = {1: 50.0, 2: 45.0}

    def test_init_stores_year(self):
        """Test that initialization stores the year."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        assert builder._year == 2020

    def test_init_creates_year_column_name(self):
        """Test that year column name is formatted correctly."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        assert builder._year_column == 'Y2020'

    def test_init_different_year_column(self):
        """Test year column name for different year."""
        builder = UpstreamChainBuilder(self.mock_context, 2025, self.lhv_map)
        assert builder._year_column == 'Y2025'

    def test_init_stores_lhv_map(self):
        """Test that initialization stores the LHV map."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        assert builder._lhv_map == self.lhv_map

    def test_init_creates_aggregated_tables(self):
        """Test that initialization creates aggregated tables."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        assert builder._product_production is not None
        assert builder._by_product_production is not None
        assert builder._carrier_production is not None

    def test_init_creates_grouped_outputs(self):
        """Test that initialization creates grouped output dicts."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        assert builder._product_outputs_by_process is not None
        assert builder._by_product_outputs_by_process is not None
        assert builder._carrier_outputs_by_process is not None


class TestUpstreamChainBuilderAggregation(unittest.TestCase):
    """Tests for aggregation methods."""

    def setUp(self):
        """Set up test fixtures."""
        empty_df = pd.DataFrame()
        self.mock_context = {
            'process_product_production_in_t': empty_df,
            'process_by_product_production_in_t': empty_df,
            'process_energy_carrier_production_in_gj': empty_df,
            'process_energy_carrier_energy_demand_in_gj': empty_df,
            'process_energy_carrier_feedstock_demand_in_gj': empty_df,
            'process_product_feedstock_demand_in_t': empty_df,
            'process_by_product_feedstock_demand_in_t': empty_df,
            'production_unit_energy_carrier_purchased_amount_in_gj': empty_df,
            'production_unit_product_purchased_amount_in_t': empty_df,
            'production_unit_by_product_purchased_amount_in_t': empty_df,
        }
        self.lhv_map = {1: 50.0}

    def test_aggregate_process_table_empty(self):
        """Test aggregation of empty table."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        result = builder._aggregate_process_table(pd.DataFrame(), 'id_product')
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_aggregate_purchase_table_empty(self):
        """Test aggregation of empty purchase table."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        result = builder._aggregate_purchase_table(pd.DataFrame(), 'id_product')
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_group_by_process_empty(self):
        """Test grouping by process with empty input."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        result = builder._group_by_process({})
        assert isinstance(result, dict)

    def test_group_by_output_empty(self):
        """Test grouping by output with empty input."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        result = builder._group_by_output({})
        assert isinstance(result, dict)


class TestUpstreamChainBuilderProducerMethods(unittest.TestCase):
    """Tests for producer query methods."""

    def setUp(self):
        """Set up test fixtures."""
        empty_df = pd.DataFrame()
        self.mock_context = {
            'process_product_production_in_t': empty_df,
            'process_by_product_production_in_t': empty_df,
            'process_energy_carrier_production_in_gj': empty_df,
            'process_energy_carrier_energy_demand_in_gj': empty_df,
            'process_energy_carrier_feedstock_demand_in_gj': empty_df,
            'process_product_feedstock_demand_in_t': empty_df,
            'process_by_product_feedstock_demand_in_t': empty_df,
            'production_unit_energy_carrier_purchased_amount_in_gj': empty_df,
            'production_unit_product_purchased_amount_in_t': empty_df,
            'production_unit_by_product_purchased_amount_in_t': empty_df,
        }
        self.lhv_map = {1: 50.0}

    def test_product_producers_empty_for_unknown_product(self):
        """Test product_producers returns empty for unknown product ID."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        result = list(builder._product_producers(999))
        assert len(result) == 0

    def test_by_product_producers_empty_for_unknown(self):
        """Test by_product_producers returns empty for unknown ID."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        result = list(builder._by_product_producers(999))
        assert len(result) == 0

    def test_carrier_producers_empty_for_unknown(self):
        """Test carrier_producers returns empty for unknown carrier ID."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, self.lhv_map)
        result = list(builder._carrier_producers(999))
        assert len(result) == 0


if __name__ == '__main__':
    unittest.main()
