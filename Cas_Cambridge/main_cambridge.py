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

import os, sys

from IBPSA_Final.omegalpes.energy.units.consumption_units import FixedConsumptionUnit, ShiftableConsumptionUnit

sys.path.append('../')

import pandas as pd
from pulp import GUROBI_CMD
from omegalpes.general.optimisation.elements import DynamicConstraint
from omegalpes.general.utils.output_data import save_energy_flows
from omegalpes.general.optimisation.model import OptimisationModel, compute_gurobi_IIS
from omegalpes.general.time import TimeUnit
from omegalpes.general.utils.input_data import select_csv_file_between_dates
from omegalpes.energy.energy_nodes import EnergyNode
from omegalpes.energy.units.storage_units import StorageUnit
from omegalpes.energy.units.production_units import ProductionUnit
from omegalpes.energy.units.consumption_units import ConsumptionUnit, VariableConsumptionUnit, FixedConsumptionUnit,ShiftableConsumptionUnit
from omegalpes.energy.units.conversion_units import \
    ElectricalToThermalConversionUnit, HeatPump
from omegalpes.energy.buildings.thermal import HeatingLoad
#from Chapitre_3.heat_elements import create_heat_dissipation, create_heat_storage
from heat_load_creation import\
    create_all_heating_nodes
from utils import convert_hourly_data_into_static_values

import plotly.graph_objects as go
import plotly.express as px

import pandas as pd

SAVE_PATH = "C:\\Users\\caby\\Documents\\Analyse IBPSA\\sans_pv\\Sans_charge\\10_min\\"

def create_scenario_reference(time, bld_df, unit='kW',
                                       T_set=20, t_marg=1):
    """

    :param time:
    :param bld_df:
    :param unit:
    :return:
    """
    # Creation of the heating nodes and heat pumps
    bld_heat_nodes = create_all_heating_nodes(time, bld_df, temp_margin=t_marg,
                                              Tset=T_set)
    app_df = pd.read_csv('./data/csv_app_10min_kW.csv', delimiter=';',
                         header=[0, 1])
    light_df = pd.read_csv('./data/csv_light_10min_kW.csv', delimiter=';',
                           header=[0])
    app_df = app_df.iloc[0:time.LEN]
    light_df = light_df.iloc[0:time.LEN]

    # Creating the elec loads
    elec_units = []
    electrical_units = []
    for k in range(len(bld_df)):
        name = bld_df.at[k, 'Name']
        app_fixed = app_df[name, 'total_consumption'].to_list()
        light_fixed = light_df[name].to_list()
        fixed_load = FixedConsumptionUnit(time, name=name + "_app", p=app_fixed, energy_type='Electrical')
        light_load = FixedConsumptionUnit(time, name=name + "_light", p=light_fixed, energy_type='Electrical')

        elec_units.append(fixed_load)
        elec_units.append(light_load)


    # Adding constraint on the energy provided by the ground water
    #

    # Minimizing energy consumed by the heat pumps
    for bld_heat_node in bld_heat_nodes:
        units = bld_heat_node.get_connected_energy_units
        for e_unit in units:
            if isinstance(e_unit, HeatingLoad):
               e_unit.maximize_thermal_comfort()
            if isinstance(e_unit, ProductionUnit):
                parent = e_unit.parent
                pmax = e_unit.p.ub
                e_unit.max_ramp_up = pmax/2
                # e_unit.minimize_production()
                parent.elec_consumption_unit.minimize_consumption()
            #if isinstance(e_unit, HeatingLoad):
             #   e_unit.add_max_temp_ramp_down(0.2)

    return bld_heat_nodes, elec_units


