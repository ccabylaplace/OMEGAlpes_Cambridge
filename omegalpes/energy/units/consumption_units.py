#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module defines the consumption units**

 The consumption_units module defines various classes of consumption units,
 from generic to specific ones.

 It includes :
    - ConsumptionUnit : simple consumption unit. It inherits from EnergyUnit,
      its power flow direction is always 'in'. \n
      3 Objectives are also available :

            * minimize consumption,
            * maximize consumption,
            * minimize consumption costs.

    - FixedConsumptionUnit :  consumption with a fixed load profile. It
      inherits from ConsumptionUnit.

    - VariableConsumptionUnit : consumption unit allowing for a variation of
      power between p_min et p_max. It inherits from ConsumptionUnit.

And also :
 - SeveralConsumptionUnit: Consumption unit based on a fixed consumption curve
   enabling to multiply several times (nb_unit) the same consumption profile
 - SeveralImaginaryConsumptionUnit: Consumption unit based on a fixed
   consumption curve enabling to multiply several times (nb_unit) the same
   consumption profile. Be careful, the solution may be imaginary as nb_unit
   can be continuous. The accurate number of the Consumption units should be
   calculated later
 - SquareConsumptionUnit: Consumption unit with a fixed value and fixed
   duration.
 - ShiftableConsumptionUnit: Consumption unit with shiftable consumption
   profile.

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
from .energy_units import *
del AssemblyUnit
from ...general.optimisation.elements import *
__docformat__ = "restructuredtext en"


