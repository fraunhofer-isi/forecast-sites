# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class Carrier:
    def __init__(self, carrier_id: int, name: str) -> None:
        self._id = carrier_id
        self.name = name

    @property
    def id(self) -> int:
        """Carrier ID (semantic: carrier_id)"""
        return self._id

    def __repr__(self) -> str:
        class_name = type(self).__name__
        return f'{class_name}({self.id}, {self.name})'

    @staticmethod
    def _check_for_non_exiting_interim_year(year: int, last_year_str: str) -> None:
        if year < int(last_year_str):
            message = f'Year {year} not found in data.'
            raise KeyError(message)

    @property
    def unit(self):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    @property
    def maximum_production_in_unit(self):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def minimum_use_in_unit(self, _year: int, _simulation_options: dict) -> float:
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def purchase_price_in_euro_per_unit(self, _year: int) -> float:
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def sell_price_in_euro_per_unit(self, _year: int) -> float:
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def upstream_emission_in_t_co2_per_unit(self, _year: int, _simulation_options: dict) -> float:
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def downstream_emission_in_t_co2_per_unit(self, _year: int, _simulation_options: dict) -> float:
        """
        Return downstream emissions in t CO2 per carrier unit for given year.

        Subclasses must implement this and return a numeric emission factor.
        """
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def renewably_bound_co2_emission_in_t_co2_per_unit(self, _year: int, _simulation_options: dict) -> float:
        """
        Return renewably bound emissions (credit) in t CO2 per carrier unit.

        Subclasses must implement this and return a numeric emission factor (often 0).
        """
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def taxes_in_euro_per_unit(self, _year: int, _simulation_options: dict) -> float:
        return 0.0

    def subsidies_in_euro_per_unit(self, _year: int, _simulation_options: dict) -> float:
        return 0.0