def create_flex_scenario_without_lncmi(time, bld_df, obj='CO2', unit='kW',
                                       T_set=20, t_marg=1):
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

    # Adding CO2 rate
    # Electrical CO2 emissions
    elec_CO2_df = select_csv_file_between_dates('./data/Elec_co2_em.csv',
                                                start=time.DATES[0],
                                                end=time.DATES[-1], sep=';',
                                                v_cols=['Elec_CO2_em[g/kWh]'])

    # CO2 emissions [kg/kWh]
    CO2_emissions = [e / 1000 for e in elec_CO2_df['Elec_CO2_em[g/kWh]']]

    # Convert into 10 minutes
    co2_elec = convert_hourly_data_into_static_values(CO2_emissions, dt=time.DT)

    # Adding electricity costs
    operating_cost_hp = []

    # Adding constraint on the energy provided by the ground water
    #

    # Creation of the heating nodes and heat pumps
    bld_heat_nodes = create_all_heating_nodes(time, bld_df, temp_margin=t_marg,
                                              Tset=T_set)
    #Adding the elec profiles
    app_df = pd.read_csv('./data/csv_app_10min_kW.csv', delimiter=';',
                         header=[0, 1])
    light_df = pd.read_csv('./data/csv_light_10min_kW.csv', delimiter=';',
                           header=[0])
    app_df = app_df.iloc[0:time.LEN]
    light_df = light_df.iloc[0:time.LEN]

    bld_elec_units = []

    for k in range(len(bld_df)):
        name = bld_df.at[k, 'Name']
        app_fixed = app_df[name, 'total_consumption'].to_list()
        light_fixed = light_df[name].to_list()
        fixed_load = FixedConsumptionUnit(time, name=name + "_app", p=app_fixed, energy_type='Electrical')
        light_load = FixedConsumptionUnit(time, name=name + "_light", p=light_fixed, energy_type='Electrical')
        bld_elec_units.append(fixed_load)
        bld_elec_units.append(light_load)
    # Adding constraint on the energy provided by the ground water
    #

    # Creation of the objective
    for bld_heat_node in bld_heat_nodes:
        units = bld_heat_node.get_connected_energy_units
        for e_unit in units:
            if isinstance(e_unit, HeatingLoad):
               e_unit.maximize_thermal_comfort()
            if isinstance(e_unit, ProductionUnit):
                parent = e_unit.parent
                pmax = e_unit.p.ub
                e_unit.max_ramp_up = pmax/2
                # e_unit.minimize_production()
                parent.elec_consumption_unit.minimize_consumption()
                bld_elec_units.append(parent.elec_consumption_unit)
                # if obj == 'CO2':
                #     parent.elec_consumption_unit._add_co2_emissions(co2_elec)
                #     parent.elec_consumption_unit.minimize_co2_emissions()
                # elif obj == 'cost':
                #     # e_unit._add_operating_cost(operating_cost_hp)
                #     e_unit.minimize_production()

    return bld_heat_nodes, bld_elec_units



def print_results(nodes):
    save_energy_flows(*nodes, file_name='cambridge_results')


def save_phi_s(*nodes, file_name=None, sep='\t'):
    import csv

    if file_name is None:
        file_name = 'phi_s_results.csv'
    else:
        file_name += '.csv'

    time = getattr(nodes[0], 'time')

    phi_s = [
        ['date'] + [date.to_pydatetime() for date in time.DATES] + ['hour']]
    for node in nodes:
        for unit in node.get_connected_energy_units:
            if isinstance(unit, HeatingLoad):
                isol = unit.tz.I_sol
                irad = unit.tz.I_rad
                v = getattr(isol, 'value')
                v2 = getattr(irad, 'value')
                name = getattr(unit, 'name')

                if isinstance(v, list):
                    # Using european format
                    phi_s.append([name + '_I_sol'] + v)
                elif isinstance(v, dict):
                    phi_s.append([name + '_I_sol'] + list(v.values()))
                else:
                    pass

                if isinstance(v2, list):
                    phi_s.append([name + '_I_rad'] + v2)
                elif isinstance(v2, dict):
                    phi_s.append([name + '_I_rad'] + list(v2.values()))
                else:
                    pass

    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=sep)
        writer.writerows(zip(*phi_s))

def save_hp_elec(*nodes, file_name=None, sep='\t'):
    import csv

    if file_name is None:
        file_name = 'hp_elec_results.csv'
    else:
        file_name += '.csv'

    time = getattr(nodes[0], 'time')

    hp_elec = [
        ['date'] + [date.to_pydatetime() for date in time.DATES] + ['hour']]
    for node in nodes:
        for unit in node.get_connected_energy_units:
            if isinstance(unit, ProductionUnit):
                parent = unit.parent
                hp_elec_cons = parent.elec_consumption_unit.p
                v = getattr(hp_elec_cons, 'value')
                name = getattr(parent, 'name')

                if isinstance(v, list):
                    # Using european format
                    hp_elec.append([name + '_elec_cons'] + v)
                elif isinstance(v, dict):
                    hp_elec.append([name + '_elec_cons'] + list(v.values()))
                else:
                    pass


    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=sep)
        writer.writerows(zip(*hp_elec))


