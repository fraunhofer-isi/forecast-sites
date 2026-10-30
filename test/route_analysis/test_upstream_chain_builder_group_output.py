# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for UpstreamChainBuilder._group_by_output method."""

import unittest

from route_analysis.upstream_chain_builder import UpstreamChainBuilder


class TestUpstreamChainBuilderGroupByOutput(unittest.TestCase):
    """Test UpstreamChainBuilder._group_by_output static method."""

    def test_group_by_output_empty(self):
        """Test _group_by_output with empty dict."""
        result = UpstreamChainBuilder._group_by_output({})
        assert result == {}

    def test_group_by_output_single_output(self):
        """Test _group_by_output with single output."""
        values = {(1, 10): 100.0, (2, 10): 50.0}
        result = UpstreamChainBuilder._group_by_output(values)

        assert 10 in result
        assert len(result[10]) == 2
        assert (1, 100.0) in result[10]
        assert (2, 50.0) in result[10]

    def test_group_by_output_multiple_outputs(self):
        """Test _group_by_output with multiple outputs."""
        values = {
            (1, 10): 100.0,
            (2, 10): 50.0,
            (3, 20): 75.0,
            (4, 20): 25.0,
        }
        result = UpstreamChainBuilder._group_by_output(values)

        assert len(result) == 2
        assert len(result[10]) == 2
        assert len(result[20]) == 2
