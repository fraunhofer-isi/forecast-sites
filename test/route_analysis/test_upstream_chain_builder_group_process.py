# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for UpstreamChainBuilder._group_by_process method."""

import unittest

from route_analysis.upstream_chain_builder import UpstreamChainBuilder


class TestUpstreamChainBuilderGroupByProcess(unittest.TestCase):
    """Test UpstreamChainBuilder._group_by_process static method."""

    def test_group_by_process_empty(self):
        """Test _group_by_process with empty dict."""
        result = UpstreamChainBuilder._group_by_process({})
        assert result == {}

    def test_group_by_process_single_process(self):
        """Test _group_by_process with single process."""
        values = {(1, 10): 100.0, (1, 20): 50.0}
        result = UpstreamChainBuilder._group_by_process(values)

        assert 1 in result
        assert len(result[1]) == 2
        assert (10, 100.0) in result[1]
        assert (20, 50.0) in result[1]

    def test_group_by_process_multiple_processes(self):
        """Test _group_by_process with multiple processes."""
        values = {
            (1, 10): 100.0,
            (1, 20): 50.0,
            (2, 30): 75.0,
            (2, 40): 25.0,
        }
        result = UpstreamChainBuilder._group_by_process(values)

        assert len(result) == 2
        assert len(result[1]) == 2
        assert len(result[2]) == 2
