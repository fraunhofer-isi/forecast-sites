# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from test_utils.isi_mock import Mock, fixture, patch

from by_product.by_product_factory import ByProductFactory
from data_layer.data_interface import DataInterface
from energy_carrier.energy_carrier_factory import EnergyCarrierFactory
from optimization.optimization_factory import OptimizationFactory
from processes.process_factory import ProcessFactory
from product.product_factory import ProductFactory
from region.region import Region
from region.region_factory import RegionFactory
from sector.sector_factory import SectorFactory
from sites.site_factory import SiteFactory


def data_interface_init_mock(
    self,
    _id_scenario,
    _scenario_options,
    _id_region,
):
    pass


def region_init_mock(
    self,
    _region_id,
    _data_interface,
):
    self.id = None
    self._sites = [Mock(), Mock]
    self.accept = Mock()


@fixture
@patch(OptimizationFactory.__init__, None)
def sut():
    mocked_scenario_options = {'optimization_type': 'mocked_optimization_type'}
    region_factory = RegionFactory('mocked_id_scenario', mocked_scenario_options)
    return region_factory


def test_construction(sut):
    assert sut is not None


@patch(RegionFactory._create_region, 'mocked_region')
def test_create_regions(sut):
    sut._simulation_options['region_ids'] = [1, 2]
    regions = sut.create_regions()
    assert regions[1] == 'mocked_region'
    assert regions[2] == 'mocked_region'


def mocked_energy_carrier_factory_init(self, _data_interface):
    self.create_map = Mock()


def mocked_sector_factory_init(self, _data_interface):
    self.create_map = Mock()


def mocked_product_factory_init(self, _data_interface):
    self.create_map = Mock()


def mocked_by_product_factory_init(self, _data_interface):
    self.create_map = Mock()


def mocked_process_factory_init(
    self,
    _data_interface,
    _energy_carrier_map,
    _product_map,
    _by_product_map,
    _simulation_options,
):
    self.create_map = Mock()


@patch(DataInterface.__init__, None)
@patch(EnergyCarrierFactory.__init__, mocked_energy_carrier_factory_init)
@patch(SectorFactory.__init__, mocked_sector_factory_init)
@patch(ProductFactory.__init__, mocked_product_factory_init)
@patch(ByProductFactory.__init__, mocked_by_product_factory_init)
@patch(ProcessFactory.__init__, mocked_process_factory_init)
@patch(SiteFactory.__init__, None)
@patch(Region.__init__, None)
def test_create_region(sut):
    region = sut._create_region(1)
    assert isinstance(region, Region)
