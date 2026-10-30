# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from carrier.carrier import Carrier
from carrier.carrier_unit import CarrierUnit
from interpolation import interpolator
from interpolation.interpolation_data import InterpolationData


class Product(Carrier):
    def __init__(self, id_product: int, name: str, data: dict) -> None:
        super().__init__(id_product, name)
        self.name = name

        self._purchase_price_in_euro_per_t = data['purchase_price_in_euro_per_t']
        self._sell_price_in_euro_per_t = data['sell_price_in_euro_per_t']

        self._upstream_emission_interpolation_data_in_t_co2_per_t = InterpolationData(
            data['upstream_emission_start_year_in_t_co2_per_t'],
            data['upstream_emission_end_year_in_t_co2_per_t'],
        )
        self._renewably_bound_co2_emission_in_t_co2_per_t = 0

        self._downstream_emission_in_t_co2_per_t = data['downstream_emission_in_t_co2_per_t']

        self._maximum_production_in_t = data['maximum_production_in_t']

    @property
    def unit(self) -> CarrierUnit:
        t = CarrierUnit.T
        return t

    @property
    def maximum_production_in_unit(self) -> float:
        return self._maximum_production_in_t

    def minimum_use_in_unit(self, _year: int, _simulation_options: dict) -> float:
        return 0

    def purchase_price_in_euro_per_t(self, year: int) -> float:
        year_string = str(year)
        if year_string in self._purchase_price_in_euro_per_t:
            return self._purchase_price_in_euro_per_t[year_string]
        last_year_str = max(self._purchase_price_in_euro_per_t.keys())
        self._check_for_non_exiting_interim_year(year, last_year_str)
        return self._purchase_price_in_euro_per_t[last_year_str]

    def purchase_price_in_euro_per_unit(self, year: int) -> float:
        return self.purchase_price_in_euro_per_t(year)

    def purchase_cost_in_euro(self, amount_in_t: float, year: int) -> float:
        price_in_euro_per_t = self.purchase_price_in_euro_per_t(year)
        cost_in_euro = amount_in_t * price_in_euro_per_t
        return cost_in_euro

    def sell_price_in_euro_per_unit(self, year: int) -> float:
        return self.sell_price_in_euro_per_t(year)

    def sell_price_in_euro_per_t(self, year: int) -> float:
        year_string = str(year)
        if year_string in self._sell_price_in_euro_per_t:
            return self._sell_price_in_euro_per_t[year_string]
        last_year_str = max(self._sell_price_in_euro_per_t.keys())
        self._check_for_non_exiting_interim_year(year, last_year_str)
        return self._sell_price_in_euro_per_t[last_year_str]

    def upstream_emission_in_t_co2_per_t(self, year: int, simulation_options: dict) -> float:
        return interpolator.interpolate(
            year,
            simulation_options,
            self._upstream_emission_interpolation_data_in_t_co2_per_t,
        )

    def upstream_emission_in_t_co2_per_unit(self, year: int, simulation_options: dict) -> float:
        emission = self.upstream_emission_in_t_co2_per_t(year, simulation_options)
        return emission

    def downstream_emission_in_t_co2_per_unit(self, _year: int, _simulation_options: dict) -> float:
        return self._downstream_emission_in_t_co2_per_t

    def renewably_bound_co2_emission_in_t_co2_per_unit(self, _year: int, _simulation_options: dict) -> float:
        return self._renewably_bound_co2_emission_in_t_co2_per_t