def save_Top(*nodes, file_name=None, sep='\t'):
    import csv

    if file_name is None:
        file_name = 'Top_results.csv'
    else:
        file_name += '.csv'

    time = getattr(nodes[0], 'time')

    t_op = [
        ['date'] + [date.to_pydatetime() for date in time.DATES] + ['hour']]
    for node in nodes:
        for unit in node.get_connected_energy_units:
            if isinstance(unit, HeatingLoad):
                tair = unit.tz.prop.T_int
                thetac = unit.tz.prop.theta_c
                top = unit.tz.prop.T_op
                v = getattr(top, 'value')
                v2 = getattr(tair, 'value')
                v3 = getattr(thetac, 'value')
                name = getattr(unit, 'name')

                if isinstance(v, list):
                    # Using european format
                    t_op.append([name + '_T_op'] + v)
                elif isinstance(v, dict):
                    t_op.append([name + '_T_op'] + list(v.values()))
                else:
                    pass

                if isinstance(v2, list):
                    t_op.append([name + '_T_air'] + v2)
                elif isinstance(v2, dict):
                    t_op.append([name + '_T_air'] + list(v2.values()))
                else:
                    pass

                if isinstance(v3, list):
                    t_op.append([name + '_theta_c'] + v3)
                elif isinstance(v3, dict):
                    t_op.append([name + '_theta_c'] + list(v3.values()))
                else:
                    pass

    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=sep)
        writer.writerows(zip(*t_op))


def launch_reference_scenario(time, bld_df, T_set=20, t_marg=1):
    bld_heat_nodes, bld_elec_nodes = create_scenario_reference(time, bld_df,
                                       T_set=T_set, t_marg=t_marg)
    model = OptimisationModel(time, name='Cambridge_opt_model_ref')
    model.add_nodes(*bld_heat_nodes)

    # compute_gurobi_IIS(opt_model=model)
    model.solve_and_update(GUROBI_CMD(options=[('NumericFocus', 3),
                                               ('MIPGap', 0.005)]))
    # model.solve_and_update()
    save_energy_flows(*bld_heat_nodes,
                      file_name='results/cambridge_ref_scenario_4_results')

    save_phi_s(*bld_heat_nodes,
               file_name='results/cambridge_ref_scenario_4_results_phi_s')

    save_Top(*bld_heat_nodes,
             file_name='results/cambridge_ref_scenario_4_results_top')
    
    return bld_heat_nodes


def launch_flex_without_lncmi_scenario(time, bld_df, obj='CO2', T_set=20,
                                       t_marg=1):
    bld_heat_nodes = create_flex_scenario_without_lncmi(time, bld_df, obj,
                                                        T_set=T_set,
                                                        t_marg=t_marg)

    model = OptimisationModel(time, name='Cambridge_opt_model_flex_only')
    model.add_nodes(*bld_heat_nodes)
    model.solve_and_update(GUROBI_CMD(options=[('NumericFocus', 3)]))

    save_energy_flows(*bld_heat_nodes,
                      file_name='results/cambridge_flex_only_scenario_2_results')

    save_Top(*bld_heat_nodes,
             file_name='results/cambridge_flex_only_scenario_2_results_top')
    
    return bld_heat_nodes
    

