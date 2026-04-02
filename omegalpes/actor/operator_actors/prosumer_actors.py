#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module describes the Prosumer (producer and consumer) actor**

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

from omegalpes.actor.operator_actors.consumer_actors import Consumer
from omegalpes.actor.operator_actors.producer_actors import Producer
from omegalpes.energy.units.storage_units import StorageUnit
from omegalpes.general.optimisation.elements import *
from omegalpes.general.utils.maths import def_abs_value

__docformat__ = "restructuredtext en"


class Prosumer(Consumer, Producer):
    # TODO : rajouter le stockage dans les unités opérées
    """
    **Description**

        Prosumer class inherits from the the class OperatorActor, Consumer
        and Producer. It enables one to model an actor which is at the same
        time an energy producer and consumer
    """

    def __init__(self, name, operated_consumption_unit_list,
                 operated_production_unit_list,
                 operated_storage_unit_list, operated_node_list=None,
                 verbose=True):
        Consumer.__init__(self, name=name,
                          operated_unit_list=operated_consumption_unit_list,
                          operated_node_list=operated_node_list,
                          verbose=verbose)
        Producer.__init__(self, name=name,
                          operated_unit_list=operated_production_unit_list,
                          operated_node_list=operated_node_list,
                          verbose=False)
        self.operated_consumption_unit_list = operated_consumption_unit_list
        self.operated_production_unit_list = operated_production_unit_list
        self.operated_storage_unit_list = operated_storage_unit_list
        self.operated_unit_list = operated_consumption_unit_list + \
                                  operated_production_unit_list + \
                                  operated_storage_unit_list

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

    def _check_operated_storage_list(self, obj_operated_unit_list):
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
            final_operated_unit_list = self.operated_storage_unit_list
        else:
            final_operated_unit_list = self._check_operated_unit_list(
                obj_operated_unit_list)
        return final_operated_unit_list

    # OBJECTIVE #
    #TODO : rajouter le minimize capacity comme objectif
    def maximize_conso_prod_match(self,
                                  time,
                                  obj_operated_consumption_unit_list=None,
                                  obj_operated_production_unit_list=None,
                                  weight=1,
                                  pareto=False):
        """
        To create the objective in order to match at each time the consumption
        with the local production of the prosumer's units (all or part of
        them).

        :param obj_operated_consumption_unit_list: List of consumption units on
            which the objective will be applied. Might be empty.
        :param obj_operated_production_unit_list: List of production units on
            which the objective will be applied. Might be empty.
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_consumption_unit_list = \
            self._check_operated_consumption_list(
                obj_operated_consumption_unit_list)
        final_operated_production_unit_list = \
            self._check_operated_production_list(
                obj_operated_production_unit_list)

        consumption_p_string = ''
        production_p_string = ''
        for consumption_unit in final_operated_consumption_unit_list[:-1]:
            consumption_p_string += '{}_p[t] + '.format(consumption_unit.name)
        consumption_p_string += '{}_p[t]'.format(
            final_operated_consumption_unit_list[-1].name)
        for production_unit in final_operated_production_unit_list[:-1]:
            production_p_string += '{}_p[t] + '.format(production_unit.name)
        production_p_string += '{}_p[t]'.format(
            final_operated_production_unit_list[-1].name)

        self.conso_prod_match = Quantity(name='conso_prod_match',
                                         description='conso_prod_match '
                                                     'for objective',
                                         vlen=time.LEN, parent=self)

        self.calc_conso_prod_match = DefinitionDynamicConstraint(
            name='calc_conso_prod_match',
            exp_t='{0}_conso_prod_match[t] == ({1} - ( {2} )) * '
                  'time.DT'.format(
                self.name, production_p_string, consumption_p_string),
            t_range='for t in time.I', parent=self)

        self.conso_prod_match_abs = def_abs_value(
            self.conso_prod_match, q_min=-1e+5, q_max=1e+5)

        self.max_conso_prod_match = Objective(name='max_conso_prod_match',
                                              exp='lpSum({'
                                                  '}_conso_prod_match_abs[t] '
                                                  'for t in time.I)'.format(
                                                  self.name),
                                              weight=weight, pareto=pareto,
                                              parent=self)

    def maximize_selfconsumption_rate(
            self, time, obj_operated_production_unit_list=None,
            obj_operated_selfconsummed_production_export_list=None,
            obj_operated_selfconsummed_production_unit_list=None,
            weight=1, pareto=False):
        """
        To create the objective in order to maximize the selfconsumption rate
        of the prosumer's units (all or part of them) WHILE maximizing the
        load matching selfconsummed production is calculated with the export
        nodes.

        Selfconsumption rate = selfconsummed production / total production

        :param obj_operated_production_unit_list: List of production units on
            which the objective will be applied. Might be empty.
        :param obj_operated_selfconsummed_production_export_list: List of
            production exports from nodes on which the objective will be
            applied. Might be empty.
        :param obj_operated_selfconsummed_production_unit_list: List of
            production units on which the objective will be applied. Might be
            empty.
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_production_unit_list = \
            self._check_operated_production_list(
                obj_operated_production_unit_list)
        if obj_operated_selfconsummed_production_export_list:
            final_operated_selfconsummed_production_export_list = \
                self._check_operated_unit_list(
                    obj_operated_selfconsummed_production_export_list)
        if obj_operated_selfconsummed_production_unit_list:
            final_operated_selfconsummed_production_unit_list = \
                self._check_operated_unit_list(
                    obj_operated_selfconsummed_production_unit_list)

        production_p_string = ''
        sc_production_unit_p_string = ''
        sc_production_export_p_string = ''
        for production_unit in final_operated_production_unit_list[:-1]:
            production_p_string += '{}_p[t] + '.format(production_unit.name)
        production_p_string += '{}_p[t]'.format(
            final_operated_production_unit_list[-1].name)
        if obj_operated_selfconsummed_production_export_list:
            for sc_production_export in \
                    final_operated_selfconsummed_production_export_list[:-1]:
                sc_production_export_p_string += '{0}_{1}[t] + '.format(
                    sc_production_export.parent.name,
                    sc_production_export.name)
            sc_production_export_p_string += '{0}_{1}[t]'.format(
                final_operated_selfconsummed_production_export_list[
                    -1].parent.name,
                final_operated_selfconsummed_production_export_list[-1].name)
        if obj_operated_selfconsummed_production_unit_list:
            for sc_production_unit in \
                    final_operated_selfconsummed_production_unit_list[:-1]:
                sc_production_unit_p_string += '{}_p[t] + '.format(
                    sc_production_unit.name)
            sc_production_unit_p_string += '{}_p[t]'.format(
                final_operated_selfconsummed_production_unit_list[-1].name)

        self.selfconsumption_rate = Quantity(
            name='selfconsumption_rate', description='maximize selfconsumption'
                                                     'rate WHILE maximizing '
                                                     'the'
                                                     'load matching',
            vlen=time.LEN, parent=self)

        self.calc_selfconsumption_rate = DefinitionDynamicConstraint(
            name='calc_selfconsumption_rate',
            exp_t='{0}_selfconsumption_rate[t] == ({1} + {2} - ( {3} '
                  ')) * time.DT'.format(self.name,
                                        sc_production_export_p_string,
                                        sc_production_unit_p_string,
                                        production_p_string),
            t_range='for t in time.I', parent=self)

        self.selfconsumption_rate_abs = def_abs_value(
            self.selfconsumption_rate, q_min=-1e+5, q_max=1e+5)

        self.max_selfconsumption_rate = Objective(
            name='max_selfconsumption_rate',
            exp='lpSum({}_selfconsumption_rate_abs[t] for t in time.I)'
                .format(self.name),
            weight=weight, pareto=pareto, parent=self)

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
        final_operated_unit_list = self._check_operated_unit_list(obj_operated_unit_list)
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


    def maximize_selfproduction_rate(
            self, time, obj_operated_consumption_unit_list=None,
            obj_operated_selfproduced_consumption_export_list=None,
            obj_operated_selfproduced_consumption_unit_list=None,
            weight=1, pareto=False):
        """
        To create the objective in order to maximize the selfproduction rate
        of the prosumer's units (all or part of them) WHILE maximizing the
        load matching selfproduced consumption may required export nodes

        Selfproduction rate = selfproduced consumption / total consumption

        :param obj_operated_consumption_unit_list: List of consumption units on
            which the objective will be applied. Might be empty.
        :param obj_operated_selfproduced_consumption_export_list: List of
            production exports from nodes on which the objective will be
            applied.
            Might be empty.
        :param obj_operated_selfproduced_consumption_unit_list: List of
            production units on which the objective will be applied.
            Might be empty.
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_consumption_unit_list = \
            self._check_operated_consumption_list(
                obj_operated_consumption_unit_list)
        if obj_operated_selfproduced_consumption_export_list:
            final_operated_sp_consumption_export_list = \
                self._check_operated_unit_list(
                    obj_operated_selfproduced_consumption_export_list)
        if obj_operated_selfproduced_consumption_unit_list:
            final_operated_sp_consumption_unit_list = \
                self._check_operated_unit_list(
                    obj_operated_selfproduced_consumption_unit_list)

        consumption_p_string = ''
        sp_consumption_export_p_string = ''
        sp_consumption_unit_p_string = ''
        for consumption_unit in final_operated_consumption_unit_list[:-1]:
            consumption_p_string += '{}_p[t] + '.format(consumption_unit.name)
        consumption_p_string += '{}_p[t]'.format(
            final_operated_consumption_unit_list[-1].name)
        if obj_operated_selfproduced_consumption_export_list:
            for sp_consumption_export in \
                    final_operated_sp_consumption_export_list[:-1]:
                sp_consumption_export_p_string += '{0}_{1}[t] + '.format(
                    sp_consumption_export.parent.name,
                    sp_consumption_export.name)
            sp_consumption_export_p_string += '{0}_{1}[t]'.format(
                final_operated_sp_consumption_export_list[-1].parent.name,
                final_operated_sp_consumption_export_list[
                    -1].name)
        if obj_operated_selfproduced_consumption_unit_list:
            for sp_consumption_unit in \
                    final_operated_sp_consumption_unit_list[:-1]:
                sp_consumption_unit_p_string += '{}_p[t] + '.format(
                    sp_consumption_unit.name)
                sp_consumption_unit_p_string += '{}_p[t]'.format(
                    final_operated_sp_consumption_unit_list[-1].name)

        self.selfproduction_rate = Quantity(
            name='selfproduction_rate', description='maximize selfconsumption'
                                                    'rate WHILE maximizing the'
                                                    'load matching',
            vlen=time.LEN, parent=self)

        self.calc_selfproduction_rate = DefinitionDynamicConstraint(
            name='calc_selfproduction_rate',
            exp_t='{0}_selfproduction_rate[t] == ({1} + {2} - ( {3} '
                  ')) * time.DT'.format(
                self.name, sp_consumption_export_p_string,
                sp_consumption_unit_p_string, consumption_p_string),
            t_range='for t in time.I', parent=self)

        self.selfproduction_rate_abs = def_abs_value(
            self.selfproduction_rate, q_min=-1e+5, q_max=1e+5)

        self.max_selfproduction_rate = Objective(
            name='max_selfproduction_rate',
            exp='lpSum({}_selfproduction_rate_abs[t] for t in time.I)'
                .format(self.name),
            weight=weight, pareto=pareto, parent=self)

    def add_fixed_repartition_key(self, pv_consumption_list, pv_prod_tot):
        for i in pv_consumption_list:
            self.fixed_repartition_key = ActorDynamicConstraint(
                name='fixed_repartition_key',
                exp='{}[t]={}[t] for t in time.I'.format(
                    pv_consumption_list[0], pv_consumption_list[i]),
                parent=self)

    def add_nb_unit_minimum(self, nb_unit_min, energy_unit):
        self.nb_unit_min = ActorConstraint(
            name='nb_unit_min_{}'.format(energy_unit.name),
            exp='{0}_nb_unit >= {1}'.format(energy_unit.name,
                                            nb_unit_min)
        )

    def add_nb_unit_maximum(self, nb_unit_max, energy_unit):
        self.nb_unit_max = ActorConstraint(
            name='nb_unit_max_{}'.format(energy_unit.name),
            exp='{0}_nb_unit <= {1}'.format(energy_unit.name,
                                            nb_unit_max)
        )

    # TODO
    # def add_enedis_default_repartition_key(self, ):
