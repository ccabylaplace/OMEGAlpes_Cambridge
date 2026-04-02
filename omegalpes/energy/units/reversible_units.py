#! usr/bin/env python3
#  coding=utf-8 #

"""
**This module defines the reversible units**

 The reversible_units module defines various kinds of reversible units with
 associated attributes and methods, from simple to specific ones, inheriting
 from AssemblyUnit.

 It includes :
    - ReversibleUnit : simple reversible unit with only one consumption and
    one production units. It can both produce and consume energy but not at the
    same time.

..
    Copyright 2018 G2Elab / MAGE

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from pulp import LpBinary

from .energy_units import EnergyUnit, VariableEnergyUnit, FixedEnergyUnit, \
    SeveralEnergyUnit, SquareEnergyUnit, ShiftableEnergyUnit, AssemblyUnit
from .production_units import ProductionUnit, VariableProductionUnit, \
    FixedProductionUnit
from .consumption_units import ConsumptionUnit, FixedConsumptionUnit, \
    VariableConsumptionUnit
from ...general.optimisation.elements import *
from ...general.optimisation.elements import Objective
from ...general.optimisation.elements import Quantity

__docformat__ = "restructuredtext en"


class ReversibleUnit(AssemblyUnit):
    """
    **Description**

        Simple Reversible unit inheriting from AssemblyUnit. It is made of a
        consumption unit and a production unit that can both operate but not
        at the same time (reversible constraint).

    **Attributes**

     * production_unit (ProductionUnit)
     * consumption_unit (ConsumptionUnit)
     * def_rev (DefinitionDynamicConstraint): definition of the reversible
     constraint
     * def_rev_c (DefinitionDynamicConstraint): definition of the reversible
     constraint in the case where only the consumption is fixed
     * def_rev_p (DefinitionDynamicConstraint): definition of the reversible
     constraint in the case where only the production is fixed

    """

    def __init__(self, time, name, pmin_cons=0, pmax_cons=1e+5,
                 p_cons=None, pmin_prod=0, pmax_prod=1e+5, p_prod=None,
                 energy_type_prod=None, energy_type_cons=None, verbose=True):
        """
        :param time: time used in the studies period
        :param name: name of the reversible unit
        :param pmin_cons: minimal power for the consumption of the reversible
        unit [kW]
        :param pmax_cons: maximal power for the consumption of the reversible
        unit [kW]
        :param p_cons: power values for the consumption of the reversible
        unit [kW]
        :param pmin_prod: minimal power for the production of the reversible
        unit [kW]
        :param pmax_prod: maximal power for the production of the reversible
        unit [kW]
        :param p_prod: power values for the production of the reversible
        unit [kW]
        :param energy_type_prod: produced energy type
        :param energy_type_cons: consumed energy type
        :param verbose:

        """

        if p_prod is None:
            self.production_unit = VariableProductionUnit(
                time, name + '_prod', p_min=pmin_prod, p_max=pmax_prod,
                energy_type=energy_type_prod, verbose=verbose)
        else:
            self.production_unit = FixedProductionUnit(
                time, name + '_prod', p=p_prod,
                energy_type=energy_type_prod, verbose=verbose)

        if p_cons is None:
            self.consumption_unit = VariableConsumptionUnit(
                time, name + '_cons', p_min=pmin_cons, p_max=pmax_cons,
                energy_type=energy_type_cons, verbose=verbose)
        else:
            self.consumption_unit = FixedConsumptionUnit(
                time, name + '_cons', p=p_cons, energy_type=energy_type_cons,
                verbose=verbose)

        AssemblyUnit.__init__(self, time, name,
                              prod_units=[self.production_unit],
                              cons_units=[self.consumption_unit],
                              verbose=verbose)

        # CONSTRAINTS
        if p_cons is None and p_prod is None:
            self.def_rev = DefinitionDynamicConstraint(
                exp_t='{0}_p[t] - (1 - {1}_u[t]) * {2} <= 0'.format(
                    self.production_unit.name, self.consumption_unit.name,
                    pmax_prod),
                t_range='for t in time.I',
                name='def_rev', parent=self)

        elif p_prod is None:
            # The consumption unit is a FixedEnergyUnit and no u attribute
            # is defined for it. The reversible constraint uses the u
            # attribute of the production unit.
            self.def_rev_c = DefinitionDynamicConstraint(
                exp_t='{0}_p[t] - (1 - {1}_u[t]) * {2} <= 0'.format(
                    self.consumption_unit.name, self.production_unit.name,
                    pmax_cons),
                t_range='for t in time.I',
                name='def_rev_c', parent=self)

        elif p_cons is None:
            # The production unit is a FixedEnergyUnit and no u attribute
            # is defined for it. The reversible constraint uses the u
            # attribute of the consumption unit.
            self.def_rev_p = DefinitionDynamicConstraint(
                exp_t='{0}_p[t] - (1 - {1}_u[t]) * {2} <= 0'.format(
                    self.production_unit.name, self.consumption_unit.name,
                    pmax_prod),
                t_range='for t in time.I',
                name='def_rev_p', parent=self)

        else:
            # If both production and consumption are fixed, they should be
            # consistent with the reversible unit behaviour.
            for (pc, pp) in zip(self.production_unit.p.get_value(),
                                self.consumption_unit.p.get_value()):
                if pc != 0 and pp != 0:
                    raise TypeError("The reversible unit power values for "
                                    "production and consumption should be "
                                    "consistent: there cannot be consumption "
                                    "and production at the same time step.")
                else:
                    pass