def launch_flex_without_lncmi_scenario_with_power_limit(time, bld_df,
                                                        obj='CO2', p_max=95):
    bld_heat_nodes = create_flex_scenario_without_lncmi(time, bld_df, obj,
                                                        T_set=22.5, t_marg=2.5)

    elec_consumption_units = []
    for node in bld_heat_nodes:
        units = node.get_connected_energy_units
        for unit in units:
            if isinstance(unit, ProductionUnit):
                pac = unit.parent
                elec_cons = pac.elec_consumption_unit
                elec_consumption_units.append(elec_cons)

    elec_prod = ProductionUnit(time, 'elec_prod', p_max=p_max)
    elec_node = EnergyNode(time, 'elec_node', energy_type='Electrical')
    elec_units = [elec_prod] + elec_consumption_units

    elec_node.connect_units(*elec_units)

    model = OptimisationModel(name='Cambridge_opt_model_flex_only_pmax')
    model.add_nodes(*(bld_heat_nodes+[elec_node]))
    model.solve_and_update(GUROBI_CMD())

    save_energy_flows(*bld_heat_nodes,
                      file_name='results/cambridge_flex_only_with_power_limit_'
                                'scenario_2_results')

    save_Top(*bld_heat_nodes,
             file_name='results/cambridge_flex_only_with_power_limit'
                       '_scenario_2_results_top')


def extract_obj(heat_node):
    for unit in heat_node[0].get_connected_energy_units:
        if isinstance(unit, StorageUnit):
            capacity = unit.capacity.value
        if isinstance(unit, ProductionUnit):
            pac = unit.parent
            print(pac.elec_consumption_unit.p)
            print(pac.elec_consumption_unit.co2_emissions)
            co2 = sum(pac.elec_consumption_unit.co2_emissions.value.values())

    return capacity, co2


def filter_by_date(df, start_date, end_date, date_col="date"):
    """
    Filter a DataFrame by a date range.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    start_date : str
        Start date (inclusive), format 'YYYY-MM-DD'.
    end_date : str
        End date (inclusive), format 'YYYY-MM-DD'.
    date_col : str
        Name of the date column.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame.
    """
    return df[
        (df[date_col] >= start_date) &
        (df[date_col] <= end_date)
    ]




def plot_hp_production_vs_temperature_building(
    uncoordinated_df,
    uncoordinated_df_top,
    building_code,
    building_index,
    start_date,
    end_date,
    hp_col="heat_pump_0__therm_prod",
    scenario = 'uncoordinated'
):
    """
    Plot HP production vs operative temperature for a specified building.

    Parameters
    ----------
    uncoordinated_df : pd.DataFrame
        Main results DataFrame.
    uncoordinated_df_top : pd.DataFrame
        Top-level results DataFrame.
    building_code : str
        Building code (e.g., "CI4", "CE2") to select columns.
    building_index : int
        Building index (for reference or future use).
    start_date : str
        Start date (YYYY-MM-DD).
    end_date : str
        End date (YYYY-MM-DD).
    hp_col : str
        Heat pump thermal production column name.
    """

    # Temperature column dynamically based on building code
    temp_col = f"HL_{building_code}_T_op"
    title = f"HP Production & Temperature Over Time - {scenario} - building {building_code}"

    # Filter by date
    df_filtered = uncoordinated_df[
        (uncoordinated_df["date"] >= start_date) &
        (uncoordinated_df["date"] <= end_date)
    ]

    df_top_filtered = uncoordinated_df_top[
        (uncoordinated_df_top["date"] >= start_date) &
        (uncoordinated_df_top["date"] <= end_date)
    ]

    # Merge required columns
    merged_df = pd.merge(
        df_top_filtered[["date", temp_col]],
        df_filtered[["date", hp_col]],
        on="date"
    )

    # Create figure
    fig = go.Figure()

    # Left y-axis: HP production
    fig.add_trace(go.Scatter(
        x=merged_df["date"],
        y=merged_df[hp_col],
        mode="lines",
        name="HP production (kW)",
        yaxis="y1"
    ))

    # Right y-axis: temperature
    fig.add_trace(go.Scatter(
        x=merged_df["date"],
        y=merged_df[temp_col],
        mode="lines",
        name="Operative temperature (°C)",
        yaxis="y2"
    ))

    fig.update_layout(
        title=title,
        xaxis=dict(title="Date"),
        yaxis=dict(title="HP Production (kW)"),
        yaxis2=dict(
            title="Temperature (°C)",
            overlaying="y",
            side="right"
        ),
        template="plotly_white",
        legend=dict(x=0.01, y=0.99)
    )
    fig.write_html(SAVE_PATH + f"hp_prod_{building_code}.html")
    fig.show()



