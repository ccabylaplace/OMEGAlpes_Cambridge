#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module contains the exergy assessment routines of OMEGALPES. This
module**:

1) Determines inlet, outlet or contained exergy of, respectively, any
   ConsumptionUnit, ProductionUnit or StorageUnit.
2) Determines exergy destruction within any EnergyUnit.
2) Recognizes Electrical and Thermal energy.
3) Can calculate exergy for a single unit or for a list of units.
4) Can proceed with only one temperature value or with a list of temperatures.
   4.1. Formulates exergy for one single EnergyUnit and temperature.
   4.2. Formulates timely exergy if one single EnergyUnit and a list of
   temperatures is provided.
   4.3. Formulates exergy for each unit within a list of EnergyUnits if only
    one temperature is provided.
   4.4. Formulates timely exergy for each unit within a list of EnergyUnits if
    a list of temperatures is provided.

The exergy-related classes defined in this module are not physical units. They
are virtual units attached to their energetic counterparts. Consequently,
the exergy and exergy destruction calculated in this module are attached to
the EnergyUnit as a Quantity at the moment of calculating it.

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

from omegalpes.energy.energy_types import *
from omegalpes.energy.units.conversion_units import *
from omegalpes.energy.units.production_units import *
from omegalpes.energy.units.consumption_units import *
from omegalpes.energy.units.storage_units import StorageUnit
from omegalpes.general.optimisation.core import OptObject
from omegalpes.general.optimisation.elements import *

__docformat__ = "restructuredtext en"


class ElectricalExergy(OptObject):

    def __init__(self, energy_unit: EnergyUnit or list):
        OptObject.__init__(self, name='elect_exergy',
                           description="Exergy of an electrical flow",
                           verbose=True)

        _check_energy_unit(energy_unit)
        _check_exergy_not_assessed(energy_unit)
        _check_energy_type(energy_unit, elec)
        self._assess_elec_exergy(energy_unit)

    def _assess_elec_exergy(self, energy_unit):

        if isinstance(energy_unit, EnergyUnit):
            energy_unit.exergy = Quantity(name='exergy',
                                          description='Exergy content of the '
                                                      'energy flow interacting'
                                                      ' with this unit',
                                          vlen=energy_unit.time.LEN, unit='kW',
                                          parent=energy_unit)

            if isinstance(energy_unit, StorageUnit):
                "In storage units, the contained exergy is calculated."
                energy_unit.calc_exergy = DefinitionDynamicConstraint(
                    name='calc_exergy',
                    exp_t='{0}_exergy[t] == {0}_e[t]*time.DT'
                        .format(energy_unit.name),
                    t_range='for t in time.I',
                    parent=self)
            else:
                energy_unit.calc_exergy = DefinitionDynamicConstraint(
                    name='calc_exergy',
                    exp_t='{0}_exergy[t] == {0}_p[t]*time.DT'.
                        format(energy_unit.name),
                    t_range='for t in time.I',
                    parent=self)
        elif isinstance(energy_unit, list):
            for energy_unit in energy_unit:
                energy_unit.exergy = Quantity(name='exergy',
                                              description='Exergy content of '
                                                          'the energy flow '
                                                          'interacting with '
                                                          'this unit',
                                              vlen=energy_unit.time.LEN,
                                              unit='kW',
                                              parent=energy_unit)

                if isinstance(energy_unit, StorageUnit):
                    """"In storage units, exergy is understood as contained 
                    exergy."""
                    energy_unit.calc_exergy = DefinitionDynamicConstraint(
                        name='calc_exergy',
                        exp_t='{0}_exergy[t] == {0}_e[t]*time.DT'
                            .format(energy_unit.name),
                        t_range='for t in time.I',
                        parent=self)
                else:
                    energy_unit.calc_exergy = DefinitionDynamicConstraint(
                        name='calc_exergy',
                        exp_t='{0}_exergy[t] == {0}_p[t]*time.DT'.
                            format(energy_unit.name),
                        t_range='for t in time.I',
                        parent=self)


