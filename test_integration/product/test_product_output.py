# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import fixture


@fixture
def sut(product_output):
    return product_output


def test_construction(sut):
    assert sut is not None
    assert sut.output_in_t_per_process_count == 10
    assert sut.product.name == 'Steel'


def test__repr__(sut):
    result = repr(sut)
    assert result == 'ProductOutput(Product(1, Steel): 10)'


def test_output_in_euro_per_process_count(sut, co2_price_in_euro_per_t_co2, simulation_options):
    assert sut.output_in_euro_per_process_count(2000, co2_price_in_euro_per_t_co2, simulation_options) == 4300  # 430 €/t * 10 t


def test_output_in_t_for_multiple_executions(sut):
    assert sut.output_in_t(10) == 100  # 10*10
