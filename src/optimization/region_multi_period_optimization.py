# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

import numpy as np
from scipy import optimize as scipy_optimize

from carrier.carrier_unit import CarrierUnit
from optimization.region_multi_period_optimization_result import RegionMultiPeriodOptimizationResult
from processes.installed_process import InstalledProcess
from utils.time_utils import create_time_span


class RegionMultiPeriodOptimization:
    """Joint LP: all production units x all simulation periods with perfect foresight."""

    def __init__(self, year, region, production_units, context):
        self._year = year
        self._region = region
        self._production_units = list(production_units)
        self._context = context

        simulation_options = context.simulation_options
        interest_rate = context.interest_rate

        self._carriers = self._determine_shared_carriers()
        self._num_carriers = len(self._carriers)
        self._process_options_by_pu = {pu: list(pu.available_process_options) for pu in self._production_units}
        self._num_proc_by_pu = {pu: len(opts) for pu, opts in self._process_options_by_pu.items()}

        self._simulation_periods = self._compute_simulation_periods(year, simulation_options)
        self._num_periods = len(self._simulation_periods)

        self._vars_per_period_by_pu = {pu: self._num_proc_by_pu[pu] + self._num_carriers for pu in self._production_units}

        # Section 1: exec + carrier variables [per PU, per period]
        self._offsets_by_pu = self._compute_exec_carrier_offsets()
        # Section 2: new_capacity variables [per PU, per period]
        self._new_capacity_offsets_by_pu = self._compute_new_capacity_offsets()
        self._total_variables = self._compute_total_variables()

        self._c = self._build_objective(interest_rate, simulation_options)
        self._a_ub, self._b_ub = self._build_constraints(simulation_options)
        self._bounds = self._build_bounds()

    # ── Index helpers ──────────────────────────────────────────────────

    def _determine_shared_carriers(self):
        if not self._production_units:
            return []
        return list(self._production_units[0].available_carriers)

    @staticmethod
    def _compute_simulation_periods(start_year, simulation_options):
        return create_time_span(start_year, simulation_options['end_year'], simulation_options['year_increment'])

    def _compute_exec_carrier_offsets(self):
        offsets = {}
        offset = 0
        for pu in self._production_units:
            offsets[pu] = offset
            offset += self._vars_per_period_by_pu[pu] * self._num_periods
        return offsets

    def _compute_new_capacity_offsets(self):
        # new_capacity section starts after all exec+carrier variables
        section_start = sum(self._vars_per_period_by_pu[pu] * self._num_periods for pu in self._production_units)
        offsets = {}
        offset = section_start
        for pu in self._production_units:
            offsets[pu] = offset
            offset += self._num_proc_by_pu[pu] * self._num_periods
        return offsets

    def _compute_total_variables(self):
        exec_carrier = sum(self._vars_per_period_by_pu[pu] * self._num_periods for pu in self._production_units)
        new_cap = sum(self._num_proc_by_pu[pu] * self._num_periods for pu in self._production_units)
        return exec_carrier + new_cap

    def _exec_index(self, pu, period_index, process_option_index):
        return self._offsets_by_pu[pu] + period_index * self._vars_per_period_by_pu[pu] + process_option_index

    def _carrier_index(self, pu, period_index, carrier_index):
        return self._offsets_by_pu[pu] + period_index * self._vars_per_period_by_pu[pu] + self._num_proc_by_pu[pu] + carrier_index

    def _new_capacity_index(self, pu, period_index, process_option_index):
        return self._new_capacity_offsets_by_pu[pu] + period_index * self._num_proc_by_pu[pu] + process_option_index

    # ── Time helpers ───────────────────────────────────────────────────

    def _years_in_period(self, period_index, simulation_options):
        year = self._simulation_periods[period_index]
        if period_index + 1 < self._num_periods:
            next_year = self._simulation_periods[period_index + 1]
        else:
            next_year = year + simulation_options['year_increment']
        return list(range(year, next_year))

    def _horizon_end_year(self, simulation_options):
        last_period_start = self._simulation_periods[-1]
        return last_period_start + simulation_options['year_increment']

    def _salvage_value_in_euro(self, capex, investment_year, lifetime, interest_rate, simulation_options):
        horizon_end_year = self._horizon_end_year(simulation_options)
        years_within_horizon = horizon_end_year - investment_year
        remaining_lifetime = max(0, lifetime - years_within_horizon)
        if remaining_lifetime == 0:
            return 0.0
        salvage_fraction = remaining_lifetime / lifetime
        discount = 1.0 / (1 + interest_rate) ** (horizon_end_year - self._year)
        return capex * salvage_fraction * discount

    def _budget_end_year(self, simulation_options):
        configured = simulation_options.get('emission_budget_end_year')
        if configured is not None:
            return configured
        last_period_start = self._simulation_periods[-1]
        return last_period_start + simulation_options['year_increment'] - 1

    def _budget_years_in_period(self, period_index, simulation_options):
        budget_end = self._budget_end_year(simulation_options)
        return [y for y in self._years_in_period(period_index, simulation_options) if y <= budget_end]

    # ── Objective ──────────────────────────────────────────────────────

    def _build_objective(self, interest_rate, simulation_options):  # noqa: C901
        c = [0.0] * self._total_variables

        for pu in self._production_units:
            proc_options = self._process_options_by_pu[pu]

            for period_index, year in enumerate(self._simulation_periods):
                years = self._years_in_period(period_index, simulation_options)
                is_start_year = year == simulation_options['start_year']

                # exec coefficients: discounted operating costs
                for pi, po in enumerate(proc_options):
                    process = po.process
                    total_cost = 0.0
                    for op_year in years:
                        co2_price = self._context.co2_cost_in_euro_per_t_co2(op_year)
                        annual_cost = process.annual_cost_in_euro_per_process_count(op_year, co2_price, simulation_options)
                        discount = 1.0 / (1 + interest_rate) ** (op_year - self._year)
                        total_cost += annual_cost * discount

                    if isinstance(process, InstalledProcess):
                        period_opts = dict(simulation_options)
                        period_opts['rolling_planning_horizon_in_years'] = len(years)
                        repair = process.invest_cost_in_euro_per_process_count(year, interest_rate, period_opts)
                        discount_to_start = 1.0 / (1 + interest_rate) ** (year - self._year)
                        total_cost += repair * discount_to_start

                    c[self._exec_index(pu, period_index, pi)] = total_cost

                # carrier coefficients
                for ci, carrier in enumerate(self._carriers):
                    total_carrier_cost = 0.0
                    for op_year in years:
                        cost = self._carrier_cost_in_euro_per_unit(carrier, op_year, simulation_options)
                        discount = 1.0 / (1 + interest_rate) ** (op_year - self._year)
                        total_carrier_cost += cost * discount
                    c[self._carrier_index(pu, period_index, ci)] = total_carrier_cost

                # new_capacity coefficients: CAPEX - salvage
                for pi, po in enumerate(proc_options):
                    process = po.process
                    idx = self._new_capacity_index(pu, period_index, pi)
                    if isinstance(process, InstalledProcess):
                        c[idx] = 0.0
                        continue

                    # CAPEX that has to be paid by the investor: the start year factor scales the CAPEX before the
                    # investment funding is deducted. The salvage value refers to the same net amount.
                    capex_factor = simulation_options.get('start_year_capex_factor', 1.0) if is_start_year else 1.0
                    net_capex = process.net_capex_in_euro_per_process_count(year, simulation_options, capex_factor)

                    discount = 1.0 / (1 + interest_rate) ** (year - self._year)
                    salvage = self._salvage_value_in_euro(
                        net_capex, year, process.lifetime_in_years, interest_rate, simulation_options
                    )
                    c[idx] = net_capex * discount - salvage

        return c

    def _carrier_cost_in_euro_per_unit(self, carrier, year, simulation_options):
        purchase_price = carrier.purchase_price_in_euro_per_unit(year)
        sell_price = carrier.sell_price_in_euro_per_unit(year)
        taxes = carrier.taxes_in_euro_per_unit(year, simulation_options)
        subsidies = carrier.subsidies_in_euro_per_unit(year, simulation_options)
        co2_price = self._context.co2_cost_in_euro_per_t_co2(year)
        upstream = carrier.upstream_emission_in_t_co2_per_unit(year, simulation_options) * co2_price
        bound = -carrier.renewably_bound_co2_emission_in_t_co2_per_unit(year, simulation_options) * co2_price
        downstream = carrier.downstream_emission_in_t_co2_per_unit(year, simulation_options) * co2_price

        return purchase_price + taxes - subsidies - sell_price + upstream + downstream + bound

    # ── Constraints ────────────────────────────────────────────────────

    def _build_constraints(self, simulation_options):
        rows = []

        for period_index, year in enumerate(self._simulation_periods):
            for pu in self._production_units:
                rows += self._pu_production_constraints(pu, period_index, year)
                rows += self._pu_carrier_constraints(pu, period_index, year, simulation_options)
                rows += self._pu_capture_constraints(pu, period_index, year)
                rows += self._pu_emission_constraints(pu, period_index, year, simulation_options)

            rows += self._shared_pool_availability_constraints(period_index, year)
            rows += self._site_purchase_eligibility_constraints(period_index, year)

        for pu in self._production_units:
            rows += self._capacity_linking_constraints(pu)

        rows += self._overall_emission_budget_constraint(simulation_options)

        if not rows:
            return np.zeros((0, self._total_variables)), np.zeros(0)

        a = np.array([r[0] for r in rows])
        b = np.array([r[1] for r in rows])
        return a, b

    def _pu_production_constraints(self, pu, period_index, year):
        rows = []
        for pi, po in enumerate(self._process_options_by_pu[pu]):
            process = po.process
            if isinstance(process, InstalledProcess):
                capacity = process.available_process_execution_count(year)
            elif process.tech_available_at_year > year:
                capacity = 0
            else:
                capacity = 10e40
            c = [0.0] * self._total_variables
            c[self._exec_index(pu, period_index, pi)] = 1.0
            rows.append((c, capacity))
        return rows

    def _pu_carrier_constraints(self, pu, period_index, year, simulation_options):
        rows = []
        for ci, carrier in enumerate(self._carriers):
            # minimum export
            min_export = self._minimum_export(pu, carrier, year, simulation_options)
            c = [0.0] * self._total_variables
            for pi, po in enumerate(self._process_options_by_pu[pu]):
                net = po.process.netto_produced_or_consumed_amount_per_process_count(year, carrier)
                c[self._exec_index(pu, period_index, pi)] = -net
            c[self._carrier_index(pu, period_index, ci)] = -1.0
            rows.append((c, -min_export))

            # maximum production
            max_prod = carrier.maximum_production_in_unit
            c = [0.0] * self._total_variables
            for pi, po in enumerate(self._process_options_by_pu[pu]):
                net = po.process.netto_produced_or_consumed_amount_per_process_count(year, carrier)
                c[self._exec_index(pu, period_index, pi)] = net
            c[self._carrier_index(pu, period_index, ci)] = 1.0
            rows.append((c, max_prod))

            # minimum use
            min_use = carrier.minimum_use_in_unit(year, simulation_options)
            c = [0.0] * self._total_variables
            c[self._carrier_index(pu, period_index, ci)] = -1.0
            rows.append((c, -min_use))
        return rows

    def _pu_capture_constraints(self, pu, period_index, year):
        c = [0.0] * self._total_variables
        for pi, po in enumerate(self._process_options_by_pu[pu]):
            process = po.process
            direct = max(process.emission.direct_emissions_in_t_co2_per_process_count(year), 0)
            captured_input = process.emission.captured_input_emission_in_t_co2_per_process_count
            c[self._exec_index(pu, period_index, pi)] = -(direct - captured_input)
        return [(c, 0)]

    def _pu_emission_constraints(self, pu, period_index, year, simulation_options):
        emission_limit = simulation_options['emission_limit_in_t_co2']
        c = [0.0] * self._total_variables

        for pi, po in enumerate(self._process_options_by_pu[pu]):
            c[self._exec_index(pu, period_index, pi)] = self._process_emission_coefficient(po.process, year, simulation_options)

        for ci, carrier in enumerate(self._carriers):
            c[self._carrier_index(pu, period_index, ci)] = self._carrier_emission_coefficient(carrier, year, simulation_options)

        return [(c, emission_limit)]

    def _shared_pool_availability_constraints(self, period_index, year):
        rows = []
        assignments = {}

        for pu in self._production_units:
            site = pu._site
            for ci, carrier in enumerate(self._carriers):
                if not site.can_purchase(carrier, year):
                    continue
                pool = site.shared_pool_for(carrier)
                key = (id(pool), carrier)
                if key not in assignments:
                    assignments[key] = {'pool': pool, 'carrier': carrier, 'entries': []}
                assignments[key]['entries'].append((pu, ci))

        for assignment in assignments.values():
            pool = assignment['pool']
            carrier = assignment['carrier']
            availability = pool.carrier_availability(carrier, year)
            c = [0.0] * self._total_variables
            for pu, ci in assignment['entries']:
                c[self._carrier_index(pu, period_index, ci)] = 1.0
            rows.append((c, availability))

        return rows

    def _site_purchase_eligibility_constraints(self, period_index, year):
        rows = []
        for pu in self._production_units:
            site = pu._site
            for ci, carrier in enumerate(self._carriers):
                if site.can_purchase(carrier, year):
                    continue
                c = [0.0] * self._total_variables
                c[self._carrier_index(pu, period_index, ci)] = 1.0
                rows.append((c, 0.0))
        return rows

    def _capacity_linking_constraints(self, pu):
        rows = []
        for pi, po in enumerate(self._process_options_by_pu[pu]):
            process = po.process
            if isinstance(process, InstalledProcess):
                continue
            lifetime = process.lifetime_in_years
            for period_index, year in enumerate(self._simulation_periods):
                if process.tech_available_at_year > year:
                    c = [0.0] * self._total_variables
                    c[self._exec_index(pu, period_index, pi)] = 1.0
                    rows.append((c, 0.0))
                    continue

                c = [0.0] * self._total_variables
                c[self._exec_index(pu, period_index, pi)] = 1.0
                for prior in range(period_index + 1):
                    prior_year = self._simulation_periods[prior]
                    if year - prior_year < lifetime and process.tech_available_at_year <= prior_year:
                        c[self._new_capacity_index(pu, prior, pi)] = -1.0
                rows.append((c, 0.0))
        return rows

    def _overall_emission_budget_constraint(self, simulation_options):
        budget = simulation_options.get('overall_emission_budget_in_t_co2')
        if budget is None:
            return []

        c = [0.0] * self._total_variables
        for period_index in range(self._num_periods):
            budget_years = self._budget_years_in_period(period_index, simulation_options)
            if not budget_years:
                continue
            for pu in self._production_units:
                for pi, po in enumerate(self._process_options_by_pu[pu]):
                    emission_sum = sum(
                        self._process_emission_coefficient(po.process, y, simulation_options) for y in budget_years
                    )
                    c[self._exec_index(pu, period_index, pi)] += emission_sum

                for ci, carrier in enumerate(self._carriers):
                    emission_sum = sum(self._carrier_emission_coefficient(carrier, y, simulation_options) for y in budget_years)
                    c[self._carrier_index(pu, period_index, ci)] += emission_sum

        return [(c, budget)]

    # ── Emission helpers (keep in sync with RegionOptimization / MultiPeriodOptimization) ──

    def _process_emission_coefficient(self, process, year, simulation_options):
        scope = simulation_options['emission_constraint_scope']
        coefficient = 0.0

        if 'direct' in scope:
            direct = process.emission.direct_emissions_in_t_co2_per_process_count(year)
            captured = process.emission.captured_emission_in_t_co2_per_process_count
            coefficient += direct - captured

        if 'downstream' not in scope:
            return coefficient

        downstream = sum(
            process.netto_produced_or_consumed_amount_per_process_count(year, carrier)
            * self._carrier_downstream_emission(carrier, year, simulation_options)
            for carrier in self._carriers
        )
        return coefficient + downstream

    def _carrier_emission_coefficient(self, carrier, year, simulation_options):
        scope = simulation_options['emission_constraint_scope']
        coefficient = 0.0

        if 'upstream' in scope:
            coefficient += carrier.upstream_emission_in_t_co2_per_unit(year, simulation_options)
        if 'renewably_bound' in scope:
            coefficient -= carrier.renewably_bound_co2_emission_in_t_co2_per_unit(year, simulation_options)
        if 'downstream' not in scope:
            return coefficient
        return coefficient + self._carrier_downstream_emission(carrier, year, simulation_options)

    @staticmethod
    def _carrier_downstream_emission(carrier, year, simulation_options):
        if not hasattr(carrier, 'downstream_emission_in_t_co2_per_unit'):
            return 0.0
        return carrier.downstream_emission_in_t_co2_per_unit(year, simulation_options)

    # ── Minimum export helper ─────────────────────────────────────────

    def _minimum_export(self, pu, carrier, year, simulation_options):
        if carrier.unit is CarrierUnit.T:
            return pu.carrier_minimum_export_in_t(carrier, year, simulation_options)
        if carrier.unit is CarrierUnit.GJ:
            return 0
        msg = f'Unknown carrier unit: {carrier.unit}'
        raise TypeError(msg)

    # ── Bounds ─────────────────────────────────────────────────────────

    def _build_bounds(self):
        bounds = []

        # Section 1: exec + carrier (per PU, per period)
        for pu in self._production_units:
            for _period_index in range(self._num_periods):
                bounds.extend([(0, None) for _ in range(self._num_proc_by_pu[pu])])
                bounds.extend([(0, None) for _ in range(self._num_carriers)])

        # Section 2: new_capacity (per PU, per period)
        for pu in self._production_units:
            for _period_index, year in enumerate(self._simulation_periods):
                for po in self._process_options_by_pu[pu]:
                    process = po.process
                    if isinstance(process, InstalledProcess) or process.tech_available_at_year > year:
                        bounds.append((0, 0))
                    else:
                        bounds.append((0, None))

        return bounds

    # ── Solve ──────────────────────────────────────────────────────────

    def optimize(self):
        result = scipy_optimize.linprog(
            self._c,
            A_ub=self._a_ub,
            b_ub=self._b_ub,
            bounds=self._bounds,
            method='highs',
            options={
                'presolve': True,
                'time_limit': 500,
                'primal_feasibility_tolerance': 1e-5,
                'dual_feasibility_tolerance': 1e-5,
            },
        )

        if not result.success:
            msg = f'Region multi-period optimization failed for region {self._region.id} starting year {self._year}!\n{result}'
            raise RuntimeError(msg)

        logging.debug('Region multi-period optimization succeeded')
        return RegionMultiPeriodOptimizationResult(
            result,
            self._production_units,
            self._process_options_by_pu,
            self._carriers,
            self._simulation_periods,
            self._offsets_by_pu,
            self._new_capacity_offsets_by_pu,
            self._num_proc_by_pu,
            self._vars_per_period_by_pu,
            total_cost_in_euro=result.fun,
        )
