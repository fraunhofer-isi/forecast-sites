# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from optimization.optimization_context import OptimizationContext


class TestOptimizationContext:
    """Test cases for OptimizationContext value object."""

    def test_optimization_context_stores_co2_cost(self):
        """Test that co2_cost is stored correctly."""
        sim_opts = {'key': 'value'}
        ctx = OptimizationContext(co2_cost_in_euro_per_t_co2=50.0, interest_rate=0.05, simulation_options=sim_opts)
        assert ctx.co2_cost_in_euro_per_t_co2 == 50.0

    def test_optimization_context_stores_interest_rate(self):
        """Test that interest_rate is stored correctly."""
        sim_opts = {'key': 'value'}
        ctx = OptimizationContext(co2_cost_in_euro_per_t_co2=50.0, interest_rate=0.05, simulation_options=sim_opts)
        assert ctx.interest_rate == 0.05

    def test_optimization_context_stores_simulation_options(self):
        """Test that simulation_options are stored correctly."""
        sim_opts = {'key': 'value'}
        ctx = OptimizationContext(co2_cost_in_euro_per_t_co2=50.0, interest_rate=0.05, simulation_options=sim_opts)
        assert ctx.simulation_options == sim_opts

    def test_optimization_context_with_different_values(self):
        """Test OptimizationContext with different parameter values."""
        sim_opts = {'option1': True, 'option2': False}
        ctx = OptimizationContext(co2_cost_in_euro_per_t_co2=100.0, interest_rate=0.08, simulation_options=sim_opts)
        assert ctx.co2_cost_in_euro_per_t_co2 == 100.0
        assert ctx.interest_rate == 0.08
        assert ctx.simulation_options == sim_opts

    def test_optimization_context_zero_interest_rate(self):
        """Test OptimizationContext with zero interest rate."""
        ctx = OptimizationContext(co2_cost_in_euro_per_t_co2=0.0, interest_rate=0.0, simulation_options={})
        assert ctx.interest_rate == 0.0
        assert ctx.co2_cost_in_euro_per_t_co2 == 0.0
