#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module defines the energy units of OMEGAlpes. The production,
consumption and storage unit will inherit from it.**

 The energy_units module defines the basic attributes and methods of an
 energy unit in OMEGAlpes.

 The class EnergyUnit includes the following attributes and quantities:
    * time: instance of TimeUnit describing the studied time period.
    * energy_type: energy type of the energy unit (see energy.energy_types)
    * p: instantaneous power of the energy unit (kW)
    * e_tot: total energy either consumed or produced by the energy unit on the studied time period during the time period (kWh)
    * u: binary describing if the unit is operating (1) or not (0) at t \
    (i.e. delivering or consuming power)
    * poles: energy poles of the energy unit (see energy.io.poles)

EnergyUnit parameters can be used to add energy constraints or new attributes
calculation to the energy unit, such as e_max or starting_cost.

 This module also includes the classes:
    * FixedEnergyUnit: energy unit with a fixed power profile
    * VariableEnergyUnit: energy unit with a variable power profile
    * SquareEnergyUnit: energy unit with a defined square power profile,\
 inheriting from VariableEnergyUnit.
    * ShiftableEnergyUnit: energy unit with a power profile that can be time\
 shifted, inheriting from VariableEnergyUnit.

    * TriangleEnergyUnit: energy unit with a defined triangular power profile,\
    inheriting from VariableEnergyUnit.

    * SawtoothEnergyUnit: energy unit with a defined sawtooth power profile,\
    inheriting from VariableEnergyUnit.

    * SeveralEnergyUnit: Energy unit based on a fixed power curve enabling to\
    multiply several times (nb_unit) the same power curve.

    * AssemblyUnit: an assembly unit has at least a production unit and a\
    consumption unit and is using one or several energy types. It can also\
    integrate reversible energy units. It inherits from OptObject and it is the\
    parent class of ConversionUnit and ReversibleUnit.

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

import warnings

import numpy as np
import pandas as pd
from pulp import LpBinary, LpInteger, LpContinuous

from ..io.poles import Epole
from ...general.optimisation.core import OptObject
from ...general.optimisation.elements import *

__docformat__ = "restructuredtext en"


