#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
..
    Copyright 2018 G2Elab / MAGE
    
    Licensed under the Aheat_pumphe License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
         http://www.aheat_pumphe.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import pandas as pd
from pulp import GUROBI_CMD
from omegalpes.general.optimisation.model import OptimisationModel, compute_gurobi_IIS
from omegalpes.general.time import TimeUnit
from omegalpes.general.utils import select_csv_file_between_dates
from omegalpes.energy.energy_nodes import EnergyNode
from omegalpes.energy.units.production_units import ProductionUnit
from omegalpes.energy.units.conversion_units import \
    ElectricalToHeatConversionUnit, HeatPump
from Chapitre_3.heat_elements import create_heat_dissipation, create_heat_storage
from Chapitre_4.Cas_Cambridge.heat_load_creation import create_all_heating_loads


def create_lncmi_node(unit='MW'):
    global lncmi, heat_dissipation

    # Import LNCMI consumption data
    lncmi_df = select_csv_file_between_dates('data/cons_lncmi_v6_10_min.csv',
                                             sep=';', start=time.DATES[0],
                                             end=time.DATES[-1])
    if unit == 'kW':
        p_in_elec = list(lncmi_df)
    elif unit == 'MW':
        p_in_elec = [p/1000 for p in lncmi_df]

    # Creation of the LNCMI
    lncmi = ElectricalToHeatConversionUnit(time, name='lncmi',
                                           p_in_elec=p_in_elec,
                                           elec_to_heat_ratio=0.85)
    # Creation of the heat dissipation
    heat_dissipation = create_heat_dissipation(time, ill_on=False, unit=unit)

    # Creation of the heat node after the LNCMI magnets
    magnets_heat_node = EnergyNode(time, 'sortie_aim', energy_type='Heat')
    magnets_heat_node.connect_units(lncmi.heat_production_unit,
                                    heat_dissipation)

    return magnets_heat_node


def create_scenario_reference(time, pmin_elec_hp, pmax_elec_hp,
                    cop_hp, bld_df, unit='kW'):
    """
        Permet de déterminer la conso de référence des bâtiments
    :param time:
    :param pmin_elec_hp:
    :param pmax_elec_hp:
    :param cop_hp:
    :param bld_df:
    :param unit:
    :return:
    """
    # Creation of the heat pump
    heat_pump = HeatPump(time, 'heat_pump', pmin_in_elec=pmin_elec_hp,
                         pmax_in_elec=pmax_elec_hp, cop=cop_hp)

    # Adding constraint on the energy provided by the ground water
    #

    # Creation of the heating loads
    heat_consumption = create_all_heating_loads(time, bld_df, temp_margin=0.25)

    # Creation of the heat node for the buildings heating
    bld_heat_node = EnergyNode(time, 'bld_heat_node', energy_type='Heat')
    list_to_connect = [heat_pump.heat_production_unit] + heat_consumption
    bld_heat_node.connect_units(*list_to_connect)

    return bld_heat_node


def create_scenario_without_lncmi(time, pmin_elec_hp, pmax_elec_hp,
                    cop_hp, bld_df, obj='CO2', unit='kW'):
    """
        Permet de déterminer le min de CO2 sans le LNCMI
    :param time:
    :param pmin_elec_hp:
    :param pmax_elec_hp:
    :param cop_hp:
    :param bld_df:
    :param obj:
    :param unit:
    :return:
    """
    # Creation of the heat pump
    heat_pump = HeatPump(time, 'heat_pump', pmin_in_elec=pmin_elec_hp,
                         pmax_in_elec=pmax_elec_hp, cop=cop_hp)

    # Adding CO2 rate

    # Adding electricity costs


    # Adding constraint on the energy provided by the ground water
    #

    # Creation of the heating loads
    heat_consumption = create_all_heating_loads(time, bld_df, temp_margin=1)

    # Creation of the heat node for the buildings heating
    bld_heat_node = EnergyNode(time, 'bld_heat_node', energy_type='Heat')
    list_to_connect = [heat_pump.heat_production_unit] + heat_consumption
    bld_heat_node.connect_units(*list_to_connect)

    # Creation of the objective
    if obj == 'CO2':
        heat_pump.elec_consumption_unit.minimize_CO2_emissions()
    elif obj == 'cost':
        heat_pump.elec_consumption_unit.minimize_operating_cost()

    return bld_heat_node


def create_scenario_load_flex(time, pmin_elec_hp, pmax_elec_hp,
                    cop_hp, bld_df, unit='kW'):
    global heat_dissipation

    # Creation of the LNCMI, the heat dissipation and the heat node
    lncmi_heat_node = create_lncmi_node(unit)

    # Creation of the heat pump
    heat_pump = HeatPump(time, 'heat_pump', pmin_in_elec=pmin_elec_hp,
                         pmax_in_elec=pmax_elec_hp, cop=cop_hp)

    # Creation of the heating loads
    heat_consumption = create_all_heating_loads(time, bld_df)

    # Creation of the heat node for the buildings heating
    bld_heat_node = EnergyNode(time, 'bld_heat_node', energy_type='Heat')
    list_to_connect = [heat_pump.heat_production_unit] + heat_consumption
    bld_heat_node.connect_units(*list_to_connect)

    if unit == 'MW':
        export_min = 8.5
    elif unit == 'kW':
        export_min = 8500
    lncmi_heat_node.export_to_node(bld_heat_node, export_min=export_min)

    return lncmi_heat_node, bld_heat_node


def create_scenario_thermocline(time, storage_config=3, unit='MW'):
    # Import LNCMI consumption data
    lncmi_df = select_csv_file_between_dates('data/cons_lncmi_v6_10_min.csv',
                                             sep=';', start=time.DATES[0],
                                             end=time.DATES[-1])
    if unit == 'kW':
        p_in_elec = list(lncmi_df)
    elif unit == 'MW':
        p_in_elec = [p / 1000 for p in lncmi_df]

    # Creation of the LNCMI
    lncmi = ElectricalToHeatConversionUnit(time, name='lncmi',
                                           p_in_elec=p_in_elec,
                                           elec_to_heat_ratio=0.85)
    # Creation of the heat dissipation
    heat_dissipation = create_heat_dissipation(time, ill_on=False, unit=unit)

    # Creation of the thermal storage
    thermocline = create_heat_storage(time, storage_config=storage_config,
                                      unit=unit)

    # Creation of the heat node after the LNCMI magnets
    magnets_heat_node = EnergyNode(time, 'sortie_aim', energy_type='Heat')
    magnets_heat_node.connect_units(lncmi.heat_production_unit,
                                    heat_dissipation, thermocline)


def print_results(nodes):
    from omegalpes.general.utils import save_energy_flows
    save_energy_flows(*nodes, file_name='cambridge_results')


if __name__ == '__main__':
    start = '01/01/2018'
    end = '15/01/2018 23:50'

    pmin_hp = 0
    pmax_hp = 1e9
    cop_hp = 5
    bld_df = None

    bld_df = pd.read_csv('data/test_csv.csv', delimiter=';')

    time = TimeUnit(start=start, end=end, dt=1/6)
    nodes = create_scenario_load_flex(time, pmin_elec_hp=pmin_hp,
                                      pmax_elec_hp=pmax_hp, cop_hp=cop_hp,
                                      bld_df=bld_df, unit='MW')
    model = OptimisationModel(name='Cambridge_opt_model')
    model.add_nodes(*nodes)
    #compute_gurobi_IIS(opt_model=model)
    model.solve_and_update(GUROBI_CMD())

    print_results(nodes)

