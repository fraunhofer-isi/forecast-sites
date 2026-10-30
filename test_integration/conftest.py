# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from test_utils.isi_mock import Mock, fixture

from energy_carrier.energy_carrier import EnergyCarrier
from energy_carrier.energy_carrier_energy_demand import EnergyCarrierEnergyDemand
from interpolation.interpolation_data import InterpolationData
from optimization.optimization_context import OptimizationContext
from optimization.optimization_factory import OptimizationFactory
from optimization.optimization_type import OptimizationType
from processes.installed_process import InstalledProcess
from processes.process import Process
from processes.process_data import ProcessData
from product.product import Product
from product.product_output import ProductOutput
from production_unit.production_unit import ProductionUnit
from sector.sector import Sector
from sites.site import Site
from sub_production_unit.sub_production_unit import SubProductionUnit

# This file serves as a factory for creating instances of various classes used in integration tests.
# The file conftest.py is automatically recognized by pytest. It does not need to be imported and
# its fixtures can be used across multiple test files.


@fixture
def simulation_options():
    return {
        'start_year': 2000,
        'interim_year': 2025,
        'end_year': 2050,
        'depreciation_period_in_years': 15,
        'emission_limit_in_t_co2': 10e20,
        'rolling_planning_horizon_in_years': 15,
        'emission_constraint_scope': frozenset({'direct', 'upstream', 'renewably_bound'}),
    }


@fixture
def years(simulation_options):
    start_year = simulation_options['start_year']
    end_year = simulation_options['end_year']
    years = range(start_year, end_year + 1)
    return list(years)


@fixture
def annual_range(years):
    def annual_range_function(start_value, end_value):
        min_year = min(years)
        max_year = max(years)
        step = (end_value - start_value) / (max_year - min_year)
        dictionary = {str(year): start_value + (year - min_year) * step for year in years}
        return dictionary

    return annual_range_function


@fixture
def co2_price_in_euro_per_t_co2():
    return 100


@fixture
def energy_carrier(annual_range):
    instance = EnergyCarrier(
        1,
        'Electricity',
        {
            'purchase_price_in_euro_per_gj': annual_range(42, 40),
            'sell_price_in_euro_per_gj': annual_range(40, 38),
            'direct_emission_in_t_co2_per_gj': 0.0,
            'upstream_emission_start_year_in_t_co2_per_gj': 0.10,
            'upstream_emission_end_year_in_t_co2_per_gj': 0.05,
            'renewably_bound_co2_emission_in_t_co2_per_gj': 0.0,
            'minimum_use_start_year_in_gj': 0,
            'minimum_use_end_year_in_gj': 0,
            'subsidies_start_year_in_euro_per_gj': 2,
            'subsidies_interim_year_in_euro_per_gj': 1,
            'subsidies_end_year_in_euro_per_gj': 0,
            'taxes_start_year_in_euro_per_gj': 6,
            'taxes_end_year_in_euro_per_gj': 5,
            'maximum_production_in_gj': 10_000,
        },
    )
    return instance


@fixture
def energy_carrier_energy_demand(energy_carrier, simulation_options):
    demand_in_gj_per_process_count = 200
    efficiency_improvement_interpolation_data = InterpolationData(0, 0)
    instance = EnergyCarrierEnergyDemand(
        energy_carrier,
        demand_in_gj_per_process_count,
        efficiency_improvement_interpolation_data,
        simulation_options,
    )
    return instance


@fixture
def product(annual_range):
    instance = Product(
        1,
        'Steel',
        {
            'purchase_price_in_euro_per_t': annual_range(450, 500),
            'sell_price_in_euro_per_t': annual_range(430, 480),
            'upstream_emission_start_year_in_t_co2_per_t': 1.7,
            'upstream_emission_end_year_in_t_co2_per_t': 1.5,
            'downstream_emission_in_t_co2_per_t': 0.0,
            'maximum_production_in_t': 1_000,
        },
    )
    return instance


