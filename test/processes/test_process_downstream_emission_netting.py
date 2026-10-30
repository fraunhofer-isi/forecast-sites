# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Pins that downstream CO2 is priced on the NET carrier amount, not on the gross output.

This is the regression guard for the downstream emission double counting audit. A process that
both produces and consumes the same carrier must only be charged for what actually leaves the
system boundary. The netting is not implemented explicitly: it emerges because every Output and
every Demand applies the SAME emission adjusted price (sell_price - downstream * co2_price), so
the gross terms cancel and only the net amount remains.

That symmetry is load bearing. If any single Output or Demand implementation dropped its
'- downstream * co2_price' term, the cancellation would silently break and the objective would
price emissions on gross flows while the emission constraint still counts net flows.
"""

import pytest
from test_utils.isi_mock import Mock, fixture
from test_utils.process_data_stub import make_process_data_stub

from interpolation.interpolation_data import InterpolationData
from processes.process import Process
from product.product_feedstock_demand import ProductFeedstockDemand
from product.product_output import ProductOutput

SELL_PRICE_IN_EURO_PER_T = 100.0
DOWNSTREAM_EMISSION_IN_T_CO2_PER_T = 1.0
CO2_PRICE_IN_EURO_PER_T_CO2 = 20.0

GROSS_OUTPUT_IN_T = 10.0
GROSS_DEMAND_IN_T = 4.0
NET_OUTPUT_IN_T = GROSS_OUTPUT_IN_T - GROSS_DEMAND_IN_T

YEAR = 2023


@fixture
def simulation_options():
    return {
        'start_year': 2000,
        'interim_year': 2025,
        'end_year': 2050,
    }


@fixture
def product():
    product = Mock()
    product.sell_price_in_euro_per_t = Mock(SELL_PRICE_IN_EURO_PER_T)
    product.downstream_emission_in_t_co2_per_unit = Mock(DOWNSTREAM_EMISSION_IN_T_CO2_PER_T)
    return product


@fixture
def sut(product, simulation_options):
    """A process that produces and consumes the same product, so a net amount remains."""
    output = ProductOutput(product, GROSS_OUTPUT_IN_T)
    demand = ProductFeedstockDemand(
        product,
        GROSS_DEMAND_IN_T,
        InterpolationData(0, 0),  # no efficiency improvement, so the raw demand is used
        simulation_options,
    )
    process_data = make_process_data_stub(demands=(demand,), outputs=(output,))
    return Process(1, process_data)


class TestProcessDownstreamEmissionNetting:
    def test_value_added_is_based_on_the_net_amount(self, sut, simulation_options):
        """Should price the net amount, because the gross output and gross demand terms cancel."""
        emission_adjusted_price = SELL_PRICE_IN_EURO_PER_T - DOWNSTREAM_EMISSION_IN_T_CO2_PER_T * CO2_PRICE_IN_EURO_PER_T_CO2

        value_added = sut._value_added_in_euro_per_process_count(
            YEAR,
            CO2_PRICE_IN_EURO_PER_T_CO2,
            simulation_options,
        )

        assert value_added == pytest.approx(NET_OUTPUT_IN_T * emission_adjusted_price)

    def test_downstream_charge_applies_to_the_net_amount_only(self, sut, simulation_options):
        """Should charge downstream CO2 for 6 net units, not for the 10 gross units produced."""
        value_added_with_co2_price = sut._value_added_in_euro_per_process_count(
            YEAR,
            CO2_PRICE_IN_EURO_PER_T_CO2,
            simulation_options,
        )
        value_added_without_co2_price = sut._value_added_in_euro_per_process_count(YEAR, 0.0, simulation_options)

        downstream_charge = value_added_without_co2_price - value_added_with_co2_price

        expected_charge = NET_OUTPUT_IN_T * DOWNSTREAM_EMISSION_IN_T_CO2_PER_T * CO2_PRICE_IN_EURO_PER_T_CO2
        assert downstream_charge == pytest.approx(expected_charge)

        gross_charge = GROSS_OUTPUT_IN_T * DOWNSTREAM_EMISSION_IN_T_CO2_PER_T * CO2_PRICE_IN_EURO_PER_T_CO2
        assert downstream_charge != pytest.approx(gross_charge)
