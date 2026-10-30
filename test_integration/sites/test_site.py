# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


from test_utils.isi_mock import Mock, fixture


@fixture
def sut(site):
    return site


def test_construction(sut):
    assert sut is not None


def test_used_process_ids(sut):
    """Should return list of process IDs used at the site."""
    result = sut.used_process_ids
    assert isinstance(result, list)


def test_sectors_property(sut):
    """Should return set of sectors used by production units."""
    sectors = sut.sectors
    assert isinstance(sectors, set)


def test_accept(sut):
    """Should accept visitor pattern."""
    visitor = Mock()
    visitor.enter_site = Mock(return_value={})
    visitor.exit_site = Mock(return_value={})
    year = 2020

    result = sut.accept(visitor, year)
    assert result is not None


def test_optimize(sut):
    """Should run optimization for the site."""
    year = 2020
    # Site.optimize() does not return anything, just executes for production units
    sut.optimize(year)
    # Method should complete without errors
    assert True


def test_number_of_process_usages(sut):
    """Should return the number of times a process is used."""
    process = Mock()
    result = sut.number_of_process_usages(process)
    assert isinstance(result, int)


def test_carrier_availability(sut):
    """Should return carrier availability at the site."""
    carrier = Mock()
    carrier.name = 'Electricity'
    year = 2020
    result = sut.carrier_availability(carrier, year)
    assert result is not None


def test_consume_purchased_carrier_amounts_for_start_year(sut):
    """Should consume purchased carrier amounts for start year."""
    start_year = 2020
    # Method should complete without errors
    sut.consume_purchased_carrier_amounts_for_start_year(start_year)
    assert True


def test_consume_purchased_carrier_amount(sut):
    """Should consume purchased carrier amount for a specific carrier, amount, year and context."""
    carrier = Mock()
    carrier.unit = Mock()
    amount = 100
    year = 2020
    context = Mock()
    # Method should complete without errors
    sut.consume_purchased_carrier_amount(carrier, amount, year, context)
    assert True
