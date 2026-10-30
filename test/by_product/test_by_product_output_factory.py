# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pandas as pd
import pytest

from by_product.by_product_output import ByProductOutput
from by_product.by_product_output_factory import ByProductOutputFactory


class TestByProductOutputFactory:
    """Test the ByProductOutputFactory class."""

    @pytest.fixture
    def mock_by_product_output_data(self):
        """Create mock by-product output data."""
        return pd.DataFrame(
            {
                'id_process': [1, 1, 2, 2],
                'id_by_product': [10, 11, 10, 12],
                'output_in_t_per_process_count': [50.0, 25.0, 100.0, 15.0],
            }
        ).set_index('id_process')

    @pytest.fixture
    def mock_by_products(self):
        """Create mock by-products map."""
        return {
            10: Mock(id=10, name='Steel Scrap'),
            11: Mock(id=11, name='Aluminum Scrap'),
            12: Mock(id=12, name='Copper Scrap'),
        }

    def test_factory_initialization(self, mock_by_product_output_data, mock_by_products):
        """Should initialize with output data and by-products map."""
        factory = ByProductOutputFactory(mock_by_product_output_data, mock_by_products)
        assert factory is not None
        assert factory._carriers == mock_by_products

    def test_create_returns_list_of_outputs(self, mock_by_product_output_data, mock_by_products):
        """create() should return a list of ByProductOutput objects."""
        factory = ByProductOutputFactory(mock_by_product_output_data, mock_by_products)
        outputs = factory.create(1)

        assert isinstance(outputs, list)
        assert len(outputs) == 2
        assert all(isinstance(o, ByProductOutput) for o in outputs)

    def test_create_returns_correct_outputs_for_process(self, mock_by_product_output_data, mock_by_products):
        """Should return only outputs for specified process."""
        factory = ByProductOutputFactory(mock_by_product_output_data, mock_by_products)

        outputs_process_1 = factory.create(1)
        outputs_process_2 = factory.create(2)

        assert len(outputs_process_1) == 2
        assert len(outputs_process_2) == 2

    def test_output_object_creation(self, mock_by_product_output_data, mock_by_products):
        """Should create ByProductOutput with correct attributes."""
        factory = ByProductOutputFactory(mock_by_product_output_data, mock_by_products)

        outputs = factory.create(1)
        first_output = outputs[0]

        assert first_output.output_in_t_per_process_count == 50.0
        assert first_output.by_product == mock_by_products[10]

    def test_create_empty_when_no_matching_process(self, mock_by_product_output_data, mock_by_products):
        """Should return empty list when process ID doesn't exist."""
        factory = ByProductOutputFactory(mock_by_product_output_data, mock_by_products)

        outputs = factory.create(999)
        assert outputs == []

    def test_output_inherits_from_base_class(self, mock_by_product_output_data, mock_by_products):
        """ByProductOutputFactory should inherit from OutputFactory."""
        from output.output_factory import OutputFactory

        factory = ByProductOutputFactory(mock_by_product_output_data, mock_by_products)
        assert isinstance(factory, OutputFactory)
