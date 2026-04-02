#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module defines the conversion units, inheriting from AssemblyUnits**

The conversion_units module defines various classes of conversion units,
from generic to specific ones.

It includes :
 - ConversionUnit: simple conversion unit. It inherits from AssemblyUnit.
 - SingleConversionUnit: Conversion unit made of a single consumption unit
   and a single production unit. It can be used for any energy vector, and an
   efficiency ratio between the input (consumption) and the output (production)
 - ElectricalToThermalConversionUnit : Electrical to thermal Conversion unit
   with an electricity consumption and a thermal production linked by and
   electrical to thermal ratio. It inherits from ConversionUnit
 - HeatPump : Simple Heat Pump with an electricity consumption, a heat
   production and a heat consumption. It has a theoretical coefficient of
   performance COP and inherits from ConversionUnit.

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

from .energy_units import AssemblyUnit
from .consumption_units import FixedConsumptionUnit, VariableConsumptionUnit
from .production_units import FixedProductionUnit, VariableProductionUnit
from .reversible_units import ReversibleUnit
from ...general.optimisation.elements import *
from ..energy_types import *

__docformat__ = "restructuredtext en"


class ConversionUnit(AssemblyUnit):
    """
    **Description**

        Simple Conversion unit, inheriting from AssemblyUnit

    **Attributes**

     * time : TimeUnit describing the studied time period
     * prod_units : list of the production units
     * cons_units : list of the consumption units
     * poles : dictionary of the poles of the conversion unit

    """

    def __init__(self, time, name, prod_units=None, cons_units=None,
                 rev_units=None, verbose=True):
        AssemblyUnit.__init__(self, time=time, name=name,
                              prod_units=prod_units,
                              cons_units=cons_units,
                              rev_units=rev_units, verbose=verbose)


class SingleConversionUnit(ConversionUnit):
    """
    **Description**

    Conversion unit made of a single consumption unit and a single production
    unit. It can be used for any energy vector, and an efficiency ratio
    between the input (consumption) and the output (production)

    **Attributes**
        * production_unit: output of the conversion unit
        * consumption_unit: input of the conversion unit
        * conversion: Definition Dynamic Constraint linking the input to the \
        output through a ratio
    """

    def __init__(self, time, name, pmin_in=0, pmax_in=1e+5, p_in=None,
                 energy_type_in=None, pmin_out=0, pmax_out=1e+5,
                 p_out=None, energy_type_out=None, efficiency_ratio=1,
                 verbose=True):

        """
        :param time: TimeUnit describing the studied time period
        :param name: name of the single conversion unit
        :param pmin_in: minimal incoming power
        :param pmax_in: maximal incoming power
        :param energy_type_in: energy type of the input of the conversion
        unit: either elec, thermal or gas (see energy_types)
        :param p_in: power input for the electrical consumption unit
        :param pmin_out: minimal power output
        :param pmax_out: maximal power output
        :param p_out: power output
        :param energy_type_out: energy type of the output of the conversion
        unit: either elec, thermal or gas (see energy_types)
        :param efficiency_ratio: consumption to production ratio <=1
        """

        if p_out is None:
            self.production_unit = VariableProductionUnit(
                time, name + '_prod', energy_type=energy_type_out,
                p_min=pmin_out, p_max=pmax_out, verbose=verbose)
        else:
            self.production_unit = FixedProductionUnit(
                time, name + '_prod', energy_type=energy_type_out,
                p=p_out, verbose=verbose)

        if p_in is None:
            self.consumption_unit = VariableConsumptionUnit(
                time, name + '_cons', p_min=pmin_in,
                p_max=pmax_in, energy_type=energy_type_in,
                verbose=verbose)
        else:
            self.consumption_unit = FixedConsumptionUnit(
                time, name + '_cons', p=p_in,
                energy_type=energy_type_in, verbose=verbose)

        ConversionUnit.__init__(self, time, name,
                                prod_units=[self.production_unit],
                                cons_units=[self.consumption_unit])

        if isinstance(efficiency_ratio, (int, float)):
            if efficiency_ratio <= 1:
                self.conversion = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t] == {1} * {2}_p[t]'.format(
                        self.production_unit.name,
                        efficiency_ratio,
                        self.consumption_unit.name),
                    t_range='for t in time.I', name='conversion', parent=self)
            else:
                raise ValueError('The efficiency_ratio should be lower '
                                 'than 1 (production<=consumption)')

        elif isinstance(efficiency_ratio, list):
            if len(efficiency_ratio) == self.time.LEN:  # it must have the
                #  right size, i.e. the TimeUnit length.
                if all(e <= 1 for e in efficiency_ratio):
                    self.conversion = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.production_unit.name,
                            efficiency_ratio,
                            self.consumption_unit.name),
                        t_range='for t in time.I', name='conversion',
                        parent=self)
                else:
                    raise ValueError(
                        'The efficiency_ratio values should be '
                        'lower than 1 (production<=consumption)')
            else:
                raise IndexError('The length of the efficiency_ratio '
                                 'vector should be of the same length as the '
                                 'TimeUnit of the studied period')

        elif isinstance(efficiency_ratio, dict):  # efficiency_ratio is a dict
            # of values
            if len(efficiency_ratio) == self.time.LEN:
                if all(e <= 1 for e in efficiency_ratio.values()):
                    self.conversion = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.production_unit.name,
                            efficiency_ratio,
                            self.consumption_unit.name),
                        t_range='for t in time.I', name='conversion',
                        parent=self)
                else:
                    raise ValueError(
                        'The efficiency_ratio values should be '
                        'lower than 1 (production<=consumption)')
            else:
                raise IndexError('The length of the efficiency_ratio '
                                 'dictionary should be of the same length as '
                                 'the TimeUnit of the studied period')
        else:
            raise TypeError(
                "Efficiency ratio should be a mean value or a "
                "vector (list or dict) on the whole time period !")


