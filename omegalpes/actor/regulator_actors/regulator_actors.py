#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module defines the operator_actor and its scope of responsibility**

 One constraint is available :
    - co2_emission_maximum

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
from ..actor import Actor
from ...general.optimisation.elements import *
from ...energy.units.production_units import ProductionUnit


class RegulatorActor(Actor):
    """
    **Description**

        RegulatorActor class inherits from the the basic class Actor. It
        enables one to model an actor who can add constraints on all
        energy units of the study case.

    **Attributes**

     - name : name of the actor
    """

    def __init__(self, name, verbose=True):
        Actor.__init__(self, name=name, verbose=verbose)

        self.description = 'Regulator Actor OptObject'

    def add_co2_emission_maximum(self, time, co2_max, cst_production_list):
        """
        To create the actor constraint of a maximum of CO2 emission.

        :param co2_max: Maximum of the CO2 emission. May be an int,
            float or a list with the size of the period study
        :param time: period of the study
        :param cst_production_list: List of production units on which the
        constraint will be applied.

        """
        for production_unit in cst_production_list:
            if isinstance(production_unit, ProductionUnit):
                pass
            else:
                raise TypeError('Should be ProductionUnit type for '
                                'co2_emission_maximum constraint')

        production_name_string = ''
        for production_unit in cst_production_list:
            production_name_string += '_{}'.format(
                production_unit.name)

        production_p_string = ''
        for production_unit in cst_production_list[:-1]:
            production_p_string += '{}_co2_emissions[t] + '.format(
                production_unit.name)
        production_p_string += '{}_co2_emissions[t]'.format(
            cst_production_list[-1].name)

        cst_name = 'max_co2_emission{}'.format(production_name_string)

        if isinstance(co2_max, (int, float)):
            exp = '{0} <= {1}'.format(production_p_string, co2_max)
            setattr(self, cst_name, ActorConstraint(exp=exp,
                                                    name=cst_name))

        elif isinstance(co2_max, list):
            if len(co2_max) != time.LEN:
                raise IndexError(
                    "co2_max should be the size of the time "
                    "period : {} but equals {}.".format(time.LEN,
                                                        len(co2_max)))
            else:
                exp_t = '{0} <= {1}[t]'.format(production_p_string, co2_max)
                setattr(self, cst_name, ActorDynamicConstraint(exp_t=exp_t,
                                                               name=cst_name,
                                                               t_range='for '
                                                                       't in '
                                                                 'time.I'))
        else:
            raise TypeError('co2_max should be an int, '
                            'a float or a list.')

    def add_particles_emission_maximum(self, time, particle_max,
                                       cst_production_list):
        """
        To create the actor constraint of a maximum of CO2 emission.

        :param particle_max: Maximum of the particle emission. May be an int,
            float or a list with the size of the period study
        :param time: period of the study
        :param cst_production_list: List of production units on which the
        constraint will be applied.

        """
        for production_unit in cst_production_list:
            if isinstance(production_unit, ProductionUnit):
                pass
            else:
                raise TypeError('Should be ProductionUnit type for '
                                'particle_emission_maximum constraint')

        production_name_string = ''
        for production_unit in cst_production_list:
            production_name_string += '_{}'.format(
                production_unit.name)

        production_p_string = ''
        for production_unit in cst_production_list[:-1]:
            production_p_string += '{}_particle_emissions[t] + '.format(
                production_unit.name)
        production_p_string += '{}_particle_emissions[t]'.format(
            cst_production_list[-1].name)

        cst_name = 'max_particle_emission{}'.format(production_name_string)

        if isinstance(particle_max, (int, float)):
            exp = '{0} <= {1}'.format(production_p_string, particle_max)
            setattr(self, cst_name, ActorConstraint(exp=exp,
                                                    name=cst_name))

        elif isinstance(particle_max, list):
            if len(particle_max) != time.LEN:
                raise IndexError(
                    "particle_max should be the size of the time "
                    "period : {} but equals {}.".format(time.LEN,
                                                        len(particle_max)))
            else:
                exp_t = '{0} <= {1}[t]'.format(production_p_string,
                                               particle_max)
                setattr(self, cst_name, ActorDynamicConstraint(
                    exp_t=exp_t, name=cst_name, t_range='for t in time.I'))
        else:
            raise TypeError('particle_max should be an int, '
                            'a float or a list.')


class LocalAuthorities(RegulatorActor):
    """
    **Description**

        LocalAuthorities class inherits from the basic class RegulatorActor. It
        focuses on local Authorities constraints

    """

    def __init__(self, name):
        RegulatorActor.__init__(self, name=name)


class StateAuthorities(RegulatorActor):
    """
    **Description**

        StateAuthorities class inherits from the basic class RegulatorActor. It
        focuses on local Authorities constraints

    """

    def __init__(self, name):
        RegulatorActor.__init__(self, name=name)
