#! usr/bin/env python3
#  coding=utf-8 #

"""
**This module defines the electric vehicle units**

 The electric_vehicle_unit module defines electric vehicle units with
 associated attributes and methods, from simple to specific ones.

 It includes :
    - ElectricVehicleUnit: simple electric vehicle unit inheriting from storage unit,
      consumption unit, and energy node, with electric vehicle specific attributes.
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

from .energy_units import AssemblyUnit
from .reversible_units import ReversibleUnit
from .consumption_units import FixedConsumptionUnit
from .storage_units import StorageUnit
from ...general.optimisation.elements import *
import warnings

__docformat__ = "restructuredtext en"


class ElectricVehicleUnit(AssemblyUnit):
    """
    **Description**

        Electric Vehicle unit


    **Attributes** TODO

     * charge (VariableConsumptionUnit) : represents the charge part of the
     storage unit
     * discharge (VariableProductionUnit) : represents the discharge part of
     the storage unit
     * capacity (Quantity): maximal energy that can be stored [kWh]
     * e (Quantity): energy at time t in the storage [kWh]
     * p (Quantity): power at time t in the storage [kW]
     * e (Quantity): energy at time t in the storage [Binary]
     * set_soc_min (TechnicalDynamicConstraint): constraining the energy to be
       above the value : soc_min*capacity
     * set_soc_max (TechnicalDynamicConstraint): constraining the energy to be
       below the value : soc_max*capacity
       storage unit : 0 : Not charging & 1 : charging
     * calc_e (DefinitionDynamicConstraint) : energy calculation at time t ;
       relation power/energy
     * calc_p (DefinitionDynamicConstraint) : power calculation at time t ;
     power
       flow equals charging power minus discharging power
     * on_off_stor (DefinitionDynamicConstraint) : making u[t] matching with
       storage modes (on/off)
     * set_e_0 (ActorConstraint) : set the energy state for t=0
     * e_f (Quantity) : energy in the storage at the end of the time
       horizon, i.e. after the last time step [kWh]
     * e_f_min (TechnicalConstraint) : e_f value is constrained above
       soc_min*capacity
     * e_f_max (TechnicalConstraint) : e_f value is constrained below
       soc_max*capacity
     * set_e_f (ActorConstraint) : when e_f is given, it is set in the
       same way the energy is, but after the last time step
     * calc_e_f (DefinitionConstraint) : when e_f is not given,
       it is calculated in the same way the energy is, but after the last
       time step
     * ef_is_e0 (TechnicalConstraint) : Imposing ef=e0 on the time period.
     * cycles (TechnicalDynamicConstraint) : setting a cycle constraint
       e[t] = e[t+cycles/dt]

    """

    def __init__(self, time, name, disconnection_profile=None,
                 usage_profile=None, pc_min=None, pc_max=None,
                 pd_min=None, pd_max=None, capacity=None, e_0=None,
                 e_f=None, soc_min=0, soc_max=1, eff_c=1, eff_d=1,
                 self_disch=0, self_disch_t=0, ef_is_e0=False,
                 energy_type=None,verbose=True):
        """ TODO
        :param time: TimeUnit describing the studied time period
        :param name: name of the storage unit
        :param pc_min: minimal charging power [kW]
        :param pc_max: maximal charging power [kW], if not assigned,
        if storage capacity isn't a optimization variable, its value is
        equal to the capacity vlalue
                        if storage capacity is a optimisation variable,
                        pc_max also is an optimisation variable
        :param pd_min: minimal discharging power [kW]
        :param pd_max: maximal discharging power [kW], if not assigned,
        if storage capacity isn't a optimization variable, its value is
        equal to the capacity vlalue
                        if storage capacity is a optimisation variable,
                        pd_max also is an optimisation variable
        :param capacity: maximal energy that can be stored [kWh]
        :param e_0: initial level of energy [kWh]
        :param e_f: final level of energy [kWh]
        :param soc_min: minimal state of charge [pu]
        :param soc_max: maximal state of charge [pu]
        :param eff_c: charging efficiency
        :param eff_d: discharging efficiency
        :param self_disch: part of the capacity that is self-discharging [pu/h]
        :param self_disch_t: part of the energy that is self-discharging [pu/h]
        :param ef_is_e0: binary describing whether the storage is working at
        constant energy during the entire time period (e_0=e_f) or not.
        """


        if disconnection_profile is None:
            warnings.warn("The disconnection profile has not been provided,"
                          "The vehicle will be 100% plugged in for the entire period")
            disconnection_profile = [0] * time.LEN

        if usage_profile is None:
            warnings.warn("The usage profile of the vehicle has not been provided"
                          "No external consumption or charging profile will be applied")
            usage_profile = [0] * time.LEN

        unconsistentTimeSteps = []
        for t in range(time.LEN):
            if usage_profile[t] != 0 and disconnection_profile[t] == 0:
                unconsistentTimeSteps.append(t)
            if usage_profile[t] > pd_max or -usage_profile[t] > pc_max:
                raise ValueError('The usage profile exceeds the charging or discharging capacity '
                                 'of the vehicle at time step {}.'.format(t))

        if len(unconsistentTimeSteps)>0:
            warnings.warn("The usage profile and the disconnectionprofile of the vehicle may be unconsistent"
                          "The vehicle is used while connected at time steps {}.".format(unconsistentTimeSteps))

        self.battery = StorageUnit(time=time, name="{}_battery".format(name), pc_min=pc_min, pc_max=pc_max,
                                   pd_min=pd_min,
                                   pd_max=pd_max, capacity=capacity, e_0=e_0, e_f=e_f, soc_min=soc_min,
                                   soc_max=soc_max, eff_c=eff_c, eff_d=eff_d, self_disch=self_disch,
                                   self_disch_t=self_disch_t, ef_is_e0=ef_is_e0)

        #Converting the usage signal into a consumption and a production signal for the definition
        cons_profile=[c if c>0 else 0 for c in usage_profile]
        prod_profile=[-c if c<0 else 0 for c in usage_profile]
        self.usage = ReversibleUnit(time=time, name="{}_usage".format(name),p_cons=cons_profile,p_prod=prod_profile,
                                    energy_type_cons=energy_type,energy_type_prod=energy_type,verbose=verbose)

        self.set_max_export = [max_export * avail for avail in availability]
        self.set_max_import = [max_import * avail for avail in availability]

        self.connector = ReversibleUnit(time=time, name="{}_usage".format(name),
                                   # energy_type_cons=energy_type, energy_type_prod=energy_type, verbose=verbose)






        if pc_max is None:
            if capacity is None:
                pc_max_eq = 1e5
            else:
                pc_max_eq = capacity
                print(
                    "---------------------------------------------------------"
                    "------------------------------")
                print(
                    "pc_max is not defined: the maximum charging power is set"
                    " to the value of the capacity")
                print(
                    "---------------------------------------------------------"
                    "------------------------------")
        else:
            pc_max_eq = pc_max

        if pd_max is None:
            if capacity is None:
                pd_max_eq = 1e5
            else:
                pd_max_eq = capacity
                print(
                    "---------------------------------------------------------"
                    "------------------------------")
                print("pd_max is not defined: the maximum charging power is "
                      "set to the value of the capacity")
                print(
                    "---------------------------------------------------------"
                    "------------------------------")
        else:
            pd_max_eq = pd_max

        self.discharge = VariableProductionUnit(time, name + '_discharge',
                                                p_min=pd_min, p_max=pd_max_eq,
                                                e_min=e_min_disch,
                                                e_max=e_max_disch,
                                                energy_type=energy_type)

        self.charge = VariableConsumptionUnit(time, name + '_charge',
                                              p_min=pc_min, p_max=pc_max_eq,
                                              e_min=e_min_ch, e_max=e_max_ch,
                                              energy_type=energy_type)

        AssemblyUnit.__init__(self, time, name,
                              prod_units=[self.discharge],
                              cons_units=[self.charge])

        # --- Checking the state of charge boundaries of the storage system ---
        if isinstance(soc_min, (float, int)) and isinstance(soc_max, (float,
                                                                      int)):
            if soc_min > soc_max:
                raise ValueError('You cannot have soc_min > soc_max')
            elif soc_min > 1 or soc_min < 0 or soc_max > 1 or soc_max < 0:
                raise ValueError('The soc_min and soc_max values are '
                                 'expressed as percentages of the capacity and'
                                 ' must be set between 0 and 1')
        if soc_min is None or soc_max is None:
            raise ValueError('soc_min and soc_max should not be None')

        self.energy_type = energy_type

        self.capacity = Quantity(name='capacity', unit='kWh', value=capacity,
                                 lb=0, vlen=1, parent=self)

        if capacity is None:
            warnings.warn("If you are not using minimize_capacity, "
                          "the capacity value should be defined")

        self.e = Quantity(name='e', opt=True,
                          description='energy at t in the storage',
                          unit='kWh', vlen=time.LEN,
                          lb=0, ub=capacity, parent=self)

        self.u = Quantity(name='u',
                          description='indicates if the unit is operating '
                                      'at t',
                          vtype=LpBinary, vlen=time.LEN, parent=self)

        self.p = Quantity(name='p', opt=True,
                          description='power at t in the storage',
                          unit='kW', vlen=time.LEN,
                          lb=-pd_max_eq, ub=pc_max_eq, parent=self)

        self.e_tot = Quantity(name='e_tot',
                              description='total energy during the time '
                                          'period', lb=0, ub=capacity, vlen=1,
                              unit='kWh', parent=self)

        self.calc_e_tot = DefinitionConstraint(name='calc_e_tot', parent=self,
                                               exp='{0}_e_tot == time.DT * '
                                                   'lpSum({0}_p[t] for t in '
                                                   'time.I)'
                                               .format(self.name))
        # Giving an equivalent value to pc and pd maximal value in case they
        # are not defined

        self.pc_max = Quantity(name='pc_max', description='maximum charging '
                                                          'power', unit='kW',
                               value=pc_max if pc_max is not None else
                               capacity,
                               lb=0, vlen=1, parent=self)

        self.pd_max = Quantity(name='pd_max', description='maximum '
                                                          'discharging power',
                               unit='kW',
                               value=pd_max if pd_max is not None else
                               capacity,
                               lb=0, vlen=1, parent=self)

        self.self_disch_t = self_disch_t

        if isinstance(soc_min, (int, float)):
            self.set_soc_min = TechnicalDynamicConstraint(
                exp_t='{0}_e[t] >= {1} * {0}_capacity'.format(self.name,
                                                              soc_min),
                name='set_soc_min', parent=self)

        elif isinstance(soc_min, list):
            self.set_soc_min = TechnicalDynamicConstraint(
                exp_t='{0}_e[t] >= {1}[t] * {0}_capacity'.format(self.name,
                                                                 soc_min),
                name='set_soc_min', parent=self)

        if isinstance(soc_max, (int, float)):
            self.set_soc_max = TechnicalDynamicConstraint(
                exp_t='{0}_e[t] <= {1} * {0}_capacity'.format(self.name,
                                                              soc_max),
                name='set_soc_max', parent=self)

        elif isinstance(soc_max, list):
            self.set_soc_max = TechnicalDynamicConstraint(
                exp_t='{0}_e[t] <= {1}[t] * {0}_capacity'.format(self.name,
                                                                 soc_max),
                name='set_soc_max', parent=self)

        # CONSTRAINTS
        # Relation power/energy
        if 0 <= self_disch <= 1 and 0 <= self_disch_t <= 1:
            self.calc_e = \
                DefinitionDynamicConstraint(name='calc_e',
                                            t_range=' for t in time.I[:-1]',
                                            exp_t='{0}_e[t+1] - {0}_e[t]*('
                                                  '1-{1}*time.DT)'
                                                  ' - time.DT * ({5}_p[t]*{3}'
                                                  '- {6}_p[t]*1/{4}- {2}*'
                                                  '{0}_capacity) == 0'
                                            .format(self.name, self_disch_t,
                                                    self_disch,
                                                    eff_c, eff_d,
                                                    self.charge.name,
                                                    self.discharge.name),
                                            parent=self)

        else:
            raise ValueError('self_disch & self_disch_t should have values '
                             'between 0 and 1 and are set to {0} and {1}'
                             .format(self_disch, self_disch_t))

        # Power flow equals charging power minus discharging power
        self.calc_p = DefinitionDynamicConstraint(
            exp_t='{0}_p[t] == {1}_p[t] - {2}_p[t]'.format(self.name,
                                                           self.charge.name,
                                                           self.discharge.name),
            t_range='for t in time.I', name='calc_p', parent=self)

        # For storage, as the power can be both positive and negative,
        # two constraints are needed to make u[t] match with on/off

        self.on_off_stor = DefinitionDynamicConstraint(
            exp_t='{0}_charge_p[t] + {0}_discharge_p[t] - {0}_u[t] * {eps}'
                  ' >= 0'.format(self.name, eps=0.001),
            t_range='for t in time.I',
            name='on_off_stor', parent=self)

        # This constraint forces the discharge to be off when the charge is on

        if self.pc_max.opt:
            self.def_max_discharging = DefinitionDynamicConstraint(
                exp_t='{2}_p[t] - (1 - {1}_u[t]) * 1e5 <= 0'.format(
                    self.name, self.charge.name, self.discharge.name),
                t_range='for t in time.I',
                name='def_max_discharging', parent=self)
        else:
            self.def_max_discharging = DefinitionDynamicConstraint(
                exp_t='{2}_p[t] - (1 - {1}_u[t]) * {0}_pc_max <= 0'.format(
                    self.name, self.charge.name, self.discharge.name),
                t_range='for t in time.I',
                name='def_max_discharging', parent=self)

        # --- Constraints for initial and final states of charge ---
        # Setting the state of charge for t=0
        if e_0 is not None:
            self.set_e_0 = ActorConstraint(name='set_e_0',
                                           exp='{0}_e[0] == {1}'
                                           .format(self.name, e_0),
                                           parent=self)

        # e_f should be in between the boundaries
        # [soc_min*capacity; soc_max*capacity]
        # (even when the capacity is not defined), and the result of the
        # last charging/ discharging powers and losses applied the energy at
        # the last timestep.
        if e_f is not None:
            self.e_f = Quantity(name='e_f', opt=False, value=e_f,
                                description='energy in the storage at the '
                                            'end of the time horizon, i.e.'
                                            ' after the last time step',
                                unit='kWh', vlen=1, lb=0, ub=capacity,
                                parent=self)

            if isinstance(soc_min, (int, float)):
                self.e_f_min = DefinitionConstraint(
                    exp='{0}_e_f >= {1} * {0}_capacity'.format(self.name,
                                                               soc_min),
                    name='e_f_min', parent=self)

            elif isinstance(soc_min, list):
                self.e_f_min = DefinitionConstraint(
                    exp='{0}_e_f >= {1}[{2}] * {0}_capacity'.format(
                        self.name, soc_min, time.I[-1]),
                    name='set_soc_min', parent=self)

            if isinstance(soc_max, (int, float)):
                self.e_f_max = DefinitionConstraint(
                    exp='{0}_e_f <= {1} * {0}_capacity'.format(self.name,
                                                               soc_max),
                    name='e_f_max', parent=self)

            elif isinstance(soc_max, list):
                self.e_f_max = DefinitionConstraint(
                    exp='{0}_e_f <= {1}[{2}] * {0}_capacity'.format(
                        self.name, soc_max, time.I[-1]),
                    name='set_soc_max', parent=self)

            self.set_e_f = ActorConstraint \
                (name='set_e_f',
                 exp='{0}_e_f-{0}_e[{1}] == {2}*({7}_p[{1}]*{3}-'
                     '{8}_p[{1}]*1/{4}-{5}*{0}_e[{1}]-{6}*{0}_capacity)'
                 .format(self.name, time.I[-1], time.DT, eff_c,
                         eff_d, self_disch_t, self_disch,
                         self.charge.name, self.discharge.name), parent=self)
        else:
            self.e_f = Quantity(name='e_f', opt=True,
                                description='energy in the storage at the end '
                                            'of the time horizon, i.e. after '
                                            'the last time step', unit='kWh',
                                vlen=1, lb=0, ub=capacity, parent=self)
            if isinstance(soc_min, (int, float)):
                self.e_f_min = DefinitionConstraint(
                    exp='{0}_e_f >= {1} * {0}_capacity'.format(self.name,
                                                               soc_min),
                    name='e_f_min', parent=self)

            elif isinstance(soc_min, list):
                self.e_f_min = DefinitionConstraint(
                    exp='{0}_e_f >= {1}[{2}] * {0}_capacity'.format(
                        self.name, soc_min, time.I[-1]),
                    name='set_soc_min', parent=self)

            if isinstance(soc_max, (int, float)):
                self.e_f_max = DefinitionConstraint(
                    exp='{0}_e_f <= {1} * {0}_capacity'.format(self.name,
                                                               soc_max),
                    name='e_f_max', parent=self)

            elif isinstance(soc_max, list):
                self.e_f_max = DefinitionConstraint(
                    exp='{0}_e_f <= {1}[{2}] * {0}_capacity'.format(
                        self.name, soc_max, time.I[-1]),
                    name='set_soc_max', parent=self)

            # e_f calculation
            self.calc_e_f = DefinitionConstraint \
                (name='calc_e_f',
                 exp='{0}_e_f-{0}_e[{1}] == {2}*({7}_p[{1}]*{3}-'
                     '{8}_p[{1}]*1/{4}-{5}*{0}_e[{1}]-{6}*{0}_capacity)'
                 .format(self.name, time.I[-1], time.DT, eff_c,
                         eff_d, self_disch_t, self_disch,
                         self.charge.name, self.discharge.name), parent=self)

        # Impose ef_is_e0 on the time period
        if ef_is_e0:
            if e_f is None or e_0 is None or e_f == e_0:
                self.ef_is_e0 = ActorConstraint(
                    exp='{0}_e[0] == {0}_e_f'.format(self.name),
                    name='ef_is_e0', parent=self)
            else:
                raise ValueError('When ef_is_e0 is set to True, e_f OR e_0 '
                                 'should remain set to None')

        if cycles is not None:
            if type(cycles) == int:
                delta_t = int(cycles / time.DT)
                self.set_cycles = TechnicalDynamicConstraint(
                    name='set_cycles',
                    exp_t='{0}_e[t] == {0}_e[t+{1}]'.format(self.name,
                                                            delta_t),
                    t_range='for t in time.I[:-{0}]'.format(delta_t),
                    parent=self)
            else:
                raise TypeError('cycles should be an integer : number of '
                                'hours between cycling (e[t] = e[t+cycles/dt]')

    # OBJECTIVES
    def minimize_capacity(self, pc_max_ratio: float = None,
                          pd_max_ratio: float = None,
                          weight=1):

        """
        Objective of minimizing the capacity. If pc_max_ratio and
        pd_max_ratio are set AND pc_max and pd_max have None value in the
        StorageUnit, pc_max and pd_max are constrained to have values in
        accordance with the given ratio of the capacity.

        :param weight: Weight coefficient for the objective
        :param pc_max_ratio : ratio of the capacity for pc_max value i.e. if
        pc_max_ratio is 1/2, pc_max = capacity / 2. This ratio should be
        taken in accordance with the value of the time step.
        :param pd_max_ratio : ratio of the capacity for pd_max value i.e. if
        pd_max_ratio is 1/2, pd_max = capacity / 2. This ratio should be
        taken in accordance with the value of the time step.
        """
        def_capacity = DefinitionDynamicConstraint(
            exp_t='{0}_e[t] <= {0}_capacity'
                .format(self.name),
            t_range='for t in time.I',
            name='def_capacity', parent=self)

        if self.pc_max.opt:
            if pc_max_ratio is None:
                def_pc_max_calc = TechnicalConstraint(
                    exp='{0}_pc_max == {0}_capacity*{1}'.format(
                        self.name, 1), name='def_pc_max_calc',
                    parent=self)
                print(
                    "---------------------------------------------------------"
                    "------------------------------")
                print("pc_max_ratio is not defined: the maximum charging "
                      "power is set to the value of the capacity")
                print(
                    "---------------------------------------------------------"
                    "------------------------------")
                # pc_max definition with the dynamic pc[t]
                def_pc_max = TechnicalDynamicConstraint(exp_t='{1}_p[t] <= '
                                                              '{0}_pc_max'
                                                        .format(self.name,
                                                                self.charge
                                                                .name),
                                                        t_range='for t in '
                                                                'time.I',
                                                        name='def_pc_max',
                                                        parent=self)
                setattr(self, 'def_pc_max', def_pc_max)
                setattr(self, 'def_pc_max_calc', def_pc_max_calc)
            else:
                if isinstance(pc_max_ratio, float):
                    # pc_max calculation with the pc_max_ratio
                    def_pc_max_calc = TechnicalConstraint(
                        exp='{0}_pc_max == {0}_capacity*{1}'.format(
                            self.name, pc_max_ratio), name='def_pc_max_calc',
                        parent=self)
                    # pc_max definition with the dynamic pc[t]
                    def_pc_max = TechnicalDynamicConstraint(
                        exp_t='{1}_p[t] <= '
                              '{0}_pc_max'
                            .format(self.name, self.charge.name),
                        t_range='for t in time.I',
                        name='def_pc_max',
                        parent=self)
                    setattr(self, 'def_pc_max', def_pc_max)
                    setattr(self, 'def_pc_max_calc', def_pc_max_calc)
                else:
                    raise ValueError('pc_max ratio should be a float')

        if self.pd_max.opt:
            if pd_max_ratio is None:
                def_pd_max_calc = TechnicalConstraint(
                    exp='{0}_pd_max == {0}_capacity*{1}'.format(
                        self.name, 1), name='def_pd_max_calc',
                    parent=self)
                print(
                    "---------------------------------------------------------"
                    "------------------------------")
                print("pd_max_ratio is not defined: the maximum charging "
                      "power is set to the value of the capacity")
                print(
                    "---------------------------------------------------------"
                    "------------------------------")
                # pd_max definition with the dynamic pd[t]
                def_pd_max = TechnicalDynamicConstraint(exp_t='{1}_p[t] <= '
                                                              '{0}_pd_max'
                                                        .format(self.name,
                                                                self.discharge
                                                                .name),
                                                        t_range='for t in '
                                                                'time.I',
                                                        name='def_pd_max',
                                                        parent=self)
                setattr(self, 'def_pd_max', def_pd_max)
                setattr(self, 'def_pd_max_calc', def_pd_max_calc)
            else:
                if isinstance(pd_max_ratio, float):
                    # pd_max calculation with the pd_max_ratio
                    def_pd_max_calc = TechnicalConstraint(
                        exp='{0}_pd_max == {0}_capacity*{1}'.format(
                            self.name, pd_max_ratio), name='def_pd_max_calc',
                        parent=self)
                    # pd_max definition with the dynamic pd[t]
                    def_pd_max = TechnicalDynamicConstraint(
                        exp_t='{1}_p[t] <= '
                              '{0}_pd_max'
                            .format(self.name, self.discharge.name),
                        t_range='for t in time.I',
                        name='def_pd_max',
                        parent=self)
                    setattr(self, 'def_pd_max', def_pd_max)
                    setattr(self, 'def_pd_max_calc', def_pd_max_calc)
                else:
                    raise ValueError('pd_max_ratio should be a float')

        min_capacity = Objective(name='min_capacity',
                                 exp='{0}_capacity'.format(self.name),
                                 weight=weight,
                                 parent=self)

        setattr(self, 'def_capacity', def_capacity)
        setattr(self, 'min_capacity', min_capacity)


class StorageUnitTm1(StorageUnit):
    """
    **Description**
        Storage unit where the energy is described at the end of a timestep.
        Calculation :
        e[t]-e[t-1] = dt * (pc[t]*eff_c - pd[t]*1/eff_d - self_disch*capa
        - self_disch_t*e[t])
        In this case, e_f is not defined as a quantity

    **Attributes**
        * capacity (Quantity): maximal energy that can be stored [kWh]
        * e (Quantity): energy at time t in the storage [kWh]
        * set_soc_min (DynamicConstraint): constraining the energy to be
        above the value : soc_min*capacity
        * set_soc_max (DynamicConstraint): constraining the energy to be
        below the value : soc_max*capacity
        * pc (Quantity) : charging power [kW]
        * pd (Quantity) : discharging power [kW]
        * uc (Quantity) : binary variable describing the charge of the
        storage unit : 0 : Not charging & 1 : charging
        * calc_e (DynamicConstraint) : energy calculation at time t ;
        relation power/energy
        * calc_p (DynamicConstraint) : power calculation at time t ; power
        flow equals charging power minus discharging power
        * on_off_stor (DynamicConstraint) : making u[t] matching with
        storage modes (on/off)
        * def_max_charging (DynamicConstraint) : defining the max charging
        power, avoiding charging and discharging at the same time
        * def_max_discharging (DynamicConstraint) : defining the max
        discharging power, avoiding charging and discharging at the same time
        * def_min_charging (DynamicConstraint) : defining the min charging
        power, avoiding charging and discharging at the same time
        * def_min_discharging (DynamicConstraint) : defining the min
        discharging power, avoiding charging and discharging at the same time
        * set_e_0 (ExternalConstraint) : set the energy state for t=0
        * set_e_f (ExternalConstraint) : set the energy state for the last
        time step
        * ef_is_e0 (ExternalConstraint) : Imposing ef=e0 on the time period.
        * cycles (ExternalDynamicConstraint) : setting a cycle constraint
        e[t] = e[t+cycles/dt]

    """

    def __init__(self, time, name='StUtm1', pc_min=1e-5, pc_max=1e+5,
                 pd_min=1e-5, pd_max=1e+5, capacity=None, e_0=None,
                 e_f=None, soc_min=0, soc_max=1, eff_c=1, eff_d=1,
                 self_disch=0, self_disch_t=0, ef_is_e0=False, cycles=None,
                 energy_type=None, operator=None):
        """
        :param time: TimeUnit describing the studied time period
        :param name: name of the storage unit
        :param pc_min: minimal charging power [kW]
        :param pc_max: maximal charging power [kW]
        :param pd_min: minimal discharging power [kW]
        :param pd_max: maximal discharging power [kW]
        :param capacity: maximal energy that can be stored [kWh]
        :param e_0: initial level of energy [kWh]
        :param e_f: final level of energy [kWh]
        :param soc_min: minimal state of charge [pu]
        :param soc_max: maximal state of charge [pu]
        :param eff_c: charging efficiency
        :param eff_d: discharging efficiency
        :param self_disch: part of the capacity that is self-discharging [pu/h]
        :param self_disch_t: part of the energy that is self-discharging [pu/h]
        :param ef_is_e0: binary describing whether the storage is working at
        constant energy during the entire time period (e_0=e_f) or not.
        :param cycles: number of hours between cycling (e[t] = e[t+cycles/dt]
        :param energy_type: energy type the storage unit is used with
        :param operator: operator of the storage unit
        """

        StorageUnit.__init__(self, time, name=name, pc_min=pc_min,
                             pc_max=pc_max, pd_min=pd_min, pd_max=pd_max,
                             capacity=capacity, e_0=e_0, e_f=e_f,
                             soc_min=soc_min, soc_max=soc_max, eff_c=eff_c,
                             eff_d=eff_d, self_disch=self_disch,
                             ef_is_e0=ef_is_e0, energy_type=energy_type,
                             operator=operator)

        # CONSTRAINTS
        # Relation power/energy
        if 0 <= self_disch <= 1 and 0 <= self_disch_t <= 1:
            self.calc_e = \
                DynamicConstraint(name='calc_e',
                                  t_range=' for t in time.I[1:]',
                                  exp_t='{0}_e[t]*(1+{1}*time.DT) - {0}_e[t-1]'
                                        ' - time.DT * ({5}_p[t]*{3}- '
                                        '{6}_p[t]*1/{4}- {2}*'
                                        '{0}_capacity) == 0'
                                  .format(self.name, self_disch_t, self_disch,
                                          eff_c, eff_d, self.charge.name,
                                          self.discharge.name), parent=self)

        else:
            raise ValueError('self_disch & self_disch_t should have values '
                             'between 0 and 1 and are set to {0} and {1}'
                             .format(self_disch, self_disch_t))

        # --- External constraints for initial and final states of charge ---
        # Setting the state of charge for t=0
        if e_0 is not None:
            self.set_e_0 = ExternalConstraint(name='set_e_0',
                                              exp='{0}_e[0] == {1}'
                                              .format(self.name, e_0),
                                              parent=self)

        # Setting the state of charge for t=t_end
        # No e_f management here since the energy calculation goes from the
        # second time step to the last : e_f is already in the energy
        # calculation.
        self.e_f_min.active = False
        self.e_f_max.active = False
        if e_f is not None:
            self.set_e_f.exp = '{0}_e[time.I[-1]] == {0}_e_f'.format(self.name)
        else:
            self.e_f.opt = False
            self.calc_e_f.active = False

        # Impose ef_is_e0 on the time period
        if ef_is_e0:
            if e_f is None or e_0 is None or e_f == e_0:
                self.ef_is_e0.exp = '{0}_e[0] == {0}_e[time.I[-1]]'.format(
                    self.name)


class ThermoclineStorage(StorageUnit):
    """
    **Description**

        Class ThermoclineStorage : class defining a thermocline heat storage,
        inheriting from StorageUnit.

    **Attributes**

        * is_soc_max (Quantity) : indicating if the storage is fully charged
          0:No 1:Yes
        * def_is_soc_max_inf (DynamicConstraint) : setting the right value
          for is_soc_max
        * def_is_soc_max_sup (DynamicConstraint) : setting the right value
          for is_soc_max
        * force_soc_max (TechnicalDynamicConstraint) : The energy has to be
        at least
          once at its maximal value during the period Tcycl.
    """

    def __init__(self, time, name, pc_min=1e-5, pc_max=1e+5,
                 pd_min=1e-5, pd_max=1e+5,
                 capacity=None, e_0=None, e_f=None, soc_min=0,
                 soc_max=1, eff_c=1, eff_d=1, self_disch=0, e_min_ch=None,
                 e_max_ch=None, e_min_disch=None, e_max_disch=None,
                 Tcycl=120, ef_is_e0=False):
        """
        :param time: TimeUnit describing the studied time period
        :param name: name of the storage unit
        :param pc_min: minimal charging power [kW]
        :param pc_max: maximal charging power [kW]
        :param pd_min: minimal discharging power [kW]
        :param pd_max: maximal discharging power [kW]
        :param capacity: maximal energy that can be stored [kWh]
        :param e_0: initial level of energy [kWh]
        :param e_f: final level of energy [kWh]
        :param soc_min: minimal state of charge [pu]
        :param soc_max: maximal state of charge [pu]
        :param eff_c: charging efficiency
        :param eff_d: discharging efficiency
        :param self_disch: part of the soc that is self-discharging [pu]
        :param Tcycl: period over which the storage is cycling (reaching at
        least once its max state of charge) [hours]
        :param e_min: minimal energy consumed by the storage on the whole
        studied period
        :param e_max: maximal energy consumed by the storage on the whole
        studied period
        :param ef_is_e0: binary describing whether the storage is working at
        constant energy during the entire time period (e_0=e_f) or not.
         """
        StorageUnit.__init__(self, time, name=name, pc_min=pc_min,
                             pc_max=pc_max, pd_min=pd_min, pd_max=pd_max,
                             capacity=capacity, e_0=e_0, e_f=e_f,
                             soc_min=soc_min, soc_max=soc_max, eff_c=eff_c,
                             eff_d=eff_d, self_disch=self_disch,
                             ef_is_e0=ef_is_e0, e_min_ch=e_min_ch,
                             e_max_ch=e_max_ch, e_min_disch=e_min_disch,
                             e_max_disch=e_max_disch, energy_type='Thermal')

        # DECISION VARIABLES AND PARAMETERS
        # Creation of quantities needed for the Thermocline model
        self.is_soc_max = Quantity(name='is_soc_max', opt=True, vlen=time.LEN,
                                   vtype=LpBinary,
                                   description='indicates if the storage is '
                                               'fully charged 0:No 1:Yes',
                                   parent=self)

        # CONSTRAINTS
        # Thermocline constraints for charge and discharge
        # Set when we are at the maximal state of charge (soc_max) or not
        epsilon = 0.1

        self.def_is_soc_max_inf = DefinitionDynamicConstraint(
            exp_t='{0}_capacity * {0}_is_soc_max[t] >= ({0}_e[t] - '
                  '{0}_capacity + {1})'.format(self.name, epsilon),
            t_range='for t in time.I', name='def_is_soc_max_inf', parent=self)

        self.def_is_soc_max_sup = DefinitionDynamicConstraint(
            exp_t='{0}_capacity * {0}_is_soc_max[t] <= '
                  '{0}_e[t]'.format(self.name), t_range='for t in time.I',
            name='def_is_soc_max_sup', parent=self)

        # The soc has to be at least one time at soc_max during 5 days
        self.force_soc_max = TechnicalDynamicConstraint(
            exp_t='lpSum({0}_is_soc_max[k] for k in range(t-{1}+1, t)) '
                  '>= 1'.format(self.name, round(Tcycl / time.DT)),
            t_range='for t in time.I[{0}:]'.format(round(Tcycl / time.DT)),
            name='force_soc_max', parent=self)
