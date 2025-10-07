# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from mock import MagicMock, patch

from visitor.visitor import Visitor


@pytest.fixture
@patch.multiple(Visitor, __abstractmethods__=set())
def sut():
    return Visitor()


def test_visit_region(sut):
    with pytest.raises(NotImplementedError):
        sut.visit_region(region=MagicMock(), year=2020)


def test_visit_site(sut):
    with pytest.raises(NotImplementedError):
        sut.visit_site(site=MagicMock(), year=2020)


def test_production_unit(sut):
    with pytest.raises(NotImplementedError):
        sut.visit_production_unit(production_unit=MagicMock(), year=2020)


def test_visit_product(sut):
    with pytest.raises(NotImplementedError):
        sut.visit_product(product=MagicMock(), year=2020)


def test_visit_process(sut):
    with pytest.raises(NotImplementedError):
        sut.visit_process(process=MagicMock(), year=2020)


def test_finalize(sut):
    with pytest.raises(NotImplementedError):
        sut.finalize()
