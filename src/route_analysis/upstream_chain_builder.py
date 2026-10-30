# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from collections import defaultdict, deque

from route_analysis.upstream_chain import UpstreamChain


class UpstreamChainBuilder:
    MAX_DEPTH = 10
    DEFAULT_LHV_GJ_PER_T = 40.0
    MIN_VALUE = 1e-9

    def __init__(self, context, year: int, lhv_map: dict[int, float]):
        self._year = year
        self._year_column = f'Y{year}'
        self._lhv_map = lhv_map

        self._product_production = self._aggregate_process_table(context.get('process_product_production_in_t'), 'id_product')
        self._by_product_production = self._aggregate_process_table(
            context.get('process_by_product_production_in_t'), 'id_by_product'
        )
        self._carrier_production = self._aggregate_process_table(
            context.get('process_energy_carrier_production_in_gj'), 'id_energy_carrier'
        )
        self._energy_demand = self._aggregate_process_table(
            context.get('process_energy_carrier_energy_demand_in_gj'), 'id_energy_carrier'
        )
        self._carrier_feedstock_demand = self._aggregate_process_table(
            context.get('process_energy_carrier_feedstock_demand_in_gj'), 'id_energy_carrier'
        )
        self._product_feedstock = self._aggregate_process_table(
            context.get('process_product_feedstock_demand_in_t'), 'id_product'
        )
        self._by_product_feedstock = self._aggregate_process_table(
            context.get('process_by_product_feedstock_demand_in_t'), 'id_by_product'
        )

        self._purchased_carriers = self._aggregate_purchase_table(
            context.get('production_unit_energy_carrier_purchased_amount_in_gj'), 'id_energy_carrier'
        )
        self._purchased_products = self._aggregate_purchase_table(
            context.get('production_unit_product_purchased_amount_in_t'), 'id_product'
        )
        self._purchased_by_products = self._aggregate_purchase_table(
            context.get('production_unit_by_product_purchased_amount_in_t'), 'id_by_product'
        )

        self._product_outputs_by_process = self._group_by_process(self._product_production)
        self._by_product_outputs_by_process = self._group_by_process(self._by_product_production)
        self._carrier_outputs_by_process = self._group_by_process(self._carrier_production)
        self._energy_demand_by_process = self._group_by_process(self._energy_demand)
        self._carrier_feedstock_by_process = self._group_by_process(self._carrier_feedstock_demand)
        self._product_feedstock_by_process = self._group_by_process(self._product_feedstock)
        self._by_product_feedstock_by_process = self._group_by_process(self._by_product_feedstock)

        self._product_producers_by_id = self._group_by_output(self._product_production)
        self._by_product_producers_by_id = self._group_by_output(self._by_product_production)
        self._carrier_producers_by_id = self._group_by_output(self._carrier_production)

    def trace_upstream(self, target_product_id: int) -> UpstreamChain:
        chain = UpstreamChain()
        pending_amounts = defaultdict(float)
        processed_amounts = defaultdict(float)
        minimum_depths = {}
        queued_keys = set()
        queue = deque()

        def enqueue(process_id: int, output_kind: str, output_id: int, amount: float, unit: str, depth: int):
            if amount <= self.MIN_VALUE or depth > self.MAX_DEPTH:
                return
            key = (process_id, output_kind, output_id, unit)
            pending_amounts[key] += amount
            minimum_depths[key] = min(minimum_depths.get(key, depth), depth)
            if key not in queued_keys:
                queue.append(key)
                queued_keys.add(key)

        for process_id, amount_t in self._product_producers(target_product_id):
            chain.final_product_outputs.append((process_id, target_product_id, amount_t))
            enqueue(process_id, 'product', target_product_id, amount_t, 't', 0)

        while queue:
            key = queue.popleft()
            queued_keys.discard(key)
            delta_amount = pending_amounts[key] - processed_amounts[key]
            processed_amounts[key] = pending_amounts[key]

            process_id, output_kind, output_id, unit = key
            depth = minimum_depths.get(key, 0)

            allocation_factor = self._compute_allocation_factor(process_id, output_kind, output_id, delta_amount, unit)
            if allocation_factor <= self.MIN_VALUE:
                continue

            chain.process_ids.add(process_id)
            self._append_energy_demands(chain, enqueue, process_id, allocation_factor, depth)
            self._append_product_feedstock_flows(chain, enqueue, process_id, allocation_factor, depth)
            self._append_by_product_feedstock_flows(chain, enqueue, process_id, allocation_factor, depth)

        return chain

    def _append_energy_demands(self, chain: UpstreamChain, enqueue, process_id: int, factor: float, depth: int):
        for carrier_id, amount_gj in self._energy_demand_by_process.get(process_id, []):
            allocated_gj = amount_gj * factor
            if allocated_gj <= self.MIN_VALUE:
                continue
            chain.energy_demands.append((process_id, carrier_id, allocated_gj, 'energy'))
            self._append_carrier_sources(chain, enqueue, process_id, carrier_id, allocated_gj, depth)

        for carrier_id, amount_gj in self._carrier_feedstock_by_process.get(process_id, []):
            allocated_gj = amount_gj * factor
            if allocated_gj <= self.MIN_VALUE:
                continue
            chain.energy_demands.append((process_id, carrier_id, allocated_gj, 'feedstock'))
            self._append_carrier_sources(chain, enqueue, process_id, carrier_id, allocated_gj, depth)

    def _append_carrier_sources(
        self,
        chain: UpstreamChain,
        enqueue,
        consuming_process_id: int,
        carrier_id: int,
        allocated_gj: float,
        depth: int,
    ):
        internal_required_gj, purchased_required_gj = self._split_carrier_pool(carrier_id, allocated_gj)
        producers = self._carrier_producers(carrier_id)
        total_internal_gj = sum(amount_gj for _, amount_gj in producers)

        if internal_required_gj > self.MIN_VALUE and total_internal_gj > self.MIN_VALUE:
            for producing_process_id, produced_amount_gj in producers:
                producer_share_gj = internal_required_gj * (produced_amount_gj / total_internal_gj)
                if producer_share_gj <= self.MIN_VALUE:
                    continue
                chain.internal_carrier_pool_inputs.append((producing_process_id, carrier_id, producer_share_gj))
                chain.carrier_flows.append((producing_process_id, carrier_id, consuming_process_id, producer_share_gj))
                enqueue(producing_process_id, 'energy_carrier', carrier_id, producer_share_gj, 'GJ', depth + 1)
        else:
            purchased_required_gj += internal_required_gj

        if purchased_required_gj > self.MIN_VALUE:
            chain.purchased_carrier_flows.append((carrier_id, consuming_process_id, purchased_required_gj))

    def _append_product_feedstock_flows(self, chain: UpstreamChain, enqueue, process_id: int, factor: float, depth: int):
        for product_id, amount_t in self._product_feedstock_by_process.get(process_id, []):
            allocated_t = amount_t * factor
            if allocated_t <= self.MIN_VALUE:
                continue

            producers = self._product_producers(product_id)
            total_internal_t = sum(output_t for _, output_t in producers)
            internal_allocated_t = min(allocated_t, total_internal_t) if total_internal_t > self.MIN_VALUE else 0.0

            if internal_allocated_t > self.MIN_VALUE and total_internal_t > self.MIN_VALUE:
                for producing_process_id, produced_amount_t in producers:
                    producer_share_t = internal_allocated_t * (produced_amount_t / total_internal_t)
                    if producer_share_t <= self.MIN_VALUE:
                        continue
                    chain.product_flows.append((producing_process_id, product_id, process_id, producer_share_t))
                    enqueue(producing_process_id, 'product', product_id, producer_share_t, 't', depth + 1)

            purchased_t = allocated_t - internal_allocated_t
            if purchased_t > self.MIN_VALUE:
                chain.purchased_product_flows.append((product_id, process_id, purchased_t))

    def _append_by_product_feedstock_flows(self, chain: UpstreamChain, enqueue, process_id: int, factor: float, depth: int):
        for by_product_id, amount_t in self._by_product_feedstock_by_process.get(process_id, []):
            allocated_t = amount_t * factor
            if allocated_t <= self.MIN_VALUE:
                continue

            producers = self._by_product_producers(by_product_id)
            total_internal_t = sum(output_t for _, output_t in producers)
            internal_allocated_t = min(allocated_t, total_internal_t) if total_internal_t > self.MIN_VALUE else 0.0

            if internal_allocated_t > self.MIN_VALUE and total_internal_t > self.MIN_VALUE:
                for producing_process_id, produced_amount_t in producers:
                    producer_share_t = internal_allocated_t * (produced_amount_t / total_internal_t)
                    if producer_share_t <= self.MIN_VALUE:
                        continue
                    chain.by_product_flows.append((producing_process_id, by_product_id, process_id, producer_share_t))
                    enqueue(producing_process_id, 'by_product', by_product_id, producer_share_t, 't', depth + 1)

            purchased_t = allocated_t - internal_allocated_t
            if purchased_t > self.MIN_VALUE:
                chain.purchased_by_product_flows.append((by_product_id, process_id, purchased_t))

    def _get_process_outputs(self, process_id: int) -> list[tuple[str, int, float, str]]:
        outputs = []
        outputs.extend(
            ('product', output_id, amount_t, 't') for output_id, amount_t in self._product_outputs_by_process.get(process_id, [])
        )
        outputs.extend(
            ('by_product', output_id, amount_t, 't')
            for output_id, amount_t in self._by_product_outputs_by_process.get(process_id, [])
        )
        outputs.extend(
            ('energy_carrier', output_id, amount_gj, 'GJ')
            for output_id, amount_gj in self._carrier_outputs_by_process.get(process_id, [])
        )
        return [(kind, output_id, amount, unit) for kind, output_id, amount, unit in outputs if amount > self.MIN_VALUE]

    def _compute_allocation_factor(
        self,
        process_id: int,
        output_kind: str,
        _output_id: int,
        required_amount: float,
        _required_unit: str,
    ) -> float:
        outputs = self._get_process_outputs(process_id)
        if not outputs:
            return 0.0

        same_kind_outputs = [(kind, item_id, amount, unit) for kind, item_id, amount, unit in outputs if kind == output_kind]
        if not same_kind_outputs:
            same_kind_outputs = outputs

        total_basis = sum(amount for _, _, amount, _ in same_kind_outputs)
        factor = required_amount / total_basis
        return max(0.0, min(1.0, factor))

    def _split_carrier_pool(self, carrier_id: int, allocated_gj: float) -> tuple[float, float]:
        internal_total_gj = sum(amount_gj for _, amount_gj in self._carrier_producers(carrier_id))
        purchased_total_gj = self._purchased_carriers.get(carrier_id, 0.0)
        pool_total_gj = internal_total_gj + purchased_total_gj

        if pool_total_gj <= self.MIN_VALUE:
            return 0.0, allocated_gj

        internal_share_gj = allocated_gj * (internal_total_gj / pool_total_gj)
        purchased_share_gj = allocated_gj - internal_share_gj
        return internal_share_gj, purchased_share_gj

    def _carrier_producers(self, carrier_id: int) -> list[tuple[int, float]]:
        return self._carrier_producers_by_id.get(carrier_id, [])

    def _product_producers(self, product_id: int) -> list[tuple[int, float]]:
        return self._product_producers_by_id.get(product_id, [])

    def _by_product_producers(self, by_product_id: int) -> list[tuple[int, float]]:
        return self._by_product_producers_by_id.get(by_product_id, [])

    def _aggregate_process_table(self, df, value_column_id: str) -> dict[tuple[int, int], float]:
        if df is None or df.empty or self._year_column not in df.columns:
            return {}

        grouped = df.groupby(['id_process', value_column_id], dropna=False)[self._year_column].sum().reset_index()
        return {
            (int(row['id_process']), int(row[value_column_id])): float(row[self._year_column])
            for _, row in grouped.iterrows()
            if abs(float(row[self._year_column])) > self.MIN_VALUE
        }

    def _aggregate_purchase_table(self, df, value_column_id: str) -> dict[int, float]:
        if df is None or df.empty or self._year_column not in df.columns:
            return {}

        grouped = df.groupby([value_column_id], dropna=False)[self._year_column].sum().reset_index()
        return {
            int(row[value_column_id]): float(row[self._year_column])
            for _, row in grouped.iterrows()
            if abs(float(row[self._year_column])) > self.MIN_VALUE
        }

    @staticmethod
    def _group_by_process(values: dict[tuple[int, int], float]) -> dict[int, list[tuple[int, float]]]:
        grouped = defaultdict(list)
        for (process_id, output_id), amount in values.items():
            grouped[process_id].append((output_id, amount))
        return dict(grouped)

    @staticmethod
    def _group_by_output(values: dict[tuple[int, int], float]) -> dict[int, list[tuple[int, float]]]:
        grouped = defaultdict(list)
        for (process_id, output_id), amount in values.items():
            grouped[output_id].append((process_id, amount))
        return dict(grouped)