def plot_hp_electrical_consumption(
    uncoordinated_df,
    start_date,
    end_date,
    title="HP electrical consumption - uncoordinated - all buildings"
):
    """
    Plot heat pump electrical consumption for all buildings (uncoordinated case).

    Parameters
    ----------
    coordinated_df : pd.DataFrame
        Coordinated electrical results DataFrame.
    start_date : str
        Start date (YYYY-MM-DD).
    end_date : str
        End date (YYYY-MM-DD).
    title : str
        Plot title.
    """

    # Filter by date
    uncoordinated_filtered = uncoordinated_df[
        (uncoordinated_df["date"] >= start_date) &
        (uncoordinated_df["date"] <= end_date)
    ].copy()

    # Convert date and numeric columns
    uncoordinated_filtered["date"] = pd.to_datetime(uncoordinated_filtered["date"])

    value_cols = [c for c in uncoordinated_filtered.columns if c != "date"]
    uncoordinated_filtered[value_cols] = uncoordinated_filtered[value_cols].apply(
        pd.to_numeric, errors="coerce"
    )

    # Plot
    fig = px.line(
        uncoordinated_filtered,
        x="date",
        y=value_cols
    )

    fig.update_layout(
        title=title,
        xaxis=dict(title="Date"),
        yaxis=dict(
            title="electrical consumption (kW)",
            rangemode="tozero"
        ),
        template="plotly_white",
        legend=dict(x=0.01, y=0.99)
    )
    fig.write_html(SAVE_PATH + "hp_prod_all_buildings.html")
    fig.show()



def plot_total_hp_electrical_consumption(
    uncoordinated_df,
    start_date,
    end_date,
    title="HP electrical consumption - uncoordinated - all buildings"
):
    """
    Compute and plot total HP electrical consumption (uncoordinated case).

    Parameters
    ----------
    uncoordinated_df : pd.DataFrame
        Uncoordinated electrical results DataFrame.
    start_date : str
        Start date (YYYY-MM-DD).
    end_date : str
        End date (YYYY-MM-DD).
    title : str
        Plot title.
    """

    # Identify electrical consumption columns
    cons_cols = [col for col in uncoordinated_df.columns if col.endswith("__elec_cons")]

    # Compute total consumption
    df = uncoordinated_df.copy()
    df["total_elec_cons"] = df[cons_cols].sum(axis=1)

    # Filter by date
    df_filtered = df[
        (df["date"] >= start_date) &
        (df["date"] <= end_date)
    ]

    # Prepare plotting DataFrame
    merged_df = df_filtered[["date", "total_elec_cons"]].copy()
    merged_df["date"] = pd.to_datetime(merged_df["date"])

    # Plot
    fig = px.line(merged_df, x="date", y="total_elec_cons")

    fig.update_layout(
        title=title,
        xaxis=dict(title="Date"),
        yaxis=dict(title="electrical consumption (kW)"),
        template="plotly_white",
        legend=dict(x=0.01, y=0.99)
    )
    fig.write_html(SAVE_PATH + "hp_elec_cons_all_buildings.html")
    fig.show()

