#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module describes the Producer actor**

 Few objectives and constraints are available.

 Objectives :
    - maximize_production
    - minimize_production
    - minimize_time_of_use
    - minimize_co2_emissions
    - minimize_costs
    - minimize_operating_cost
    - minimize_starting_cost

 Constraints :
    - energy_production_minimum
    - energy_production_maximum
    - power_production_minimum
    - power_production_maximum

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

from ..operator_actors.operator_actors import OperatorActor
from ...general.optimisation.elements import *
from ...energy.units.production_units import ProductionUnit
from ...energy.energy_nodes import EnergyNode

__docformat__ = "restructuredtext en"


class Producer(OperatorActor):
    """
    **Description**

        Producer class inherits from the the class OperatorActor. It enables
        one to model an energy producer actor.
    """

    def __init__(self, name, operated_unit_list, operated_node_list=None,
                 verbose=True):
        OperatorActor.__init__(self, name=name,
                               operated_unit_type_tuple=(ProductionUnit,
                                                         EnergyNode),
                               operated_unit_list=operated_unit_list,
                               operated_node_list=operated_node_list,
                               verbose=verbose)

    # OBJECTIVES #
    # Energy objectives
    def maximize_production(self, obj_operated_unit_list=None, weight=1,
                            pareto=False):
        """
        To create the objective in order to maximize the production of the
        producer's units (all or part of them).

        :param obj_operated_unit_list: List of units on which the
            objective will be applied. Might be empty.
        :param weight: Weight coefficient for the objective
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            if isinstance(operated_unit, ProductionUnit):
                operated_unit.maximize_production(weight=weight,
                                                  pareto=pareto)

    def minimize_production(self, obj_operated_unit_list=None, weight=1,
                            pareto=False):
        """
        To create the objective in order to minimize the production of the
        producer's units (all or part of them).

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

    def minimize_time_of_use(self, obj_operated_unit_list=None, weight=1,
                             pareto=False):
        """
        To create the objective in order to minimize the time of use of the
        producer's units (all or part of them).

        :param obj_operated_unit_list: List of units on which the
            objective will be applied. Might be empty.
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            operated_unit.minimize_time_of_use(weight=weight,
                                               pareto=pareto)

    # CO2 objectives
    def minimize_co2_emissions(self, obj_operated_unit_list=None, weight=1,
                               pareto=False):
        """
        To create the objective in order to minimize the co2 emissions of the
        producer's units (all or part of them).
        based on the quantity "co2_emission"

        :param obj_operated_unit_list: list of the operated energy units on
            which the objective will be applied
        :param weight: weight of the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            if isinstance(operated_unit, ProductionUnit):
                operated_unit.minimize_co2_emissions(weight=weight,
                                                     pareto=pareto)

    # Economic objectives
    def minimize_costs(self, obj_operated_unit_list=None, weight=1,
                       pareto=False):
        """
        To create the objective in order to minimize the cost of the
        producer's units (all or part of them).

        :param obj_operated_unit_list: list of the operated energy units on
            which the objective will be applied
        :param weight: weight of the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            operated_unit.minimize_costs(weight=weight, pareto=pareto)

    def minimize_operating_cost(self, obj_operated_unit_list=None, weight=1,
                                pareto=False):
        """
        To create the objective in order to minimize the operating costs of the
        producer's units (all or part of them).

        :param obj_operated_unit_list: list of the operated energy units on
            which the objective will be applied
        :param weight: weight of the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            operated_unit.minimize_operating_cost(weight=weight, pareto=pareto)

    def minimize_starting_cost(self, obj_operated_unit_list=None, weight=1,
                               pareto=False):
        """
        To create the objective in order to minimize the starting costs of the
        producer's units (all or part of them).

        :param obj_operated_unit_list: list of the operated energy units on
            which the objective will be applied
        :param weight: weight of the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        final_operated_unit_list = self._check_operated_unit_list(
            obj_operated_unit_list)
        for operated_unit in final_operated_unit_list:
            operated_unit.minimize_starting_cost(weight=weight, pareto=pareto)

    # CONSTRAINTS #
    # Energy constraints
    def add_energy_production_minimum(self, min_e_tot,
                                      cst_operated_unit_list=None):
        """
        To create the actor constraint of a minimum of energy production.

        :param min_e_tot: Minimum of the total energy production over the
            period of the study
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        if isinstance(min_e_tot, (int, float)):
            final_operated_unit_list = self._check_operated_unit_list(
                cst_operated_unit_list)

            production_name_string = ''
            for production_unit in final_operated_unit_list:
                production_name_string += '_{}'.format(
                    production_unit.name)

                production_p_string = ''
            for production_unit in final_operated_unit_list[:-1]:
                production_p_string += '{}_p[t] + '.format(
                    production_unit.name)
            production_p_string += '{}_p[t]'.format(
                final_operated_unit_list[-1].name)

            cst_name = 'min_energy_prod{}'.format(production_name_string)
            exp = 'lpSum({0} for t in time.I) >= {1}'.format(
                production_p_string, min_e_tot)

            setattr(self, cst_name, ActorConstraint(exp=exp,
                                                    name=cst_name,
                                                    parent=self))

        else:
            raise TypeError('min_e_tot in energy_production_minimum should be '
                            'an int or a float')

    def add_energy_production_maximum(self, max_e_tot,
                                      cst_operated_unit_list=None):
        """
        To create the actor constraint of a maximum of energy production.

        :param max_e_tot: Maximum of the total energy production over the
            period of the study
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        if isinstance(max_e_tot, (int, float)):
            final_operated_unit_list = self._check_operated_unit_list(
                cst_operated_unit_list)

            production_name_string = ''
            for production_unit in final_operated_unit_list:
                production_name_string += '_{}'.format(
                    production_unit.name)

            production_p_string = ''
            for production_unit in final_operated_unit_list[:-1]:
                production_p_string += '{}_p[t] + '.format(
                    production_unit.name)
            production_p_string += '{}_p[t] '.format(
                final_operated_unit_list[-1].name)

            cst_name = 'max_energy_prod{}'.format(production_name_string)
            exp = 'lpSum({0} for t in time.I) <= {1}'.format(
                production_p_string, max_e_tot)

            setattr(self, cst_name, ActorConstraint(exp=exp,
                                                    name=cst_name,
                                                    parent=self))

        else:
            raise TypeError('max_e_tot in energy_production_maximum should be '
                            'an int or a float')

    def add_power_production_by_unit_minimum(self, min_p, time,
                                             cst_operated_unit_list=None):
        """
        To create the actor constraint of a minimum of power production
        for each unit.

        :param min_p: Minimum of the power production. May be an int,
            float or a list with the size of the period study
        :param time: period of the study
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        final_operated_unit_list = self._check_operated_unit_list(
            cst_operated_unit_list)

        for production_unit in final_operated_unit_list:

            cst_name = 'min_by_unit_power_prod_{}'.format(
                production_unit.name)

            if isinstance(min_p, (int, float)):
                exp_t = '{0}_p[t] >= {1}'.format(
                    production_unit.name,
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
                    exp_t = '{0}_p[t] >= {1}[t]'.format(production_unit.name,
                                                        min_p)
                    setattr(self, cst_name, ActorDynamicConstraint(
                        exp_t=exp_t, name=cst_name, parent=self))
            else:
                raise TypeError('Your minimal power should be an int, '
                                'a float or a list.')

    def add_power_production_by_unit_maximum(self, max_p, time,
                                             cst_operated_unit_list=None):
        """
        To create the actor constraint of a maximum of power production
        for each unit.

        :param max_p: Maximum of the power production. May be an int,
            float or a list with the size of the period study
        :param time: period of the study
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        final_operated_unit_list = self._check_operated_unit_list(
            cst_operated_unit_list)

        for production_unit in final_operated_unit_list:

            cst_name = 'max_by_unit_power_prod_{}'.format(
                production_unit.name)

            if isinstance(max_p, (int, float)):
                exp_t = '{0}_p[t] <= {1}'.format(
                    production_unit.name,
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
                    exp_t = '{0}_p[t] <= {1}[t]'.format(production_unit.name,
                                                        max_p)
                    setattr(self, cst_name, ActorDynamicConstraint(
                        exp_t=exp_t, name=cst_name, parent=self))
            else:
                raise TypeError('Your maximal power should be an int, '
                                'a float or a list.')

    def add_power_production_total_minimum(self, min_p, time,
                                           cst_operated_unit_list=None):
        """
        To create the constraint of a minimum of power production
        considering all the units.

        :param min_p: Minimum of the power production. May be an int,
            float or a list with the size of the period study
        :param time: period of the study
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        final_operated_unit_list = self._check_operated_unit_list(
            cst_operated_unit_list)

        production_name_string = ''
        for production_unit in final_operated_unit_list:
            production_name_string += '_{}'.format(
                production_unit.name)

        production_p_string = ''
        for production_unit in final_operated_unit_list[:-1]:
            production_p_string += '{}_p[t] + '.format(production_unit.name)
        production_p_string += '{}_p[t]'.format(
            final_operated_unit_list[-1].name)

        cst_name = 'min_total_power_prod{}'.format(production_name_string)

        if isinstance(min_p, (int, float)):
            exp = '{0} >= {1}'.format(production_p_string, min_p)
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
                exp_t = '{0} >= {1}[t]'.format(production_p_string, min_p)
                setattr(self, cst_name, ActorDynamicConstraint(exp_t=exp_t,
                                                               name=cst_name,
                                                               t_range='for '
                                                                       't in '
                                                                       'time.I',
                                                               parent=self))
        else:
            raise TypeError('Your minimal power should be an int, '
                            'a float or a list.')

    def add_power_production_total_maximum(self, max_p, time,
                                           cst_operated_unit_list=None):
        """
        To create the actor constraint of a maximum of power production.

        :param max_p: Minimum of the power production. May be an int,
            float or a list with the size of the period study
        :param time: period of the study
        :param cst_operated_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        final_operated_unit_list = self._check_operated_unit_list(
            cst_operated_unit_list)

        production_name_string = ''
        for production_unit in final_operated_unit_list:
            production_name_string += '_{}'.format(
                production_unit.name)

        production_p_string = ''
        for production_unit in final_operated_unit_list[:-1]:
            production_p_string += '{}_p[t] + '.format(production_unit.name)
        production_p_string += '{}_p[t]'.format(
            final_operated_unit_list[-1].name)

        cst_name = 'max_total_power_prod{}'.format(production_name_string)

        if isinstance(max_p, (int, float)):
            exp = '{0} <= {1}'.format(production_p_string, max_p)
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
                exp_t = '{0} <= {1}[t]'.format(production_p_string, max_p)
                setattr(self, cst_name, ActorDynamicConstraint(exp_t=exp_t,
                                                               name=cst_name,
                                                               t_range='for '
                                                                       't in '
                                                                       'time.I',
                                                               parent=self))
        else:
            raise TypeError('Your maximal power should be an int, '
                            'a float or a list.')

    def add_temporary_stop(self, time, start='YYYY-MM-DD HH:MM:SS',
                           end='YYYY-MM-DD HH:MM:SS',
                           period_index=None,
                           cst_production_unit_list=None):
        """
        To create the actor constraint giving the possibility to stop the
        production during a period.

        :param start: start of the stop period
        :param end: end of the stop period
        :param period_index: period index for the stop period, to use
            instead of start and end
        :param cst_production_unit_list: List of units on which the constraint
            will be applied. Might be empty.

        """
        final_production_unit_list = self._check_operated_unit_list(
            cst_production_unit_list)

        production_name_string = ''
        for production_unit in final_production_unit_list:
            production_name_string += '_{}'.format(
                production_unit.name)

        production_p_string = ''
        for production_unit in final_production_unit_list[:-1]:
            production_p_string += '{}_p[t] + '.format(production_unit.name)
        production_p_string += '{}_p[t]'.format(
            final_production_unit_list[-1].name)

        if period_index is None:
            if start == 'YYYY-MM-DD HH:MM:SS':
                index_start = ''
            else:
                index_start = time.get_index_for_date(start)

            if end == 'YYYY-MM-DD HH:MM:SS':
                index_end = ''
            else:
                index_end = time.get_index_for_date(end)

            period_index = 'time.I[{start}:{end}]'.format(start=index_start,
                                                          end=index_end)

        exp_t = '{} == 0'.format(production_p_string)
        cst_name = 'stop_constraint'
        t_range = 'for t in {}'.format(period_index)
        setattr(self, cst_name, ActorDynamicConstraint(exp_t=exp_t,
                                                       name=cst_name,
                                                       t_range=t_range,
                                                       parent=self))

    def power_consumption_minimum(self, min_p, time,
                                  cst_operated_unit_list=None):
        """
            +++++++++++++++++++++++++++++++++++++++++++++++++++
                        **DEPRECATED: please use**
                   **add_power_production_total_minimum or**
             **add_power_production_by_units_minimum instead**
            ++++++++++++++++++++++++++++++++++++++++++++++++++++


        To create the actor constraint of a minimum of power consumption.

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

        cst_name = 'min_power_conso{}'.format(consumption_name_string)

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

    def power_consumption_maximum(self, max_p, time,
                                  cst_operated_unit_list=None):
        """
            +++++++++++++++++++++++++++++++++++++++++++++++++++
                        **DEPRECATED: please use**
                   **add_power_production_total_maximum or**
             **add_power_production_by_units_maximum instead**
            ++++++++++++++++++++++++++++++++++++++++++++++++++++
        To create the actor constraint of a maximum of power consumption.

        :param max_p: Maximum of the power consumption. May be an int,
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

        cst_name = 'max_power_conso{}'.format(consumption_name_string)

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
