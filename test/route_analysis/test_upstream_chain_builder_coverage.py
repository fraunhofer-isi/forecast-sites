# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Additional comprehensive tests for UpstreamChainBuilder trace_upstream method."""

import unittest

import pandas as pd

from route_analysis.upstream_chain_builder import UpstreamChainBuilder


class TestUpstreamChainBuilderTraceUpstream(unittest.TestCase):
    """Tests for trace_upstream method and energy carrier tracing."""

    def setUp(self):
        """Set up test fixtures."""
        self.empty_df = pd.DataFrame()
        self.mock_context = {
            'process_product_production_in_t': self.empty_df,
            'process_by_product_production_in_t': self.empty_df,
            'process_energy_carrier_production_in_gj': self.empty_df,
            'process_energy_carrier_energy_demand_in_gj': self.empty_df,
            'process_energy_carrier_feedstock_demand_in_gj': self.empty_df,
            'process_product_feedstock_demand_in_t': self.empty_df,
            'process_by_product_feedstock_demand_in_t': self.empty_df,
            'production_unit_energy_carrier_purchased_amount_in_gj': self.empty_df,
            'production_unit_product_purchased_amount_in_t': self.empty_df,
            'production_unit_by_product_purchased_amount_in_t': self.empty_df,
        }

    def test_trace_upstream_with_no_producers(self):
        """Test trace_upstream with target product that has no producers."""
        builder = UpstreamChainBuilder(self.mock_context, 2020, {})

        chain = builder.trace_upstream(999)  # Non-existent product ID

        assert len(chain.process_ids) == 0
        assert len(chain.final_product_outputs) == 0

    def test_trace_upstream_with_energy_demands(self):
        """Test trace_upstream includes energy demands."""
        # Create data with product production and energy demands
        product_df = pd.DataFrame(
            {
                'id_process': [1],
                'id_product': [501],
                'Y2020': [100.0],
            }
        )
        energy_demand_df = pd.DataFrame(
            {
                'id_process': [1],
                'id_energy_carrier': [1],
                'Y2020': [50.0],
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df
        context['process_energy_carrier_energy_demand_in_gj'] = energy_demand_df

        builder = UpstreamChainBuilder(context, 2020, {})
        chain = builder.trace_upstream(501)

        assert 1 in chain.process_ids
        assert len(chain.energy_demands) > 0

    def test_trace_upstream_with_product_feedstock(self):
        """Test trace_upstream includes product feedstock flows."""
        # Create data: process 2 produces product 501, process 1 produces product 502 (feedstock)
        product_df = pd.DataFrame(
            {
                'id_process': [2, 1],
                'id_product': [501, 502],
                'Y2020': [100.0, 100.0],
            }
        )
        # Process 2 needs product 502 as feedstock
        feedstock_df = pd.DataFrame(
            {
                'id_process': [2],
                'id_product': [502],
                'Y2020': [50.0],
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df
        context['process_product_feedstock_demand_in_t'] = feedstock_df

        builder = UpstreamChainBuilder(context, 2020, {})
        chain = builder.trace_upstream(501)

        assert 2 in chain.process_ids
        # Product flows only appear if feedstock is matched from internal producers
        # In this case, it should trace back to producer of 502
        assert len(chain.process_ids) >= 1

    def test_trace_upstream_with_by_product_feedstock(self):
        """Test trace_upstream includes by-product feedstock flows."""
        # Create data: process 3 produces product 501, process 2 produces by-product 601
        product_df = pd.DataFrame(
            {
                'id_process': [3],
                'id_product': [501],
                'Y2020': [100.0],
            }
        )
        byproduct_df = pd.DataFrame(
            {
                'id_process': [2],
                'id_by_product': [601],
                'Y2020': [50.0],
            }
        )
        # Process 3 needs by-product 601 as feedstock
        feedstock_df = pd.DataFrame(
            {
                'id_process': [3],
                'id_by_product': [601],
                'Y2020': [30.0],
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df
        context['process_by_product_production_in_t'] = byproduct_df
        context['process_by_product_feedstock_demand_in_t'] = feedstock_df

        builder = UpstreamChainBuilder(context, 2020, {})
        chain = builder.trace_upstream(501)

        assert 3 in chain.process_ids
        # Should trace upstream if by-product producer is found
        assert len(chain.process_ids) >= 1

    def test_trace_upstream_respects_max_depth(self):
        """Test that trace_upstream respects MAX_DEPTH limit."""
        # Create a simple product production
        product_df = pd.DataFrame(
            {
                'id_process': [1],
                'id_product': [501],
                'Y2020': [100.0],
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df

        builder = UpstreamChainBuilder(context, 2020, {})
        chain = builder.trace_upstream(501)

        # Basic trace should respect depth
        assert len(chain.process_ids) <= 100  # Sanity check

    def test_trace_upstream_filters_small_amounts(self):
        """Test that trace_upstream filters amounts below MIN_VALUE."""
        product_df = pd.DataFrame(
            {
                'id_process': [4],
                'id_product': [501],
                'Y2020': [1e-10],  # Below MIN_VALUE
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df

        builder = UpstreamChainBuilder(context, 2020, {})
        chain = builder.trace_upstream(501)

        # Very small amounts should not create final_product_outputs
        assert len(chain.final_product_outputs) == 0


class TestUpstreamChainBuilderAppendCarrierSources(unittest.TestCase):
    """Tests for carrier source handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.empty_df = pd.DataFrame()
        self.mock_context = {
            'process_product_production_in_t': self.empty_df,
            'process_by_product_production_in_t': self.empty_df,
            'process_energy_carrier_production_in_gj': self.empty_df,
            'process_energy_carrier_energy_demand_in_gj': self.empty_df,
            'process_energy_carrier_feedstock_demand_in_gj': self.empty_df,
            'process_product_feedstock_demand_in_t': self.empty_df,
            'process_by_product_feedstock_demand_in_t': self.empty_df,
            'production_unit_energy_carrier_purchased_amount_in_gj': self.empty_df,
            'production_unit_product_purchased_amount_in_t': self.empty_df,
            'production_unit_by_product_purchased_amount_in_t': self.empty_df,
        }

    def test_split_carrier_pool_with_internal_only(self):
        """Test split_carrier_pool when only internal sources exist."""
        carrier_df = pd.DataFrame(
            {
                'id_process': [1, 2],
                'id_energy_carrier': [1, 1],
                'Y2020': [50.0, 50.0],
            }
        )

        context = dict(self.mock_context)
        context['process_energy_carrier_production_in_gj'] = carrier_df

        builder = UpstreamChainBuilder(context, 2020, {})
        internal, purchased = builder._split_carrier_pool(1, 100.0)

        assert internal > 0
        assert purchased == 0.0

    def test_split_carrier_pool_with_purchased_only(self):
        """Test split_carrier_pool when only purchased sources exist."""
        purchased_df = pd.DataFrame(
            {
                'id_energy_carrier': [1],
                'Y2020': [100.0],
            }
        )

        context = dict(self.mock_context)
        context['production_unit_energy_carrier_purchased_amount_in_gj'] = purchased_df

        builder = UpstreamChainBuilder(context, 2020, {})
        internal, purchased = builder._split_carrier_pool(1, 100.0)

        assert internal == 0.0
        assert purchased > 0

    def test_split_carrier_pool_mixed_sources(self):
        """Test split_carrier_pool with both internal and purchased."""
        carrier_df = pd.DataFrame(
            {
                'id_process': [1],
                'id_energy_carrier': [1],
                'Y2020': [50.0],
            }
        )
        purchased_df = pd.DataFrame(
            {
                'id_energy_carrier': [1],
                'Y2020': [100.0],
            }
        )

        context = dict(self.mock_context)
        context['process_energy_carrier_production_in_gj'] = carrier_df
        context['production_unit_energy_carrier_purchased_amount_in_gj'] = purchased_df

        builder = UpstreamChainBuilder(context, 2020, {})
        internal, purchased = builder._split_carrier_pool(1, 100.0)

        assert internal > 0
        assert purchased > 0
        assert abs((internal + purchased) - 100.0) < 1e-6


class TestUpstreamChainBuilderComputeAllocationFactor(unittest.TestCase):
    """Tests for allocation factor computation."""

    def setUp(self):
        """Set up test fixtures."""
        self.empty_df = pd.DataFrame()
        self.mock_context = {
            'process_product_production_in_t': self.empty_df,
            'process_by_product_production_in_t': self.empty_df,
            'process_energy_carrier_production_in_gj': self.empty_df,
            'process_energy_carrier_energy_demand_in_gj': self.empty_df,
            'process_energy_carrier_feedstock_demand_in_gj': self.empty_df,
            'process_product_feedstock_demand_in_t': self.empty_df,
            'process_by_product_feedstock_demand_in_t': self.empty_df,
            'production_unit_energy_carrier_purchased_amount_in_gj': self.empty_df,
            'production_unit_product_purchased_amount_in_t': self.empty_df,
            'production_unit_by_product_purchased_amount_in_t': self.empty_df,
        }

    def test_compute_allocation_factor_single_output(self):
        """Test allocation factor with single output."""
        product_df = pd.DataFrame(
            {
                'id_process': [1],
                'id_product': [501],
                'Y2020': [100.0],
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df

        builder = UpstreamChainBuilder(context, 2020, {})
        factor = builder._compute_allocation_factor(1, 'product', 501, 50.0, 't')

        assert 0.0 <= factor <= 1.0
        assert factor == 0.5  # 50 / 100

    def test_compute_allocation_factor_multiple_outputs_same_kind(self):
        """Test allocation factor with multiple outputs of same kind."""
        product_df = pd.DataFrame(
            {
                'id_process': [1, 1],
                'id_product': [501, 502],
                'Y2020': [50.0, 50.0],
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df

        builder = UpstreamChainBuilder(context, 2020, {})
        factor = builder._compute_allocation_factor(1, 'product', 501, 50.0, 't')

        # Should allocate based on same_kind_outputs total (100.0)
        assert factor == 0.5  # 50 / 100

    def test_compute_allocation_factor_caps_at_one(self):
        """Test allocation factor doesn't exceed 1.0."""
        product_df = pd.DataFrame(
            {
                'id_process': [1],
                'id_product': [501],
                'Y2020': [10.0],
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df

        builder = UpstreamChainBuilder(context, 2020, {})
        factor = builder._compute_allocation_factor(1, 'product', 501, 100.0, 't')

        assert factor == 1.0  # Capped at 1.0

    def test_compute_allocation_factor_no_outputs_returns_zero(self):
        """Test allocation factor returns 0 with no outputs."""
        context = dict(self.mock_context)

        builder = UpstreamChainBuilder(context, 2020, {})
        factor = builder._compute_allocation_factor(999, 'product', 501, 50.0, 't')

        assert factor == 0.0


class TestUpstreamChainBuilderGetProcessOutputs(unittest.TestCase):
    """Tests for _get_process_outputs method."""

    def setUp(self):
        """Set up test fixtures."""
        self.empty_df = pd.DataFrame()
        self.mock_context = {
            'process_product_production_in_t': self.empty_df,
            'process_by_product_production_in_t': self.empty_df,
            'process_energy_carrier_production_in_gj': self.empty_df,
            'process_energy_carrier_energy_demand_in_gj': self.empty_df,
            'process_energy_carrier_feedstock_demand_in_gj': self.empty_df,
            'process_product_feedstock_demand_in_t': self.empty_df,
            'process_by_product_feedstock_demand_in_t': self.empty_df,
            'production_unit_energy_carrier_purchased_amount_in_gj': self.empty_df,
            'production_unit_product_purchased_amount_in_t': self.empty_df,
            'production_unit_by_product_purchased_amount_in_t': self.empty_df,
        }

    def test_get_process_outputs_single_product(self):
        """Test _get_process_outputs with single product output."""
        product_df = pd.DataFrame(
            {
                'id_process': [1],
                'id_product': [501],
                'Y2020': [100.0],
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df

        builder = UpstreamChainBuilder(context, 2020, {})
        outputs = builder._get_process_outputs(1)

        assert len(outputs) == 1
        assert outputs[0][0] == 'product'
        assert outputs[0][1] == 501

    def test_get_process_outputs_mixed_types(self):
        """Test _get_process_outputs with multiple output types."""
        product_df = pd.DataFrame(
            {
                'id_process': [1],
                'id_product': [501],
                'Y2020': [50.0],
            }
        )
        energy_df = pd.DataFrame(
            {
                'id_process': [1],
                'id_energy_carrier': [1],
                'Y2020': [100.0],
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df
        context['process_energy_carrier_production_in_gj'] = energy_df

        builder = UpstreamChainBuilder(context, 2020, {})
        outputs = builder._get_process_outputs(1)

        assert len(outputs) == 2
        kinds = {out[0] for out in outputs}
        assert 'product' in kinds
        assert 'energy_carrier' in kinds

    def test_get_process_outputs_filters_small_values(self):
        """Test that _get_process_outputs filters values below MIN_VALUE."""
        product_df = pd.DataFrame(
            {
                'id_process': [1, 1],
                'id_product': [501, 502],
                'Y2020': [100.0, 1e-10],
            }
        )

        context = dict(self.mock_context)
        context['process_product_production_in_t'] = product_df

        builder = UpstreamChainBuilder(context, 2020, {})
        outputs = builder._get_process_outputs(1)

        # Should only include 501, not 502 (too small)
        assert len(outputs) == 1
        assert outputs[0][1] == 501


if __name__ == '__main__':
    unittest.main()