def plot_total_hp_electrical_consumption_comparison(
    coordinated_df,
    uncoordinated_df,
    start_date,
    end_date,
    title="HP electrical consumption – coordinated vs uncoordinated"
):
    """
    Compare total HP electrical consumption between coordinated and uncoordinated cases.

    Parameters
    ----------
    coordinated_df : pd.DataFrame
        Coordinated electrical results.
    uncoordinated_df : pd.DataFrame
        Uncoordinated electrical results.
    start_date : str
        Start date (YYYY-MM-DD).
    end_date : str
        End date (YYYY-MM-DD).
    title : str
        Plot title.
    """

    # --- Compute total electrical consumption ---
    for df in (coordinated_df, uncoordinated_df):
        cons_cols = [c for c in df.columns if c.endswith("__elec_cons")]
        df["total_elec_cons"] = df[cons_cols].sum(axis=1)

    # --- Filter by date ---
    coordinated_filtered = coordinated_df[
        (coordinated_df["date"] >= start_date) &
        (coordinated_df["date"] <= end_date)
    ]

    uncoordinated_filtered = uncoordinated_df[
        (uncoordinated_df["date"] >= start_date) &
        (uncoordinated_df["date"] <= end_date)
    ]

    # --- Merge ---
    merged_df = pd.merge(
        uncoordinated_filtered[["date", "total_elec_cons"]],
        coordinated_filtered[["date", "total_elec_cons"]],
        on="date",
        suffixes=("_uncoordinated", "_coordinated")
    )

    # --- Prepare for plotting ---
    merged_df["date"] = pd.to_datetime(merged_df["date"])
    value_cols = [c for c in merged_df.columns if c != "date"]
    merged_df[value_cols] = merged_df[value_cols].apply(
        pd.to_numeric, errors="coerce"
    )

    # --- Plot ---
    fig = px.line(merged_df, x="date", y=value_cols)

    fig.update_layout(
        title=title,
        xaxis=dict(title="Date"),
        yaxis=dict(
            title="electrical consumption (kW)",
            rangemode="tozero"
        ),
        template="plotly_white",
        legend=dict(x=0.01, y=0.99)
    )
    fig.write_html(SAVE_PATH + "hp_elec_cons_comparison.html")
    fig.show()


def plot_operative_temperature_comparison_building(
    coordinated_df_top,
    uncoordinated_df_top,
    building_code,
    building_index,
    start_date,
    end_date
):
    """
    Plot operative temperature comparison between coordinated and uncoordinated scenarios
    for a specific building.

    Parameters
    ----------
    coordinated_df_top : pd.DataFrame
        Coordinated top-level results.
    uncoordinated_df_top : pd.DataFrame
        Uncoordinated top-level results.
    building_code : str
        Building code (e.g., "CI4", "CE2") to select temperature column.
    building_index : int
        Building index (for reference or future use).
    start_date : str
        Start date (YYYY-MM-DD).
    end_date : str
        End date (YYYY-MM-DD).
    """

    # Temperature column dynamically based on building code
    temp_col = f"HL_{building_code}_T_op"
    title = f"Operative temperature comparison - building {building_code} (index {building_index})"

    # Filter by date
    coordinated_filtered = coordinated_df_top[
        (coordinated_df_top["date"] >= start_date) &
        (coordinated_df_top["date"] <= end_date)
    ]

    uncoordinated_filtered = uncoordinated_df_top[
        (uncoordinated_df_top["date"] >= start_date) &
        (uncoordinated_df_top["date"] <= end_date)
    ]

    # Merge
    merged_df = pd.merge(
        uncoordinated_filtered[["date", temp_col]],
        coordinated_filtered[["date", temp_col]],
        on="date",
        suffixes=("_uncoordinated", "_coordinated")
    )

    # Reshape for Plotly
    melted_df = merged_df.melt(
        id_vars="date",
        var_name="Scenario",
        value_name="Operative Temperature"
    )

    melted_df["Scenario"] = melted_df["Scenario"].map({
        f"{temp_col}_uncoordinated": "Uncoordinated",
        f"{temp_col}_coordinated": "Coordinated"
    })

    # Plot
    fig = px.line(
        melted_df,
        x="date",
        y="Operative Temperature",
        color="Scenario",
        title=title,
        labels={"Operative Temperature": "°C", "date": "Date"}
    )

    fig.update_layout(template="plotly_white")
    fig.write_html(SAVE_PATH + "operative_temperature_comparison.html")
    fig.show()




