#! usr/bin/env python3
#  -*- coding: utf-8 -*-


"""
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
import pandas as pd
from omegalpes.energy.energy_nodes import EnergyNode
from omegalpes.energy.units.consumption_units import FixedConsumptionUnit, ShiftableConsumptionUnit
from omegalpes.energy.units.conversion_units import HeatPump
from omegalpes.energy.buildings.thermal import HeatingLoad, ThermalZone, \
    ZEA_RCNetwork_1

from weather_data import import_weather_data
from utils import convert_hourly_data_into_mean_values


def create_rc_network(time, rc_name, T_ext, A_f, A_w, A_ext_v, A_roof,
                      footprint, U_win, U_wall, U_roof, U_base, construction,
                      floors, e_win=None, e_wall=None, e_roof=None,
                      a_wall=None, a_roof=None):
    """

    :param time:
    :param rc_name:
    :param T_ext:
    :param A_f:
    :param A_w:
    :param A_ext_v:
    :param A_roof:
    :param footprint:
    :param U_win:
    :param U_wall:
    :param U_roof:
    :param U_base:
    :param construction:
    :param floors:
    :param e_win:
    :param e_wall:
    :param e_roof:
    :param a_wall:
    :param a_roof:
    :return:
    """

    rc_network = ZEA_RCNetwork_1(time, name=rc_name, T_ext=T_ext,
                                 A_f=A_f, A_win=A_w, Aext_v=A_ext_v,
                                 A_roof=A_roof, footprint=footprint,
                                 U_win=U_win, U_wall=U_wall, U_roof=U_roof,
                                 U_base=U_base, construction=construction,
                                 floors=floors, e_roof=e_roof, e_win=e_win,
                                 e_wall=e_wall, a_roof=a_roof, a_wall=a_wall,
                                 f_hc_cv=0.5)
    return rc_network


def create_thermal_zone(phi_i_a, phi_i_l, phi_i_p, Isol_av, Fsh_win,
                        T_dew, T_mean, rc_network):
    """

    :param phi_i_a:
    :param phi_i_l:
    :param phi_i_p:
    :param Isol_av:
    :param Fsh_win:
    :param T_dew:
    :param T_mean:
    :param rc_network:
    :return:
    """

    tz = ThermalZone(rc_network, phi_i_a=phi_i_a, phi_i_l=phi_i_l,
                     phi_i_p=phi_i_p, I_sol_av=Isol_av, T_mean=T_mean,
                     T_dew=T_dew, Fsh_win=Fsh_win)
    return tz


def create_single_heating_load(time, bld_name, P_max, T_set, phi_i_a, phi_i_l,
                               phi_i_p, I_sol_av, A_f, A_w, A_ext_v, A_roof,
                               footprint, U_win, U_wall, U_roof, U_base,
                               construction, floors, T_ext, T_dew, Fsh_win,
                               e_win, e_wall, e_roof, a_wall,
                               a_roof, temp_margin=1, T_mean=None):
    """

    :param time:
    :param bld_name:
    :param P_max:
    :param T_set:
    :param phi_i_a:
    :param phi_i_l:
    :param phi_i_p:
    :param phi_s:
    :param A_f:
    :param A_w:
    :param A_ext:
    :param A_roof:
    :param footprint:
    :param U_win:
    :param U_wall:
    :param U_roof:
    :param U_base:
    :param construction:
    :param wwr:
    :param floors:
    :param T_ext:
    :param T_dew:
    :param T_mean:
    :return:
    """

    if T_mean is None:
        T_mean = T_set

    # Creation of the RC network
    rc_name = "RC_" + bld_name
    rc_network = create_rc_network(time, rc_name, T_ext, A_f, A_w, A_ext_v,
                                   A_roof, footprint, U_win, U_wall, U_roof,
                                   U_base, construction, floors, e_win=e_win,
                                   e_wall=e_wall, e_roof=e_roof,
                                   a_wall=a_wall, a_roof=a_roof)

    # Creation of the thermal zone
    tz = create_thermal_zone(phi_i_a, phi_i_l, phi_i_p,  I_sol_av, Fsh_win,
                             T_dew, T_mean, rc_network)

    # Creation of the heating load
    hl_name = 'HL_' + bld_name
    heating_load = HeatingLoad(time, hl_name, tz, p_max=P_max, T_set=T_set,
                               temp_margin=temp_margin)

    return heating_load


def create_all_heating_nodes_with_fixed_consumption(time,
                                                    bld_df,
                                                    bld_load_profiles_df,
                                                    pac='all',
                                                    pmax_hp_elec=500):
    if pac == 'all':
        heating_nodes = []
        for k in range(len(bld_df)):
            name = bld_df.at[k, 'Name']
            cop = float(bld_df.at[k, 'COP'])
            pmax = float(bld_df.at[k, 'P_max'])*2

            power_profile = list(bld_load_profiles_df['HL_' + name])
            new_load = FixedConsumptionUnit(time, name=name, energy_type='Thermal',
                                            p=power_profile)

            # Creation of the heat pump
            heat_pump = HeatPump(time, 'heat_pump_{}_'.format(k),
                                 pmax_in_elec=1e9, cop=cop)    # pmax_out_heat

            heat_pump.thermal_production_unit.add_max_ramp_up(pmax/2)

            # Creation of the heat node for the building heating
            bld_heat_node = EnergyNode(time, 'bld_heat_node_{}_'.format(k),
                                       energy_type='Thermal')
            bld_heat_node.connect_units(heat_pump.thermal_production_unit, new_load)

            heating_nodes.append(bld_heat_node)

        return heating_nodes

    elif pac == 1:

        # Creation of the heat pump
        heat_pump = HeatPump(time, 'heat_pump', pmax_in_elec=pmax_hp_elec,
                             cop=5)
        heat_pump.thermal_production_unit.e_tot.ub = 1e12
        heat_pump.thermal_production_unit.add_max_ramp_up(5*pmax_hp_elec / 2)

        # Creation of the total load
        power_profile = pd.read_csv(
            'results/cambridge_ref_scenario_2_results.csv',
                                    delimiter=';')
        total_load = FixedConsumptionUnit(time, name='all_loads',
                                          energy_type='thermal',
                                          p=list(power_profile['tot'])[
                                            0:time.LEN])
        heating_loads = [total_load] + [heat_pump.thermal_production_unit]

        return heating_loads


def create_all_heating_nodes(time, bld_df, temp_margin=1, Tset=20):
    # Import weather data
    T_ext, T_dew, Isol_av = import_weather_data(time)

    gains_df = pd.read_csv('./data/internal_gains.csv', delimiter=';',
                           header=[0, 1])
    gains_df = gains_df.iloc[0:time.LEN]
    temp_df = pd.read_csv('./data/csv_temperature.csv')

    # T_set = Tset

    # Creating the heating loads
    heating_nodes = []
    electrical_units = []
    for k in range(len(bld_df)):
        name = bld_df.at[k, 'Name']
        pmax = float(bld_df.at[k, 'P_max'])*2
        cop = float(bld_df.at[k, 'COP'])
        # Tset = float(bld_df.at[k, 'T_set'])
        T_set = temp_df[name].fillna(method='ffill').astype(float).to_list()
        Af = float(bld_df.at[k, 'A_f'])
        Aw = float(bld_df.at[k, 'A_w'])
        Aext_v = float(bld_df.at[k, 'A_ext_v'])
        Aroof = float(bld_df.at[k, 'A_roof'])
        footprint = float(bld_df.at[k, 'footprint'])
        Uroof = float(bld_df.at[k, 'U_roof'])
        Uwin = float(bld_df.at[k, 'U_win'])
        Uwall = float(bld_df.at[k, 'U_wall'])
        Ubase = float(bld_df.at[k, 'U_base'])
        construction = bld_df.at[k, 'construction']
        floors = int(bld_df.at[k, 'floors'])

        Fsh_win = float(bld_df.at[k, 'Fsh_win'])
        e_win = float(bld_df.at[k, 'e_win'])
        e_wall = float(bld_df.at[k, 'e_wall'])
        e_roof = float(bld_df.at[k, 'e_roof'])
        a_wall = float(bld_df.at[k, 'a_wall'])
        a_roof = float(bld_df.at[k, 'a_roof'])

        bld_gain_df = gains_df[name]

        phi_i_a = list(bld_gain_df['machine_gains'])
        phi_i_l = list(bld_gain_df['light_gains'])
        phi_i_p = list(bld_gain_df['human_gains'])

        # phi_i_a = convert_hourly_data_into_mean_values(phi_i_a, time.DT)
        # phi_i_l = convert_hourly_data_into_mean_values(phi_i_l, time.DT)
        # phi_i_p = convert_hourly_data_into_mean_values(phi_i_p, time.DT)
        
        T_mean = sum(T_set)/len(T_set)
    

        new_load = create_single_heating_load(time, bld_name=name,
                                              P_max=pmax, T_set=T_set,
                                              phi_i_a=phi_i_a, phi_i_l=phi_i_l,
                                              phi_i_p=phi_i_p, I_sol_av=Isol_av,
                                              A_f=Af, A_w=Aw, A_ext_v=Aext_v,
                                              A_roof=Aroof, footprint=footprint,
                                              U_win=Uwin, U_wall=Uwall,
                                              U_roof=Uroof, U_base=Ubase,
                                              construction=construction,
                                              floors=floors, Fsh_win=Fsh_win,
                                              T_ext=T_ext, T_dew=T_dew,
                                              T_mean=T_mean,
                                              temp_margin=temp_margin,
                                              a_roof=a_roof, a_wall=a_wall,
                                              e_roof=e_roof, e_wall=e_wall,
                                              e_win=e_win)

        # Creation of the heat pump
        heat_pump = HeatPump(time, 'heat_pump_{}_'.format(k),
                             pmax_in_elec=pmax, cop=cop)    # pmax_out_heat
        # Creation of the heat pump
        # heat_pump = HeatPump(time, 'heat_pump_{}_'.format(k),pmax_in_elec=1e4,
        #                      pmax_out_therm=pmax, cop=cop)    # pmax_out_heat

        # heat_pump.elec_consumption_unit.max_ramp_up = pmax/5
        # heat_pump.elec_consumption_unit.max_ramp_down = pmax/5
        heat_pump.thermal_production_unit._add_max_ramp_up(pmax/2)
        heat_pump.thermal_production_unit._add_max_ramp_down(pmax/2)

        # Creation of the heat node for the building heating
        bld_heat_node = EnergyNode(time, 'bld_heat_node_{}_'.format(k),
                                   energy_type='Thermal')

        bld_heat_node.connect_units(heat_pump.thermal_production_unit, new_load)

        heating_nodes.append(bld_heat_node)
        

    return heating_nodes



