#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module defines the energy nodes that will allow energy transmission
between the various energy units and conversion units**

The energy_node module includes the EnergyNode class for energy transmission
between production, consumption, conversion and storage. Defining several
energy nodes and exporting/importing energy between them can also allow for a
better demarcation of the energy system.

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
from ..general.optimisation.core import OptObject
from ..energy.io.poles import FlowPole, Epole
from .units.energy_units import EnergyUnit, AssemblyUnit
from .units.storage_units import StorageUnit
from ..general.optimisation.elements import *

__docformat__ = "restructuredtext en"


class EnergyNode(OptObject):
    """
    This class defines an energy node.
    """

    def __init__(self, time, name, energy_type=None, operator=None):
        OptObject.__init__(self, name=name, description='Energy Node')

        self.time = time
        self.energy_type = energy_type
        self._connected_energy_units = []
        self._poles_list = []
        self._exports = []
        self._imports = []
        self.operator = operator

    @property
    def get_connected_energy_units(self):
        """ Return the list of connected EnergyUnits in the EnergyNode """
        return self._connected_energy_units

    @property
    def get_flows(self):
        """ Get all the power flows of the energy node
        :rtype: list
        :return: list of power flows
        """
        return [pole['p'] for pole in self.get_poles]

    @property
    def get_poles(self):
        """ Return the list of energy poles in the EnergyNode """
        return self._poles_list

    @property
    def get_input_poles(self):
        input_poles = []

        for pole in self.get_poles:
            if not isinstance(pole, FlowPole):
                raise TypeError('Wrong Type of arguments,\
                arguments should be an FlowPole')
            if isinstance(pole[pole.flow], Quantity) and (pole.flow in pole):
                if pole[pole.direction] == 'out':
                    # even if, on the node point of view, we look for input
                    # poles, the direction of the pole is 'out' as it comes
                    # from a production unit (thus with the direction 'out')
                    input_poles.append(pole)
                else:
                    pass
        return input_poles

    @property
    def get_output_poles(self):
        output_poles = []

        for pole in self.get_poles:
            if not isinstance(pole, FlowPole):
                raise TypeError('Wrong Type of arguments,\
                arguments should be an FlowPole')
            if isinstance(pole[pole.flow], Quantity) and (pole.flow in pole):
                if pole[pole.direction] == 'in':
                    # even if, on the node point of view, we look for output
                    # poles, the direction of the pole is 'in' as it goes
                    # into a
                    # consumption unit (thus with the direction 'in')
                    output_poles.append(pole)
                else:
                    pass
        return output_poles

    @property
    def get_exports(self):
        """ Return the list of exports to the EnergyNode"""
        return self._exports

    @property
    def get_imports(self):
        """ Return the list of imports to the EnergyNode"""
        return self._imports

    def add_connected_energy_unit(self, unit):
        """ Add an EnergyUnit to the connected_units list """
        if isinstance(unit, EnergyUnit):
            if unit not in self.get_connected_energy_units:
                self._connected_energy_units.append(unit)

                if unit.energy_type is None:
                    unit.energy_type = self.energy_type

                elif self.energy_type is None:
                    self.energy_type = unit.energy_type

                elif unit.energy_type != self.energy_type:
                    raise TypeError('You cannot connect an {0} EnergyUnit to a'
                                    ' {1} EnergyNode.'.format(unit.energy_type,
                                                              self.energy_type)
                                    )
                self.add_pole(unit.poles[1])
        elif isinstance(unit, StorageUnit):
            charge = unit.charge
            discharge = unit.discharge
            if charge not in self.get_connected_energy_units:
                self._connected_energy_units.append(charge)

                if charge.energy_type is None:
                    charge.energy_type = self.energy_type

                elif self.energy_type is None:
                    self.energy_type = charge.energy_type

                elif charge.energy_type != self.energy_type:
                    raise TypeError('You cannot connect an {0} EnergyUnit to a'
                                    ' {1} EnergyNode.'.format(charge.energy_type,
                                                              self.energy_type)
                                    )
                self.add_pole(charge.poles[1])
            if discharge not in self.get_connected_energy_units:
                self._connected_energy_units.append(discharge)

                if discharge.energy_type is None:
                    discharge.energy_type = self.energy_type

                elif self.energy_type is None:
                    self.energy_type = discharge.energy_type

                elif discharge.energy_type != self.energy_type:
                    raise TypeError('You cannot connect an {0} EnergyUnit to a'
                                    ' {1} EnergyNode.'.format(
                        discharge.energy_type, self.energy_type)
                                    )
                self.add_pole(discharge.poles[1])
        elif isinstance(unit, AssemblyUnit) and not isinstance(unit, StorageUnit):
            raise TypeError(
                "The unit {0} is an AssemblyUnit: you should connect "
                "the Energy units within this assembly unit to the "
                "node, not the whole unit!".format(unit.name))
        else:
            raise TypeError(
                "The unit {0} to connect to an EnergyNode should be an "
                "EnergyUnit and is {1}".format(unit, type(unit)))

    def add_pole(self, pole: Epole) -> None:
        """ Add an energy pole to the poles_list

        :param pole: Epole
        """
        assert isinstance(pole, Epole)
        if pole not in self.get_poles:
            self._poles_list.append(pole)

    def connect_units(self, *units):
        """
        Connecting all EnergyUnit to the EnergyNode

        :param units: EnergyUnits connected to the EnergyNode
        :type units: EnergyUnit
        """

        for unit in units:
            self.add_connected_energy_unit(unit)

    def set_power_balance(self):
        """ Set the power balance equation for the EnergyNode """
        exp_t = ''

        for pole in self.get_poles:
            if not isinstance(pole, FlowPole):
                raise TypeError('Wrong Type of arguments,\
                arguments should be an FlowPole')
            if isinstance(pole[pole.flow], Quantity) and (pole.flow in pole):
                if pole[pole.direction] == 'in':
                    exp_t += '-' + pole[pole.flow].parent.name + \
                             '_' + pole[pole.flow].name + '[t]'
                elif pole[pole.direction] == 'out':
                    exp_t += '+' + pole[pole.flow].parent.name + \
                             '_' + pole[pole.flow].name + '[t]'
        exp_t += ' == 0'

        if exp_t[0] == '+':
            exp_t = exp_t[1:]

        setattr(self, 'power_balance', DefinitionDynamicConstraint(exp_t=exp_t,
                                                                   name='power_balance',
                                                                   parent=self))

    def create_export(self, node, export_min, export_max):
        """Create the export from the EnergyNode (self)
        to the EnergyNode (node)

        :param node: EnergyNode to whom power can be exported
        :param export_min: Minimal value of exported power when there is export
        :param export_max: Maximal value of exported power when there is export
        :return: Quantity that defines the power exported
        """
        energy_export = Quantity(
            name='energy_export_to_{0}'.format(node.name), opt=True, lb=0,
            ub=export_max, vlen=self.time.LEN, parent=self)

        is_exporting = Quantity(
            name='is_exporting_to_{0}'.format(node.name),
            description='The node is exporting :1 or not :0',
            vtype=LpBinary, vlen=self.time.LEN, parent=self)

        setattr(self, 'energy_export_to_{0}'.format(node.name),
                energy_export)
        setattr(self, 'is_exporting_to_{0}'.format(node.name), is_exporting)

        if isinstance(export_min, (int, float)):
            set_export_min = TechnicalDynamicConstraint(
                exp_t='{0}_is_exporting_to_{1}[t] * {2} <= '
                      '{0}_energy_export_to_{1}[t]'.format(self.name,
                                                           node.name,
                                                           export_min),
                name='set_export_min_{0}_min'.format(node.name), parent=self)
            setattr(self, 'set_export_to_{0}_min'.format(node.name),
                    set_export_min)

        elif isinstance(export_min, list):
            set_export_min = TechnicalDynamicConstraint(
                exp_t='{0}_is_exporting_to_{1}[t] * {2}[t] <= '
                      '{0}_energy_export_to_{1}[t]'.format(self.name,
                                                           node.name,
                                                           export_min),
                name='set_export_min', parent=self)
            setattr(self, 'set_export_min', set_export_min)

        if isinstance(export_max, (int, float)):
            set_export_max = TechnicalDynamicConstraint(
                exp_t='{0}_is_exporting_to_{1}[t] * {2} >= '
                      '{0}_energy_export_to_{1}[t]'.format(self.name,
                                                           node.name,
                                                           export_max),
                name='set_export_to_{0}_max'.format(node.name), parent=self)
            setattr(self, 'set_export_to_{0}_max'.format(node.name),
                    set_export_max)
        elif isinstance(export_max, list):
            set_export_max = TechnicalDynamicConstraint(
                exp_t='{0}_is_exporting_to_{1}[t] * {2}[t] >= '
                      '{0}_energy_export_to_{1}[t]'.format(self.name,
                                                           node.name,
                                                           export_max),
                name='set_export_to_{0}_max'.format(node.name), parent=self)
            setattr(self, 'set_export_to_{0}_max'.format(node.name), set_export_max)

        self._exports.append(energy_export)
        node._imports.append(energy_export)

        return energy_export

    def export_to_node(self, node, export_min=0, export_max=1e+5):
        """ Add an export of power from the node to another node

        :param node: EnergyNode to whom power can be exported
        :param export_min: Minimal value of exported power when there is export
        :param export_max: Maximal value of exported power when there is export
        """
        if not isinstance(node, EnergyNode):
            raise TypeError(
                'The node {0} should be an EnergyNode'.format(node))

        if node.energy_type != self.energy_type:
            raise AttributeError(
                'You cannot export energy from an EnergyNode '
                'with energy_type "{0}" to an EnergyNode with '
                'energy_type "{1}"'.format(node.energy_type, self.energy_type))
        else:
            energy_export = self.create_export(node, export_min, export_max)

            self.add_pole(Epole(p=energy_export, direction='in',
                                energy_type=self.energy_type))
            node.add_pole(Epole(p=energy_export, direction='out',
                                energy_type=self.energy_type))

    def import_from_node(self, node, import_min=0, import_max=1e5):
        """

        :param node: EnergyNode from whom power can be imported
        :param import_min: Minimal value of imported power when there is import
        :param import_max: Maximal value of imported power when there is import
        """

        node.export_to_node(self, export_min=import_min, export_max=import_max)

    def is_import_flow(self, flow):
        """ Get if the power flow is an import or not"""
        is_import = flow in self.get_imports
        return is_import

    def is_export_flow(self, flow):
        """ Get if the power flow is an export or not"""
        is_export = flow in self.get_exports
        return is_export