class ThermalExergy(OptObject):

    def __init__(self, energy_unit: EnergyUnit or list,
                 temp_heat: int or float or list,
                 temp_ref=20):
        OptObject.__init__(self, name='thermal_exergy',
                           description="Exergy of a thermal energy flow",
                           verbose=True)

        _check_energy_unit(energy_unit)
        _check_exergy_not_assessed(energy_unit)
        _check_energy_type(energy_unit, thermal)
        self._check_temperature(energy_unit, temp_heat)

        if isinstance(energy_unit, EnergyUnit) or isinstance(energy_unit, StorageUnit):
            energy_unit.exergy = Quantity(name='exergy',
                                          description='Exergy content of the energy'
                                                      ' flow interacting with this unit',
                                          vlen=energy_unit.time.LEN, unit='kW',
                                          parent=energy_unit)
            energy_unit.calc_exergy = DefinitionDynamicConstraint(
                name='calc_exergy',
                exp_t='{0}_exergy[t] == {0}_p[t] * '
                                                              '(1 -({1}+273.15)/({1}+273.15))*time.DT'
                .format(
                                                            energy_unit.name,
                                                            temp_ref),
                t_range='for t in time.I',
                parent=self)
        else:
            for energy_unit in energy_unit:
                energy_unit.exergy = Quantity(name='exergy',
                                              description='Exergy content of the energy'
                                                          ' flow interacting with this unit',
                                              vlen=energy_unit.time.LEN,
                                              unit='kW',
                                              parent=energy_unit)
                energy_unit.calc_exergy = DefinitionDynamicConstraint(
                    name='calc_exergy',
                    exp_t='{0}_exergy[t] == {0}_p[t] * '
                          '(1 -({1}+273.15)/({1}+273.15))*time.DT'
                        .format(energy_unit.name, temp_ref),
                    t_range='for t in time.I',
                    parent=self)

        self._assess_th_exergy(energy_unit, temp_ref, temp_heat)

    def _check_temperature(self, energy_unit, temp_heat):
        if temp_heat is None:
            raise ValueError('Please define a temperature to assess thermal '
                             'exergy of the unit named "{0}".'.format(
                energy_unit.name))
        else:
            if not isinstance(temp_heat, (int, float, list)):
                raise TypeError(
                    'Temperatures for thermal exergy assessment should'
                    ' be an int, a float or a list. In your unit named'
                    ' "{0}", temperature is a {1}. Please check it.'.
                        format(energy_unit.name, type(temp_heat)))
            else:
                if isinstance(temp_heat, list):
                    for t_heat in temp_heat:
                        if not isinstance(t_heat, (int, float, list)):
                            raise TypeError('Temperatures for thermal exergy '
                                            'assessment should be an int, a '
                                            'float or a list. In one of your '
                                            'instantiations you entered a temp'
                                            ' that is a {}, please check it.'.
                                            format(type(t_heat)))
                    if isinstance(energy_unit, list):
                        if len(temp_heat) != len(energy_unit) and len(
                                temp_heat) != energy_unit[0].time.LEN:
                            raise IndexError('Wrong length in your temp list. '
                                             '1) To assess thermal exergy of a'
                                             ' list of units with constant '
                                             'temperature, the list of units '
                                             'and the list of temperatures '
                                             'must be the same length. 2) To '
                                             'assess thermal exergy of a list '
                                             'of units with dynamic temp '
                                             'throughout the year, the list of'
                                             ' temps must be the same length '
                                             'of the time unit. 3) If your '
                                             'thermal units have different '
                                             'timely temperature profiles, '
                                             'you have to assess their '
                                             'exergies separately and always '
                                             'satisfying condition #2.')
                    else:
                        if len(temp_heat) != energy_unit.time.LEN:
                            raise IndexError('Please make sure that the list '
                                             'of temperatures that you provide'
                                             ' for the unit named "{0}" has '
                                             'the same length as the time'
                                             'unit.'.format(energy_unit.name))

    def _assess_th_exergy(self, energy_unit, temp_ref, temp_heat=None):

        """ Calculate thermal exergy of a thermal unit """

        if isinstance(temp_heat, list):
            if isinstance(energy_unit, list):
                if len(temp_heat) == len(energy_unit):
                    for e_unit in energy_unit and temp_heat in temp_heat:
                        e_unit.temp_heat = Quantity(
                            name='t_heat',
                            description='Temperature of the thermal flow',
                            lb=0, value=temp_heat, vlen=1, parent=self)
                        if isinstance(e_unit, StorageUnit):
                            e_unit.calc_exergy = DefinitionDynamicConstraint(
                                name='calc_exergy',
                                exp_t='{0}_exergy[t] == {0}_e[t] * '
                                      '(1 -({1}+273.15)/({0}_t_heat+273.15))*'
                                      'time.DT'
                                    .format(e_unit.name, temp_ref),
                                t_range='for t in time.I',
                                parent=self)
                        else:
                            e_unit.calc_exergy = DefinitionDynamicConstraint(
                                name='calc_exergy',
                                exp_t='{0}_exergy[t] == {0}_p[t] * '
                                      '(1 -({1}+273.15)/({0}_t_heat+273.15))*'
                                      'time.DT'
                                    .format(e_unit.name, temp_ref),
                                t_range='for t in time.I',
                                parent=self)
                elif len(temp_heat) == energy_unit[0].time.LEN:
                    for e_unit in energy_unit:
                        e_unit.temp_heat = Quantity(name='t_heat',
                                                    description='Temperature '
                                                                'of heat flow',
                                                    lb=0, value=temp_heat,
                                                    vlen=e_unit.time.LEN,
                                                    # unit=temp_unit,
                                                    parent=self)
                        if isinstance(e_unit, StorageUnit):
                            e_unit.calc_exergy = DefinitionDynamicConstraint(
                                name='calc_exergy',
                                exp_t='{0}_exergy[t] == {0}_e[t] * '
                                      '(1 -({1}+273.15)/({0}_t_heat[t]+273.15))*'
                                      'time.DT'
                                    .format(e_unit.name, temp_ref),
                                t_range='for t in time.I',
                                parent=self)
                        else:
                            e_unit.calc_exergy = DefinitionDynamicConstraint(
                                name='calc_exergy',
                                exp_t='{0}_exergy[t] == {0}_p[t] * '
                                      '(1 -({1}+273.15)/({0}_t_heat[t]+273.15))*'
                                      'time.DT'
                                    .format(e_unit.name, temp_ref),
                                t_range='for t in time.I',
                                parent=self)
            else:
                energy_unit.temp_heat = Quantity(name='t_heat',
                                                 description='Temperature '
                                                             'of heat flow',
                                                 lb=0, value=temp_heat,
                                                 vlen=energy_unit.time.LEN,
                                                 # unit=temp_unit,
                                                 parent=self)
                if isinstance(energy_unit, StorageUnit):
                    energy_unit.calc_exergy = DefinitionDynamicConstraint(
                        name='calc_exergy',
                        exp_t='{0}_exergy[t] == {0}_e[t] * '
                              '(1 -({1}+273.15)/({0}_t_heat[t]+273.15))*time.DT'
                            .format(energy_unit.name, temp_ref),
                        t_range='for t in time.I',
                        parent=self)

                else:
                    energy_unit.calc_exergy = DefinitionDynamicConstraint(
                        name='calc_exergy',
                        exp_t='{0}_exergy[t] == {0}_p[t] * '
                              '(1 -({1}+273.15)/({0}_t_heat[t]+273.15))*time.DT'
                            .format(energy_unit.name, temp_ref),
                        t_range='for t in time.I',
                        parent=self)
        else:
            if isinstance(energy_unit, list):
                for e_unit in energy_unit:
                    e_unit.temp_heat = Quantity(
                        name='t_heat',
                        description='Temperature of the thermal flow',
                        lb=0, value=temp_heat, vlen=1, parent=self)

                    if isinstance(e_unit, StorageUnit):
                        e_unit.calc_exergy = DefinitionDynamicConstraint(
                            name='calc_exergy',
                            exp_t='{0}_exergy[t] == {0}_e[t] * '
                                  '(1 -({1}+273.15)/({2}+273.15))*time.DT'
                                .format(e_unit.name, temp_ref,
                                        e_unit.temp_heat),
                            t_range='for t in time.I',
                            parent=self)
                    else:
                        e_unit.calc_exergy = DefinitionDynamicConstraint(
                            name='calc_exergy',
                            exp_t='{0}_exergy[t] == {0}_p[t] * '
                                  '(1 -({1}+273.15)/({2}+273.15))*time.DT'
                                .format(e_unit.name, temp_ref,
                                        e_unit.temp_heat),
                            t_range='for t in time.I',
                            parent=self)
            else:
                energy_unit.temp_heat = Quantity(
                    name='t_heat',
                    description='Temperature of the thermal flow',
                    lb=0, value=temp_heat, vlen=1, parent=self)
                if isinstance(energy_unit, StorageUnit):
                    energy_unit.calc_exergy = DefinitionDynamicConstraint(
                        name='calc_exergy',
                        exp_t='{0}_exergy[t] == {0}_e[t] * '
                              '(1 -({1}+273.15)/({2}+273.15))*time.DT'
                            .format(energy_unit.name, temp_ref,
                                    energy_unit.temp_heat),
                        t_range='for t in time.I',
                        parent=self)
                else:
                    energy_unit.calc_exergy = DefinitionDynamicConstraint(
                        name='calc_exergy',
                        exp_t='{0}_exergy[t] == {0}_p[t] * '
                              '(1 -({1}+273.15)/({2}+273.15))*time.DT'
                            .format(energy_unit.name, temp_ref,
                                    energy_unit.temp_heat),
                        t_range='for t in time.I',
                        parent=self)


