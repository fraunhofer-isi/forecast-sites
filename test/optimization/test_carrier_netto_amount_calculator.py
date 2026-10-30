# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from optimization.carrier_netto_amount_calculator import CarrierNettoAmountCalculator


class _FakeProcess:
    """Process stub that returns a fixed netto amount per carrier."""

    def __init__(self, netto_by_carrier):
        self._netto_by_carrier = netto_by_carrier

    def netto_produced_or_consumed_amount_per_process_count(self, year, carrier):
        return self._netto_by_carrier.get(carrier, 0.0)


class _FakeProcessOption:
    """ProcessOption stub wrapping a _FakeProcess; hashable so it can be a dict key."""

    def __init__(self, netto_by_carrier):
        self.process = _FakeProcess(netto_by_carrier)


def _process_option(netto_by_carrier):
    return _FakeProcessOption(netto_by_carrier)


class TestCarrierNettoAmountCalculator:
    def test_single_process_single_carrier_produced(self):
        """One process that produces 10 t of carrier A."""
        carrier_a = object()
        po = _process_option({carrier_a: 10.0})
        process_execution_counts = {po: 3.0}  # 3 executions * 10 t/exec = 30 t

        result = CarrierNettoAmountCalculator().calculate(process_execution_counts, [carrier_a], 2030)

        assert result[carrier_a] == 30.0

    def test_single_process_single_carrier_consumed(self):
        """One process that consumes 5 t per execution."""
        carrier_a = object()
        po = _process_option({carrier_a: -5.0})
        process_execution_counts = {po: 2.0}  # 2 * -5 = -10

        result = CarrierNettoAmountCalculator().calculate(process_execution_counts, [carrier_a], 2030)

        assert result[carrier_a] == -10.0

    def test_multiple_processes_sum_contributions(self):
        """Two processes both producing carrier A; netto is the sum."""
        carrier_a = object()
        po1 = _process_option({carrier_a: 8.0})
        po2 = _process_option({carrier_a: 3.0})
        process_execution_counts = {po1: 1.0, po2: 2.0}  # 8 + 6 = 14

        result = CarrierNettoAmountCalculator().calculate(process_execution_counts, [carrier_a], 2030)

        assert result[carrier_a] == 14.0

    def test_zero_execution_count_contributes_zero(self):
        """Process with zero execution count contributes nothing."""
        carrier_a = object()
        po = _process_option({carrier_a: 100.0})
        process_execution_counts = {po: 0.0}

        result = CarrierNettoAmountCalculator().calculate(process_execution_counts, [carrier_a], 2030)

        assert result[carrier_a] == 0.0

    def test_unknown_carrier_returns_zero(self):
        """Carrier not in any process coefficients gets zero netto."""
        carrier_a = object()
        carrier_b = object()
        po = _process_option({carrier_a: 5.0})
        process_execution_counts = {po: 2.0}

        result = CarrierNettoAmountCalculator().calculate(process_execution_counts, [carrier_a, carrier_b], 2030)

        assert result[carrier_a] == 10.0
        assert result[carrier_b] == 0.0

    def test_all_carriers_present_in_result(self):
        """Result dict contains every carrier in the input list."""
        c1, c2, c3 = object(), object(), object()
        process_execution_counts = {}

        result = CarrierNettoAmountCalculator().calculate(process_execution_counts, [c1, c2, c3], 2030)

        assert set(result.keys()) == {c1, c2, c3}

    def test_empty_process_options_gives_zero_for_all_carriers(self):
        """No processes means every carrier netto is zero."""
        carrier_a = object()
        result = CarrierNettoAmountCalculator().calculate({}, [carrier_a], 2030)

        assert result[carrier_a] == 0.0