class ConsumptionUnit(EnergyUnit):
    """
    **Description**

        Simple Consumption unit. The parameters and attributes are described
        in EnergyUnit parent class. Here, consumption_cost is the cost
        associated to the energy consumption of the unit (€/kWh).

     """

    def __init__(self, time, name, p=None, p_min=0, p_max=1e+5, e_min=None,
                 e_max=None, co2_out=None, starting_cost=None,
                 consumption_cost=None, min_time_on=None, min_time_off=None,
                 max_ramp_up=None, max_ramp_down=None, availability_hours=None,
                 energy_type=None, verbose=True):
        EnergyUnit.__init__(self, time, name, flow_direction='in', p=p,
                            p_min=p_min, p_max=p_max, e_min=e_min, e_max=e_max,
                            co2_out=co2_out, starting_cost=starting_cost,
                            operating_cost=consumption_cost,
                            min_time_on=min_time_on,
                            min_time_off=min_time_off, max_ramp_up=max_ramp_up,
                            max_ramp_down=max_ramp_down,
                            availability_hours=availability_hours,
                            energy_type=energy_type,
                            verbose=verbose)

    # OBJECTIVES#
    def minimize_consumption(self, weight=1, pareto=False):
        """
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        self.minimize_energy(weight=weight, pareto=pareto)
        self.min_energy.name = 'min_consumption'

    def maximize_consumption(self, weight=1, pareto=False):
        """
        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        self.minimize_energy(weight=-1 * weight, pareto=pareto)
        self.min_energy.name = 'max_consumption'

    def minimize_consumption_cost(self, weight=1, pareto=False):
        """

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        self.minimize_operating_cost(weight, pareto=pareto)
        self.min_operating_cost.name = 'min_consumption_cost'


class FixedConsumptionUnit(FixedEnergyUnit, ConsumptionUnit):
    """
    **Description**

        Consumption unit with a fixed consumption profile.

    **Attributes**

        * p : instantaneous power demand known in advance (kW)
        * energy_type : type of energy ('Electrical', 'Heat', ...)
        * consumption_cost : cost associated to the energy consumption

    """

    def __init__(self, time, name, p: list or dict or pd.DataFrame = None,
                 co2_out=None,
                 starting_cost=None, operating_cost=None, energy_type=None,
                 verbose=True):
        ConsumptionUnit.__init__(self, time=time, name=name, verbose=verbose)
        FixedEnergyUnit.__init__(self, time, name=name, p=p,
                                 flow_direction='in',
                                 starting_cost=starting_cost,
                                 operating_cost=operating_cost, co2_out=co2_out,
                                 energy_type=energy_type,
                                 verbose=False)


class VariableConsumptionUnit(VariableEnergyUnit, ConsumptionUnit):
    """
    **Description**

        Consumption unit with a variation of power between p_min et p_max.

    **Attributes**

        * p_max : maximal instantaneous power consumption (kW)
        * p_min : minimal instantaneous power consumption (kW)
        * energy_type : type of energy ('Electrical', 'Heat', ...)

    """

    def __init__(self, time, name, p_min=0, p_max=1e+5, e_min=None,
                 e_max=None, co2_out=None, starting_cost=None,
                 operating_cost=None, min_time_on=None, min_time_off=None,
                 max_ramp_up=None, max_ramp_down=None, energy_type=None,
                 verbose=True, no_warn=True):
        ConsumptionUnit.__init__(self, time=time, name=name, verbose=verbose)
        VariableEnergyUnit.__init__(self, time, name=name,
                                    flow_direction='in', p_min=p_min,
                                    p_max=p_max, e_min=e_min, e_max=e_max,
                                    starting_cost=starting_cost,
                                    operating_cost=operating_cost,
                                    min_time_on=min_time_on,
                                    min_time_off=min_time_off,
                                    max_ramp_up=max_ramp_up,
                                    max_ramp_down=max_ramp_down,
                                    co2_out=co2_out, energy_type=energy_type,
                                    verbose=False, no_warn=no_warn)


class SeveralConsumptionUnit(VariableConsumptionUnit, SeveralEnergyUnit):
    """
    **Description**

        Consumption unit based on a fixed consumption curve enabling to multiply
        several times (nb_unit) the same consumption curve.

    **Attributes**

        * fixed_cons : fixed consumption curve

    """

    def __init__(self, time, name, fixed_cons, imaginary=False,
                 p_min=0, p_max=1e+5, e_min=None,
                 e_max=None, nb_unit_min=0, nb_unit_max=None, co2_out=None,
                 starting_cost=None, operating_cost=None, max_ramp_up=None,
                 max_ramp_down=None, energy_type=None,
                 verbose=True, no_warn=True):
        VariableConsumptionUnit.__init__(self, time=time, name=name,
                                         verbose=verbose)
        SeveralEnergyUnit.__init__(self, time, name=name,
                                   fixed_power=fixed_cons,
                                   imaginary=imaginary, p_min=p_min,
                                   p_max=p_max, e_min=e_min,
                                   e_max=e_max, nb_unit_min=nb_unit_min,
                                   nb_unit_max=nb_unit_max,
                                   flow_direction='in',
                                   starting_cost=starting_cost,
                                   operating_cost=operating_cost,
                                   max_ramp_up=max_ramp_up,
                                   max_ramp_down=max_ramp_down,
                                   co2_out=co2_out, energy_type=energy_type,
                                   verbose=False,
                                   no_warn=no_warn)


class SquareConsumptionUnit(SquareEnergyUnit, VariableConsumptionUnit):
    """
    **Description**

        | Consumption unit with a fixed value and fixed duration.
        | Only the time of beginning can be modified
        | Operation can be mandatory or not

    **Attributes**

        * p : instantaneous power consumption (kW)
        * duration : duration of the power delivery (hours)
        * mandatory : indicates if the power delivery is mandatory or not
        * energy_type : type of energy ('Electrical', 'Heat', ...)
        * consumption_cost : cost associated to the energy consumption

    """

    def __init__(self, time, name, p_square, duration, n_square,
                 t_between_sq, co2_out=None, starting_cost=None,
                 operating_cost=None, energy_type=None,
                 verbose=True, no_warn=False):
        duration /= time.DT
        if duration < 1:
            raise ValueError('The duration of operation of the '
                             'SquareConsumptionUnit should be longer than the '
                             'time step.')
        duration = int(round(duration))
        VariableConsumptionUnit.__init__(self, time=time, name=name,
                                         verbose=verbose)
        SquareEnergyUnit.__init__(self, time, name=name, p_square=p_square,
                                  n_square=n_square, t_square=duration,
                                  t_between_sq=t_between_sq,
                                  flow_direction='in',
                                  starting_cost=starting_cost,
                                  operating_cost=operating_cost,
                                  co2_out=co2_out, energy_type=energy_type,
                                  verbose=False,
                                  no_warn=no_warn)


class ShiftableConsumptionUnit(ShiftableEnergyUnit, VariableConsumptionUnit):
    """
    **Description**

        Consumption unit with shiftable consumption profile.

    **Attributes**

        * power_values : consumption profile to shift (kW)
        * mandatory : indicates if the consumption is mandatory (True) or not (False)
        * starting_cost : cost of the starting of the consumption
        * operating_cost : cost of the operation (€/kW)
        * energy_type : type of energy ('Electrical', 'Heat', ...)

    """

    def __init__(self, time, name: str, power_values, mandatory=True,
                 co2_out=None, starting_cost=None, operating_cost=None,
                 energy_type=None, verbose=True):
        VariableConsumptionUnit.__init__(self, time=time, name=name,
                                         verbose=verbose)
        ShiftableEnergyUnit.__init__(self, time, name=name,
                                     flow_direction='in',
                                     power_values=power_values,
                                     mandatory=mandatory, co2_out=co2_out,
                                     starting_cost=starting_cost,
                                     operating_cost=operating_cost,
                                     energy_type=energy_type,
                                     verbose=False)