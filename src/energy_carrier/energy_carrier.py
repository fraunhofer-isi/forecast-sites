# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from carrier.carrier import Carrier
from carrier.carrier_unit import CarrierUnit
from interpolation import interpolator
from interpolation.interpolation_data import InterpolationData


class EnergyCarrier(Carrier):
    def __init__(self, id_energy_carrier: int, name: str, data: dict) -> None:
        super().__init__(id_energy_carrier, name)

        self._purchase_price_in_euro_per_gj = data['purchase_price_in_euro_per_gj']
        self._sell_price_in_euro_per_gj = data['sell_price_in_euro_per_gj']

        self._direct_emission_in_t_co2_per_gj = data['direct_emission_in_t_co2_per_gj']

        self._maximum_production_in_gj = data['maximum_production_in_gj']

        self._upstream_emission_interpolation_data_in_t_co2_per_gj = InterpolationData(
            data['upstream_emission_start_year_in_t_co2_per_gj'],
            data['upstream_emission_end_year_in_t_co2_per_gj'],
        )

        # Downstream emissions for energy carriers are equal to direct emissions
        # per user instruction: downstream_emission = direct_emission
        self._downstream_emission_in_t_co2_per_gj = data.get(
            'downstream_emission_in_t_co2_per_gj', self._direct_emission_in_t_co2_per_gj
        )

        self._renewably_bound_co2_emission_in_t_co2_per_gj = data['renewably_bound_co2_emission_in_t_co2_per_gj']

        self._minimum_use_interpolation_data_in_gj = InterpolationData(
            data['minimum_use_start_year_in_gj'],
            data['minimum_use_end_year_in_gj'],
        )

        self._subsidies_interpolation_data_in_euro_per_gj = InterpolationData(
            data['subsidies_start_year_in_euro_per_gj'],
            data['subsidies_end_year_in_euro_per_gj'],
            data['subsidies_interim_year_in_euro_per_gj'],
        )

        self._taxes_interpolation_data_in_euro_per_gj = InterpolationData(
            data['taxes_start_year_in_euro_per_gj'],
            data['taxes_end_year_in_euro_per_gj'],
        )

    @property
    def unit(self) -> CarrierUnit:
        gj = CarrierUnit.GJ
        return gj

    @property
    def direct_emission_in_t_co2_per_gj(self) -> float:
        return self._direct_emission_in_t_co2_per_gj

    @property
    def maximum_production_in_unit(self) -> float:
        return self._maximum_production_in_gj

    def upstream_emission_in_t_co2_per_gj(self, year: int, simulation_options: dict) -> float:
        return interpolator.interpolate(
            year,
            simulation_options,
            self._upstream_emission_interpolation_data_in_t_co2_per_gj,
        )

    def upstream_emission_in_t_co2_per_unit(self, year: int, simulation_options: dict) -> float:
        emission = self.upstream_emission_in_t_co2_per_gj(year, simulation_options)
        return emission

    def downstream_emission_in_t_co2_per_unit(self, _year: int, _simulation_options: dict) -> float:
        return self._downstream_emission_in_t_co2_per_gj

    def renewably_bound_co2_emission_in_t_co2_per_unit(self, _year: int, _simulation_options: dict) -> float:
        return self._renewably_bound_co2_emission_in_t_co2_per_gj

    def purchase_price_in_euro_per_gj(self, year: int) -> float:
        year_string = str(year)
        if year_string in self._purchase_price_in_euro_per_gj:
            return self._purchase_price_in_euro_per_gj[year_string]
        last_year_str = max(self._purchase_price_in_euro_per_gj.keys())
        self._check_for_non_exiting_interim_year(year, last_year_str)
        return self._purchase_price_in_euro_per_gj[last_year_str]

    def purchase_price_in_euro_per_unit(self, year: int) -> float:
        return self.purchase_price_in_euro_per_gj(year)

    def purchase_cost_in_euro(self, amount_in_gj: float, year: int) -> float:
        price_in_euro_per_gj = self.purchase_price_in_euro_per_gj(year)
        cost_in_euro = amount_in_gj * price_in_euro_per_gj
        return cost_in_euro

    def sell_price_in_euro_per_unit(self, year: int) -> float:
        return self.sell_price_in_euro_per_gj(year)

    def sell_price_in_euro_per_gj(self, year: int) -> float:
        year_string = str(year)
        if year_string in self._sell_price_in_euro_per_gj:
            return self._sell_price_in_euro_per_gj[year_string]
        last_year_str = max(self._sell_price_in_euro_per_gj.keys())
        self._check_for_non_exiting_interim_year(year, last_year_str)
        return self._sell_price_in_euro_per_gj[last_year_str]

    def minimum_use_in_unit(self, year: int, simulation_options: dict) -> float:
        return interpolator.interpolate(
            year,
            simulation_options,
            self._minimum_use_interpolation_data_in_gj,
        )

    def subsidies_in_euro_per_gj(self, year: int, simulation_options: dict) -> float:
        return interpolator.interpolate_cost(
            year,
            simulation_options,
            self._subsidies_interpolation_data_in_euro_per_gj,
        )

    def taxes_in_euro_per_gj(self, year: int, simulation_options: dict) -> float:
        return interpolator.interpolate(
            year,
            simulation_options,
            self._taxes_interpolation_data_in_euro_per_gj,
        )

    def taxes_in_euro_per_unit(self, year: int, simulation_options: dict) -> float:
        return self.taxes_in_euro_per_gj(year, simulation_options)

    def subsidies_in_euro_per_unit(self, year: int, simulation_options: dict) -> float:
        return self.subsidies_in_euro_per_gj(year, simulation_options)
