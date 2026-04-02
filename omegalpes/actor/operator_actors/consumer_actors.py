#! usr/bin/env python3
# -*- coding: utf-8 -*-

"""
**This module describes the Consumer actor**

 Few objectives and constraints are available.

 Objectives :
    - maximize_consumption
    - minimize_consumption
    - minimize_co2_consumption
    - minimize_consumption_costs

 Constraints :
    - energy_consumption_minimum
    - energy_consumption_maximum
    - power_consumption_minimum
    - power_consumption_maximum

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
from ...energy.energy_nodes import EnergyNode

__docformat__ = "restructuredtext en"


class Consumer(OperatorActor):
    """
    **Description**

        Consumer class inherits from the the class OperatorActor. It enables
        one to model a consumer actor.

    """

    def __init__(self, name, operated_unit_list, operated_node_list=None,
                 verbose=True):
        OperatorActor.__init__(self, name=name,
                               operated_unit_type_tuple=(ConsumptionUnit,
                                                         EnergyNode),
                               operated_unit_list=operated_unit_list,
                               operated_node_list=operated_node_list,
                               verbose=verbose)

    # OBJECTIVES #
    # Energy objectives
    def minimize_consumption(self, obj_operated_unit_list=None, weight=1,
                             pareto=False):
        """
        To create the objective in order to minimize the consumption of the
        consumer's units (all or part of them).

        :param obj_operated_unit_list: List of units on which the
            objective will be applied. Might be empty
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            if isinstance(operated_unit, ConsumptionUnit):
                operated_unit.minimize_consumption(weight=weight,
                                                   pareto=pareto)

    def maximize_consumption(self, obj_operated_unit_list=None, weight=1,
                             pareto=False):
        """
        To create the objective in order to maximize the consumption of the
        consumer's units (all or part of them).

        :param obj_operated_unit_list: List of units on which the objective
            will be applied. Might be empty
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            if isinstance(operated_unit, ConsumptionUnit):
                operated_unit.maximize_consumption(weight=weight,
                                                   pareto=pareto)

    # Economic objectives
    def minimize_consumption_cost(self, obj_operated_unit_list=None,
                                  weight=1, pareto=False):
        """
        To create the objective in order to minimize the expenses due to the
        consumer's units (all or part of them).

        :param obj_operated_unit_list: List of units on which the objective
            will be applied. Might be empty
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            operated_unit.minimize_consumption_cost(weight=weight,
                                                    pareto=pareto)

    # CO2 objectives
    def minimize_co2_consumption(self, obj_operated_unit_list=None, weight=1,
                                 pareto=False):
        """
        To create the objective in order to minimize the co2 emissions due to
        the consumer's units (all or part of them).

        :param obj_operated_unit_list: List of units on which the objective
            will be applied. Might be empty
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            operated_unit.minimize_co2_emissions(weight=weight,
                                                 pareto=pareto)

    # CONSTRAINTS #
    # Energy constraints
    def add_energy_consumption_minimum(self, min_e_tot,
                                       cst_operated_unit_list=None):
        """
        To create the actor constraint of a minimum of energy consumption.

        :param min_e_tot: Minimum of the total energy consumption over the
            study period
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        if isinstance(min_e_tot, (int, float)):
            final_operated_unit_list = self._check_operated_unit_list(
                cst_operated_unit_list)

            consumption_name_string = ''
            for consumption_unit in final_operated_unit_list:
                consumption_name_string += '_{}'.format(
                    consumption_unit.name)

            consumption_p_string = ''
            for consumption_unit in final_operated_unit_list[:-1]:
                consumption_p_string += '{}_p[t] + '.format(
                    consumption_unit.name)
            consumption_p_string += '{}_p[t] '.format(
                final_operated_unit_list[-1].name)

            cst_name = 'min_energy_conso{}'.format(consumption_name_string)
            exp = 'lpSum({0} for t in time.I) >= {1}'.format(
                consumption_p_string, min_e_tot)

            setattr(self, cst_name, ActorConstraint(exp=exp,
                                                    name=cst_name,
                                                    parent=self))

        else:
            raise TypeError('min_e_tot in energy_consumption_minimum '
                            'constraint should be an int or a float')

    def add_energy_consumption_maximum(self, max_e_tot,
                                       cst_operated_unit_list=None):
        """
        To create the actor constraint of a maximum of energy consumption.

        :param max_e_tot: Maximum of the total energy consumption over the
            study period
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        if isinstance(max_e_tot, (int, float)):
            final_operated_unit_list = self._check_operated_unit_list(
                cst_operated_unit_list)

            consumption_name_string = ''
            for consumption_unit in final_operated_unit_list:
                consumption_name_string += '_{}'.format(
                    consumption_unit.name)

            consumption_p_string = ''
            for consumption_unit in final_operated_unit_list[:-1]:
                consumption_p_string += '{}_p[t] + '.format(
                    consumption_unit.name)
            consumption_p_string += '{}_p[t] '.format(
                final_operated_unit_list[-1].name)

            cst_name = 'max_energy_conso{}'.format(consumption_name_string)
            exp = 'lpSum({0} for t in time.I) <= {1}'.format(
                consumption_p_string, max_e_tot)

            setattr(self, cst_name, ActorConstraint(exp=exp,
                                                    name=cst_name,
                                                    parent=self))
        else:
            raise TypeError('max_e_tot in max_energy_conso '
                            'constraint should be an int or a float')

    def add_power_consumption_by_unit_minimum(self, min_p, time,
                                              cst_operated_unit_list=None):
        """
        To create the actor constraint of a minimum of power consumption
        for each unit.

        :param min_p: Minimum of the power consumption. May be an int,
            float or a list with the size of the period study
        :param time: period of the study
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        final_operated_unit_list = self._check_operated_unit_list(
            cst_operated_unit_list)

        for consumption_unit in final_operated_unit_list:

            cst_name = 'min_by_unit_power_conso_{}'.format(
                consumption_unit.name)

            if isinstance(min_p, (int, float)):
                exp_t = '{0}_p[t] >= {1}'.format(
                    consumption_unit.name,
                    min_p)
                setattr(self, cst_name, ActorDynamicConstraint(
                    exp_t=exp_t, name=cst_name, parent=self))

            elif isinstance(min_p, list):
                if len(min_p) != time.LEN:
                    raise IndexError(
                        "Your minimal power should be the size of the time "
                        "period : {} but equals {}.".format(time.LEN,
                                                            len(min_p)))
                else:
                    exp_t = '{0}_p[t] >= {1}[t]'.format(consumption_unit.name,
                                                        min_p)
                    setattr(self, cst_name, ActorDynamicConstraint(
                        exp_t=exp_t, name=cst_name, parent=self))
            else:
                raise TypeError('Your minimal power should be an int, '
                                'a float or a list.')

    def add_power_consumption_by_unit_maximum(self, max_p, time,
                                              cst_operated_unit_list=None):
        """
        To create the actor constraint of a maximum of power consumption
        for each unit.

        :param max_p: Maximum of the power consumption. May be an int,
            float or a list with the size of the period study
        :param time: period of the study
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        final_operated_unit_list = self._check_operated_unit_list(
            cst_operated_unit_list)

        for consumption_unit in final_operated_unit_list:

            cst_name = 'max_by_unit_power_conso_{}'.format(
                consumption_unit.name)

            if isinstance(max_p, (int, float)):
                exp_t = '{0}_p[t] <= {1}'.format(
                    consumption_unit.name,
                    max_p)
                setattr(self, cst_name, ActorDynamicConstraint(
                    exp_t=exp_t, name=cst_name, parent=self))

            elif isinstance(max_p, list):
                if len(max_p) != time.LEN:
                    raise IndexError(
                        "Your maximal power should be the size of the time "
                        "period : {} but equals {}.".format(time.LEN,
                                                            len(max_p)))
                else:
                    exp_t = '{0}_p[t] <= {1}[t]'.format(consumption_unit.name,
                                                        max_p)
                    setattr(self, cst_name, ActorDynamicConstraint(
                        exp_t=exp_t, name=cst_name, parent=self))
            else:
                raise TypeError('Your maximal power should be an int, '
                                'a float or a list.')

    def add_power_consumption_total_minimum(self, min_p, time,
                                            cst_operated_unit_list=None):
        """
        To create the constraint of a minimum of power consumption
        considering all the units.

        :param min_p: Minimum of the power consumption. May be an int,
            float or a list with the size of the period study
        :param time: period of the study
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        final_operated_unit_list = self._check_operated_unit_list(
            cst_operated_unit_list)

        consumption_name_string = ''
        for consumption_unit in final_operated_unit_list:
            consumption_name_string += '_{}'.format(
                consumption_unit.name)

        consumption_p_string = ''
        for consumption_unit in final_operated_unit_list[:-1]:
            consumption_p_string += '{}_p[t] + '.format(consumption_unit.name)
        consumption_p_string += '{}_p[t]'.format(
            final_operated_unit_list[-1].name)

        cst_name = 'min_total_power_conso{}'.format(consumption_name_string)

        if isinstance(min_p, (int, float)):
            exp = '{0} >= {1}'.format(consumption_p_string, min_p)
            setattr(self, cst_name, ActorConstraint(exp=exp,
                                                    name=cst_name,
                                                    parent=self))
        elif isinstance(min_p, list):
            if len(min_p) != time.LEN:
                raise IndexError(
                    "Your minimal power should be the size of the time "
                    "period : {} but equals {}.".format(time.LEN,
                                                        len(min_p)))
            else:
                exp_t = '{0} >= {1}[t]'.format(consumption_p_string, min_p)
                setattr(self, cst_name, ActorDynamicConstraint(exp_t=exp_t,
                                                               name=cst_name,
                                                               t_range='for '
                                                                       't in '
                                                                       'time.I',
                                                               parent=self))
        else:
            raise TypeError('Your minimal power should be an int, '
                            'a float or a list.')

    def add_power_consumption_total_maximum(self, max_p, time,
                                            cst_operated_unit_list=None):
        """
        To create the actor constraint of a maximum of power consumption.

        :param max_p: Minimum of the power consumption. May be an int,
            float or a list with the size of the period study
        :param time: period of the study
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        final_operated_unit_list = self._check_operated_unit_list(
            cst_operated_unit_list)

        consumption_name_string = ''
        for consumption_unit in final_operated_unit_list:
            consumption_name_string += '_{}'.format(
                consumption_unit.name)

        consumption_p_string = ''
        for consumption_unit in final_operated_unit_list[:-1]:
            consumption_p_string += '{}_p[t] + '.format(consumption_unit.name)
        consumption_p_string += '{}_p[t]'.format(
            final_operated_unit_list[-1].name)

        cst_name = 'max_total_power_conso{}'.format(consumption_name_string)

        if isinstance(max_p, (int, float)):
            exp = '{0} <= {1}'.format(consumption_p_string, max_p)
            setattr(self, cst_name, ActorConstraint(exp=exp,
                                                    name=cst_name,
                                                    parent=self))

        elif isinstance(max_p, list):
            if len(max_p) != time.LEN:
                raise IndexError(
                    "Your maximal power should be the size of the time "
                    "period : {} but equals {}.".format(time.LEN,
                                                        len(max_p)))
            else:
                exp_t = '{0} <= {1}[t]'.format(consumption_p_string, max_p)
                setattr(self, cst_name, ActorDynamicConstraint(exp_t=exp_t,
                                                               name=cst_name,
                                                               t_range='for '
                                                                       't in '
                                                                       'time.I',
                                                               parent=self))
        else:
            raise TypeError('Your maximal power should be an int, '
                            'a float or a list.')
