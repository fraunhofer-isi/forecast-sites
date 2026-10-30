# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import Mock, fixture


@fixture
def sut(region):
    return region


def test_construction(sut):
    assert sut is not None


def test_id_scenario(sut):
    """Should return the id_scenario from data_interface."""
    result = sut.id_scenario
    assert result is not None


def test_site_data(sut):
    """Should return site_data from data_interface."""
    result = sut.site_data
    assert result is not None


def test_accept(sut):
    """Should accept visitor pattern and delegate to sites."""
    visitor = Mock()
    visitor.enter_region = Mock(return_value={})
    visitor.exit_region = Mock(return_value={})
    year = 2020

    result = sut.accept(visitor, year)

    assert result is not None


def test_consume_purchased_carrier_amounts_for_start_year(sut):
    """Should delegate consumption calculation to sites."""
    result = sut.consume_purchased_carrier_amounts_for_start_year
    assert result is not None


def test_consume_purchased_carrier_amount(sut):
    """Should calculate total carrier consumption across all sites."""
    carrier = Mock()
    year = 2020

    result = sut.consume_purchased_carrier_amount(carrier, year)
    assert result is not None


def test_provide_produced_carrier_amounts_for_start_year(sut):
    """Should delegate production calculation to sites."""
    result = sut.provide_produced_carrier_amounts_for_start_year
    assert result is not None


def test_provide_produced_carrier_amount(sut):
    """Should calculate total carrier production across all sites."""
    carrier = Mock()
    year = 2020

    result = sut.provide_produced_carrier_amount(carrier, year)
    assert result is not None


def test_co2_cost_in_euro_per_t_co2(sut):
    """Should return CO2 cost from region."""
    year = 2020
    result = sut.co2_cost_in_euro_per_t_co2(year)
    assert result == 100


def test_carrier_availability(sut):
    """Should return carrier availability."""
    carrier = Mock()
    result = sut.carrier_availability(carrier)
    assert result == 1e10


def test_process_ids_for_site(sut):
    """Should return process IDs for a given site."""
    site = Mock()

    result = sut.process_ids_for_site(site)
    assert result is not None
