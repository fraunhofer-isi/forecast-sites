# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Transport cost calculator for inter-site material and energy flows.

Enables modeling of transport costs for moving products, carriers, and by-products
between sites within clusters, supporting supply chain optimization across
multi-site portfolios.
"""

import math


class TransportCost:
    """
    Data class for transport cost specification.

    Represents the cost of transporting a unit of carrier/product between two sites.
    """

    def __init__(
        self,
        distance_km: float,
        cost_per_unit_per_km: float,
        carrier_id: int | None = None,
        product_id: int | None = None,
    ):
        """
        Initialize transport cost.

        Args:
            distance_km: Distance between sites in kilometers
            cost_per_unit_per_km: Cost per unit of transported material per km
            carrier_id: ID of energy carrier (if transport is energy carrier)
            product_id: ID of product (if transport is product)

        """
        if distance_km < 0:
            msg = 'Distance must be non-negative'
            raise ValueError(msg)
        if cost_per_unit_per_km < 0:
            msg = 'Cost per unit per km must be non-negative'
            raise ValueError(msg)

        self.distance_km = distance_km
        self.cost_per_unit_per_km = cost_per_unit_per_km
        self.carrier_id = carrier_id
        self.product_id = product_id

    @property
    def total_cost_per_unit(self) -> float:
        """Get total cost to transport one unit (distance x cost_per_km)."""
        return self.distance_km * self.cost_per_unit_per_km

    def transport_cost_for_amount(self, amount: float) -> float:
        """
        Calculate transport cost for a given amount.

        Args:
            amount: Quantity to transport (in t or GJ depending on carrier/product)

        Returns:
            Total transport cost in EUR

        """
        if amount < 0:
            msg = 'Transport amount must be non-negative'
            raise ValueError(msg)
        return amount * self.total_cost_per_unit

    def __repr__(self) -> str:
        return (
            f'TransportCost(distance={self.distance_km}km, '
            f'cost_per_unit_per_km={self.cost_per_unit_per_km}EUR/unit/km, '
            f'total_per_unit={self.total_cost_per_unit}EUR/unit)'
        )


class TransportCostMatrix:
    """
    Matrix of transport costs between sites in a cluster.

    Provides efficient lookup of transport costs between any two sites,
    with caching for repeated queries.
    """

    def __init__(self, site_ids: list[int]):
        """
        Initialize transport cost matrix.

        Args:
            site_ids: List of site IDs in the cluster

        """
        self.site_ids = sorted(site_ids)
        self._costs: dict[tuple[int, int], TransportCost] = {}
        self._distances: dict[tuple[int, int], float] = {}

    def set_transport_cost(
        self,
        from_site_id: int,
        to_site_id: int,
        transport_cost: TransportCost,
    ) -> None:
        """
        Set transport cost from one site to another.

        Args:
            from_site_id: Origin site ID
            to_site_id: Destination site ID
            transport_cost: TransportCost object with distance and cost specification

        """
        if from_site_id not in self.site_ids:
            msg = f'Site {from_site_id} not in cluster'
            raise ValueError(msg)
        if to_site_id not in self.site_ids:
            msg = f'Site {to_site_id} not in cluster'
            raise ValueError(msg)

        key = (from_site_id, to_site_id)
        self._costs[key] = transport_cost
        self._distances[key] = transport_cost.distance_km

    def get_transport_cost(
        self,
        from_site_id: int,
        to_site_id: int,
    ) -> TransportCost | None:
        """
        Get transport cost from one site to another.

        Args:
            from_site_id: Origin site ID
            to_site_id: Destination site ID

        Returns:
            TransportCost if defined, None otherwise

        """
        return self._costs.get((from_site_id, to_site_id))

    def get_distance_km(
        self,
        from_site_id: int,
        to_site_id: int,
    ) -> float | None:
        """
        Get distance between two sites.

        Args:
            from_site_id: Origin site ID
            to_site_id: Destination site ID

        Returns:
            Distance in kilometers if defined, None otherwise

        """
        return self._distances.get((from_site_id, to_site_id))

    def calculate_cost_for_flow(
        self,
        from_site_id: int,
        to_site_id: int,
        amount: float,
    ) -> float:
        """
        Calculate transport cost for a flow between sites.

        Args:
            from_site_id: Origin site ID
            to_site_id: Destination site ID
            amount: Amount to transport

        Returns:
            Total transport cost in EUR, 0 if no route defined

        """
        cost = self.get_transport_cost(from_site_id, to_site_id)
        if cost is None:
            return 0.0
        return cost.transport_cost_for_amount(amount)

    def __repr__(self) -> str:
        return f'TransportCostMatrix(sites={len(self.site_ids)}, routes={len(self._costs)})'


class DistanceCalculator:
    """
    Calculator for geographic distances between sites.

    Provides haversine distance calculation based on latitude/longitude.
    """

    EARTH_RADIUS_KM = 6371.0088

    @staticmethod
    def haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """
        Calculate haversine distance between two geographic points.

        Args:
            lat1: Latitude of point 1 (degrees)
            lon1: Longitude of point 1 (degrees)
            lat2: Latitude of point 2 (degrees)
            lon2: Longitude of point 2 (degrees)

        Returns:
            Distance in kilometers

        """
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        distance_km = DistanceCalculator.EARTH_RADIUS_KM * c
        return distance_km


class TransportCostFactory:
    """
    Factory for creating transport cost matrices from site data.

    Simplifies common patterns for setting up transport costs.
    """

    @staticmethod
    def create_from_distances(
        site_ids: list[int],
        distances: dict[tuple[int, int], float],
        cost_per_unit_per_km: float,
    ) -> TransportCostMatrix:
        """
        Create transport cost matrix from distance dictionary.

        Args:
            site_ids: List of site IDs
            distances: Dictionary of (from_site, to_site) -> distance_km
            cost_per_unit_per_km: Uniform cost per unit per km for all routes

        Returns:
            TransportCostMatrix with costs calculated from distances

        """
        matrix = TransportCostMatrix(site_ids)

        for (from_site, to_site), distance_km in distances.items():
            transport_cost = TransportCost(
                distance_km=distance_km,
                cost_per_unit_per_km=cost_per_unit_per_km,
            )
            matrix.set_transport_cost(from_site, to_site, transport_cost)

        return matrix

    @staticmethod
    def create_uniform_mesh(
        site_ids: list[int],
        distance_km: float,
        cost_per_unit_per_km: float,
    ) -> TransportCostMatrix:
        """
        Create transport cost matrix with uniform distance between all sites.

        Useful for testing or simplified models.

        Args:
            site_ids: List of site IDs
            distance_km: Uniform distance between any two sites
            cost_per_unit_per_km: Cost per unit per km

        Returns:
            TransportCostMatrix with uniform costs

        """
        matrix = TransportCostMatrix(site_ids)

        for from_site in site_ids:
            for to_site in site_ids:
                if from_site != to_site:
                    transport_cost = TransportCost(
                        distance_km=distance_km,
                        cost_per_unit_per_km=cost_per_unit_per_km,
                    )
                    matrix.set_transport_cost(from_site, to_site, transport_cost)

        return matrix

    @staticmethod
    def create_from_coordinates(
        site_coordinates: dict[int, tuple[float, float]],
        cost_per_unit_per_km: float,
    ) -> TransportCostMatrix:
        """
        Create transport cost matrix from site coordinates.

        Uses haversine distance calculation.

        Args:
            site_coordinates: Dictionary of site_id -> (latitude, longitude)
            cost_per_unit_per_km: Cost per unit per km

        Returns:
            TransportCostMatrix with haversine distances

        """
        site_ids = list(site_coordinates.keys())
        matrix = TransportCostMatrix(site_ids)

        for from_site in site_ids:
            for to_site in site_ids:
                if from_site != to_site:
                    lat1, lon1 = site_coordinates[from_site]
                    lat2, lon2 = site_coordinates[to_site]

                    distance_km = DistanceCalculator.haversine_distance(lat1, lon1, lat2, lon2)

                    transport_cost = TransportCost(
                        distance_km=distance_km,
                        cost_per_unit_per_km=cost_per_unit_per_km,
                    )
                    matrix.set_transport_cost(from_site, to_site, transport_cost)

        return matrix