class ElectricalToThermalConversionUnit(ConversionUnit):
    """
    **Description**
        DEPRECATED: please now use SingleConversionUnit with relevant energy
        types

        Electrical to thermal Conversion unit with an electricity consumption
        and a thermal production

    **Attributes**

     * thermal_production_unit : thermal production unit (thermal output)
     * elec_consumption_unit : electricity consumption unit (electrical
       input)
     * conversion : Definition Dynamic Constraint linking the electrical input to \
        the thermal output through the electrical to thermal ratio

    """
    print(
        "DEPRECATED: please now use SingleConversionUnit with relevant energy"
        "types")

    def __init__(self, time, name, pmin_in_elec=0, pmax_in_elec=1e+5,
                 p_in_elec=None, pmin_out_therm=0, pmax_out_therm=1e+5,
                 p_out_therm=None, elec_to_therm_ratio=1,
                 verbose=True):

        """
        :param time: TimeUnit describing the studied time period
        :param name: name of the electrical to thermal conversion unit
        :param pmin_in_elec: minimal incoming electrical power
        :param pmax_in_elec: maximal incoming electrical power
        :param p_in_elec: power input for the electrical consumption unit
        :param pmin_out_therm: minimal power output (thermal)
        :param pmax_out_therm: maximal power output (thermal)
        :param p_out_therm: power output (thermal)
        :param elec_to_therm_ratio: electricity to thermal ratio <=1
        """

        if p_out_therm is None:
            self.thermal_production_unit = VariableProductionUnit(
                time, name + '_therm_prod', energy_type='Thermal',
                p_min=pmin_out_therm, p_max=pmax_out_therm,
                verbose=verbose)
        else:
            self.thermal_production_unit = FixedProductionUnit(
                time, name + '_therm_prod', energy_type='Thermal',
                p=p_out_therm, verbose=verbose)

        if p_in_elec is None:
            self.elec_consumption_unit = VariableConsumptionUnit(
                time, name + '_elec_cons', p_min=pmin_in_elec,
                p_max=pmax_in_elec, energy_type='Electrical',
                verbose=verbose)
        else:
            self.elec_consumption_unit = FixedConsumptionUnit(
                time, name + '_elec_cons', p=p_in_elec,
                energy_type='Electrical', verbose=verbose)

        ConversionUnit.__init__(self, time, name,
                                prod_units=[self.thermal_production_unit],
                                cons_units=[self.elec_consumption_unit])

        if isinstance(elec_to_therm_ratio, (int, float)):  # e2h_ratio is a
            # mean value
            if elec_to_therm_ratio <= 1:
                self.conversion = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t] == {1} * {2}_p[t]'.format(
                        self.thermal_production_unit.name,
                        elec_to_therm_ratio,
                        self.elec_consumption_unit.name),
                    t_range='for t in time.I', name='conversion', parent=self)
            else:
                raise ValueError('The elec_to_therm_ratio should be lower '
                                 'than 1 (therm_production<elec_consumption)')

        elif isinstance(elec_to_therm_ratio, list):  # e2h_ratio is a list of
            # values
            if len(elec_to_therm_ratio) == self.time.LEN:  # it must have the
                #  right size, i.e. the TimeUnit length.
                if all(e <= 1 for e in elec_to_therm_ratio):
                    self.conversion = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.thermal_production_unit.name,
                            elec_to_therm_ratio,
                            self.elec_consumption_unit.name),
                        t_range='for t in time.I', name='conversion',
                        parent=self)
                else:
                    raise ValueError(
                        'The elec_to_therm_ratio values should be '
                        'lower than 1 (therm_production<elec_'
                        'consumption)')
            else:
                raise IndexError('The length of the elec_to_therm_ratio '
                                 'vector should be of the same length as the '
                                 'TimeUnit of the studied period')

        elif isinstance(elec_to_therm_ratio, dict):  # e2h_ratio is a dict of
            # values
            if len(elec_to_therm_ratio) == self.time.LEN:
                if all(e <= 1 for e in elec_to_therm_ratio.values()):
                    self.conversion = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.thermal_production_unit.name,
                            elec_to_therm_ratio,
                            self.elec_consumption_unit.name),
                        t_range='for t in time.I', name='conversion',
                        parent=self)
                else:
                    raise ValueError(
                        'The elec_to_therm_ratio values should be '
                        'lower than 1 (therm_production<elec_'
                        'consumption)')
            else:
                raise IndexError('The length of the elec_to_therm_ratio '
                                 'dictionary should be of the same length as '
                                 'the TimeUnit of the studied period')
        else:
            raise TypeError(
                "Electricity to thermal ratio should be a mean value or a "
                "vector (list or dict) on the whole time period !")


