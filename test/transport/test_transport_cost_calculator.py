# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Tests for transport cost calculator.

Validates cost calculation for inter-site material and energy flows,
distance calculations, and transport cost matrices.
"""

import pytest

from transport.transport_cost_calculator import (
    DistanceCalculator,
    TransportCost,
    TransportCostFactory,
    TransportCostMatrix,
)


class TestTransportCost:
    """Tests for TransportCost class."""

    def test_transport_cost_creation(self):
        """TransportCost can be created with distance and cost rate."""
        cost = TransportCost(
            distance_km=100.0,
            cost_per_unit_per_km=0.5,
        )

        assert cost.distance_km == 100.0
        assert cost.cost_per_unit_per_km == 0.5

    def test_total_cost_per_unit(self):
        """Total cost per unit is distance x cost_per_km."""
        cost = TransportCost(
            distance_km=100.0,
            cost_per_unit_per_km=0.5,
        )

        # 100 km x 0.5 EUR/unit/km = 50 EUR/unit
        assert cost.total_cost_per_unit == 50.0

    def test_transport_cost_for_amount(self):
        """Transport cost for amount is total_per_unit x amount."""
        cost = TransportCost(
            distance_km=100.0,
            cost_per_unit_per_km=0.5,
        )

        # 50 EUR/unit x 10 units = 500 EUR
        total = cost.transport_cost_for_amount(10.0)
        assert total == 500.0

    def test_transport_cost_zero_amount(self):
        """Transport cost for zero amount is zero."""
        cost = TransportCost(distance_km=100.0, cost_per_unit_per_km=0.5)
        assert cost.transport_cost_for_amount(0.0) == 0.0

    def test_transport_cost_negative_distance_raises(self):
        """Negative distance raises ValueError."""
        with pytest.raises(ValueError, match='Distance must be non-negative'):
            TransportCost(distance_km=-10.0, cost_per_unit_per_km=0.5)

    def test_transport_cost_negative_cost_raises(self):
        """Negative cost per unit per km raises ValueError."""
        with pytest.raises(ValueError, match='Cost per unit per km must be non-negative'):
            TransportCost(distance_km=100.0, cost_per_unit_per_km=-0.5)

    def test_transport_cost_negative_amount_raises(self):
        """Negative transport amount raises ValueError."""
        cost = TransportCost(distance_km=100.0, cost_per_unit_per_km=0.5)
        with pytest.raises(ValueError, match='Transport amount must be non-negative'):
            cost.transport_cost_for_amount(-5.0)

    def test_transport_cost_with_carrier_id(self):
        """TransportCost can include carrier ID."""
        cost = TransportCost(
            distance_km=100.0,
            cost_per_unit_per_km=0.5,
            carrier_id=1,
        )

        assert cost.carrier_id == 1
        assert cost.product_id is None

    def test_transport_cost_with_product_id(self):
        """TransportCost can include product ID."""
        cost = TransportCost(
            distance_km=100.0,
            cost_per_unit_per_km=0.5,
            product_id=2,
        )

        assert cost.product_id == 2
        assert cost.carrier_id is None

    def test_transport_cost_repr_includes_cost_summary(self):
        cost = TransportCost(distance_km=10.0, cost_per_unit_per_km=2.5)

        result = repr(cost)

        assert 'distance=10.0km' in result
        assert 'total_per_unit=25.0EUR/unit' in result


class TestTransportCostMatrix:
    """Tests for TransportCostMatrix class."""

    def test_matrix_creation(self):
        """TransportCostMatrix can be created with site list."""
        sites = [1, 2, 3, 4, 5]
        matrix = TransportCostMatrix(sites)

        assert sorted(matrix.site_ids) == sorted(sites)

    def test_set_and_get_transport_cost(self):
        """Transport cost can be set and retrieved."""
        sites = [1, 2, 3]
        matrix = TransportCostMatrix(sites)

        cost = TransportCost(distance_km=50.0, cost_per_unit_per_km=0.3)
        matrix.set_transport_cost(1, 2, cost)

        retrieved = matrix.get_transport_cost(1, 2)
        assert retrieved is cost
        assert retrieved.distance_km == 50.0

    def test_get_nonexistent_route_returns_none(self):
        """Getting undefined route returns None."""
        sites = [1, 2, 3]
        matrix = TransportCostMatrix(sites)

        result = matrix.get_transport_cost(1, 2)
        assert result is None

    def test_get_distance_km(self):
        """Distance can be retrieved for a route."""
        sites = [1, 2, 3]
        matrix = TransportCostMatrix(sites)

        cost = TransportCost(distance_km=75.0, cost_per_unit_per_km=0.4)
        matrix.set_transport_cost(2, 3, cost)

        distance = matrix.get_distance_km(2, 3)
        assert distance == 75.0

    def test_calculate_cost_for_flow(self):
        """Cost for a flow is calculated correctly."""
        sites = [1, 2, 3]
        matrix = TransportCostMatrix(sites)

        cost = TransportCost(distance_km=100.0, cost_per_unit_per_km=0.5)
        matrix.set_transport_cost(1, 2, cost)

        flow_cost = matrix.calculate_cost_for_flow(1, 2, amount=20.0)
        # 100 km x 0.5 EUR/unit/km x 20 units = 1000 EUR
        assert flow_cost == 1000.0

    def test_calculate_cost_for_undefined_flow_returns_zero(self):
        """Cost for undefined flow returns zero."""
        sites = [1, 2, 3]
        matrix = TransportCostMatrix(sites)

        flow_cost = matrix.calculate_cost_for_flow(1, 2, amount=20.0)
        assert flow_cost == 0.0

    def test_set_cost_invalid_from_site_raises(self):
        """Setting cost for unknown site raises error."""
        sites = [1, 2, 3]
        matrix = TransportCostMatrix(sites)

        cost = TransportCost(distance_km=100.0, cost_per_unit_per_km=0.5)
        with pytest.raises(ValueError, match='not in cluster'):
            matrix.set_transport_cost(999, 2, cost)

    def test_set_cost_invalid_to_site_raises(self):
        """Setting cost for unknown destination raises error."""
        sites = [1, 2, 3]
        matrix = TransportCostMatrix(sites)

        cost = TransportCost(distance_km=100.0, cost_per_unit_per_km=0.5)
        with pytest.raises(ValueError, match='not in cluster'):
            matrix.set_transport_cost(1, 999, cost)

    def test_multiple_routes(self):
        """Multiple routes can be defined and retrieved."""
        sites = [1, 2, 3, 4]
        matrix = TransportCostMatrix(sites)

        cost_12 = TransportCost(distance_km=50.0, cost_per_unit_per_km=0.3)
        cost_23 = TransportCost(distance_km=75.0, cost_per_unit_per_km=0.4)
        cost_34 = TransportCost(distance_km=100.0, cost_per_unit_per_km=0.5)

        matrix.set_transport_cost(1, 2, cost_12)
        matrix.set_transport_cost(2, 3, cost_23)
        matrix.set_transport_cost(3, 4, cost_34)

        assert matrix.get_transport_cost(1, 2) is cost_12
        assert matrix.get_transport_cost(2, 3) is cost_23
        assert matrix.get_transport_cost(3, 4) is cost_34
        assert matrix.get_transport_cost(1, 3) is None

    def test_matrix_repr_reports_site_and_route_counts(self):
        matrix = TransportCostMatrix([3, 1, 2])
        matrix.set_transport_cost(1, 2, TransportCost(distance_km=50.0, cost_per_unit_per_km=0.3))

        result = repr(matrix)

        assert result == 'TransportCostMatrix(sites=3, routes=1)'


class TestDistanceCalculator:
    """Tests for DistanceCalculator class."""

    def test_haversine_same_point(self):
        """Distance between same point is zero."""
        distance = DistanceCalculator.haversine_distance(
            lat1=45.0,
            lon1=10.0,
            lat2=45.0,
            lon2=10.0,
        )

        assert abs(distance) < 0.001

    def test_haversine_equatorial_distance(self):
        """Distance calculation on equator."""
        # Two points 1 degree apart on equator ≈ 111 km
        distance = DistanceCalculator.haversine_distance(
            lat1=0.0,
            lon1=0.0,
            lat2=0.0,
            lon2=1.0,
        )

        # Should be approximately 111 km
        assert 110 < distance < 112

    def test_haversine_meridian_distance(self):
        """Distance calculation on meridian."""
        # Two points 1 degree apart on meridian ≈ 111 km
        distance = DistanceCalculator.haversine_distance(
            lat1=0.0,
            lon1=0.0,
            lat2=1.0,
            lon2=0.0,
        )

        # Should be approximately 111 km
        assert 110 < distance < 112

    def test_haversine_real_world_example(self):
        """Real-world distance example: New York to London."""
        # Approximate coordinates
        ny_lat, ny_lon = 40.7128, -74.0060
        london_lat, london_lon = 51.5074, -0.1278

        distance = DistanceCalculator.haversine_distance(
            lat1=ny_lat,
            lon1=ny_lon,
            lat2=london_lat,
            lon2=london_lon,
        )

        # Actual distance is approximately 5570 km
        assert 5500 < distance < 5650

    def test_haversine_symmetry(self):
        """Distance A→B equals distance B→A."""
        lat1, lon1 = 45.0, 10.0
        lat2, lon2 = 52.0, 13.0

        dist_ab = DistanceCalculator.haversine_distance(lat1, lon1, lat2, lon2)
        dist_ba = DistanceCalculator.haversine_distance(lat2, lon2, lat1, lon1)

        assert abs(dist_ab - dist_ba) < 0.001


class TestTransportCostFactory:
    """Tests for TransportCostFactory class."""

    def test_create_from_distances(self):
        """Factory creates matrix from distance dictionary."""
        sites = [1, 2, 3]
        distances = {
            (1, 2): 50.0,
            (2, 3): 75.0,
            (1, 3): 125.0,
        }

        matrix = TransportCostFactory.create_from_distances(
            site_ids=sites,
            distances=distances,
            cost_per_unit_per_km=0.5,
        )

        assert matrix.get_distance_km(1, 2) == 50.0
        assert matrix.get_distance_km(2, 3) == 75.0
        assert matrix.get_distance_km(1, 3) == 125.0

    def test_create_uniform_mesh(self):
        """Factory creates uniform distance mesh."""
        sites = [1, 2, 3, 4]
        matrix = TransportCostFactory.create_uniform_mesh(
            site_ids=sites,
            distance_km=100.0,
            cost_per_unit_per_km=0.4,
        )

        # All inter-site distances should be 100 km
        assert matrix.get_distance_km(1, 2) == 100.0
        assert matrix.get_distance_km(2, 3) == 100.0
        assert matrix.get_distance_km(1, 4) == 100.0

        # Same site should have no route defined
        assert matrix.get_transport_cost(1, 1) is None

    def test_create_from_coordinates(self):
        """Factory creates matrix from geographic coordinates."""
        site_coords = {
            1: (45.0, 10.0),  # Base coordinate
            2: (45.0, 11.0),  # 1 degree east (≈111 km)
            3: (46.0, 10.0),  # 1 degree north (≈111 km)
        }

        matrix = TransportCostFactory.create_from_coordinates(
            site_coordinates=site_coords,
            cost_per_unit_per_km=0.5,
        )

        # Check that distances are approximately correct for 1-degree differences
        # At lat 45°, 1 degree longitude ≈ 78.6 km, 1 degree latitude ≈ 111 km
        assert 77 < matrix.get_distance_km(1, 2) < 80  # 1° longitude at lat 45°
        assert 110 < matrix.get_distance_km(1, 3) < 112  # 1° latitude


class TestTransportCostIntegration:
    """Integration tests for transport cost scenarios."""

    def test_cluster_transport_costs_scenario(self):
        """Realistic scenario: 3-site cluster with transport costs."""
        sites = [1, 2, 3]
        distances = {
            (1, 2): 50.0,
            (2, 1): 50.0,
            (2, 3): 30.0,
            (3, 2): 30.0,
            (1, 3): 80.0,
            (3, 1): 80.0,
        }

        matrix = TransportCostFactory.create_from_distances(
            site_ids=sites,
            distances=distances,
            cost_per_unit_per_km=0.1,
        )

        # Flow from site 1 to site 2: 100 units
        # Cost: 50 km x 0.1 EUR/unit/km x 100 units = 500 EUR
        flow_1_to_2 = matrix.calculate_cost_for_flow(1, 2, 100.0)
        assert flow_1_to_2 == 500.0

        # Flow from site 2 to site 3: 50 units
        # Cost: 30 km x 0.1 EUR/unit/km x 50 units = 150 EUR
        flow_2_to_3 = matrix.calculate_cost_for_flow(2, 3, 50.0)
        assert flow_2_to_3 == 150.0

        # Total inter-site transport for this scenario: 650 EUR
        total_transport = flow_1_to_2 + flow_2_to_3
        assert total_transport == 650.0

    def test_multi_commodity_transport(self):
        """Transport costs for different commodities."""
        sites = [1, 2]
        matrix = TransportCostMatrix(sites)

        # Heavy commodity (e.g., coal): high transport cost per unit
        coal_cost = TransportCost(
            distance_km=200.0,
            cost_per_unit_per_km=0.05,
            product_id=1,
        )

        # Light commodity (e.g., hydrogen): low transport cost per unit
        TransportCost(
            distance_km=200.0,
            cost_per_unit_per_km=0.02,
            carrier_id=1,
        )

        matrix.set_transport_cost(1, 2, coal_cost)

        # Coal transport: 200 km x 0.05 x 100 units = 1000 EUR
        coal_transport = matrix.calculate_cost_for_flow(1, 2, 100.0)
        assert coal_transport == 1000.0

    def test_geographic_cluster_transport(self):
        """Transport costs based on actual geographic locations."""
        # Three German industrial sites
        site_coords = {
            1: (51.4555, 7.0116),  # Essen
            2: (51.3397, 12.3731),  # Leipzig
            3: (48.3705, 11.5175),  # Munich
        }

        matrix = TransportCostFactory.create_from_coordinates(
            site_coordinates=site_coords,
            cost_per_unit_per_km=0.15,
        )

        # Essen to Leipzig (great-circle distance, not driving distance)
        essen_to_leipzig = matrix.get_distance_km(1, 2)
        assert 370 < essen_to_leipzig < 375  # ≈372 km great-circle

        # Calculate transport cost for 50 units
        cost = matrix.calculate_cost_for_flow(1, 2, 50.0)
        expected_cost = essen_to_leipzig * 0.15 * 50.0
        assert abs(cost - expected_cost) < 0.01