class EnergyUnit(OptObject):
    """
        **Description**

        Module dedicated to the parent class (EnergyUnit) of :

         - production units
         - consumption units
         - storage units
    """

    def __init__(self, time, name, flow_direction='in', p=None, p_min=0,
                 p_max=1e+4, e_min=None, e_max=None, starting_cost=None,
                 operating_cost=None, min_time_on=None, min_time_off=None,
                 max_ramp_up=None, max_ramp_down=None, co2_out=None,
                 availability_hours=None, energy_type=None,
                 no_warn=True, verbose=True):
        """
        :param time: TimeUnit for the studied time period
        :type time: TimeUnit
        :param name: name of the EnergyUnit
        :type name: str
        :param flow_direction: direction of the energy flow for this unit.
        'in' for consumption, 'out' for production.
        :param p: power of the energy unit (kW).
        :param p_min: minimum power value of the operating energy unit (kW).
        :param p_max: maximum power value of the operating energy unit (kW).
        :param e_min: if not None, constrains the minimum energy value
        consumed or produced by the energy unit over the studied time period
        (kWh).
        :param e_max: if not None, constrains the maximum energy value consumed
         or produced by the energy unit over the studied time period (kWh)
        :param starting_cost: if not None, adds a starting cost for the
        energy unit (€/start).
        :param operating_cost: if not None, adds an operating cost for the
        energy unit (€/kWh)
        :param min_time_on: if not None, constrains the minimum time the
        energy unit must be operating.
        :param min_time_off: if not None, constrains the minimum time the
        unit must be out of operation.
        :param max_ramp_up: if not None, constrains the maximum power ramp up
        the energy unit can operate with between two consecutive time step
        (kW). Beware the time step value !
        :param max_ramp_down: if not None, constrains the maximum power ramp
        down the energy unit can operate with between two consecutive time step
        (kW). Beware the time step value !
        :param co2_out: if not None, adds CO2 emissions value depending on
        the energy consumption - production (kg_eq_CO2/kWh).
        :param availability_hours: if not None, constrains the availability
        time of the energy unit (hours), i.e. the number of hours the energy
        unit can operate during the studied time period.
        :param energy_type: energy type of the energy unit.
        :param no_warn:
        :param verbose: if True, print a message for the energy unit
        creation in the prompt.
        :type verbose: bool
        """

        OptObject.__init__(self, name=name, description='Energy unit',
                           verbose=verbose)

        self.parent = None
        self.time = time  # Time unit
        self.energy_type = energy_type
        self._p_min = p_min

        # p and e_tot lower and upper bounds calculation
        if isinstance(p_max, (int, float)):
            max_e = p_max * time.DT * time.LEN  # p_max * number of hours
            p_ub = p_max
        elif isinstance(p_max, list):
            max_e = sum(p_max)
            p_ub = [max(0, p) for p in p_max]  # Could be 0 when turn off
        else:
            raise TypeError('The parameter p_max should be either an '
                            'integer, a float or a list but '
                            'is {0}'.format(type(p_max)))
        if isinstance(p_min, (int, float)):
            p_lb = min(0, p_min)  # Could be 0 when turn off
            min_e = p_lb * time.DT * time.LEN  # min(p_min,0) times the
            # number of hours. p_min can be below 0 for storage units.

        elif isinstance(p_min, list):
            p_lb = [min(0, p) for p in p_min]  # Could be 0 when turn off,
            # and below 0 for storage units.
            min_e = sum(p_lb)

        else:
            raise TypeError('The parameter p_min should be either an '
                            'integer, a float or a list but '
                            'is {0}'.format(type(p_min)))
        # Attributes
        self.p = Quantity(name='p',
                          description='instantaneous power of the energy unit',
                          value=p, lb=p_lb, ub=p_ub, vlen=time.LEN, unit='kW',
                          parent=self)

        self.e_tot = Quantity(name='e_tot',
                              description='total energy during the time '
                                          'period', lb=min_e, ub=max_e, vlen=1,
                              unit='kWh', parent=self)

        self.calc_e_tot = DefinitionConstraint(name='calc_e_tot', parent=self,
                                               exp='{0}_e_tot == time.DT * '
                                                   'lpSum({0}_p[t] for t in '
                                                   'time.I)'
                                               .format(self.name))

        # Defining the operating variable "u"

        if isinstance(self, VariableEnergyUnit):
            self.u = Quantity(name='u',
                              description='indicates if the unit is operating '
                                          'at t',
                              vtype=LpBinary, vlen=time.LEN, parent=self)

            if isinstance(p_max, (int, float)):
                self.on_off_max = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t] <= {0}_u[t] * {p_M}'.format(self.name,
                                                                p_M=p_max),
                    t_range='for t in time.I', name='on_off_max', parent=self)
            elif isinstance(p_max, list):
                self.on_off_max = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t] <= {0}_u[t] * {p_M}[t]'.format(self.name,
                                                                   p_M=p_max),
                    t_range='for t in time.I', name='on_off_max', parent=self)

            ## WARNING : note that if pmin=0, there is no constraint that imposes u=0 when p=0.
            ## This is in most cases useless. The only current exception is when a min_time_on constraint is added
            ## (see the corresponding function).
            if isinstance(p_min, (int, float)):
                self.on_off_min = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t] >= {0}_u[t] * {p_m}'.format(self.name,
                                                                p_m=p_min),
                    t_range='for t in time.I', name='on_off_min',
                    parent=self)
            elif isinstance(p_min, list):
                self.on_off_min = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t] >= {0}_u[t] * {p_m}[t]'.format(self.name,
                                                                   p_m=p_min),
                    t_range='for t in time.I', name='on_off_min',
                    parent=self)

        # Poles of the energy unit
        self.poles = {1: Epole(self.p, flow_direction, energy_type)}

        self._add_opt_parameters(starting_cost, operating_cost, co2_out)
        self._add_tech_constraints(min_time_on, min_time_off, max_ramp_up,
                                   max_ramp_down, e_min, e_max)
        self._add_actor_constraints(availability_hours)

    def _set_optobject_as_attr(self, optobject: OptObject,
                               attribute_name=None):
        if isinstance(optobject, OptObject):
            if attribute_name:
                self.__setattr__(attribute_name, optobject)
            else:
                self.__setattr__(optobject.name, optobject)

        else:
            raise TypeError('In the _set_optobject_as_attr method, '
                            'the object should '
                            'be an OptObject class and {0} is a '
                            '{1}'.format(optobject, type(optobject)))

    # Optional parameters
    def _add_opt_parameters(self, starting_cost, operating_cost, co2_out):
        self.start_up = None
        self.switch_off = None
        self.starting_cost = None
        self.operating_cost = None
        self.co2_emissions = None

        # Starting cost
        if starting_cost is not None:
            self._add_starting_cost(starting_cost)

        # Operating cost
        if operating_cost is not None:
            self._add_operating_cost(operating_cost)

        # CO2 emissions
        if co2_out is not None:
            self._add_co2_emissions(co2_out)

    def _add_start_up(self):
        time = self.time
        # Add a variable for start up
        self.start_up = Quantity(name='start_up',
                                 description='The EnergyUnit is '
                                             'starting :1 or not :0',
                                 vtype=LpBinary, vlen=time.LEN, parent=self)

        # When u[t] = 0 and u[t+1] = 1, start_up[t+1] = 1
        self.def_start_up = DefinitionDynamicConstraint(
            exp_t='{0}_u[t+1] - {0}_u[t] <= '
                  '{0}_start_up[t+1]'.format(self.name),
            t_range='for t in time.I[:-1]', name='def_start_up', parent=self)

        # Else start_up[t+1] = 0
        self.def_no_start_up = DefinitionDynamicConstraint(
            exp_t='{0}_start_up[t+1] <= ({0}_u[t+1] - {0}_u[t]'
                  ' + 1)/2'.format(self.name),
            t_range='for t in time.I[:-1]',
            name='def_no_start_up', parent=self)

        # Def initial start_up
        self.def_init_start_up = DefinitionConstraint(
            exp='{0}_start_up[0] == {0}_u[0]'.format(self.name),
            name='def_init_start_up', parent=self)

    def _add_switch_off(self):
        time = self.time
        if self.start_up is None:
            self._add_start_up()

        # Add a variable for switch off
        self.switch_off = Quantity(name='switch_off',
                                   description='The EnergyUnit is '
                                               'switching off :1 or not :0',
                                   vtype=LpBinary, vlen=time.LEN,
                                   parent=self)

        # When u[t} = 1 and u[t+1] = 0, switch_off[t+1] = 0
        self.def_switch_off = DefinitionDynamicConstraint(
            exp_t='{0}_switch_off[t+1] == {0}_start_up[t+1] '
                  '+ {0}_u[t] - {0}_u[t+1]'.format(self.name),
            t_range='for t in time.I[:-1]',
            name='def_switch_off', parent=self)

        # Set initial switch_off to 0
        self.def_init_switch_off = DefinitionConstraint(
            exp='{0}_switch_off[0] == 0'.format(self.name),
            name='def_init_switch_off', parent=self)

    def _add_starting_cost(self, start_cost: float):
        """
        Add a starting cost associated to the energy unit based on the value
        start_cost.
        Each time the energy unit is starting (or restarting)

            i.e. not functioning time t and functioning time t+1
            ( When start_up[t+1] = 1 corresponding to u[t] = 0 and u[t+1] = 1)

        the start_cost value is added to the starting_costs.

        :param start_cost: float: cost corresponding to the start-up of the
            energy unit
        """
        if self.starting_cost is None:
            if self.start_up is None:
                self._add_start_up()

            # Adding starting cost
            self.starting_cost = Quantity(name='starting_cost',
                                          description='Dynamic cost for the '
                                                      'start'
                                                      ' of EnergyUnit',
                                          lb=0, vlen=self.time.LEN,
                                          parent=self)

            # Defining how the starting cost is calculated
            self.calc_start_cost = DefinitionDynamicConstraint(
                exp_t='{0}_starting_cost[t] == {1} * {0}_start_up[t]'.format(
                    self.name, start_cost),
                t_range='for t in time.I[:-1]', name='calc_start_cost',
                parent=self)

        else:
            raise ValueError("The EnergyUnit {} already has a "
                             "starting cost defined.".format(self.name))

    def _add_operating_cost(self, operating_cost: float):
        """
        Add an operating cost associated to the energy unit based on the value
        operating_cost.
        For each time step the energy unit is running the operating_cost
        value is multiplied by the power production or consumption, balanced
        depending on the time step value and added to the operating_costs.

        :param operating_cost: float: cost corresponding operation of the
            energy unit. To be multiplied by the power at each time step and
            balanced depending on the time step value.
        """
        if self.operating_cost is None:
            # Adding operating cost
            self.operating_cost = Quantity(name='operating_cost',
                                           description='Dynamic cost for the '
                                                       'operation '
                                                       'of the EnergyUnit',
                                           lb=0,
                                           vlen=self.time.LEN, parent=self)

            if isinstance(operating_cost, (int, float)):
                self.calc_operating_cost = DefinitionDynamicConstraint(
                    name='calc_operating_cost',
                    exp_t='{0}_operating_cost[t] == {1} * '
                          '{0}_p[t] * time.DT'.format(self.name,
                                                      operating_cost),
                    t_range='for t in time.I', parent=self)

            elif isinstance(operating_cost, list):
                if len(operating_cost) != self.time.LEN:
                    raise IndexError(
                        "Your operating cost should be the size of the time "
                        "period. The time period is of {0} and your operating "
                        "cost have a size of {1}".format(self.time.LEN,
                                                         len(operating_cost)))
                else:
                    self.calc_operating_cost = DefinitionDynamicConstraint(
                        name='calc_operating_cost',
                        exp_t='{0}_operating_cost[t] == {1}[t] * '
                              '{0}_p[t] * time.DT'.format(self.name,
                                                          operating_cost),
                        t_range='for t in time.I', parent=self)
            else:
                raise TypeError('The operating_cost should be an int, a float '
                                'or a list.')
        else:
            raise ValueError("The EnergyUnit {} already has an "
                             "operating cost defined.".format(self.name))

    def _add_co2_emissions(self, co2_out: float):
        """
        Add an CO2 emissions associated to the energy unit based on the value
        co2_out.
        For each time step the energy unit is running the co2_out
        value is multiplied by the power production or consumption and
        added to the co2_emissions of the energy unit.

        :param co2_out: float: co2 emissions corresponding to the operation
            of the energy unit. To be multiplied by the power at each
            time step
        """
        if self.co2_emissions is None:
            # Adding CO2 emissions from production/consumption
            self.co2_emissions = Quantity(
                name='co2_emissions', description='Dynamic CO2 emissions '
                                                  'generated by the '
                                                  'EnergyUnit', lb=0,
                vlen=self.time.LEN, parent=self)

            if isinstance(co2_out, (int, float)):
                self.calc_co2_emissions = DefinitionDynamicConstraint(
                    exp_t='{0}_co2_emissions[t] == {1} * '
                          '{0}_p[t] * time.DT'.format(self.name, co2_out),
                    name='calc_co2_emissions', parent=self)
            elif isinstance(co2_out, list):
                if len(co2_out) != self.time.LEN:
                    raise IndexError(
                        "Your CO2 emissions (CO2_out) should be the size of "
                        "the time period. The time period is of {0} and your "
                        "CO2 emissions have a size of {1}".format(
                            self.time.LEN,
                            len(co2_out)))
                else:
                    self.calc_co2_emissions = DefinitionDynamicConstraint(
                        exp_t='{0}_co2_emissions[t] == {1}[t] * '
                              '{0}_p[t] * time.DT'.format(self.name, co2_out),
                        name='calc_co2_emissions', parent=self)
            else:
                raise TypeError('co2_out should be an int, a float or a list.')
        else:
            raise ValueError("The EnergyUnit {} already has CO2 "
                             "emissions defined.".format(self.name))

    # Technical constraints
    def _add_tech_constraints(self, min_time_on, min_time_off, max_ramp_up,
                              max_ramp_down, e_min, e_max):
        self.set_max_ramp_up = None
        self.set_max_ramp_down = None
        self.set_min_up_time = None
        self.set_min_down_time = None
        self.set_e_min = None
        self.set_e_max = None

        # Adding a maximal ramp up
        if max_ramp_up is not None:
            self._add_max_ramp_up(max_ramp_up)

        # Adding a maximal ramp down
        if max_ramp_down is not None:
            self._add_max_ramp_down(max_ramp_down)

        # Adding a minimum time on
        if min_time_on is not None:
            self._add_min_time_on(min_time_on)

        # Adding a minimum time off
        if min_time_off is not None:
            self._add_min_time_off(min_time_off)

        if e_min is not None:
            self._add_e_min(e_min)

        if e_max is not None:
            self._add_e_max(e_max)

    def _add_max_ramp_up(self, max_ramp_up: float):
        """
        Add a maximal ramp value between two consecutive power values
        increase

        :param max_ramp_up: float: maximal ramp value between two consecutive
            power values increase
        """
        if self.set_max_ramp_up is None:
            self.set_max_ramp_up = TechnicalDynamicConstraint(
                exp_t='{0}_p[t+1] - {0}_p[t] <= {1}'.format(self.name,
                                                            max_ramp_up),
                t_range='for t in time.I[:-1]', name='set_max_ramp_up',
                parent=self)
        else:
            raise ValueError("The EnergyUnit {} already has a maximal "
                             "ramp up defined.".format(self.name))

    def _add_max_ramp_down(self, max_ramp_down: float):
        """
        Add a maximal ramp value between two consecutive power values
        decreasing

        :param max_ramp_down: float: maximal ramp value between two consecutive
            power values decreasing
        """
        if self.set_max_ramp_down is None:
            self.set_max_ramp_down = TechnicalDynamicConstraint(
                exp_t='{0}_p[t] - {0}_p[t+1] <= {1}'.format(self.name,
                                                            max_ramp_down),
                t_range='for t in time.I[:-1]', name='set_max_ramp_down',
                parent=self)
        else:
            raise ValueError("The EnergyUnit {} already has a maximal "
                             "ramp down".format(self.name))

    def _add_min_time_on(self, min_time_on: float):
        """
        Add a minimal time during which the energy unit should function once
        it is started-up

        :param min_time_on: float: minimal time during which the energy unit
            should function once it is started-up
        """
        if self._p_min == 0:
            self.on_off_min = DefinitionDynamicConstraint(
                exp_t='{0}_p[t] >= {0}_u[t] * {p_m}'.format(self.name,
                                                            p_m=1e-5),
                t_range='for t in time.I', name='on_off_min',
                parent=self)

        if self.set_min_up_time is None:
            if self.start_up is None:
                self._add_start_up()

            # When the unit starts, it should be on during min_time_on
            self.set_min_up_time = TechnicalDynamicConstraint(
                exp_t='{0}_u[t] >= lpSum({0}_start_up[i] for i in range('
                      'max(t - {1} + 1, 0), t))'.format(self.name,
                                                        min_time_on),
                t_range='for t in time.I'.format(min_time_on), name='set_min_up_time', parent=self)
        else:
            raise ValueError("The EnergyUnit {} already has a "
                             "minimum time on.".format(self.name))

    def _add_min_time_off(self, min_time_off: float):
        """
        Add a minimal time during which the energy unit has to remain off
        once it is switched off

        :param min_time_off: float: minimal time during which the energy unit
            has to remain off once it is switched off
        """
        if self.set_min_down_time is None:
            if self.switch_off is None:
                self._add_switch_off()
            # When the unit switches off, it should be off during min_time_off
            self.set_min_down_time = TechnicalDynamicConstraint(
                exp_t='1 - {0}_u[t] >= lpSum({0}_switch_off[i] for i in range('
                      'max(t - {1} + 1, 0), t))'.format(self.name,
                                                        min_time_off),
                t_range='for t in time.I', name='set_min_down_time',
                parent=self)
        else:
            raise ValueError("The EnergyUnit {} already has a "
                             "minimum time down.".format(self.name))

    def _add_e_min(self, e_min: int or float):
        """
        Add a minimum value for the total energy consumed over the studied
        time period
        :param e_min: int or float: minimal value of energy consumed during
        the studied time period (kWh)
        """
        if self.set_e_min is None:
            self.set_e_min = TechnicalConstraint(
                exp='{0}_e_tot >= {1}'.format(self.name, e_min),
                name='set_e_min', parent=self)
        else:
            raise ValueError("The EnergyUnit {} already has an e_min "
                             "constraint defined.".format(self.name))

    def _add_e_max(self, e_max: int or float):
        """
        Add a maximum value for the total energy consumed over the studied
        time period
        :param e_max: int or float: maximal value of energy consumed during
        the studied time period (kWh)
        """
        if self.set_e_max is None:
            self.set_e_max = TechnicalConstraint(
                exp='{0}_e_tot <= {1}'.format(self.name, e_max),
                name='set_e_max', parent=self)
        else:
            raise ValueError("The EnergyUnit {} already has an e_max "
                             "constraint defined.".format(self.name))

    # Actor constraints
    def _add_actor_constraints(self, availability_hours):
        self.set_availability = None

        # Adding a number of available hours of operation
        if availability_hours is not None:
            self._add_availability(availability_hours)

    def _add_availability(self, av_hours: int):
        """
        Add a number of hours of availability of the energy unit during the
        study period

        :param av_hours: int: number of hours of availability of the energy
            unit during the study period
        """
        if self.set_availability is None:
            self.set_availability = ActorConstraint(
                exp='lpSum({dt} * {name}_u[t] for t in time.I) <= '
                    '{av_h}'.format(dt=self.time.DT, name=self.name,
                                    av_h=av_hours),
                name='set_availability', parent=self)
        else:
            raise ValueError("The EnergyUnit {} already has hours of "
                             "availability defined.".format(self.name))

    # Additional constraints, not depending on energy unit parameters
    def add_operating_time_range(self, operating_time_range: [[str, str]]):
        """
        Add a range of hours during which the energy unit can be operated.
        The final time should be greater than the initial time within a time
        range, except when the final time is '00:00'.

        example: add_operating_time_range([['10:00', '12:00'], ['14:00',
        '17:00']])

        :param operating_time_range: list of lists of strings in the format\
        HH:MM [[first hour operating: str, \
            hour to stop (not operating): str], [second hour operating:\
                str, hour to stop (not operating): str], etc]

        NB: the previous version of add_operating_time_range (deprecated
        since version 0.3.1) had integers instead of str hours as
        parameters, do not forget to update it if needed !
        """

        # get the index of each hour for each range

        for time_range in range(len(operating_time_range)):
            (init_h_str, init_min_str) = operating_time_range[
                time_range][0].split(":")
            (final_h_str, final_min_str) = operating_time_range[
                time_range][1].split(":")

            init_h = int(init_h_str)
            init_min = int(init_min_str)
            final_h = int(final_h_str)
            final_min = int(final_min_str)

            start_time = datetime.datetime(year=self.time.get_days[0].year,
                                           month=self.time.get_days[
                                               0].month,
                                           day=self.time.get_days[0].day,
                                           hour=init_h, minute=init_min)
            start_index = self.time.get_index_for_date(date=start_time)

            if final_h != 0 or final_min != 0:
                end_time = datetime.datetime(year=self.time.get_days[0].year,
                                             month=self.time.get_days[0].month,
                                             day=self.time.get_days[0].day,
                                             hour=final_h, minute=final_min)
                end_index = self.time.get_index_for_date(date=end_time)
            else:
                end_index = 24 * 1 / self.time.DT

            operating_time_range[time_range] = [start_index, end_index]
            print('operating time range index {0}: '.format(time_range + 1),
                  operating_time_range[time_range])

        # First non-operating period before the first operating time range
        if operating_time_range[0][0] == 0:
            pass
        else:
            final_time = self.time.get_date_for_index(
                operating_time_range[0][0] - 1)

            set_start_time_range = DailyDynamicConstraint(
                exp_t='{name}_u[t] == 0'.format(name=self.name),
                time=self.time,
                init_time='00:00',
                final_time="{0}:{1}".format(final_time.hour,
                                            final_time.minute),
                name='set_operating_init_time_range_{}'.format(
                    operating_time_range[0][0]), parent=self)
            setattr(self, 'set_start_time_range_{}'.format(
                operating_time_range[0][0]), set_start_time_range)

        # Following non-operating periods between the given time range(s)
        if len(operating_time_range) != 1:
            set_time_range = []
            for i in range(1, len(operating_time_range)):
                init_time = self.time.get_date_for_index(
                    operating_time_range[i - 1][1])
                end_time = self.time.get_date_for_index(
                    operating_time_range[i][0] - 1)

                set_time_range.append(DailyDynamicConstraint(
                    exp_t='{name}_u[t] == 0'.format(name=self.name),
                    time=self.time,
                    init_time="{0}:{1}".format(init_time.hour,
                                               init_time.minute),
                    final_time="{0}:{1}".format(end_time.hour,
                                                end_time.minute),
                    name='set_time_range_{}_{}'.format(
                        operating_time_range[i - 1][1],
                        operating_time_range[i][0]),
                    parent=self))
                setattr(self,
                        'set_time_range_{}_{}'.format(
                            operating_time_range[i - 1][1],
                            operating_time_range[i][0]),
                        set_time_range[i - 1])

        # Last non-operating period after the last operating time range
        if operating_time_range[-1][1] == int(24 * 1 / self.time.DT):
            pass
        else:
            init_time = self.time.get_date_for_index(
                operating_time_range[-1][1])
            end_time = self.time.get_date_for_index(
                int(24 * 1 / self.time.DT - 1))
            set_end_time_range = DailyDynamicConstraint(
                exp_t='{name}_u[t] == 0'.format(name=self.name),
                time=self.time,
                init_time="{0}:{1}".format(init_time.hour, init_time.minute),
                final_time="{0}:{1}".format(end_time.hour, end_time.minute),
                name='set_operating_final_time_range_{}'.format(
                    operating_time_range[-1][1]),
                parent=self)
            setattr(self,
                    'set_end_time_range_{}'.format(operating_time_range[-1][
                                                       1]),
                    set_end_time_range)

    def set_operating_time_range(self, operating_time_range: [[str, str]]):
        """
        DEPRECATED: the name of the function changed to
        add_operating_time_range for code consistency, please use this
        function !

        Add a range of hours during which the energy unit can be operated.
        The final time should be greater than the initial time within a time
        range, except when the final time is '00:00'.

        example: set_operating_time_range([['10:00', '12:00'], ['14:00',
        '17:00']])

        :param operating_time_range: list of lists of strings in the format\
        HH:MM [[first hour operating: str, \
            hour to stop (not operating): str], [second hour operating:\
                str, hour to stop (not operating): str], etc]

        """

        # get the index of each hour for each range

        for time_range in range(len(operating_time_range)):
            (init_h_str, init_min_str) = operating_time_range[
                time_range][0].split(":")
            (final_h_str, final_min_str) = operating_time_range[
                time_range][1].split(":")

            init_h = int(init_h_str)
            init_min = int(init_min_str)
            final_h = int(final_h_str)
            final_min = int(final_min_str)

            start_time = datetime.datetime(year=self.time.get_days[0].year,
                                           month=self.time.get_days[
                                               0].month,
                                           day=self.time.get_days[0].day,
                                           hour=init_h, minute=init_min)
            start_index = self.time.get_index_for_date(date=start_time)

            if final_h != 0 or final_min != 0:
                end_time = datetime.datetime(year=self.time.get_days[0].year,
                                             month=self.time.get_days[0].month,
                                             day=self.time.get_days[0].day,
                                             hour=final_h, minute=final_min)
                end_index = self.time.get_index_for_date(date=end_time)
            else:
                end_index = 24 * 1 / self.time.DT

            operating_time_range[time_range] = [start_index, end_index]
            print('operating time range index {0}: '.format(time_range + 1),
                  operating_time_range[time_range])

        # First non-operating period before the first operating time range
        if operating_time_range[0][0] == 0:
            pass
        else:
            final_time = self.time.get_date_for_index(
                operating_time_range[0][0] - 1)

            set_start_time_range = DailyDynamicConstraint(
                exp_t='{name}_u[t] == 0'.format(name=self.name),
                time=self.time,
                init_time='00:00',
                final_time="{0}:{1}".format(final_time.hour,
                                            final_time.minute),
                name='set_operating_init_time_range_{}'.format(
                    operating_time_range[0][0]), parent=self)
            setattr(self, 'set_start_time_range_{}'.format(
                operating_time_range[0][0]), set_start_time_range)

        # Following non-operating periods between the given time range(s)
        if len(operating_time_range) != 1:
            set_time_range = []
            for i in range(1, len(operating_time_range)):
                init_time = self.time.get_date_for_index(
                    operating_time_range[i - 1][1])
                end_time = self.time.get_date_for_index(
                    operating_time_range[i][0] - 1)

                set_time_range.append(DailyDynamicConstraint(
                    exp_t='{name}_u[t] == 0'.format(name=self.name),
                    time=self.time,
                    init_time="{0}:{1}".format(init_time.hour,
                                               init_time.minute),
                    final_time="{0}:{1}".format(end_time.hour,
                                                end_time.minute),
                    name='set_time_range_{}_{}'.format(
                        operating_time_range[i - 1][1],
                        operating_time_range[i][0]),
                    parent=self))
                setattr(self,
                        'set_time_range_{}_{}'.format(
                            operating_time_range[i - 1][1],
                            operating_time_range[i][0]),
                        set_time_range[i - 1])

        # Last non-operating period after the last operating time range
        if operating_time_range[-1][1] == int(24 * 1 / self.time.DT):
            pass
        else:
            init_time = self.time.get_date_for_index(
                operating_time_range[-1][1])
            end_time = self.time.get_date_for_index(
                int(24 * 1 / self.time.DT - 1))
            set_end_time_range = DailyDynamicConstraint(
                exp_t='{name}_u[t] == 0'.format(name=self.name),
                time=self.time,
                init_time="{0}:{1}".format(init_time.hour, init_time.minute),
                final_time="{0}:{1}".format(end_time.hour, end_time.minute),
                name='set_operating_final_time_range_{}'.format(
                    operating_time_range[-1][1]),
                parent=self)
            setattr(self,
                    'set_end_time_range_{}'.format(operating_time_range[-1][
                                                       1]),
                    set_end_time_range)

    def add_energy_limits_on_time_period(self, e_min=0, e_max=None,
                                         start='YYYY-MM-DD HH:MM:SS',
                                         end='YYYY-MM-DD HH:MM:SS',
                                         period_index=None):
        """
        Add an energy limit during a defined time period

        :param e_min: Minimal energy set during the time period (int or float)
        :param e_max: Maximal energy set during the time period (int or float)
        :param start: Date of start of the time period  YYYY-MM-DD HH:MM:SS (
            str)
        :param end: Date of end of the time period   YYYY-MM-DD HH:MM:SS (str)
        """
        self.set_e_min_period = None
        self.set_e_max_period = None

        if period_index is None:
            if start == 'YYYY-MM-DD HH:MM:SS':
                index_start = ''
            else:
                index_start = self.time.get_index_for_date(start)

            if end == 'YYYY-MM-DD HH:MM:SS':
                index_end = ''
            else:
                index_end = self.time.get_index_for_date(end)

            period_index = 'time.I[{start}:{end}]'.format(start=index_start,
                                                          end=index_end)

        if e_min != 0:
            self.set_e_min_period = TechnicalConstraint(
                exp='time.DT * lpSum({0}_p[t] for t in {1}) '
                    '>= {2}'.format(self.name, period_index, e_min),
                name='set_e_min_period', parent=self)

        if e_max is not None:
             self.set_e_max_period = TechnicalConstraint(
                exp='time.DT * lpSum({0}_p[t] for t in {1}) '
                    '<= {2}'.format(self.name, period_index, e_max),
                name='set_e_max_period', parent=self)

    # OBJECTIVES #
    def minimize_starting_cost(self, weight=1, pareto=False):
        """
        Objective to minimize the starting costs

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        if self.starting_cost is not None:
            self.min_start_cost = Objective(name='min_start_cost',
                                            exp='lpSum({0}_starting_cost[t] '
                                                'for t '
                                                'in time.I)'
                                            .format(self.name), weight=weight,
                                            pareto=pareto,
                                            parent=self)
        else:
            raise ValueError("You should add a starting cost before trying "
                             "to minimize_starting_cost.")

    def minimize_operating_cost(self, weight=1, pareto=False):
        """
        Objective to minimize the operating costs

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        if self.operating_cost is not None:
            self.min_operating_cost = Objective(
                name='min_operating_cost',
                exp='lpSum({}_operating_cost[t] for t in time.I)'.format(
                    self.name),
                weight=weight,
                pareto=pareto,
                parent=self)
        else:
            raise ValueError("You should add an operating cost before trying "
                             "to minimize_operating_cost.")

    def minimize_costs(self, weight=1, pareto=False):
        """
        Objective to minimize the costs (starting and operating costs)

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        if self.starting_cost is not None:
            self.minimize_starting_cost(weight, pareto)

        if self.operating_cost is not None:
            self.minimize_operating_cost(weight, pareto)

    def minimize_energy(self, weight=1, pareto=False):
        """
        Objective to minimize the energy of the energy unit

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        self.min_energy = Objective(name='min_energy',
                                    exp='lpSum({0}_p[t] for t in time.I)'
                                    .format(self.name), weight=weight,
                                    pareto=pareto,
                                    parent=self)

    def minimize_time_of_use(self, weight=1, pareto=False):
        """
        Objective to minimize the time of running of the energy unit

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        self.min_time_of_use = Objective(name='min_time_of_use',
                                         exp='lpSum({0}_u[t] for t in time.I)'
                                         .format(self.name), weight=weight,
                                         pareto=pareto,
                                         parent=self)

    def minimize_co2_emissions(self, weight=1, pareto=False):
        """
        Objective to minimize the co2 emissions of the energy unit

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        self.min_co2_emissions = Objective(name='min_CO2_emissions',
                                           exp='lpSum({0}_co2_emissions[t] '
                                               'for t in time.I)'.format(
                                               self.name),
                                           weight=weight,
                                           pareto=pareto, parent=self)

    def minimize_exergy_destruction(self, weight=1, pareto=False):
        """
        This is the main objective of any exergetic optimization.

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        if hasattr(self, 'exergy_dest'):
            self.min_exergy_dest = Objective(name='min_exergy_destruction',
                                             exp='lpSum({0}_exergy_dest[t] '
                                                 'for t in time.I)'.
                                             format(self.name), weight=weight,
                                             pareto=pareto,
                                             parent=self)
        else:
            raise ValueError("You should initialize exergy calculations "
                             "on the unit named {0} before trying to "
                             "minimize its exergy destruction."
                             .format(self.name))

    def minimize_exergy(self, energy_unit=None, weight=1, pareto=False):
        """ Alternate objective of exergy optimization that may be
        interesting in some cases.

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        if hasattr(self, 'exergy'):
            self.min_exergy = Objective(name='min_exergy',
                                        exp='lpSum({0}_exergy[t] '
                                                 'for t in time.I)'.
                                        format(energy_unit.name),
                                        weight=weight,
                                        pareto=pareto,
                                        parent=energy_unit)
        else:
            raise ValueError("You should initialize exergy calculations "
                             "on the unit named {0} before trying to "
                             "minimize its exergy."
                             .format(energy_unit.name))


