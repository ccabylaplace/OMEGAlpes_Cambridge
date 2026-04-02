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
from ...energy.units.storage_units import StorageUnit
from ...energy.energy_nodes import EnergyNode

__docformat__ = "restructuredtext en"


class ElectricityGridOperator(OperatorActor):
    """
    **Description**

        Electricity_grid_operator class inherits from the the class
        OperatorActor. It,enables one to model a grid operator actor.

    """

    def __init__(self, name, operated_node_list,
                 verbose=True):
        OperatorActor.__init__(self, name=name,
                               operated_unit_type_tuple=(EnergyNode, StorageUnit),
                               operated_node_list=operated_node_list,
                               verbose=verbose)

    def add_energy_transfer_maximum(self, max_e_tot,
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

    def minimize_energy_transfer(self, obj_operated_unit_list=None,
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

    def minimize_capacity(self, obj_operated_unit_list=None, weight=1, pc_max_ratio=None, pd_max_ratio=None, max_capacity = None,
                            pareto=False):
        """
        To create the objective in order to minimize the capacity of the thermal storage
        of the HeatGridOperator's units (all or part of them).

        :param obj_operated_unit_list: List of units on which the
            objective will be applied. Might be empty.
        :param weight: Weight coefficient for the objective
        :param max_capacity: maximal capacity that can be ensured (kWh)
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        index_unit = 0
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            if isinstance(operated_unit, StorageUnit):
                if max_capacity == None:
                    operated_unit.minimize_capacity(weight=weight, pc_max_ratio=pc_max_ratio, pd_max_ratio=pd_max_ratio,
                                                        pareto=pareto, max_capacity = max_capacity)
                    index_unit += 1

                else:
                    operated_unit.minimize_capacity(weight=weight, pc_max_ratio=pc_max_ratio, pd_max_ratio=pd_max_ratio,
                                                        pareto=pareto, max_capacity = max_capacity[index_unit])

                    del operated_unit.def_max_capacity
                    operator_storage_cst = ActorConstraint(
                        exp="{0}_capacity <= {1}".format(operated_unit.name, max_capacity[index_unit]),
                        name="def_min_capacity_prosumer",
                        parent=operated_unit)

                    setattr(operated_unit, "def_min_capacity_prosumer", operator_storage_cst)
                    index_unit += 1


class HeatGridOperator(OperatorActor):
    """
    **Description**

        Electricity_grid_operator class inherits from the the class
        OperatorActor. It
        enables one to model a grid operator actor.

    """

    def __init__(self, name, operated_node_list, operated_unit_list=None,
                 verbose=True):
        OperatorActor.__init__(self, name=name,
                               operated_unit_type_tuple=(ProductionUnit,
                                                         StorageUnit,
                                                         EnergyNode),
                               operated_unit_list=operated_unit_list,
                               operated_node_list=operated_node_list,
                               verbose=verbose)

    # OBJECTIVES #
    # Energy objectives
    def minimize_production(self, obj_operated_unit_list=None, weight=1,
                            pareto=False):
        """
        To create the objective in order to minimize the production of the
        HeatGridOperator's units (all or part of them).

        :param obj_operated_unit_list: List of units on which the
            objective will be applied. Might be empty.
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            if isinstance(operated_unit, ProductionUnit):
                operated_unit.minimize_production(weight=weight,
                                                  pareto=pareto)

    def minimize_capacity(self, obj_operated_unit_list=None, weight=1, pc_max_ratio=None, pd_max_ratio=None, max_capacity = None, soc_0 = None,
                            pareto=False):
        """
        To create the objective in order to minimize the capacity of the thermal storage
        of the HeatGridOperator's units (all or part of them).

        :param obj_operated_unit_list: List of units on which the
            objective will be applied. Might be empty.
        :param weight: Weight coefficient for the objective
        :param max_capacity: maximal capacity that can be ensured (kWh)
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        index_unit = 0
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            if isinstance(operated_unit, StorageUnit):
                if max_capacity == None:
                    operated_unit.minimize_capacity(weight=weight, pc_max_ratio=pc_max_ratio, pd_max_ratio=pd_max_ratio, soc_0 = soc_0,
                                                        pareto=pareto, max_capacity = max_capacity)
                    index_unit += 1

                else:
                    operated_unit.minimize_capacity(weight=weight, pc_max_ratio=pc_max_ratio, pd_max_ratio=pd_max_ratio, soc_0 = soc_0,
                                                        pareto=pareto, max_capacity = max_capacity[index_unit])

                    del operated_unit.def_max_capacity
                    operator_storage_cst = ActorConstraint(
                        exp="{0}_capacity <= {1}".format(operated_unit.name, max_capacity[index_unit]),
                        name="def_min_capacity_prosumer",
                        parent=operated_unit)

                    setattr(operated_unit, "def_min_capacity_prosumer", operator_storage_cst)
                    index_unit += 1

    def maximize_RR_energy_rate(self, weight=1, pareto=False):
        """
        To create the objective in order to maximize the percentage rate
        of renewable or recovery energy over the study
        """
        rr_energy_pole_string = ''

        for operated_node in self.operated_node_list:
            for operated_pole in operated_node.get_input_poles:
                if operated_pole[operated_pole.flow].parent.rr_energy:
                    rr_energy_pole_string += '+ ' + operated_pole[
                        operated_pole.flow].parent.name + \
                                             '_' + operated_pole[
                                                 operated_pole.flow].name + \
                                             '[t] '

            obj_name = 'maximize_EnRR_rate_in_{}_network'.format(self.name)
            exp = 'lpSum(' + rr_energy_pole_string + 'for t in time.I)'
            print(exp)
            self.max_EnRR_rate = Objective(name=obj_name,
                                           exp=exp,
                                           weight=-1 * weight,
                                           pareto=pareto,
                                           parent=self)

    # CONSTRAINTS #
    # Energy constraints
    # TODO to adapt to a year period
    def add_RR_energy_rate_minimum_over_the_study(self, percentage_rate=50):
        """
        To create the actor constraint of a minimum of a percentage rate
        (50% by default) of renewable or recovery energy over the study.

        :param percentage_rate: Minimum of the percentage rate of renewable or
            recovery energy. 50% by default following the TVA reduction
        """
        rr_energy_pole_string = ''
        pole_string = ''

        for operated_node in self.operated_node_list:
            for operated_pole in operated_node.get_input_poles:
                pole_string += '+ ' + operated_pole[
                    operated_pole.flow].parent.name + \
                               '_' + operated_pole[
                                   operated_pole.flow].name + '[t] '

                if operated_pole[operated_pole.flow].parent.rr_energy:
                    rr_energy_pole_string += '+ ' + operated_pole[
                        operated_pole.flow].parent.name + \
                                             '_' + operated_pole[
                                                 operated_pole.flow].name + \
                                             '[t] '

            cst_name = 'minimum_EnRR_rate_over_study_in_{}_network'.format(
                self.name)
            exp = 'lpSum(' + rr_energy_pole_string + 'for t in time.I) >= ' + \
                  str(percentage_rate) + \
                  '/100 * lpSum(' + pole_string + 'for t in time.I)'
            setattr(self, cst_name, ActorConstraint(exp=exp,
                                                    name=cst_name,
                                                    parent=self))

    def add_RR_energy_rate_minimum_at_each_time_step(self, percentage_rate=50):
        """
        To create the actor constraint of a minimum of a percentage rate
        (50% by default) of renewable or recovery energy at each time step.

        :param percentage_rate: Minimum of the percentage rate of renewable or
            recovery energy. 50% by default following the TVA reduction
        """
        rr_energy_pole_string = ''
        pole_string = ''

        for operated_node in self.operated_node_list:
            for operated_pole in operated_node.get_input_poles:
                pole_string += '+ ' + operated_pole[
                    operated_pole.flow].parent.name + \
                               '_' + operated_pole[
                                   operated_pole.flow].name + '[t] '

                if operated_pole[operated_pole.flow].parent.rr_energy:
                    rr_energy_pole_string += '+ ' + operated_pole[
                        operated_pole.flow].parent.name + \
                                             '_' + operated_pole[
                                                 operated_pole.flow].name + \
                                             '[t] '

            cst_name = 'minimum_EnRR_rate_at_each_time_step_in_{' \
                       '}_network'.format(self.name)
            exp_t = rr_energy_pole_string + ' >= ' + str(percentage_rate) + \
                    '/100 * (' + pole_string + ')'
            print(exp_t, 'exp_t')
            setattr(self, cst_name, ActorDynamicConstraint(exp_t=exp_t,
                                                           name=cst_name,
                                                           parent=self))
