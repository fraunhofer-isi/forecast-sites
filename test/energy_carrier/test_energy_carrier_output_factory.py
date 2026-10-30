# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pandas as pd
import pytest

from energy_carrier.energy_carrier_output import EnergyCarrierOutput
from energy_carrier.energy_carrier_output_factory import EnergyCarrierOutputFactory


class TestEnergyCarrierOutputFactory:
    """Test the EnergyCarrierOutputFactory class."""

    @pytest.fixture
    def mock_energy_carrier_output_data(self):
        """Create mock energy carrier output data."""
        return pd.DataFrame(
            {
                'id_process': [1, 1, 2, 2],
                'id_energy_carrier': [1, 2, 1, 3],
                'output_in_gj_per_process_count': [250.0, 125.0, 500.0, 75.0],
            }
        ).set_index('id_process')

    @pytest.fixture
    def mock_energy_carriers(self):
        """Create mock energy carriers map."""
        return {
            1: Mock(id=1, name='Electricity'),
            2: Mock(id=2, name='Natural Gas'),
            3: Mock(id=3, name='Heat'),
        }

    def test_factory_initialization(self, mock_energy_carrier_output_data, mock_energy_carriers):
        """Should initialize with output data and energy carriers map."""
        factory = EnergyCarrierOutputFactory(mock_energy_carrier_output_data, mock_energy_carriers)
        assert factory is not None
        assert factory._carriers == mock_energy_carriers

    def test_create_returns_list_of_outputs(self, mock_energy_carrier_output_data, mock_energy_carriers):
        """create() should return a list of EnergyCarrierOutput objects."""
        factory = EnergyCarrierOutputFactory(mock_energy_carrier_output_data, mock_energy_carriers)
        outputs = factory.create(1)

        assert isinstance(outputs, list)
        assert len(outputs) == 2
        assert all(isinstance(o, EnergyCarrierOutput) for o in outputs)

    def test_create_returns_correct_outputs_for_process(self, mock_energy_carrier_output_data, mock_energy_carriers):
        """Should return only outputs for specified process."""
        factory = EnergyCarrierOutputFactory(mock_energy_carrier_output_data, mock_energy_carriers)

        outputs_process_1 = factory.create(1)
        outputs_process_2 = factory.create(2)

        assert len(outputs_process_1) == 2
        assert len(outputs_process_2) == 2

    def test_output_object_creation(self, mock_energy_carrier_output_data, mock_energy_carriers):
        """Should create EnergyCarrierOutput with correct attributes."""
        factory = EnergyCarrierOutputFactory(mock_energy_carrier_output_data, mock_energy_carriers)

        outputs = factory.create(1)
        first_output = outputs[0]

        assert first_output.output_in_gj_per_process_count == 250.0
        assert first_output.energy_carrier == mock_energy_carriers[1]

    def test_create_empty_when_no_matching_process(self, mock_energy_carrier_output_data, mock_energy_carriers):
        """Should return empty list when process ID doesn't exist."""
        factory = EnergyCarrierOutputFactory(mock_energy_carrier_output_data, mock_energy_carriers)

        outputs = factory.create(999)
        assert outputs == []

    def test_output_inherits_from_base_class(self, mock_energy_carrier_output_data, mock_energy_carriers):
        """EnergyCarrierOutputFactory should inherit from OutputFactory."""
        from output.output_factory import OutputFactory

        factory = EnergyCarrierOutputFactory(mock_energy_carrier_output_data, mock_energy_carriers)
        assert isinstance(factory, OutputFactory)
