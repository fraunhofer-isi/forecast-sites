# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import MagicMock

from result.collecting_result_visitor import CollectingResultVisitor


def test_initialization_creates_empty_results():
    sut = CollectingResultVisitor({'start_year': 2020})

    assert sut._absolute_results is not None
    assert sut._specific_results is not None
    assert isinstance(sut._absolute_results, dict)
    assert isinstance(sut._specific_results, dict)
    # Verify key tables are initialized
    assert 'process_production_cost_in_euro' in sut._absolute_results
    assert 'production_unit_energy_carrier_taxes_in_euro' in sut._absolute_results
    assert 'production_unit_energy_carrier_subsidies_in_euro' in sut._absolute_results
    assert 'process_carrier_cost_in_euro_per_process_count' in sut._specific_results


def test_enter_site_returns_none():
    sut = CollectingResultVisitor({'start_year': 2020})

    assert sut.enter_site(MagicMock(), 2020) is None


def test_enter_production_unit_returns_none():
    sut = CollectingResultVisitor({'start_year': 2020})

    assert sut.enter_production_unit(MagicMock(), 2020) is None


def test_enter_sub_production_unit_returns_none():
    sut = CollectingResultVisitor({'start_year': 2020})

    assert sut.enter_sub_production_unit(MagicMock(), 2020) is None


def test_initialization_sets_co2_and_interest_rate_to_none():
    sut = CollectingResultVisitor({'start_year': 2020})

    # Before entering a region, these should be None
    assert sut._co2_cost_in_euro_per_t_co2 is None
    assert sut._interest_rate is None