class FixedEnergyUnit(EnergyUnit):
    """
    **Description**

        Energy unit with a fixed power profile.

    **Attributes**

        * p : instantaneous power known by advance (kW)
        * energy_type : type of energy ('Electrical', 'Heat', ...)

    """

    def __init__(self, time, name: str, p: list or dict or pd.DataFrame or int or float,
                 flow_direction='in',
                 starting_cost=None, operating_cost=None, co2_out=None,
                 energy_type=None, verbose=True):
        if p is None:
            # FixedEnergyUnits should have data for the power values
            raise TypeError(
                "You have to define the power profile (p) for the "
                "FixedEnergyUnit !")

        # p may be a list, a dict, a dataframe (1 column only), or an int/float. The latter corresponding to a constant value.
        if isinstance(p, list):
            e_tot = sum(p) * time.DT
            p_min = min(p)
            p_max = max(p)

        elif isinstance(p, int) or isinstance(p, float):
            p_min = p
            p_max = p
            p = [p for i in range(len(time.DATES))]
            e_tot = sum(p) * time.DT

        elif isinstance(p, dict):
            # Checking the length of the dictionary corresponds to the length
            #  of the time unit
            if len(time.DATES) == len(p):
                e_tot = sum(p.values()) * time.DT
                p_min = min(p.values())
                p_max = max(p.values())

        elif isinstance(p, pd.DataFrame):
            # Checking the dataframe is composed of only one column :
            # - dates for the indexes
            # - power values for the column
            if len(p.columns) != 1:
                raise ValueError('You should have only one columns for the '
                                 'dataframe of the power values of the '
                                 'FixedEnergyUnit {0} and you have {1} '
                                 'columns'.format(name, len(p.columns)))

            # Checking that the dates of the values correspond to the date of
            #  the study based on the time unit
            if len(time.DATES) == len(p.index):
                for i in range(len(time.DATES)):
                    if not time.DATES[i] == p.index[i]:
                        raise ValueError(
                            'The FixedEnergyUnit {0} does not operate on the '
                            'same time of the model: \n'
                            'dates for the model time: {1} \n'
                            'dates for the power values: {2}'.format(name,
                                                                     time.DATES,
                                                                     p.index))
            else:
                raise ValueError(
                    'The FixedEnergyUnit {0} does not operate on the '
                    'same time of the model: \n'
                    'dates for the model time: {1} \n'
                    'dates for the power values: {2}'.format(name,
                                                             time.DATES,
                                                             p.index))

            # convert the dataframe into a list of power values to
            # calculate e_tot
            label = p.columns.values
            p = p[label[0]].tolist()
            e_tot = sum(p) * time.DT
            p_min = min(p)
            p_max = max(p)

        else:
            raise TypeError(
                "The power profile (p) for the FixedEnergyUnit should be a "
                "list, a dictionary or a dataframe")

        EnergyUnit.__init__(self, time=time, name=name, p=p, p_min=p_min,
                            p_max=p_max, flow_direction=flow_direction,
                            starting_cost=starting_cost,
                            operating_cost=operating_cost, min_time_on=None,
                            min_time_off=None, max_ramp_up=None,
                            max_ramp_down=None, co2_out=co2_out,
                            availability_hours=None, energy_type=energy_type,
                            verbose=verbose, no_warn=True)