def _check_energy_unit(energy_unit):
    if isinstance(energy_unit, list):
        for energy_unit in energy_unit:
            if not isinstance(energy_unit, EnergyUnit) and not isinstance(energy_unit, AssemblyUnit):
                raise TypeError("You are trying to assess exergy on an object "
                                "that is not an EnergyUnit. Please re-check "
                                "your exergy instantiations.")
    else:
        if not isinstance(energy_unit, EnergyUnit) and not isinstance(energy_unit, AssemblyUnit):
            raise TypeError("You are trying to assess exergy on an object "
                            "that is not an EnergyUnit. Please re-check "
                            "your exergy instantiations.")


def _check_exergy_not_assessed(energy_unit):
    if isinstance(energy_unit, list):
        for energy_unit in energy_unit:
            if hasattr(energy_unit, 'exergy'):
                raise AttributeError('You are trying to assess {0} exergy more'
                                     ' than once on the unit named "{1}". '
                                     'Please delete all redundant {0} exergy '
                                     'instantiations on that unit.'.format(
                    energy_unit.energy_type,
                    energy_unit.name))
    else:
        if hasattr(energy_unit, 'exergy'):
            raise AttributeError('You are trying to assess {0} exergy more'
                                 ' than once on the unit named "{1}". '
                                 'Please delete all redundant {0} exergy '
                                 'instantiations on that unit.'.format(
                energy_unit.energy_type,
                energy_unit.name))


