# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from pandas import DataFrame
from test_utils.isi_mock import Mock, fixture, patch

from processes.installed_process import InstalledProcess
from processes.process_option import ProcessOption
from sub_production_unit.sub_production_unit import SubProductionUnit
from sub_production_unit.sub_production_unit_factory import SubProductionUnitFactory


@fixture
def sut():
    return SubProductionUnitFactory(
        data_interface=Mock(),
        process_map={},
    )


def test_construction(sut):
    assert sut is not None


mocked_sub_production_unit_data = DataFrame(
    [
        {
            'id_process': 1,
            'year_of_last_reinvestment': 1,
            'process_execution_count_for_start_year': 1,
            'max_process_execution_count': 1,
        },
        {
            'id_process': 2,
            'year_of_last_reinvestment': 2,
            'process_execution_count_for_start_year': 2,
            'max_process_execution_count': 2,
        },
    ]
)


@patch(SubProductionUnit.__init__, None)
@patch(InstalledProcess.__init__, None)
class TestCreateForStartYear:
    @patch(
        SubProductionUnitFactory._sub_production_unit_data,
        mocked_sub_production_unit_data,
    )
    def test_normal_usage(self, sut):
        sut._process_map = {1: Mock(), 2: Mock()}
        result = sut.create_for_start_year(1)
        assert isinstance(result[0], SubProductionUnit)
        assert isinstance(result[1], SubProductionUnit)

    @patch(SubProductionUnitFactory._sub_production_unit_data, DataFrame())
    def test_no_sub_production_units_fails(self, sut):
        with pytest.raises(ValueError, match='No sub production units found'):
            sut.create_for_start_year(1)


@patch(
    InstalledProcess.__init__,
    None,
)
@patch(SubProductionUnitFactory._unique_id)
@patch(SubProductionUnit.__init__, None)
class TestCreateSubProductionUnitForProcessOption:
    def test_process_option_with_installed_process_fails(self, sut):
        installed_process = InstalledProcess(process=Mock(), sub_production_unit=Mock())
        process_option = ProcessOption(installed_process)
        production_unit = Mock(id=1)
        with pytest.raises(KeyError):
            sut.create_sub_production_unit_for_process_option(
                process_option,
                100,
                production_unit,
                2020,
            )

    def test_process_option(self, sut):
        process = Mock()
        process_option = ProcessOption(process)
        production_unit = Mock(id=1)

        result = sut.create_sub_production_unit_for_process_option(
            process_option,
            100,
            production_unit,
            2020,
        )
        assert isinstance(result, SubProductionUnit)


def test_unique_id(sut):
    sut._next_ids = {}
    result = sut._unique_id(1)
    assert result == 1010000

    result = sut._unique_id(1)
    assert result == 1010001


def test_sub_production_unit_data(sut):
    sut._data_interface.production_unit_sub_production_unit_mapping = {1: 'mocked_entry'}
    result = sut._sub_production_unit_data(1)
    assert result == 'mocked_entry'
