# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from abc import ABC, abstractmethod

NOT_IMPLEMENTED = "You should implement this."


class Visitor(ABC):
    """
    This abstract base class helps to implement the visitor pattern.
    Usage: region.accept(visitor)
    Also see
    https://gitlab.cc-asp.fraunhofer.de/fhgdemo/python/getting_started_jupyter/-/blob/master/m_design_patterns/b_behavioural/visitor.ipynb
    """

    @abstractmethod
    def visit_region(self, region, year):
        raise NotImplementedError(NOT_IMPLEMENTED)

    @abstractmethod
    def visit_site(self, site, year):
        raise NotImplementedError(NOT_IMPLEMENTED)

    @abstractmethod
    def visit_production_unit(self, production_unit, year):
        raise NotImplementedError(NOT_IMPLEMENTED)

    @abstractmethod
    def visit_product(self, product, year):
        raise NotImplementedError(NOT_IMPLEMENTED)

    @abstractmethod
    def visit_process(self, process, year):
        raise NotImplementedError(NOT_IMPLEMENTED)

    @abstractmethod
    def finalize(self):
        raise NotImplementedError(NOT_IMPLEMENTED)