def _check_energy_type(energy_unit, energy_type):
    if isinstance(energy_unit, list):
        for energy_unit in energy_unit:
            if not energy_unit.energy_type:
                raise TypeError(
                    'Exergy can only be calculated for simple units, '
                    'and not for units made up of other units, such as '
                    'your unit named {0}. Try calculating exergy in '
                    'the subunits of your unit named {0}'.
                        format(energy_unit.name))
            else:
                if energy_unit.energy_type is not energy_type:
                    raise TypeError(
                        '{0} exergy can only be evaluated for {0} units. Your '
                        'unit "{1}" is a {2} unit.'.format(energy_type,
                                                           energy_unit.name,
                                                           energy_unit.
                                                           energy_type))
    else:
        if not energy_unit.energy_type:
            raise TypeError('Exergy can only be calculated for simple units, '
                            'and not for units made up of other units, such as'
                            'your unit named {0}. Try calculating exergy in '
                            'the subunits of your unit named {0}'.
                            format(energy_unit.name))

        else:
            if energy_unit.energy_type is not energy_type:
                raise TypeError('Electrical exergy can only be evaluated for '
                                'electrical units. Your unit named {0} is a '
                                '{1} unit.'.format(energy_unit.name,
                                                   energy_unit.energy_type))


class ExergyDestruction(OptObject):
    def __init__(self, energy_unit=None, exergy_eff=1, temp_ref=20,
                 temp_heat=None):
        OptObject.__init__(self, name='elec_exergy',
                           description="Exergy of an electrical flow",
                           verbose=True)

        if hasattr(energy_unit, 'exergy_dest'):
            raise AttributeError(
                'You have already calculated exergy destruction for the unit '
                '{}'.format(energy_unit.name))

        energy_unit.exergy_dest = Quantity(name='exergy_dest',
                                           description='Exergy destruction',
                                           vlen=energy_unit.time.LEN,
                                           unit='kW', parent=self)
        energy_unit.exd_tot = Quantity(name='exd_tot', unit='kWh', parent=self,
                                       description='total exergy destruction',
                                       vlen=1)
        energy_unit.calc_exd_tot = DefinitionConstraint(name='calc_exd_tot',
                                                        parent=self,
                                                        exp='{0}_exd_tot == '
                                                            'time.DT * '
                                                  'lpSum({0}_exergy_dest[t]'
                                                  ' for t in time.I)'
                                                        .format(
                                                            energy_unit.name))

        """ Calculate exergy destruction within this unit """

        if isinstance(energy_unit, StorageUnit):
            energy_unit.calc_exergy_dest = DefinitionDynamicConstraint(
                name='calc_exergy_dest',
                exp_t='{0}_exergy_dest[t] == {0}_e[t] * {1} * '
                      '(1 -({2}+273.15)/({3}+273.15))*time.DT'
                      .format(energy_unit.name, energy_unit.self_disch_t,
                            temp_ref, temp_heat),
                t_range='for t in time.I',
                parent=self)

        elif isinstance(energy_unit, ConversionUnit):
            exd_conv_unit = energy_unit.name + '_exergy_dest[t] == '
            exergy_balance = ''
            for cons in energy_unit.cons_units:
                if hasattr(cons, 'exergy'):
                    exergy_balance += ' + ' + cons.name + '_exergy[t]'
                else:
                    raise AttributeError(
                        "You need to calculate exergy of subunit "
                        "{0} before calculating exergy destruction of"
                        " the unit named {1}.".format(cons.name,
                                                      energy_unit.name))
            for prod in energy_unit.prod_units:
                if hasattr(prod, 'exergy'):
                    exergy_balance += ' - ' + prod.name + '_exergy[t]'
                else:
                    raise AttributeError(
                        "You need to calculate exergy of subunit "
                        "{0} before calculating exergy destruction of"
                        " the unit named {1}.".format(prod.name,
                                                      energy_unit.name))
            if exergy_balance[0] == ' + ':
                exergy_balance = exergy_balance[1:]
            exd_conv_unit += exergy_balance
            energy_unit.calc_exergy_dest = DefinitionDynamicConstraint(
                name='calc_exergy_dest',
                exp_t=exd_conv_unit,
                t_range='for t in time.I', parent=self)

        elif isinstance(energy_unit, ConsumptionUnit):
            if exergy_eff is None:
                raise ValueError("You should specify an exergy efficiency for "
                                 "unit named {0}.".format(energy_unit.name))

            elif isinstance(exergy_eff, (int, float)):
                energy_unit.calc_exergy_dest = DefinitionDynamicConstraint(
                    name='calc_exergy_dest',
                    exp_t='{0}_exergy_dest[t] == '
                          '{0}_exergy[t] * (1 -{1})'
                        .format(energy_unit.name, exergy_eff),
                    t_range='for t in time.I', parent=self)

            elif isinstance(exergy_eff, list):
                if len(exergy_eff) != energy_unit.time.LEN:
                    raise IndexError('The vector containing exergy '
                                     'efficiency values of the unit named'
                                     ' {0} should be the same length of '
                                     'the time vector.')
                else:
                    energy_unit.calc_exergy_dest = DefinitionDynamicConstraint(
                        name='calc_exergy_dest',
                        exp_t='{0}_exergy_dest[t] == '
                              '{0}_exergy[t] * (1 -{1}[t])'
                            .format(energy_unit.name, exergy_eff),
                        t_range='for t in time.I', parent=self)

            else:
                raise ValueError('Exergy efficiency of the unit named {0} '
                                 'is a {1} but it should be an int, a float'
                                 ' or a list.'.format(energy_unit.name,
                                                      type(exergy_eff)))

        elif isinstance(energy_unit, ProductionUnit):
            if exergy_eff is None:
                raise ValueError("You should specify an exergy efficiency for "
                                 "unit named {0}.".format(energy_unit.name))

            elif isinstance(exergy_eff, (int, float)):
                if exergy_eff == 0:
                    raise ValueError("Exergy efficiency of the unit "
                                     "named {0} has to be greater than 0.".format(
                        energy_unit.name))
                else:
                    energy_unit.calc_exergy_dest = DefinitionDynamicConstraint(
                        name='calc_exergy_dest',
                        exp_t='{0}_exergy_dest[t] == '
                              '{0}_exergy[t] * (1/{1}-1)'
                            .format(energy_unit.name, exergy_eff),
                        t_range='for t in time.I', parent=self)

            elif isinstance(exergy_eff, list):
                if len(exergy_eff) != energy_unit.time.LEN:
                    raise IndexError('The list containing exergy '
                                     'efficiency values of the unit named'
                                     ' "{0}" should be the same length of '
                                     'the time vector.'.
                                     format(energy_unit.name))
                else:
                    for exergy_eff in exergy_eff:
                        if exergy_eff is not (int, float):
                            raise ValueError('In the unit named "{0}", all '
                                             'values in the list of '
                                             'efficiencies must be an int or '
                                             ' float.'.format(energy_unit.
                                                              name))
                        else:
                            if exergy_eff == 0:
                                raise ValueError(
                                    'Exergy efficiency of the unit '
                                    '"{0}" has to be greater than 0 '
                                    'at every time step.'.format(
                                        energy_unit.name))

                    energy_unit.calc_exergy_dest = DefinitionDynamicConstraint(
                        name='calc_exergy_dest',
                        exp_t='{0}_exergy_dest[t] == '
                              '{0}_exergy[t] * (1/{1}[t]-1)'
                            .format(energy_unit.name, exergy_eff),
                        t_range='for t in time.I', parent=self)
            else:
                raise TypeError('Exergy efficiency of the unit named {0} '
                                'is a {1} but it should be an int, a float'
                                ' or a list.'.format(energy_unit.name,
                                                     type(exergy_eff)))

        else:
            raise TypeError('Sorry, the type of the unit named {0}'
                            ' was not recognized for exergy '
                            'analysis.'.format(energy_unit.name))
