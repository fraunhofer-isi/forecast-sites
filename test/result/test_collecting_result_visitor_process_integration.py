# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for CollectingResultVisitor process collection methods (lines 199-859)."""

import unittest
from unittest import mock

from by_product.by_product import ByProduct
from carrier.carrier_unit import CarrierUnit
from energy_carrier.energy_carrier import EnergyCarrier
from energy_carrier.energy_carrier_energy_demand import EnergyCarrierEnergyDemand
from product.product import Product
from result.collecting_result_visitor import CollectingResultVisitor


class TestCollectProcessResultsFlow(unittest.TestCase):
    """Test _collect_process_results and its sub-methods (lines 386-859)."""

    def setUp(self):
        """Set up visitor with mocked storage methods to bypass DataFrame issues."""
        self.visitor = CollectingResultVisitor({'start_year': 2020})
        self.visitor._co2_cost_in_euro_per_t_co2 = 50.0
        self.visitor._interest_rate = 0.05

        # Mock process
        self.process = mock.MagicMock()
        self.process.demands = []
        self.process.emission.direct_emissions_in_t_co2.return_value = 6.0
        self.process.emission.direct_energy_emissions_in_t_co2.return_value = 4.0
        self.process.emission.captured_emission_in_t_co2.return_value = 1.0
        self.process.emission.direct_non_energy_emission_cost_in_euro.return_value = 1.0
        self.process.emission.saving_due_to_captured_emission_in_euro.return_value = 0.3
        self.process.emission.direct_emission_cost_in_euro.return_value = 2.0
        self.process.emission.direct_energy_emission_cost_in_euro.return_value = 1.5
        self.process.emission.direct_non_energy_emissions_in_t_co2.return_value = 2.0
        self.process.emission.energy_carrier_production_direct_emissions_in_t_co2.return_value = {}
        self.process.annuity_on_investment_in_euro_per_process_count.return_value = 10.0
        self.process.purchase_cost_in_euro_per_process_count.return_value = 5.0
        self.process.opex_in_euro_per_process_count.return_value = 8.0
        self.process.production_cost_in_euro_per_process_count.return_value = 25.0
        self.visitor._process = self.process

        # Mock sub_production_unit
        self.sub_pu = mock.MagicMock()
        self.sub_pu.process_execution_count = 2.0
        self.sub_pu.opex_in_euro.return_value = 16.0
        self.sub_pu.annuity_on_investment_in_euro.return_value = 20.0
        self.sub_pu.new_investment_in_euro.return_value = 200.0
        self.visitor._sub_production_unit = self.sub_pu

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_energy_carrier_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_process_emission_aggregates')
    def test_collect_process_results_calls_all_collectors(self, mock_agg, mock_ec, mock_add):
        """Lines 386-429: _collect_process_results orchestrates all collectors."""
        result = self.visitor._collect_process_results(2020)

        assert result == {}
        assert mock_add.call_count >= 14

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_energy_carrier_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_process_emission_aggregates')
    def test_collect_process_results_with_demands(self, mock_agg, mock_ec, mock_add):
        """Line 419: _collect_process_results iterates over demands."""
        mock_demand = mock.MagicMock(spec=EnergyCarrierEnergyDemand)
        mock_carrier = mock.MagicMock(spec=EnergyCarrier)
        mock_carrier.id = 5
        mock_carrier.unit = CarrierUnit.GJ
        mock_demand.carrier = mock_carrier
        mock_demand.demand_in_gj.return_value = 100.0
        mock_demand.direct_emission_in_t_co2.return_value = 0.5
        mock_demand.purchase_cost_in_euro_per_process_count.return_value = 50.0
        self.process.demands = [mock_demand]

        result = self.visitor._collect_process_results(2020)

        assert result == {}
        # Energy carrier entry called for demand metrics
        assert mock_ec.call_count >= 3

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    def test_collect_process_execution_count(self, mock_add):
        """Lines 444-451: collects process execution count."""
        count = self.visitor._collect_process_execution_count(2020)

        assert count == 2.0
        mock_add.assert_called()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    def test_collect_process_carrier_cost(self, mock_add):
        """Lines 453-460: collects carrier cost per process count."""
        self.visitor._collect_process_carrier_cost_in_euro_per_process_count(2020)

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    def test_collect_process_opex_in_euro(self, mock_add):
        """Lines 462-468: collects opex in euro."""
        self.visitor._collect_process_opex_in_euro(2020, {'start_year': 2020})

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    def test_collect_process_opex_per_count(self, mock_add):
        """Lines 470-476: collects opex per process count."""
        self.visitor._collect_process_opex_in_euro_per_process_count(2020, {'start_year': 2020})

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    def test_collect_process_annuity(self, mock_add):
        """Lines 478-486: collects annuity on investment."""
        self.visitor._collect_process_annuity_on_investment_in_euro(2020, 0.05, {'start_year': 2020})

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    def test_collect_process_annuity_per_count(self, mock_add):
        """Lines 488-501: collects annuity per process count."""
        self.visitor._collect_process_annuity_on_investment_in_euro_per_count(2020, 0.05, {'start_year': 2020})

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_energy_carrier_entry')
    def test_collect_energy_carrier_production_emission(self, mock_add):
        """Lines 431-442: collects energy carrier production direct emission."""
        mock_carrier = mock.MagicMock()
        mock_carrier.id = 7
        self.process.emission.energy_carrier_production_direct_emissions_in_t_co2.return_value = {mock_carrier: 2.5}

        self.visitor._collect_process_energy_carrier_production_direct_emission_in_t_co2(2020, 2.0)

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_energy_carrier_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_process_emission_aggregates')
    def test_collect_demand_results_energy_carrier_energy(self, mock_agg, mock_ec, mock_add):
        """Lines 509-583: demand collection for EnergyCarrierEnergyDemand."""
        mock_demand = mock.MagicMock(spec=EnergyCarrierEnergyDemand)
        mock_carrier = mock.MagicMock(spec=EnergyCarrier)
        mock_carrier.id = 5
        mock_carrier.unit = CarrierUnit.GJ
        mock_demand.carrier = mock_carrier
        mock_demand.demand_in_gj.return_value = 100.0
        mock_demand.direct_emission_in_t_co2.return_value = 0.5
        mock_demand.purchase_cost_in_euro_per_process_count.return_value = 50.0

        self.visitor._collect_demand_results(2020, mock_demand, 2.0)

        # Should call _add_energy_carrier_entry for purchase cost, demand, and emission
        assert mock_ec.call_count >= 3

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_energy_carrier_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_process_emission_aggregates')
    def test_collect_demand_results_energy_carrier_feedstock(self, mock_agg, mock_ec, mock_add):
        """Lines 584-600: demand collection for feedstock (non-EnergyCarrierEnergyDemand)."""
        mock_demand = mock.MagicMock()  # Not EnergyCarrierEnergyDemand
        mock_carrier = mock.MagicMock(spec=EnergyCarrier)
        mock_carrier.id = 7
        mock_carrier.unit = CarrierUnit.GJ
        mock_demand.carrier = mock_carrier
        mock_demand.demand_in_gj.return_value = 200.0
        mock_demand.purchase_cost_in_euro_per_process_count.return_value = 30.0

        self.visitor._collect_demand_results(2020, mock_demand, 2.0)

        # Should call _add_energy_carrier_entry for feedstock cost and demand
        assert mock_ec.call_count >= 2

    @mock.patch.object(CollectingResultVisitor, '_add_product_entry')
    def test_collect_demand_results_product(self, mock_add):
        """Lines 629-654: demand collection for Product."""
        mock_demand = mock.MagicMock()
        mock_product = mock.MagicMock(spec=Product)
        mock_product.id = 10
        mock_product.unit = CarrierUnit.T
        mock_demand.carrier = mock_product
        mock_demand.demand_in_t.return_value = 50.0
        mock_demand.purchase_cost_in_euro_per_process_count.return_value = 20.0

        self.visitor._collect_demand_results(2020, mock_demand, 2.0)

        # Should call _add_product_entry for purchase cost and demand
        assert mock_add.call_count == 2

    @mock.patch.object(CollectingResultVisitor, '_add_product_entry')
    def test_collect_demand_results_by_product(self, mock_add):
        """Lines 602-627: demand collection for ByProduct."""
        mock_demand = mock.MagicMock()
        mock_by_product = mock.MagicMock(spec=ByProduct)
        mock_by_product.id = 20
        mock_by_product.unit = CarrierUnit.T
        mock_demand.carrier = mock_by_product
        mock_demand.demand_in_t.return_value = 30.0
        mock_demand.purchase_cost_in_euro_per_process_count.return_value = 15.0

        self.visitor._collect_demand_results(2020, mock_demand, 2.0)

        # Should call _add_product_entry for purchase cost and demand
        assert mock_add.call_count == 2

    @mock.patch.object(CollectingResultVisitor, '_add_energy_carrier_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_product_entry')
    def test_collect_output_results_energy_carrier(self, mock_prod, mock_ec):
        """Lines 659-667: output results for energy carrier."""
        self.visitor._id_energy_carrier = 5
        self.visitor._id_product = None
        self.visitor._id_by_product = None

        mock_output = mock.MagicMock()
        mock_output.output_in_gj.return_value = 500.0
        mock_output.carrier = mock.MagicMock(spec=EnergyCarrier)

        result = self.visitor._collect_output_results(mock_output, 2020)

        assert result == {}
        mock_ec.assert_called()

    @mock.patch.object(CollectingResultVisitor, '_add_product_entry')
    def test_collect_output_results_product(self, mock_add):
        """Lines 669-676: output results for product."""
        self.visitor._id_energy_carrier = None
        self.visitor._id_product = 10
        self.visitor._id_by_product = None

        mock_output = mock.MagicMock()
        mock_output.output_in_t.return_value = 200.0
        mock_output.carrier = mock.MagicMock(spec=Product)

        result = self.visitor._collect_output_results(mock_output, 2020)

        assert result == {}
        mock_add.assert_called()

    @mock.patch.object(CollectingResultVisitor, '_add_by_product_entry')
    def test_collect_output_results_by_product(self, mock_add):
        """Lines 677-683: output results for by-product."""
        self.visitor._id_energy_carrier = None
        self.visitor._id_product = None
        self.visitor._id_by_product = 20

        mock_output = mock.MagicMock()
        mock_output.output_in_t.return_value = 100.0
        mock_output.carrier = mock.MagicMock(spec=ByProduct)

        result = self.visitor._collect_output_results(mock_output, 2020)

        assert result == {}
        mock_add.assert_called()

    @mock.patch.object(CollectingResultVisitor, '_add_product_entry')
    def test_collect_production_cost_product(self, mock_add):
        """Lines 700-711: production cost for product."""
        self.visitor._id_product = 10
        mock_output = mock.MagicMock()
        mock_output.carrier = mock.MagicMock(spec=Product)

        self.visitor._collect_production_cost_in_euro_per_process_count(mock_output, 2020)

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_by_product_entry')
    def test_collect_production_cost_by_product(self, mock_add):
        """Lines 712-718: production cost for by-product."""
        self.visitor._id_by_product = 20
        mock_output = mock.MagicMock()
        mock_output.carrier = mock.MagicMock(spec=ByProduct)

        self.visitor._collect_production_cost_in_euro_per_process_count(mock_output, 2020)

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_energy_carrier_entry')
    def test_collect_production_cost_energy_carrier(self, mock_add):
        """Lines 719-725: production cost for energy carrier."""
        self.visitor._id_energy_carrier = 5
        mock_output = mock.MagicMock()
        mock_output.carrier = mock.MagicMock(spec=EnergyCarrier)

        self.visitor._collect_production_cost_in_euro_per_process_count(mock_output, 2020)

        mock_add.assert_called_once()

    def test_collect_production_cost_unknown_carrier_raises(self):
        """Lines 727-728: NotImplementedError for unknown carrier type."""
        import pytest

        mock_output = mock.MagicMock()
        mock_output.carrier = mock.MagicMock()  # Not Product, ByProduct, or EnergyCarrier

        with pytest.raises(NotImplementedError, match='not yet implemented'):
            self.visitor._collect_production_cost_in_euro_per_process_count(mock_output, 2020)

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_process_emission_aggregates')
    def test_collect_process_direct_emission(self, mock_agg, mock_add):
        """Lines 739-750: direct emission collection."""
        self.visitor._collect_process_direct_emission_in_t_co2(2020, 2.0)

        mock_add.assert_called_once()
        mock_agg.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    def test_collect_process_direct_emission_cost(self, mock_add):
        """Lines 752-765: direct emission cost collection."""
        self.visitor._collect_process_direct_emission_cost_in_euro(2020, 2.0)

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    def test_collect_process_direct_energy_emission(self, mock_add):
        """Lines 771-778: direct energy emission collection."""
        self.visitor._collect_process_direct_energy_emission_in_t_co2(2020, 2.0)

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    @mock.patch.object(CollectingResultVisitor, '_add_process_emission_aggregates')
    def test_collect_process_captured_emission(self, mock_agg, mock_add):
        """Lines 834-846: captured emission collection."""
        self.visitor._collect_process_captured_emission_in_t_co2(2020, 2.0)

        mock_add.assert_called_once()
        mock_agg.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    def test_collect_process_investment(self, mock_add):
        """Lines 730-737: investment collection."""
        self.visitor._collect_process_investment_in_euro(2020, {'start_year': 2020})

        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_entry')
    def test_exit_sub_production_unit(self, mock_add):
        """Lines 199-213: exit_sub_production_unit collects production cost."""
        mock_sub_pu = mock.MagicMock()
        mock_sub_pu.production_cost_in_euro.return_value = 500.0

        result = self.visitor.exit_sub_production_unit(mock_sub_pu, 2020, {}, {'key': 'val'})

        assert result == {'key': 'val'}
        mock_add.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_region_energy_carrier_entry_or_accumulate')
    @mock.patch.object(CollectingResultVisitor, '_add_sector_energy_carrier_entry_or_accumulate')
    def test_handle_ec_result_purchased_amount(self, mock_sector, mock_region):
        """Lines 335->339: purchased_amount branch with append_unit=True."""
        self.visitor._add_region_and_sector_energy_carrier_aggregates('purchased_amount', 5, 2020, 100.0, append_unit=True)

        mock_region.assert_called_once()
        mock_sector.assert_called_once()

    @mock.patch.object(CollectingResultVisitor, '_add_region_entry_or_accumulate')
    @mock.patch.object(CollectingResultVisitor, '_add_sector_entry_or_accumulate')
    def test_handle_ec_result_non_purchased(self, mock_sector, mock_region):
        """Lines 353-358: non-purchased result branch."""
        self.visitor._add_region_and_sector_energy_carrier_aggregates(
            'upstream_emission_in_t_co2', 5, 2020, 0.5, append_unit=False
        )

        mock_region.assert_called_once()
        mock_sector.assert_called_once()
