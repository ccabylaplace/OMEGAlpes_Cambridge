#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module defines the production units**

The production_units module defines various kinds of production units with
associated attributes and methods.

It includes :
 - ProductionUnit : simple production unit inheriting from EnergyUnit and
   with an outer flow direction. The outside co2 emissions, the starting cost,
   the operating cost, the minimal operating time, the minimal non-operating
   time, the maximal increasing ramp and the maximal decreasing ramp can be
   filled.

   Objectives are also available :

    * minimize starting cost, operating cost, total cost
    * minimize production, co2_emissions, time of use
    * maximize production

 - FixedProductionUnit : Production unit with a fixed production profile.
 - VariableProductionUnit : Production unit with a variation of power between
   p_min et p_max.

And also :
 - SeveralProductionUnit: Production unit based on a fixed production curve
   enabling to multiply several times (nb_unit) the same production curve
 - SeveralImaginaryProductionUnit: Production unit based on a fixed
   production curve enabling to multiply several times (nb_unit) the same
   production curve. Be careful, the solution may be imaginary as nb_unit
   can be continuous. The accurate number of the production unit should be
   calculated later
 - SquareProductionUnit: Production unit with a fixed value and fixed
   duration.
 - ShiftableProductionUnit: Production unit with shiftable production
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

import warnings
from pulp import LpBinary, LpInteger, LpContinuous

from .energy_units import *
del AssemblyUnit
from ...general.optimisation.elements import *
from ...general.optimisation.elements import Objective
from ...general.optimisation.elements import Quantity

__docformat__ = "restructuredtext en"


