# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
import logging

from optimization.optimization_context import OptimizationContext
from result.visitor.entity import Entity


class Site(Entity):
    def __init__(self, id_site, region, geometry, processes):
        super().__init__(id_site)

        self.production_units = []
        self._region = region
        self.pool = region
        self.group = None
        self.geometry = geometry
        self._processes = processes
        # Carriers are not filtered per site. ProductionUnits receive the full
        # carrier list via ProductionUnitFactory — availability is handled later in optimization.
        self.pipeline_context = None
        self._optimization_context = None
        self._h2_first_accessible_year = None
        # When True, initialize_context skips pipeline lookups and uses the
        # pre-set pipeline_context and _h2_first_accessible_year. Used by
        # virtual group sites that copy context from a real member site.
        self._skip_pipeline_init = False

    @property
    def used_process_ids(self):
        unique_process_ids = set()
        for production_unit in self.production_units:
            current_process_ids = production_unit.used_process_ids
            unique_process_ids.update(current_process_ids)
        process_ids = list(unique_process_ids)
        return process_ids

    @property
    def sectors(self):
        used_sectors = {production_unit.sector for production_unit in self.production_units}
        return used_sectors

    def initialize_context(self, simulation):
        if not self._skip_pipeline_init:
            self.pipeline_context = self._initialize_pipeline_context(simulation)
            self._h2_first_accessible_year = self._compute_h2_first_accessible_year(simulation)
        co2_cost_in_euro_per_t_co2 = self._region.co2_cost_in_euro_per_t_co2
        interest_rate = self._region.interest_rate
        simulation_options = simulation.options
        self._optimization_context = OptimizationContext(
            co2_cost_in_euro_per_t_co2,
            interest_rate,
            simulation_options,
        )
        self._optimization_context.site = self

    def optimize(self, year):
        for production_unit in self.production_units:
            production_unit.optimize(year, self._optimization_context)

    @staticmethod
    def _is_hydrogen_carrier(carrier):
        """
        Return True for any hydrogen carrier variant, matched by name.

        Matching by name is robust to ID variations across datasets
        ('H2' and 'Hydrogen' use IDs 15 or 26 depending on sector;
        'Renewable H2' uses IDs 1015 or 1026).
        """
        name_lower = carrier.name.lower()
        return 'h2' in name_lower or 'hydrogen' in name_lower

    def can_purchase(self, carrier, year=None):
        if self._is_hydrogen_carrier(carrier):
            return self._h2_is_accessible(year)
        return True

    def shared_pool_for(self, carrier):
        return self.pool

    def accept(self, visitor, year):
        enter_results = visitor.enter_site(self, year)
        child_results = {}
        for production_unit in self.production_units:
            child_result = production_unit.accept(visitor, year)
            child_results[production_unit] = child_result
        results = visitor.exit_site(
            self,
            year,
            enter_results,
            child_results,
        )
        return results

    def number_of_process_usages(self, process):
        number_of_usages = 0
        for production_units in self.production_units:
            number_of_usages += production_units.number_of_process_usages(process)
        return number_of_usages

    def carrier_availability(self, carrier, year):
        if self._is_hydrogen_carrier(carrier):
            if not self._h2_is_accessible(year):
                logging.info('Hydrogen carrier "%s" is not accessible at site %s.', carrier.name, self.id)
                return 0
            logging.info('Hydrogen carrier "%s" is accessible at site %s.', carrier.name, self.id)

        return self.pool.carrier_availability(carrier, year)

    def consume_purchased_carrier_amounts_for_start_year(self, start_year):
        for production_unit in self.production_units:
            production_unit.consume_purchased_carrier_amounts(start_year, self._optimization_context)

    def consume_purchased_carrier_amount(self, carrier, amount, year, context):
        pool = self.shared_pool_for(carrier)
        pool.consume_purchased_carrier_amount(carrier, amount, year, context)

    def _h2_is_accessible(self, year=None):
        # Year-aware path: used by multi-period LP to model future backbone expansion
        if year is not None and self._h2_first_accessible_year is not None:
            return year >= self._h2_first_accessible_year

        # Backward-compatible path: used by single-period LP and SiteAgent
        distance_threshold_in_km = 50
        pipeline_context = self.pipeline_context
        distance_to_closest_h2_pipeline_in_km = pipeline_context['distance_to_closest_h2_pipeline_in_km']
        if distance_to_closest_h2_pipeline_in_km is None:
            return False
        return distance_to_closest_h2_pipeline_in_km < distance_threshold_in_km

    def _compute_h2_first_accessible_year(self, simulation):
        """
        Return the first year H2 becomes accessible at this site.

        Returns None when pipelines are not modeled (H2 always accessible).
        Returns float('inf') when no H2 pipeline is within range (never accessible).
        """
        if not simulation.is_recognizing_pipelines:
            return None  # Distance defaults to 0 → always accessible via old path

        pipeline_site_relations = self._pipeline_site_relations(simulation)
        pipelines_df = simulation.pipelines.pipelines_df
        distance_threshold_in_km = 50

        earliest_year = None
        for pipeline_id in pipelines_df.index:
            relation = pipeline_site_relations.loc[(self.id, pipeline_id)]
            distance = relation['distance']
            if distance is None or distance >= distance_threshold_in_km:
                continue
            commissioning_year = pipelines_df.loc[pipeline_id, 'Commissioning Year First']
            if earliest_year is None or commissioning_year < earliest_year:
                earliest_year = commissioning_year

        return earliest_year if earliest_year is not None else float('inf')

    def _initialize_pipeline_context(self, simulation):
        distance_to_closest_h2_pipeline_in_km = self._distance_to_closest_h2_pipeline_in_km(simulation)

        pipeline_context = {
            'distance_to_closest_h2_pipeline_in_km': distance_to_closest_h2_pipeline_in_km,
        }
        return pipeline_context

    def _distance_to_closest_h2_pipeline_in_km(self, simulation):
        if simulation.is_recognizing_pipelines:
            distance_to_closest_h2_pipeline = self._determine_distance_to_closest_h2_pipeline_in_km(simulation)
        else:
            distance_to_closest_h2_pipeline = 0
        return distance_to_closest_h2_pipeline

    def _determine_distance_to_closest_h2_pipeline_in_km(self, simulation):
        pipeline_site_relations = self._pipeline_site_relations(simulation)
        grouped_pipeline_site_relations = pipeline_site_relations.groupby('mode')
        number_of_groups = grouped_pipeline_site_relations.ngroups
        required_group_size = 2
        if number_of_groups == required_group_size:
            h2_group = grouped_pipeline_site_relations.get_group('H2')
            closest_h2_pipeline = h2_group.sort_values(by='distance').head(1)
            distance = closest_h2_pipeline['distance'].to_numpy()[0]
        else:
            distance = None

        return distance

    def _pipeline_site_relations(self, simulation):
        site_relations = simulation.pipeline_site_relations
        site_ids = site_relations.index.get_level_values('site')
        site_pipeline_indices = site_ids == self.id
        site_pipeline_relation = site_relations.loc[site_pipeline_indices]
        return site_pipeline_relation