class ElectricalConversionUnit(ConversionUnit):
    """
    **Description**

        Electrical Conversion unit with an electricity consumption
        and an electricity production

    **Attributes**

     * elec_production_unit : electricity production unit (electrical output)
     * elec_consumption_unit : electricity consumption unit (electrical
       input)
     * conversion : Definition Dynamic Constraint linking the electrical \
        input to the electrical output through the elec_to_elec ratio

    """

    def __init__(self, time, name, pmin_in_elec=0, pmax_in_elec=1e+5,
                 p_in_elec=None, pmin_out_elec=0, pmax_out_elec=1e+5,
                 p_out_elec=None, elec_to_elec_ratio=1):
        """
        :param time: TimeUnit describing the studied time period
        :param name: name of the electrical to elec conversion unit
        :param pmin_in_elec: minimal incoming electrical power
        :param pmax_in_elec: maximal incoming electrical power
        :param p_in_elec: power input for the electrical consumption unit
        :param pmin_out_elec: minimal power output (elec)
        :param pmax_out_elec: maximal power output (elec)
        :param p_out_elec: power output (elec)
        :param elec_to_elec_ratio: electricity to elec ratio <=1
        """

        if p_out_elec is None:
            self.elec_production_unit = VariableProductionUnit(
                time, name + '_elec_prod', energy_type='Electrical',
                p_min=pmin_out_elec, p_max=pmax_out_elec)
        else:
            self.elec_production_unit = FixedProductionUnit(
                time, name + '_elec_prod', energy_type='Electrical',
                p=p_out_elec)

        if p_in_elec is None:
            self.elec_consumption_unit = VariableConsumptionUnit(
                time, name + '_elec_cons', p_min=pmin_in_elec,
                p_max=pmax_in_elec, energy_type='Electrical')
        else:
            self.elec_consumption_unit = FixedConsumptionUnit(
                time, name, p=p_in_elec, energy_type='Electrical')

        ConversionUnit.__init__(self, time, name,
                                prod_units=[self.elec_production_unit],
                                cons_units=[self.elec_consumption_unit])

        if isinstance(elec_to_elec_ratio, (int, float)):  # e2h_ratio is a
            # mean value
            if elec_to_elec_ratio <= 1:
                self.conversion = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t] == {1} * {2}_p[t]'.format(
                        self.elec_production_unit.name,
                        elec_to_elec_ratio,
                        self.elec_consumption_unit.name),
                    t_range='for t in time.I', name='conversion', parent=self)
            else:
                raise ValueError('The elec_to_elec_ratio should be lower '
                                 'than 1 (elec_production<elec_consumption)')

        elif isinstance(elec_to_elec_ratio, list):  # e2h_ratio is a list of
            # values
            if len(elec_to_elec_ratio) == self.time.LEN:  # it must have the
                #  right size, i.e. the TimeUnit length.
                if all(e <= 1 for e in elec_to_elec_ratio):
                    self.conversion = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.elec_production_unit.name,
                            elec_to_elec_ratio,
                            self.elec_consumption_unit.name),
                        t_range='for t in time.I', name='conversion',
                        parent=self)
                else:
                    raise ValueError('The elec_to_elec_ratio values should be '
                                     'lower than 1 (elec_production<elec_'
                                     'consumption)')
            else:
                raise IndexError('The length of the elec_to_elec_ratio '
                                 'vector should be of the same length as the '
                                 'TimeUnit of the studied period')

        elif isinstance(elec_to_elec_ratio, dict):  # e2h_ratio is a dict of
            # values
            if len(elec_to_elec_ratio) == self.time.LEN:
                if all(e <= 1 for e in elec_to_elec_ratio.values()):
                    self.conversion = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.elec_production_unit.name,
                            elec_to_elec_ratio,
                            self.elec_consumption_unit.name),
                        t_range='for t in time.I', name='conversion',
                        parent=self)
                else:
                    raise ValueError('The elec_to_elec_ratio values should be '
                                     'lower than 1 (elec_production<elec_'
                                     'consumption)')
            else:
                raise IndexError('The length of the elec_to_elec_ratio '
                                 'dictionary should be of the same length as '
                                 'the TimeUnit of the studied period')
        else:
            raise TypeError(
                "Electricity to elec ratio should be a mean value or a "
                "vector (list or dict) on the whole time period !")