class VariableEnergyUnit(EnergyUnit):
    def __init__(self, time, name, flow_direction='in', p_min=0,
                 p_max=1e+4, e_min=None, e_max=None, starting_cost=None,
                 operating_cost=None, min_time_on=None, min_time_off=None,
                 max_ramp_up=None, max_ramp_down=None, co2_out=None,
                 availability_hours=None, energy_type=None,
                 verbose=True, no_warn=True):
        EnergyUnit.__init__(self, time, name, flow_direction=flow_direction,
                            p=None, p_min=p_min, p_max=p_max, e_min=e_min,
                            e_max=e_max, starting_cost=starting_cost,
                            operating_cost=operating_cost,
                            min_time_on=min_time_on,
                            min_time_off=min_time_off, max_ramp_up=max_ramp_up,
                            max_ramp_down=max_ramp_down, co2_out=co2_out,
                            availability_hours=availability_hours,
                            energy_type=energy_type,
                            verbose=verbose, no_warn=no_warn)


class SquareEnergyUnit(VariableEnergyUnit):
    def __init__(self, time, name, p_square, n_square, t_between_sq,
                 t_square=1, flow_direction='in', starting_cost=None,
                 operating_cost=None, co2_out=None, energy_type=None,
                 verbose=True, no_warn=True):
        """

        :param time:
        :param name:
        :param p_square: Power of the square
        :param n_square: Number of squares
        :param t_square: Duration of a square [h]
        :param t_between_sq: Duration between squares [h]
        :param flow_direction:
        :param e_min:
        :param e_max:
        :param starting_cost:
        :param operating_cost:
        :param min_time_on:
        :param min_time_off:
        :param max_ramp_up:
        :param max_ramp_down:
        :param co2_out:
        :param availability_hours:
        :param energy_type:
        """
        if not isinstance(t_square, int):
            raise TypeError('t_sqaure should be an integer, but is '
                            'a {}'.format(type(t_square)))

        energy = n_square * t_square * p_square

        if n_square == 1:
            min_time_on = None
            min_time_off = None
            av_h = t_square
        else:
            min_time_on = t_square
            min_time_off = t_between_sq
            av_h = None

        VariableEnergyUnit.__init__(self, time, name,
                                    flow_direction=flow_direction,
                                    p_min=p_square, p_max=p_square,
                                    e_min=energy,
                                    e_max=energy, starting_cost=starting_cost,
                                    operating_cost=operating_cost,
                                    min_time_on=min_time_on,
                                    min_time_off=min_time_off,
                                    max_ramp_up=None,
                                    max_ramp_down=None, co2_out=co2_out,
                                    availability_hours=av_h,
                                    energy_type=energy_type,
                                    verbose=verbose,
                                    no_warn=no_warn)

