# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from test_utils.isi_mock import Mock, fixture

from by_product.by_product import ByProduct
from energy_carrier.energy_carrier import EnergyCarrier
from product.product import Product
from result.visitor.indexing_visitor import IndexingVisitor


@fixture
def sut():
    return IndexingVisitor('mocked_simulation_options')


def test_construction(sut):
    assert sut is not None


def test_enter_region(sut):
    mocked_region = Mock()
    mocked_region.id = 'mocked_id_region'
    mocked_region.id_scenario = 'mocked_id_scenario'

    sut.enter_region(mocked_region, 'mocked_year')

    assert sut._region == mocked_region
    assert sut._id_scenario == 'mocked_id_scenario'
    assert sut._id_region == 'mocked_id_region'


def test_enter_site(sut):
    mocked_site = Mock()
    mocked_site.id = 'mocked_id_site'

    sut.enter_site(mocked_site, 'mocked_year')

    assert sut._site == mocked_site
    assert sut._id_site == 'mocked_id_site'


def test_enter_production_unit(sut):
    mocked_production_unit = Mock()
    mocked_production_unit.id = 'mocked_id_production_unit'

    sut.enter_production_unit(mocked_production_unit, 'mocked_year')

    assert sut._production_unit == mocked_production_unit
    assert sut._id_production_unit == 'mocked_id_production_unit'


def test_enter_sub_production_unit(sut):
    mocked_sub_production_unit = Mock()
    mocked_sub_production_unit.id = 'mocked_id_sub_production_unit'

    sut.enter_sub_production_unit(mocked_sub_production_unit, 'mocked_year')

    assert sut._sub_production_unit == mocked_sub_production_unit
    assert sut._id_sub_production_unit == 'mocked_id_sub_production_unit'


def test_enter_process(sut):
    mocked_process = Mock()
    mocked_process.id = 'mocked_id_process'

    sut.enter_process(mocked_process, 'mocked_year')

    assert sut._process == mocked_process
    assert sut._id_process == 'mocked_id_process'


def test_finalize_returns_none(sut):
    assert sut.finalize() is None


class TestEnterOutput:
    def test_energy_carrier(self, sut):
        carrier = EnergyCarrier(10, 'mocked_energy_carrier', Mock())
        mocked_output = Mock()
        mocked_output.carrier = carrier

        sut.enter_output(mocked_output, 'mocked_year')

        assert sut._energy_carrier == carrier
        assert sut._id_energy_carrier == 10

    def test_product(self, sut):
        carrier = Product(11, 'mocked_product', Mock())
        mocked_output = Mock()
        mocked_output.carrier = carrier

        sut.enter_output(mocked_output, 'mocked_year')

        assert sut._product == carrier
        assert sut._id_product == 11

    def test_by_product(self, sut):
        carrier = ByProduct(12, 'mocked_by_product', Mock())
        mocked_output = Mock()
        mocked_output.carrier = carrier

        sut.enter_output(mocked_output, 'mocked_year')

        assert sut._by_product == carrier
        assert sut._id_by_product == 12

    def test_unknown(self, sut):
        carrier = Mock()
        mocked_output = Mock()
        mocked_output.carrier = carrier

        with pytest.raises(TypeError):
            sut.enter_output(mocked_output, 'mocked_year')