@fixture
def product_output(product):
    instance = ProductOutput(product, 10)
    return instance


@fixture
def process(energy_carrier_energy_demand, product_output):
    demands = [energy_carrier_energy_demand]
    outputs = [product_output]
    process_data = ProcessData(
        {
            'lifetime_in_years': 20,
            'depreciation_period': 15,
            'tech_available_at_year': 2020,
            'life_extension_factor': 1.0,
            # TODO #66: explain how realistic value should be chosen for capex per count and choose it
            'capex_start_year_in_euro_per_process_count': 2e6,
            'capex_end_year_in_euro_per_process_count': 2.2e6,
            'opex_start_year_in_euro_per_process_count': 0.15e6,
            'opex_end_year_in_euro_per_process_count': 0.14e6,
            'investment_funding_start_year_in_euro_per_process_count': 0,
            'investment_funding_end_year_in_euro_per_process_count': 0.25e6,
            'efficiency_improvement_start_year': 0,
            'efficiency_improvement_end_year': 0.1,
            'non_energy_direct_process_emission_in_t_co2_per_process_count': 0.05,
            'carbon_capture_rate': 0.0,
        },
        demands,
        outputs,
        (1,),
    )
    instance = Process(1, process_data)
    return instance


@fixture
def sub_production_unit(process):
    instance = SubProductionUnit(
        1,
        1,
        10,
        20,
        2000,
    )

    installed_process = InstalledProcess(process, instance)
    instance.installed_process = installed_process
    return instance


@fixture
def sub_production_unit_factory(sub_production_unit):
    factory = Mock()
    factory.create_for_start_year = Mock([sub_production_unit])
    return factory


@fixture
def optimization_factory():
    instance = OptimizationFactory(OptimizationType.LINEAR_PROGRAMMING)
    return instance


@fixture
def sector():
    demo_sector = Sector(1, 'Demo Sector')
    return demo_sector


@fixture
def region():
    demo_region = Mock()
    demo_region.carrier_availability = Mock(1e10)
    demo_region.interest_rate = 0.05
    demo_region.co2_cost_in_euro_per_t_co2 = Mock(return_value=100)
    return demo_region


@fixture
def production_unit(
    energy_carrier,
    product,
    process,
    sector,
    sub_production_unit_factory,
    optimization_factory,
    site,
    simulation_options,
):
    minimum_export_in_t = {product: InterpolationData(1, 1)}
    process_map = {process.id: process}
    carriers = [energy_carrier, product]

    _production_unit_instance = ProductionUnit(
        1,
        site,
        sector,
        minimum_export_in_t,
        sub_production_unit_factory,
        optimization_factory,
        process_map,
        carriers,
        simulation_options,
    )
    return _production_unit_instance


_site_instance = None


@fixture
def site(energy_carrier, product, process, region, simulation_options):
    # simulation_options is required for proper fixture dependency ordering
    geometry = Mock()
    processes = {1: process}

    instance = Site(
        1,
        region,
        geometry,
        processes,
    )
    return instance


_region_instance = None


@fixture
def site_factory(site):
    instance = Mock()
    instance.create_sites = Mock([site])
    return instance


@fixture
def data_interface():
    instance = Mock()
    return instance


@fixture
def energy_carrier_factory(energy_carrier):
    energy_carrier_map = {energy_carrier.id: energy_carrier}
    factory = Mock()
    factory.create_map = Mock(energy_carrier_map)
    return factory


@fixture
def product_factory(product):
    product_map = {product.id: product}
    factory = Mock()
    factory.create_map = Mock(product_map)
    return factory


@fixture
def optimization_context(simulation_options, region):
    co2_cost_in_euro_per_t_co2 = Mock(100)
    interest_rate = region.interest_rate
    instance = OptimizationContext(
        co2_cost_in_euro_per_t_co2,
        interest_rate,
        simulation_options,
    )
    return instance