class ShiftableEnergyUnit(VariableEnergyUnit):
    """
    **Description**

        EnergyUnit with shiftable power profile.

    **Attributes**

        * power_values : power profile to shift (kW)
        * mandatory : indicates if the power is mandatory (True) or not (False)
        * starting_cost : cost of the starting of the EnergyUnit
        * operating_cost : cost of the operation (€/kW)
        * energy_type : type of energy ('Electrical', 'Heat', ...)

    """

    def __init__(self, time, name: str, flow_direction, power_values: list,
                 mandatory=True, co2_out=None, starting_cost=None,
                 operating_cost=None, energy_type=None,
                 verbose=True):
        # Crop the power profile
        while power_values[0] == 0:
            power_values = power_values[1:]
        while power_values[-1] == 0:
            power_values = power_values[:-1]

        # Works if all values are strictly positives
        epsilon = 0.00001 * min(p > 0 for p in power_values)
        power_profile = [max(epsilon, p) for p in power_values]

        e_max = sum(power_profile) * time.DT

        if mandatory:
            e_min = e_max
        else:
            e_min = 0

        self._e_max_value = e_max
        self._e_min_value = e_min

        p_min = min(power_profile)
        p_max = max(power_profile)

        VariableEnergyUnit.__init__(self, time, name=name,
                                    flow_direction=flow_direction,
                                    p_min=p_min, p_max=p_max, e_min=e_min,
                                    e_max=e_max, starting_cost=starting_cost,
                                    operating_cost=operating_cost,
                                    min_time_on=None, min_time_off=None,
                                    max_ramp_up=None, max_ramp_down=None,
                                    co2_out=co2_out, availability_hours=None,
                                    energy_type=energy_type,
                                    verbose=verbose,
                                    no_warn=True)

        self._add_start_up()
        # self.start_up =  Quantity(name='start_up',
        #                          description='The EnergyUnit is '
        #                                      'starting :1 or not :0',
        #                          vtype=LpBinary, vlen=time.LEN, parent=self)
        S = np.arange(0, time.LEN - len(power_values),1 )
        Slen = len(S)
        
        self.set_one_Startup = TechnicalConstraint(name="onestartup_constraint"  ,\
                                   exp ="lpSum({0}_start_up[t] for \
                                    t in range(0, {1}-{2}, 1) ) == 1".format(self.name,time.LEN,len(power_values)),\
                                        description= "ensures that the profile start \
                                            only once the horizon", parent = self)
        self.set_no_overshoot = TechnicalConstraint(name="no_overshoot_constraint"  ,\
                                   exp ="lpSum({0}_start_up[t] for \
                                    t in range({1}-{2},{1}, 1) ) == 0".format(self.name,time.LEN,len(power_values)),\
                                        description= "ensures that the profile does \
                                            not overshoot the horizon", parent = self)

        self.power_values = Quantity(name='power_values', opt=False,
                                     value=power_values, parent=self)
        
        if mandatory:
            for t in time.I:
                cst_name = 'def_{}_p'.format(t)
                cst_name_u = 'def_{}_u'.format(t)
                rhs_terms = []
                rhs_terms_u = []
                for i, tau in enumerate(S):
                    k = t-tau
                    if 0 <= k and k < len(power_values):
                        rhs_terms.append(f"{self.name}_power_values[{k}] * {self.name}_start_up[{i}]")
                        rhs_terms_u.append(f"{self.name}_start_up[{i}]")
                rhs_str = " + ".join(rhs_terms) if rhs_terms else "0"
                rhs_str_u = " + ".join(rhs_terms_u) if rhs_terms_u else "0"
                exp = f"{self.name}_p[{t}] == ({rhs_str})"
                exp_u = f"{self.name}_u[{t}] == ({rhs_str_u})"
                cst = TechnicalConstraint(name=cst_name,exp=exp,parent= self)
                setattr(self, cst_name, cst)
                cst_u = TechnicalConstraint(name=cst_name_u,exp=exp_u,parent= self)
                setattr(self, cst_name_u, cst_u)
        else:
            for i, _ in enumerate(power_values):
                cst_name = 'def_{}_power_value'.format(i)

                exp_t = "{0}_p[t] >= {0}_power_values[{1}] * " \
                        "{0}_start_up[t-{1}]".format(self.name, i)

                cst = DefinitionDynamicConstraint(name=cst_name, exp_t=exp_t,
                                                t_range="for t in time.I[{}:"
                                                        "-1]".format(i),
                                                parent=self)
                
                setattr(self, cst_name, cst)


