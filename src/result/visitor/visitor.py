# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from abc import ABC, abstractmethod

from result import aggregation

NOT_IMPLEMENTED = 'You should implement this.'


class Visitor(ABC):
    """Also see https://en.wikipedia.org/wiki/Visitor_pattern"""

    @abstractmethod
    def enter_region(self, region, year):
        raise NotImplementedError(NOT_IMPLEMENTED)

    def exit_region(
        self,
        _region,
        _year,
        _enter_results,
        site_results,
    ):
        results = aggregation.aggregate_dictionaries(site_results)
        return results

    @abstractmethod
    def enter_site(self, _site, _year):
        pass

    def exit_site(
        self,
        _site,
        _year,
        _enter_results,
        production_unit_results,
    ):
        results = aggregation.aggregate_dictionaries(production_unit_results)
        return results

    @abstractmethod
    def enter_production_unit(self, _production_unit, _year):
        pass

    def exit_production_unit(
        self,
        _production_unit,
        _year,
        _enter_results,
        sub_production_unit_results,
    ):
        results = aggregation.aggregate_dictionaries(sub_production_unit_results)
        return results

    @abstractmethod
    def enter_sub_production_unit(self, _production_unit, _year):
        pass

    def exit_sub_production_unit(
        self,
        _production_unit,
        _year,
        _enter_results,
        process_result,
    ):
        # Each sub production unit has only one process. Therefore, there is
        # no need to aggregate results from multiple processes. We just
        # pass on the results from the processes.
        # If required, we could extend the results with results on sub production level.
        results = process_result
        return results

    def enter_process(self, _process, _year):
        return {}

    def exit_process(self, _process, _year, enter_results, output_results):
        process_results = enter_results

        # merge aggregated output_results into process results
        aggregated_output_results = aggregation.aggregate_dictionaries(output_results)
        process_results.update(aggregated_output_results)
        return process_results

    def enter_output(self, _output, _year):
        return {}

    def exit_output(
        self,
        _output,
        _year,
        _enter_results,
    ):
        return {}

    @abstractmethod
    def finalize(self):
        pass