class ProductionUnit(EnergyUnit):
    """
    **Description**

        Simple Production unit. The parameters and attributes are described
        in EnergyUnit parent class.



    """

    def __init__(self, time, name, p=None, p_min=0, p_max=1e+5, e_min=None,
                 e_max=None, co2_out=None, particle_emission=None,
                 starting_cost=None,
                 operating_cost=None, min_time_on=None, min_time_off=None,
                 max_ramp_up=None, max_ramp_down=None, availability_hours=None,
                 energy_type=None, rr_energy=False, verbose=True,
                 no_warn=True):
        """
        :param rr_energy: True if the energy produced is renewable or
        recovery energy.
        :param particle_emission: if not None, adds particle emissions value
        depending on the energy production (ex: kg_particle/kWh).
        """

        EnergyUnit.__init__(self, time, name, flow_direction='out', p=p,
                            p_min=p_min, p_max=p_max, e_min=e_min, e_max=e_max,
                            co2_out=co2_out, starting_cost=starting_cost,
                            operating_cost=operating_cost,
                            min_time_on=min_time_on,
                            min_time_off=min_time_off, max_ramp_up=max_ramp_up,
                            max_ramp_down=max_ramp_down,
                            availability_hours=availability_hours,
                            energy_type=energy_type,
                            verbose=verbose, no_warn=no_warn)

        self.rr_energy = rr_energy
        self.particle_emission = None

        if particle_emission is not None:
            self._add_particle_emissions(particle_emission)

    def minimize_production(self, weight=1, pareto=False):
        """

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        self.minimize_energy(weight=weight, pareto=pareto)
        self.min_energy.name = 'min_production'

    def maximize_production(self, weight=1, pareto=False):
        """

        :param weight: Weight coefficient for the objective
        :param pareto: if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)
        """
        self.minimize_energy(weight=-1 * weight, pareto=pareto)
        self.min_energy.name = 'max_production'

    def minimize_peak_power(self, weight=1, pareto=False):
        
        self.epsilon = Quantity(name='peak_power',lb=0, opt=True)
        cst = DefinitionDynamicConstraint(exp_t="{0}_p[t] <= {0}_peak_power"
                                          .format(self.name))
        setattr(self,'peak_power_minimization',cst)

        self.min_peak = Objective(name='min_peak',
                                    exp='{0}_peak_power'
                                    .format(self.name), weight=weight,
                                    pareto=pareto,
                                    parent=self)
    
    def minimize_peak_to_average_ratio(self, time, weight=1, pareto=False):
        
        self.epsilon = Quantity(name='peak_power',lb=0, opt=True)
        cst = DefinitionDynamicConstraint(exp_t="{0}_p[t] <= {0}_peak_power"
                                          .format(self.name))
        setattr(self,'peak_power_minimization',cst)

        self.min_peak = Objective(name='min_peak_average',
                                    exp='{0}_peak_power - lpSum({0}_p[t] for t in time.I)/{1}'
                                    .format(self.name,time.LEN), weight=weight,
                                    pareto=pareto,
                                    parent=self)

    def _add_particle_emissions(self, particle_emission):
        """
        Add a particle emissions associated to the energy unit based on the
        value particle_emission.
        For each time step the energy unit is running the particle_emission
        value is multiplied by the power production and
        added to the particle_emission of the production unit.

        :param particle_emission: particle emissions corresponding to the
        operationb of the production unit. To be multiplied by the power at
        each time step
        """
        if self.particle_emission is None:
            # Adding particle_emission from production
            self.particle_emission = Quantity(
                name='particle_emission',
                description='Dynamic particle_emission generated by the '
                            'ProductionUnit',
                lb=0, vlen=self.time.LEN, parent=self)

            if isinstance(particle_emission, (int, float)):
                self.calc_particle_emission = DefinitionDynamicConstraint(
                    exp_t='{0}_particle_emission[t] == {1} * '
                          '{0}_p[t] * time.DT'.format(self.name,
                                                      particle_emission),
                    name='calc_particle_emission', parent=self)
            elif isinstance(particle_emission, list):
                if len(particle_emission) != self.time.LEN:
                    raise IndexError(
                        "Your particle emission (particle_emission)"
                        "should be the size of "
                        "the time period. The time period is of {0} and your "
                        "particle_emission have a size of {1}".format(
                            self.time.LEN,
                            len(particle_emission)))
                else:
                    self.calc_particle_emission = DefinitionDynamicConstraint(
                        exp_t='{0}_particle_emission[t] == {1}[t] * '
                              '{0}_p[t] * time.DT'.format(self.name,
                                                          particle_emission),
                        name='calc_particle_emission', parent=self)
            else:
                raise TypeError('particle_emission should be an int, a float '
                                'or a list.')
        else:
            raise ValueError("The ProductionUnit {} already has "
                             "particle_emission defined.".format(self.name))


class FixedProductionUnit(FixedEnergyUnit, ProductionUnit):
    """
    **Description**

        Production unit with a fixed production profile.

    **Attributes**

     * p : instantaneous power production known by advance (kW)
     * energy_type : type of energy ('Electrical', 'Heat', ...)


    """

    def __init__(self, time, name: str, p: list or dict or pd.DataFrame = None,
                 co2_out=None, particle_emission=None,
                 starting_cost=None, operating_cost=None, energy_type=None,
                 rr_energy=False,
                 verbose=True):
        ProductionUnit.__init__(self, time=time, name=name,
                                rr_energy=rr_energy,
                                particle_emission=particle_emission,
                                verbose=verbose)
        FixedEnergyUnit.__init__(self, time, name=name, p=p,
                                 flow_direction='out',
                                 starting_cost=starting_cost,
                                 operating_cost=operating_cost, co2_out=co2_out,
                                 energy_type=energy_type,
                                 verbose=False)


class VariableProductionUnit(VariableEnergyUnit, ProductionUnit):
    """
    **Description**

        Production unit with a variation of power between p_min et p_max.

    **Attributes**

     * p_max : maximal instantaneous power production (kW)
     * p_min : minimal instantaneous power production (kW)
     * energy_type : type of energy ('Electrical', 'Heat', ...)

    """

    def __init__(self, time, name, p_min=0, p_max=1e+5, e_min=None,
                 e_max=None, co2_out=None,
                 particle_emission=None, starting_cost=None,
                 operating_cost=None, min_time_on=None, min_time_off=None,
                 max_ramp_up=None, max_ramp_down=None, energy_type=None,
                 rr_energy=False,
                 verbose=True, no_warn=True):
        ProductionUnit.__init__(self, time=time, name=name,
                                rr_energy=rr_energy,
                                particle_emission=particle_emission,
                                verbose=verbose)
        VariableEnergyUnit.__init__(self, time, name=name,
                                    flow_direction='out', p_min=p_min,
                                    p_max=p_max, e_min=e_min, e_max=e_max,
                                    starting_cost=starting_cost,
                                    operating_cost=operating_cost,
                                    min_time_on=min_time_on,
                                    min_time_off=min_time_off,
                                    max_ramp_up=max_ramp_up,
                                    max_ramp_down=max_ramp_down,
                                    co2_out=co2_out, energy_type=energy_type,
                                    verbose=False,
                                    no_warn=no_warn)


class SeveralProductionUnit(VariableProductionUnit, SeveralEnergyUnit):
    """
    **Description**

        Production unit based on a fixed production curve enabling to multiply
        several times (nb_unit) the same production curve.
        nb_unit is an integer variable.

    **Attributes**

     * fixed_prod : fixed production curve

    """

    def __init__(self, time, name, fixed_prod, imaginary=False,
                 p_min=0, p_max=1e+5, e_min=None, e_max=None,
                 nb_unit_min=0, nb_unit_max=None, co2_out=None,
                 particle_emission=None,
                 starting_cost=None, operating_cost=None, max_ramp_up=None,
                 max_ramp_down=None, energy_type=None, rr_energy=False,
                 verbose=True, no_warn=True):
        VariableProductionUnit.__init__(self, time=time, name=name,
                                        rr_energy=rr_energy,
                                        particle_emission=particle_emission,
                                        verbose=verbose)
        SeveralEnergyUnit.__init__(self, time, name=name,
                                   fixed_power=fixed_prod,
                                   imaginary=imaginary, p_min=p_min,
                                   p_max=p_max, e_min=e_min,
                                   e_max=e_max, nb_unit_min=nb_unit_min,
                                   nb_unit_max=nb_unit_max,
                                   flow_direction='out',
                                   starting_cost=starting_cost,
                                   operating_cost=operating_cost,
                                   max_ramp_up=max_ramp_up,
                                   max_ramp_down=max_ramp_down,
                                   co2_out=co2_out, energy_type=energy_type,
                                   verbose=False,
                                   no_warn=no_warn)


class SquareProductionUnit(SquareEnergyUnit, VariableProductionUnit):
    """
    **Description**

        | Production unit with a fixed value and fixed duration.
        | Only the time of beginning can be modified.
        | Operation can be mandatory or not.

    **Attributes**

     * p : instantaneous power production (kW)
     * duration : duration of the power delivery (hours)
     * mandatory : indicates if the power delivery is mandatory or not
     * energy_type : type of energy ('Electrical', 'Heat', ...)

    """

    def __init__(self, time, name, p_square, duration, n_square,
                 t_between_sq, co2_out=None,
                 particle_emission=None, starting_cost=None,
                 operating_cost=None, energy_type=None, rr_energy=False,
                 verbose=True, no_warn=True):
        duration /= time.DT
        if duration < 1:
            raise ValueError('The duration of operation of the '
                             'SquareProductionUnit should be longer than the '
                             'time step.')
        VariableProductionUnit.__init__(self, time=time, name=name,
                                        rr_energy=rr_energy,
                                        particle_emission=particle_emission,
                                        verbose=verbose)
        SquareEnergyUnit.__init__(self, time, name=name, p_square=p_square,
                                  n_square=n_square, t_square=duration,
                                  t_between_sq=t_between_sq,
                                  flow_direction='out',
                                  starting_cost=starting_cost,
                                  operating_cost=operating_cost,
                                  co2_out=co2_out, energy_type=energy_type,
                                  verbose=False,
                                  no_warn=no_warn)


class ShiftableProductionUnit(ShiftableEnergyUnit, VariableProductionUnit):
    """
    **Description**

        Production unit with shiftable production profile.

    **Attributes**

     * power_values : production profile to shift (kW)
     * mandatory : indicates if the production is mandatory : True
       or not : False
     * starting_cost : cost of the starting of the production
     * operating_cost : cost of the operation (€/kW)
     * energy_type : type of energy ('Electrical', 'Heat', ...)

    """

    def __init__(self, time, name: str, power_values, mandatory=True,
                 co2_out=None, particle_emission=None, starting_cost=None,
                 operating_cost=None,
                 energy_type=None, rr_energy=False, verbose=True):

        VariableProductionUnit.__init__(self, time=time, name=name,
                                        rr_energy=rr_energy,
                                        particle_emission=particle_emission,
                                        verbose=verbose)
        ShiftableEnergyUnit.__init__(self, time, name=name,
                                     flow_direction='out',
                                     power_values=power_values,
                                     mandatory=mandatory, co2_out=co2_out,
                                     starting_cost=starting_cost,
                                     operating_cost=operating_cost,
                                     energy_type=energy_type,
                                     verbose=False)