class TriangleEnergyUnit(ShiftableEnergyUnit):
    def __init__(self, time, name, flow_direction, p_peak, alpha_peak,
                 t_triangle: list, mandatory=True, starting_cost=None,
                 operating_cost=None, co2_out=None, energy_type=None,
                 verbose=True):

        if not isinstance(t_triangle, int):
            raise TypeError('t_triangle should be an integer, but is '
                            'a {}'.format(type(t_triangle)))

        t_peak = alpha_peak * t_triangle

        if alpha_peak == 0:
            ramp_1 = 0
            ramp_2 = - p_peak / (t_triangle - t_peak)
        elif alpha_peak == 1:
            ramp_1 = p_peak / t_peak
            ramp_2 = 0
        else:
            ramp_1 = p_peak / t_peak
            ramp_2 = - p_peak / (t_triangle - t_peak)

        t = np.arange(0, t_triangle)

        triangle_profile = np.piecewise(
            t, [t <= t_peak - 1, (t_peak - 1 < t) & (t < t_peak), t_peak <= t],
            [lambda t: ramp_1 * (2 * t + 1) / 2,
             lambda t: (ramp_1 * t * (t_peak - t)
                        + ramp_2 * (t + 1 - t_triangle) * (t + 1 - t_peak)
                        + p_peak) / 2,
             lambda t: ramp_2 * (2 * t + 1 - 2 * t_triangle) / 2])

        triangle_profile = [float(p) for p in triangle_profile]

        ShiftableEnergyUnit.__init__(self, time, name,
                                     flow_direction=flow_direction,
                                     power_values=list(triangle_profile),
                                     mandatory=mandatory, co2_out=co2_out,
                                     starting_cost=starting_cost,
                                     operating_cost=operating_cost,
                                     energy_type=energy_type,
                                     verbose=verbose,
                                     no_warn=True)


