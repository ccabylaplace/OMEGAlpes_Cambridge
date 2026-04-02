#! usr/bin/env python3
# -*- coding: utf-8 -*-

"""
**This module describes the grid operator**

 Few objectives and constraints are available.

 Objectives :


 Constraints :


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

from .operator_actors import OperatorActor
from ...general.optimisation.elements import *
from ...energy.units.consumption_units import ConsumptionUnit
from ...energy.units.production_units import ProductionUnit
from ...energy.energy_nodes import EnergyNode

__docformat__ = "restructuredtext en"


class Supplier(OperatorActor):
    """
    **Description**

        Supplier class inherits from the the class OperatorActor, Consumer
        and Producer. It enables one to model a supplier.
    """

    def __init__(self, name, operated_consumption_unit_list,
                 operated_production_unit_list, operated_node_list=None,
                 verbose=True):
        OperatorActor.__init__(self, name=name,
                               operated_unit_list=operated_consumption_unit_list,
                               operated_unit_type_tuple=(ConsumptionUnit,
                                                         ProductionUnit),
                               operated_node_list=operated_node_list,
                               verbose=verbose)
        self.operated_consumption_unit_list = operated_consumption_unit_list
        self.operated_production_unit_list = operated_production_unit_list
        self.operated_unit_list = operated_consumption_unit_list + \
                                  operated_production_unit_list
        self.operated_node_list = operated_node_list

    # CONSTRAINTS #
    # Energy constraints

    def _check_operated_consumption_list(self, obj_operated_unit_list):
        """
        Check if the objective must be applied to the whole energy units
        under the scope of responsibility (if obj_operated_unit_list is
        empty); or to selected units and in this case, if the units are under
        the scope of responsibility. Only for consumption units

        :param obj_operated_unit_list: List of units on which the
            objective will be applied. Might be empty.
        :return: the list of the operated energy unit in order to apply
            the objective on these units
        """
        final_operated_unit_list = []
        if not obj_operated_unit_list:
            final_operated_unit_list = self.operated_consumption_unit_list
        else:
            final_operated_unit_list = self._check_operated_unit_list(
                obj_operated_unit_list)
        return final_operated_unit_list

    def _check_operated_production_list(self, obj_operated_unit_list):
        """
        Check if the objective must be applied to the whole energy units
        under the scope of responsibility (if obj_operated_unit_list is
        empty); or to selected units and in this case, if the units are under
        the scope of responsibility. Only for production units

        :param obj_operated_unit_list: List of units on which the
            objective will be applied. Might be empty.
        :return: the list of the operated energy unit in order to apply
            the objective on these units
        """
        final_operated_unit_list = []
        if not obj_operated_unit_list:
            final_operated_unit_list = self.operated_production_unit_list
        else:
            final_operated_unit_list = self._check_operated_unit_list(
                obj_operated_unit_list)
        return final_operated_unit_list

    def add_energy_collected_maximum(self, max_e_tot,
                                     cst_operated_unit_list=None,
                                     cst_operated_exports_list=None,
                                     ):
        """
        To create the actor constraint of a maximum of energy collected.

        :param max_e_tot: Maximum of the total energy collected over the
            study period
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        if isinstance(max_e_tot, (int, float)):
            final_operated_consumption_unit_list = cst_operated_unit_list

            consumption_name_string = ''
            consumption_p_string = '+'
            if cst_operated_unit_list:
                for consumption_unit in final_operated_consumption_unit_list:
                    consumption_name_string += '_{}'.format(
                        consumption_unit.name)

                for consumption_unit in final_operated_consumption_unit_list[
                                        :-1]:
                    consumption_p_string += '{}_p[t] + '.format(
                        consumption_unit.name)
                consumption_p_string += '{}_p[t] '.format(
                    final_operated_consumption_unit_list[-1].name)

            export_string = ''
            if cst_operated_exports_list:
                for export in cst_operated_exports_list[:-1]:
                    export_string += '+ {0}_{1}[t] '.format(
                        export.parent.name, export.name)
                export_string += '+ {0}_{1}[t] '.format(
                    cst_operated_exports_list[-1].parent.name,
                    cst_operated_exports_list[-1].name)

            cst_name = 'collected_energy_max{}'.format(
                consumption_name_string)
            exp = 'lpSum({0} {1} for t in time.I) <= {2}'.format(
                consumption_p_string, export_string, max_e_tot)

            setattr(self, cst_name, ActorConstraint(exp=exp,
                                                    name=cst_name,
                                                    parent=self))
        else:
            raise TypeError('max_e_tot in max_collected_energy '
                            'constraint should be an int or a float')

    def minimize_energy_collection(self, obj_operated_unit_list=None,
                                   obj_operated_exports_list=None,
                                   pareto=False, weight=1):
        """
        To create the objective in order to maximize the consumption of the
        consumer's units (all or part of them).

        :param obj_operated_unit_list: List of units on which the objective
            will be applied. Might be empty
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        if not obj_operated_exports_list:
            obj_operated_unit_list = self._check_operated_unit_list(
                obj_operated_unit_list)

        consumption_name_string = ''
        consumption_p_string = '+'
        if obj_operated_unit_list:
            for consumption_unit in obj_operated_unit_list:
                consumption_name_string += '_{}'.format(
                    consumption_unit.name)

            for consumption_unit in obj_operated_unit_list[:-1]:
                consumption_p_string += '{}_p[t] + '.format(
                    consumption_unit.name)
            consumption_p_string += '{}_p[t] '.format(
                obj_operated_unit_list[-1].name)

        export_string = ''
        if obj_operated_exports_list:
            for export in obj_operated_exports_list[:-1]:
                export_string += '+ {0}_{1}[t] '.format(
                    export.parent.name, export.name)
            export_string += '+ {0}_{1}[t] '.format(
                obj_operated_exports_list[-1].parent.name,
                obj_operated_exports_list[-1].name)

        cst_name = 'minimize_energy_collection{}'.format(
            consumption_name_string)
        exp = 'lpSum({0} {1} for t in time.I)'.format(
            consumption_p_string, export_string)

        setattr(self, cst_name, Objective(exp=exp,
                                          name=cst_name,
                                          parent=self,
                                          pareto=pareto,
                                          weight=weight))