class ReversibleConversionUnit(ConversionUnit):
    """
    **Description**

        Reversible Conversion unit with two reversible units,
        one for each side of the conversion unit. Theses sides will be
        called upstream and downstream.

    **Attributes**

     * rev_unit_upstream: reversible unit upstream
     * rev_unit_downstream: reversible unit downstream
     * conversion_up2down: Definition Dynamic Constraint linking the \
        consumption of the upstream reversible unit to the production \
            of the downstream reversible unit through the up2down_eff
     * conversion_down2up:  Definition Dynamic Constraint linking the consumption of the \
        downstream reversible unit to the production of the upstream reversible \
            unit through the down2up_eff

    """

    def __init__(self, time, name, pmin_up=0, pmax_up=1e+5, pmin_down=0,
                 pmax_down=1e+5, up2down_eff=1, down2up_eff=1,
                 energy_type_up=None, energy_type_down=None, verbose=True):
        """

        :param time: time for the studied time period
        :param name: name of the reversible conversion unit
        :param pmin_up: pmin for both consumption and production unit of the
        upstream reversible unit
        :param pmax_up: pmax for both consumption and production unit of the
        upstream reversible unit
        :param pmin_down: pmin for both consumption and production unit of the
        downstream reversible unit
        :param pmax_down: pmax for both consumption and production unit of the
        downstream reversible unit
        :param up2down_eff: efficiency of the conversion from upstream to
        downstream
        :param down2up_eff: efficiency of the conversion from downstream to
        upstream
        :param energy_type_up: energy type of the upstream reversible unit
        :param energy_type_down: energy type of the downstream reversible unit
        """

        self.rev_unit_upstream = \
            ReversibleUnit(time=time, name=name + '_upstream',
                           pmin_cons=pmin_up,
                           pmax_cons=pmax_up, pmin_prod=pmin_up,
                           pmax_prod=pmax_up, energy_type_prod=energy_type_up,
                           energy_type_cons=energy_type_up, verbose=verbose)

        self.rev_unit_downstream = \
            ReversibleUnit(time=time, name=name + '_downstream',
                           pmin_cons=pmin_down, pmax_cons=pmax_down,
                           pmin_prod=pmin_down, pmax_prod=pmax_down,
                           energy_type_cons=energy_type_down, verbose=verbose)

        ConversionUnit.__init__(self, time, name,
                                rev_units=[self.rev_unit_upstream,
                                           self.rev_unit_downstream])

        # Managing the upstream to downstream conversion for various types
        # of up2down_eff:

        if isinstance(up2down_eff, (int, float)):  # up2down_eff is a mean
            # value
            if up2down_eff <= 1:
                self.conversion_up2down = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t] == {1} * {2}_p[t]'.format(
                        self.rev_unit_downstream.production_unit.name,
                        up2down_eff,
                        self.rev_unit_upstream.consumption_unit.name),
                    t_range='for t in time.I', name='conversion_up2down',
                    parent=self)
            else:
                raise ValueError('The up2down_efficiency should be lower '
                                 'than 1')

        elif isinstance(up2down_eff, list):  # up2down_eff is a list of
            # values
            if len(up2down_eff) == self.time.LEN:  # it must have the right
                # size, i.e. the TimeUnit length.
                if all(e <= 1 for e in up2down_eff):
                    self.conversion_up2down = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.rev_unit_downstream.production_unit.name,
                            up2down_eff,
                            self.rev_unit_upstream.consumption_unit.name),
                        t_range='for t in time.I', name='conversion_up2down',
                        parent=self)
                else:
                    raise ValueError('The up2down efficiency values should be '
                                     'lower than 1')
            else:
                raise IndexError('The length of the up2down efficiency '
                                 'vector should be of the same length as the '
                                 'TimeUnit of the studied period')

        elif isinstance(up2down_eff, dict):  # up2down_eff is a dict of
            # values
            if len(up2down_eff) == self.time.LEN:
                if all(e <= 1 for e in up2down_eff.values()):
                    self.conversion_up2down = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.rev_unit_downstream.production_unit.name,
                            up2down_eff.values(),
                            self.rev_unit_upstream.consumption_unit.name),
                        t_range='for t in time.I', name='conversion_up2down',
                        parent=self)
                else:
                    raise ValueError('The up2down efficiency values should be '
                                     'lower than 1')
            else:
                raise IndexError('The length of the up2down efficiency '
                                 'dictionary should be of the same length as '
                                 'the TimeUnit of the studied period')
        else:
            raise TypeError(
                "The up2down efficiency should be a mean value or a vector "
                "(list or dict) on the whole time period !")

        # Managing the downstream to upstream conversion for various types
        # of down2up_eff:

        if isinstance(down2up_eff, (int, float)):  # down2up_eff is a mean
            # value
            if down2up_eff <= 1:
                self.conversion_down2up = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t] == {1} * {2}_p[t]'.format(
                        self.rev_unit_upstream.production_unit.name,
                        down2up_eff,
                        self.rev_unit_downstream.consumption_unit.name),
                    t_range='for t in time.I', name='conversion_down2up',
                    parent=self)
            else:
                raise ValueError('The down2up_efficiency should be lower '
                                 'than 1')

        elif isinstance(down2up_eff, list):  # down2up_eff is a list of
            # values
            if len(down2up_eff) == self.time.LEN:  # it must have the right
                # size, i.e. the TimeUnit length.
                if all(e <= 1 for e in down2up_eff):
                    self.conversion_down2up = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.rev_unit_upstream.production_unit.name,
                            down2up_eff,
                            self.rev_unit_downstream.consumption_unit.name),
                        t_range='for t in time.I', name='conversion_down2up',
                        parent=self)
                else:
                    raise ValueError('The down2up efficiency values should be '
                                     'lower than 1')
            else:
                raise IndexError('The length of the down2up efficiency '
                                 'vector should be of the same length as the '
                                 'TimeUnit of the studied period')

        elif isinstance(down2up_eff, dict):  # down2up_eff is a dict of
            # values
            if len(down2up_eff) == self.time.LEN:
                if all(e <= 1 for e in down2up_eff.values()):
                    self.conversion_down2up = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.rev_unit_upstream.production_unit.name,
                            down2up_eff.values(),
                            self.rev_unit_downstream.consumption_unit.name),
                        t_range='for t in time.I', name='conversion_down2up',
                        parent=self)
                else:
                    raise ValueError('The down2up efficiency values should be '
                                     'lower than 1')
            else:
                raise IndexError('The length of the down2up efficiency '
                                 'dictionary should be of the same length as '
                                 'the TimeUnit of the studied period')
        else:
            raise TypeError(
                "The down2up efficiency should be a mean value or a vector "
                "(list or dict) on the whole time period !")