class SawtoothEnergyUnit(ShiftableEnergyUnit):
    def __init__(self, time, name, flow_direction, p_peak, p_low, alpha_peak,
                 t_triangle, t_sawtooth, mandatory=True, starting_cost=None,
                 operating_cost=None, co2_out=None, energy_type=None,
                 verbose=True):
        if not isinstance(t_triangle, int):
            raise TypeError('t_triangle should be an integer, but is '
                            'a {}'.format(type(t_triangle)))
        if not isinstance(t_sawtooth, int):
            raise TypeError('t_sawtooth should be an integer, but is '
                            'a {}'.format(type(t_sawtooth)))

        t_peak = alpha_peak * t_triangle

        if alpha_peak == 0:
            ramp_1 = 0
            ramp_2 = - p_peak / (t_triangle - t_peak)
        elif alpha_peak == 1:
            ramp_1 = p_peak / t_peak
            ramp_2 = 0
        else:
            ramp_1 = p_peak / t_peak
            ramp_2 = - p_peak / (t_triangle - t_peak)

        t = np.arange(0, t_triangle)

        triangle_profile = np.piecewise(
            t, [t <= t_peak - 1, (t_peak - 1 < t) & (t < t_peak), t_peak <= t],
            [lambda t: ramp_1 * (2 * t + 1) / 2,
             lambda t: (ramp_1 * t * (t_peak - t)
                        + ramp_2 * (t + 1 - t_triangle) * (t + 1 - t_peak)
                        + p_peak) / 2,
             lambda t: ramp_2 * (2 * t + 1 - 2 * t_triangle) / 2])

        for espace in range(t_sawtooth - 2 * t_triangle + 1):
            if (t_sawtooth - t_triangle) % (t_triangle + espace) == 0:
                N = int((t_sawtooth + espace) / (t_triangle + espace))
                break

        triangle = [float(P) for P in triangle_profile]

        sawtooth_profile = triangle + (N - 1) * (espace * [p_low] + triangle)

        ShiftableEnergyUnit.__init__(self, time, name,
                                     flow_direction=flow_direction,
                                     power_values=list(sawtooth_profile),
                                     mandatory=mandatory, co2_out=co2_out,
                                     starting_cost=starting_cost,
                                     operating_cost=operating_cost,
                                     energy_type=energy_type,
                                     verbose=verbose,
                                     no_warn=True)


