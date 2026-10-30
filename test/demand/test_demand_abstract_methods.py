# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from unittest.mock import MagicMock

from demand.demand import Demand
from demand.demand_factory import DemandFactory


class TestDemandAbstractMethods:
    """Test that abstract methods in Demand raise NotImplementedError."""

    def test_purchase_cost_raises_not_implemented(self):
        demand = Demand(None, None, {})
        with pytest.raises(NotImplementedError, match='Needs to be implemented'):
            demand.purchase_cost_in_euro_per_process_count(2020)

    def test_opportunity_cost_raises_not_implemented(self):
        demand = Demand(None, None, {})
        with pytest.raises(NotImplementedError, match='Needs to be implemented'):
            demand.opportunity_cost_in_euro_per_process_count(2020, 100)

    def test_subsidies_raises_not_implemented(self):
        demand = Demand(None, None, {})
        with pytest.raises(NotImplementedError, match='Needs to be implemented'):
            demand.subsidies_in_euro_per_process_count(2020, {})

    def test_taxes_raises_not_implemented(self):
        demand = Demand(None, None, {})
        with pytest.raises(NotImplementedError, match='Needs to be implemented'):
            demand.taxes_in_euro_per_process_count(2020, {})


class TestDemandFactoryAbstractMethods:
    """Test that abstract methods in DemandFactory raise NotImplementedError."""

    def test_demand_raises_not_implemented(self):
        factory = DemandFactory(None, None, None, {})
        with pytest.raises(NotImplementedError, match='Needs to be implemented'):
            factory._demand(None)

    def test_demand_entries_for_process_raises_key_error_when_no_entries(self):
        """Test that _demand_entries_for_process raises KeyError when no entries found."""
        mock_data = MagicMock()
        mock_data.query.side_effect = KeyError('id_process')
        
        factory = DemandFactory(mock_data, None, None, {})
        
        with pytest.raises(KeyError, match='No entries for id_process 123'):
            factory._demand_entries_for_process(123)