def plot_hp_production_comparison_building(
    coordinated_df,
    uncoordinated_df,
    building_code,
    building_index,
    start_date,
    end_date,
    hp_col="heat_pump_0__therm_prod"
):
    """
    Filter coordinated and uncoordinated DataFrames by date and plot
    heat pump thermal production comparison for a specific building.

    Parameters
    ----------
    coordinated_df : pd.DataFrame
        Coordinated scenario data with 'date' column.
    uncoordinated_df : pd.DataFrame
        Uncoordinated scenario data with 'date' column.
    building_code : str
        Building code (e.g., "CI4") to include in the title.
    building_index : int
        Index of the building (for reference in the title).
    start_date : str
        Start date (inclusive) in YYYY-MM-DD format.
    end_date : str
        End date (inclusive) in YYYY-MM-DD format.
    hp_col : str
        Column name for heat pump thermal production.
    """

    # Update title dynamically
    title = f"HP production comparison - building {building_code} (index {building_index})"

    # --- Filter by date ---
    coordinated_filtered = coordinated_df[
        (coordinated_df["date"] >= start_date) & 
        (coordinated_df["date"] <= end_date)
    ].copy()

    uncoordinated_filtered = uncoordinated_df[
        (uncoordinated_df["date"] >= start_date) & 
        (uncoordinated_df["date"] <= end_date)
    ].copy()

    # --- Merge ---
    merged_df = pd.merge(
        uncoordinated_filtered[["date", hp_col]],
        coordinated_filtered[["date", hp_col]],
        on="date",
        suffixes=("_uncoordinated", "_coordinated")
    )

    # --- Reshape for Plotly ---
    melted_df = merged_df.melt(
        id_vars="date",
        var_name="Scenario",
        value_name="HP production"
    )

    melted_df["Scenario"] = melted_df["Scenario"].map({
        f"{hp_col}_uncoordinated": "Uncoordinated",
        f"{hp_col}_coordinated": "Coordinated"
    })

    # --- Plot ---
    fig = px.line(
        melted_df,
        x="date",
        y="HP production",
        color="Scenario",
        title=title,
        labels={"HP production": "kW", "date": "Date"}
    )

    fig.update_layout(template="plotly_white")
    fig.write_html(SAVE_PATH + "hp_production_comparison.html")
    fig.show()


def prepare_elec_consumption_comparison(
    coordinated_df,
    uncoordinated_df,
    start_date,
    end_date,
    print_stats=True
):
    """
    Compute total electrical consumption for coordinated and uncoordinated scenarios,
    filter by date, merge the results, and optionally print statistics.

    Parameters
    ----------
    coordinated_df : pd.DataFrame
        Coordinated scenario data.
    uncoordinated_df : pd.DataFrame
        Uncoordinated scenario data.
    start_date : str
        Start date (inclusive) in YYYY-MM-DD.
    end_date : str
        End date (inclusive) in YYYY-MM-DD.
    print_stats : bool
        If True, prints PAR, max, and mean for both scenarios.

    Returns
    -------
    pd.DataFrame
        Merged DataFrame with total consumption for both scenarios.
    """

    # --- Compute total consumption ---
    for df in (coordinated_df, uncoordinated_df):
        cons_cols = [c for c in df.columns if c.endswith("__elec_cons")]
        df["total_elec_cons"] = df[cons_cols].sum(axis=1)

    # --- Filter by date ---
    coordinated_filtered = coordinated_df[
        (coordinated_df["date"] >= start_date) &
        (coordinated_df["date"] <= end_date)
    ]

    uncoordinated_filtered = uncoordinated_df[
        (uncoordinated_df["date"] >= start_date) &
        (uncoordinated_df["date"] <= end_date)
    ]

    # --- Merge ---
    merged_df = pd.merge(
        uncoordinated_filtered[["date", "total_elec_cons"]],
        coordinated_filtered[["date", "total_elec_cons"]],
        on="date",
        suffixes=("_uncoordinated", "_coordinated")
    )

    # --- Print stats if requested ---
    if print_stats:
        par_uncoordinated = merged_df["total_elec_cons_uncoordinated"].max() / merged_df["total_elec_cons_uncoordinated"].mean()
        par_coordinated = merged_df["total_elec_cons_coordinated"].max() / merged_df["total_elec_cons_coordinated"].mean()
        print(f"PAR uncoordinated: {par_uncoordinated:.2f}")
        print(f"PAR coordinated: {par_coordinated:.2f}")
        print(f"Max power uncoordinated: {merged_df['total_elec_cons_uncoordinated'].max():.2f} kW")
        print(f"Max power coordinated: {merged_df['total_elec_cons_coordinated'].max():.2f} kW")
        print(f"Average uncoordinated: {merged_df['total_elec_cons_uncoordinated'].mean():.2f} kW")
        print(f"Average coordinated: {merged_df['total_elec_cons_coordinated'].mean():.2f} kW")

    return merged_df