class SeveralEnergyUnit(VariableEnergyUnit):
    """
    **Description**

        Energy unit based on a fixed power curve enabling to multiply
        several times (nb_unit) the same power curve.

        Be careful, if imaginary == True, the solution may be imaginary as
        nb_unit can be continuous. The accurate number of the power unit
        should be calculated later

    **Attributes**

        * fixed_power : fixed power curve

    """

    def __init__(self, time, name, fixed_power, p_min=0, p_max=1e+5,
                 imaginary=False, e_min=None, e_max=None, nb_unit_min=0,
                 nb_unit_max=None, flow_direction='in', starting_cost=None,
                 operating_cost=None, max_ramp_up=None, max_ramp_down=None,
                 co2_out=None, energy_type=None,
                 verbose=True, no_warn=True):
        VariableEnergyUnit.__init__(self, time=time, name=name,
                                    flow_direction=flow_direction,
                                    p_min=p_min, p_max=p_max, e_min=e_min,
                                    e_max=e_max, starting_cost=starting_cost,
                                    operating_cost=operating_cost,
                                    min_time_on=None, min_time_off=None,
                                    max_ramp_up=max_ramp_up,
                                    max_ramp_down=max_ramp_down,
                                    co2_out=co2_out, availability_hours=None,
                                    energy_type=energy_type,
                                    verbose=verbose,
                                    no_warn=no_warn)

        self.power_curve = Quantity(name='power_curve', opt=False,
                                    value=fixed_power, vlen=time.LEN,
                                    parent=self)

        if imaginary:
            self.nb_unit = Quantity(name='nb_unit', opt=True,
                                    vtype=LpContinuous,
                                    lb=nb_unit_min, ub=nb_unit_max, vlen=1,
                                    parent=self)
            warnings.warn(
                'The solution may be imaginary as nb_unit is continuous')
        else:
            self.nb_unit = Quantity(name='nb_unit', opt=True, vtype=LpInteger,
                                    lb=nb_unit_min, ub=nb_unit_max, vlen=1,
                                    parent=self)

        self.calc_power_with_nb_unit_cst = DefinitionDynamicConstraint(
            exp_t='{0}_p[t] == {0}_nb_unit * {0}_power_curve[t]'.format(
                self.name), name='calc_power_with_nb_unit',
            t_range='for t in time.I', parent=self)


class AssemblyUnit(OptObject):
    """
    **Description**

        Simple Assembly unit: assembly units has at least a production unit
        and a consumption unit and is using one or several energy types.
        It  can also integrate reversible energy units. It inherits from
        OptObject and it  is the parent class of ConversionUnit and
        ReversibleUnit.

    **Attributes**

     * time: TimeUnit describing the studied time period
     * prod_units: list of the production units in the assembly unit.
     * cons_units: list of the consumption units in the assembly unit.
     * rev_units: list of the reversible units in the assembly unit.
     * poles: dictionary of the poles of the assembly unit

    """

    def __init__(self, time, name, prod_units=None, cons_units=None,
                 rev_units=None, verbose=True):
        OptObject.__init__(self, name=name, description='Assembly unit',
                           verbose=verbose)

        from .production_units import ProductionUnit
        from .consumption_units import ConsumptionUnit
        from .reversible_units import ReversibleUnit

        self.time = time
        self.prod_units = []  # Initialize an empty list for the
        # production units
        self.cons_units = []  # Initialize an empty list for the consumption
        # units
        self.rev_units = []  # Initialize an empty list for the reversible
        # units
        self.poles = {}  # Initialize an empty dictionary for the poles

        # An assembly unit is created with at least a production unit and a
        # consumption unit,or a reversible unit.
        # If a reversible unit is added, possibility to add (or not)
        # production and/or consumption units.
        if rev_units:
            if not isinstance(rev_units, list):
                raise TypeError('rev_units should be a list.')
            else:
                # if list or rev_units, adding rev_units
                for rev_unit in rev_units:
                    # rev_units should only contain ReversibleUnit objects
                    if not isinstance(rev_unit, ReversibleUnit):
                        raise TypeError(
                            'The elements in rev_units have to be the'
                            ' type "ReversibleUnit".')
                    else:
                        self._add_reversible_unit(rev_unit)

                # if rev_units is not None, possibility to add prod_units
                # (or not)
                if prod_units is None:
                    pass
                elif not isinstance(prod_units, list):
                    raise TypeError('prod_units should be a list')
                else:
                    for prod_unit in prod_units:
                        # prod_units should only contain ProductionUnit objects
                        if not isinstance(prod_unit, ProductionUnit):
                            raise TypeError(
                                'The elements in prod_units have to be the'
                                ' type "ProductionUnit".')
                        else:
                            self._add_production_unit(prod_unit)

                # if rev_units is not None, possibility to add cons_units
                # (or not)
                if cons_units is None:
                    pass
                elif not isinstance(cons_units, list):
                    raise TypeError('cons_units should be a list')
                else:
                    for cons_unit in cons_units:
                        # cons_units should only contain ConsumptionUnit
                        # objects
                        if not isinstance(cons_unit, ConsumptionUnit):
                            raise TypeError(
                                'The elements in cons_units have to be the'
                                ' type "ConsumptionUnit".')
                        else:
                            self._add_consumption_unit(cons_unit)

        # If there is no reversible unit, the assembly unit needs at least
        # one consumption and one production unit.
        else:
            if not prod_units:
                raise IndexError(
                    'You have to fill at least a production unit.')
            elif not isinstance(prod_units, list):
                raise TypeError('prod_units should be a list.')
            else:
                for prod_unit in prod_units:
                    # prod_units should only contain ProductionUnit objects
                    if not isinstance(prod_unit, ProductionUnit):
                        raise TypeError(
                            'The elements in prod_units have to be the'
                            ' type "ProductionUnit".')
                    else:
                        self._add_production_unit(prod_unit)

            if not cons_units:
                raise IndexError(
                    'You have to fill at least a consumption unit.')
            elif not isinstance(cons_units, list):
                raise TypeError('cons_units should be a list.')
            else:
                for cons_unit in cons_units:
                    # cons_units should only contain ConsumptionUnit
                    if not isinstance(cons_unit, ConsumptionUnit):
                        raise TypeError(
                            'The elements in cons_units have to be the'
                            ' type "ConsumptionUnit".')
                    else:
                        self._add_consumption_unit(cons_unit)

    def _add_production_unit(self, prod_unit):
        """
        :param prod_unit: production unit to be added to the
            production_units list
        """
        if prod_unit not in self.prod_units:
            poles_nb = len(self.poles)
            self.poles[poles_nb + 1] = prod_unit.poles[1]
            self.prod_units.append(prod_unit)
            prod_unit.parent = self
        else:
            print('Production unit {0} already in the production_units '
                  'list'.format(prod_unit.name))

    def _add_consumption_unit(self, cons_unit):
        """
        :param cons_unit: consumption unit to be added to the
            consumption_units list
        """
        if cons_unit not in self.cons_units:
            poles_nb = len(self.poles)
            self.poles[poles_nb + 1] = cons_unit.poles[1]
            self.cons_units.append(cons_unit)
            cons_unit.parent = self
        else:
            print('Consumption unit {0} already in the consumption_units '
                  'list'.format(cons_unit.name))

    def _add_reversible_unit(self, rev_unit):
        """
        :param rev_unit: reversible unit to be added to the
            reversible_units list
        """
        if rev_unit not in self.rev_units:
            poles_nb = len(self.poles)
            # Adding the various poles of the reversible_unit to the
            # assembly_unit.
            for p in range(1, len(rev_unit.poles) + 1):
                self.poles[poles_nb + p] = rev_unit.poles[p]
            self.rev_units.append(rev_unit)
            rev_unit.parent = self
        else:
            print('Reversible unit {0} already in the reversible_units list'
                  .format(rev_unit.name))

    def minimize_exergy_destruction(self, weight=1, pareto=False):
        """ This is the main objective of any exergetic optimization.

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        if hasattr(self, 'exergy_dest'):
            self.min_exergy_dest = Objective(name='min_exergy_destruction',
                                             exp='lpSum({0}_exergy_dest[t] '
                                                 'for t in time.I)'.
                                             format(self.name), weight=weight,
                                             pareto=pareto,
                                             parent=self)
        else:
            raise ValueError("You should initialize exergy calculations "
                             "on the unit named {0} before trying to "
                             "minimize its exergy destruction."
                             .format(self.name))
        
        
        
