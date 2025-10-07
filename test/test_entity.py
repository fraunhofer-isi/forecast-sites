# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from mock import MagicMock, patch

from entity import Entity


@patch.multiple(Entity, __abstractmethods__=set())
def test_entity():
    entity = Entity()

    with pytest.raises(NotImplementedError):
        entity.accept(visitor=MagicMock(), year=2020)