class HeatPump(ConversionUnit):
    """
    **Description**

        Simple Heat Pump with an electricity consumption, a thermal production
        and a thermal consumption. It has a theoretical coefficient of
        performance COP and inherits from ConversionUnit.

    **Attributes**

     * thermal_production_unit : thermal production unit (condenser)
     * elec_consumption_unit : electricity consumption unit (electrical
       input)
     * thermal_consumption_unit : heay consumption unit (evaporator)
     * COP : Quantity describing the coefficient of performance of the
       heat pump
     * conversion : Definition Dynamic Constraint linking the electrical\
     input to the thermal output through the electrical to thermal ratio
     * power_flow : Definition Dynamic constraint linking the thermal output\
     to the electrical and thermal inputs in relation to the losses.

    """

    def __init__(self, time, name, pmin_in_elec=0, pmax_in_elec=1e+5,
                 p_in_elec=None, pmin_in_therm=0, pmax_in_therm=1e+5,
                 p_in_therm=None, pmin_out_therm=0, pmax_out_therm=1e+5,
                 p_out_therm=None, cop=3, losses=0, min_time_on=None):
        """
        :param time: TimeUnit describing the studied time period
        :param name: name of the heat pump
        :param pmin_in_elec:  minimal incoming electrical power
        :param pmax_in_elec: maximal incoming electrical power
        :param p_in_elec: power input for the electrical consumption unit
        :param pmin_in_therm: minimal incoming thermal power
        :param pmax_in_therm: maximal incoming thermal power
        :param p_in_therm: power input for the thermal consumption unit
        :param pmin_out_therm: minimal power output (thermal)
        :param pmax_out_therm: maximal power output (thermal)
        :param p_out_therm: power output (thermal)
        :param cop: Coefficient Of Performance of the Heat Pump (cop>1)
        :param losses: losses as a percentage of thermal energy produced (
        p_out)
        """

        if p_out_therm is None:
            self.thermal_production_unit = VariableProductionUnit(
                time, name + '_therm_prod', energy_type='Thermal',
                p_min=pmin_out_therm, p_max=pmax_out_therm,
                min_time_on=min_time_on)
        else:
            self.thermal_production_unit = FixedProductionUnit(
                time, name + '_therm_prod', energy_type='Thermal',
                p=p_out_therm)

        if p_in_therm is None:
            self.thermal_consumption_unit = VariableConsumptionUnit(
                time, name + '_therm_cons', energy_type='Thermal',
                p_min=pmin_in_therm, p_max=pmax_in_therm)
        else:
            self.thermal_consumption_unit = FixedConsumptionUnit(
                time, name + '_therm_cons', energy_type='Thermal',
                p=p_in_therm)

        if p_in_elec is None:
            self.elec_consumption_unit = VariableConsumptionUnit(
                time, name + '_elec_cons', p_min=pmin_in_elec,
                p_max=pmax_in_elec, energy_type='Electrical')
        else:
            self.elec_consumption_unit = FixedConsumptionUnit(
                time, name, p=p_in_elec, energy_type='Electrical')

        ConversionUnit.__init__(self, time, name,
                                prod_units=[self.thermal_production_unit],
                                cons_units=[self.thermal_consumption_unit,
                                            self.elec_consumption_unit])

        self.COP = Quantity(name='COP', value=cop, parent=self)

        if isinstance(self.COP.value, (int, float)):  # The cop has a single
            #  value
            if self.COP.value >= 1:  # The cop value should be greater than 1
                self.conversion = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t] == {1} * {2}_p[t]'.format(
                        self.thermal_production_unit.name,
                        self.COP.value,
                        self.elec_consumption_unit.name),
                    t_range='for t in time.I', name='conversion', parent=self)

                self.power_flow = DefinitionDynamicConstraint(
                    exp_t='{0}_p[t]*(1+{1}) == {2}_p[t] + {3}_p[t]'
                        .format(self.thermal_production_unit.name, losses,
                                self.thermal_consumption_unit.name,
                                self.elec_consumption_unit.name),
                    t_range='for t in time.I',
                    name='power_flow', parent=self)
            else:
                raise ValueError("The COP value should be greater than 1")

        elif isinstance(self.COP.value, list):  # The cop has a list of values
            if len(self.COP.value) == self.time.LEN:
                if all(c >= 1 for c in self.COP.value):
                    self.conversion = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.thermal_production_unit.name,
                            self.COP.value,
                            self.elec_consumption_unit.name),
                        t_range='for t in time.I', name='conversion',
                        parent=self)
                    self.power_flow = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t]*(1+{1}) == {2}_p[t] + {3}_p[t]'
                            .format(self.thermal_production_unit.name, losses,
                                    self.thermal_consumption_unit.name,
                                    self.elec_consumption_unit.name),
                        t_range='for t in time.I',
                        name='power_flow', parent=self)
                else:
                    raise ValueError("The COP values should be greater than 1")
            else:
                raise IndexError("The COP should have the same length as the "
                                 "studied time period")

        elif isinstance(self.COP.value, dict):  # The cop has a dict
            # referencing its values.
            if len(self.COP.value) == self.time.LEN:
                if all(c >= 1 for c in self.COP.value.values()):
                    self.conversion = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t] == {1}[t] * {2}_p[t]'.format(
                            self.thermal_production_unit.name,
                            self.COP.value,
                            self.elec_consumption_unit.name),
                        t_range='for t in time.I', name='conversion',
                        parent=self)
                    self.power_flow = DefinitionDynamicConstraint(
                        exp_t='{0}_p[t]*(1+{1}) == {2}_p[t] + {3}_p[t]'
                            .format(self.thermal_production_unit.name, losses,
                                    self.thermal_consumption_unit.name,
                                    self.elec_consumption_unit.name),
                        t_range='for t in time.I',
                        name='power_flow', parent=self)
                else:
                    raise ValueError("The COP values should be greater than 1")
            else:
                raise IndexError("The COP should have the same length as the "
                                 "studied time period")
        else:
            raise TypeError(
                "The assigned cop should be a mean value or a vector "
                "(dict or list) over the studied time period !")
