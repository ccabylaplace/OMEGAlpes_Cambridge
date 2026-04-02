#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module includes the following display utils:**

    - plot_node_energetic_flows() : enables one to plot the energy flows
      through an EnergyNode
    - plot_energy_mix() : enables one to plot the energy flows connected to a
      node
    - plot_pareto2D() : enables one to plot a pareto front based on two
      quantities
    - plot_quantity() : enables one to plot easily a Quantity
    - plot_quantity_bar() : enables one to plot easily a Quantity as a bar
    - sum_quantities_in_quantity() : enables one to to plot several quantities
      in one once the optimisation is done

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

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from ...energy.energy_nodes import EnergyNode
from ...energy.units.production_units import ProductionUnit
from ...energy.units.storage_units import StorageUnit
from ...energy.units.consumption_units import ConsumptionUnit
from ..optimisation.elements import Quantity

__docformat__ = "restructuredtext en"


def plot_node_energetic_flows(node):
    """
    **Description**

    This function allows to plot the energy flows through an EnergyNode

    The display is realized :

       - with histograms for production and storage flow
       - with dashed curve for consumption flow

    :param node: EnergyNode
    """
    matplotlib.style.use('seaborn')

    if not isinstance(node, EnergyNode):
        raise TypeError(
            'The element {0} should be an EnergyNode.'.format(node))
    energy_fig = plt.figure()

    print(
        "\nPreparing to plot the energy flows through the node {0}.".format(
            node.name))

    cons = energy_fig.add_subplot(111)
    previous_energy_production = [0] * node.time.LEN  # Build the base to the
    # bar graph

    # For all production units connected to the node
    flows = node.get_flows
    for flow in flows:
        print(("\tAdd power from {0}.".format(flow.parent.name)))

        label = flow.parent.name
        parent = flow.parent

        # Get the power profiles
        if isinstance(flow.value, list):
            energy_flow = flow.value
        elif isinstance(flow.value, dict):
            energy_flow = list(flow.value.values())

        # If production or import
        if isinstance(parent, ProductionUnit) or node.is_import_flow(flow):
            try:
                plt.bar(node.time.I * node.time.DT, energy_flow,
                        width=0.8 * node.time.DT,
                        bottom=[previous_energy_production[t] for t
                                in range(node.time.LEN)],
                        label=label)

            except IndexError:
                plt.bar(node.time.I * node.time.DT, energy_flow,
                        width=0.8 * node.time.DT,
                        bottom=[previous_energy_production[t] for t
                                in range(node.time.LEN)],
                        label=label)

            for t in range(node.time.LEN):
                previous_energy_production[t] += energy_flow[t]

        # If consumption or export
        elif isinstance(parent, ConsumptionUnit) or node.is_export_flow(flow):
            cons.plot(node.time.I * node.time.DT, energy_flow, marker='.',
                      label=label,
                      linewidth=1.5, linestyle='dotted', markersize=10) #linewidth=0.8 linestyle='--'

        # If storage
        elif isinstance(parent, StorageUnit):
            energy_discharge = list(max(-1 * p, 0) for p in energy_flow)
            energy_charge = list(min(-1 * p, 0) for p in energy_flow)

            # Plot the discharge
            try:
                plt.bar(node.time.I * node.time.DT, energy_discharge,
                        width=0.8 * node.time.DT,
                        bottom=[previous_energy_production[t] for t
                                in range(node.time.LEN)],
                        label=label + 'discharge')

            except IndexError:
                plt.bar(node.time.I * node.time.DT, energy_discharge,
                        width=0.8 * node.time.DT,
                        bottom=[previous_energy_production[t] for t
                                in range(node.time.LEN)],
                        label=label)

            for t in range(node.time.LEN):
                previous_energy_production[t] += energy_discharge[t]

            # Plot the charge
            plt.bar(node.time.I * node.time.DT, energy_charge,
                    width=0.8 * node.time.DT,
                    label=label + ' charge')

    # for flow in node._exports:
    #     export = list(flow.value.values())
    #     cons.plot(export, marker='x', label='export')

    plt.title(
        'Power flow for the units connected to the node {0}'.format(node.name))
    if node.time.DT == 1:
        plt.xlabel('Time (hours)')
        plt.ylabel("Hourly mean power (kW)")
    elif node.time.DT == 24:
        plt.xlabel('Time (days)')
        plt.ylabel("Daily total energy (kWh)")

    plt.legend()
    return plt


def plot_energy_mix(node):
    if not isinstance(node, EnergyNode):
        raise TypeError(
            'The element {0} should be an EnergyNode.'.format(node))
    data = []
    legend = []

    _, ax = plt.subplots()
    plt.axis('equal')  # Should be a circle

    flows = node.get_flows
    for flow in flows:
        if isinstance(flow.parent, ProductionUnit):
            energy_prod = sum(flow.value.values())
            data.append(energy_prod)
            legend.append(flow.parent.name)

    ax.pie(data, labels=legend, autopct='%1.1f%%')

    plt.title('Energy mix of the node {0}'.format(node.name))
    plt.legend()


def plot_pareto2D(model, quantity_1, quantity_2, title=None, legend_on=True):
    """
    **Description**

    Plot a Pareto front for two quantities.
    Before using it, you should have added in your model two objectives with
    the pareto parameter activated (pareto=True)

    **Parameters**

    :param model:
    :param quantity_1: the first quantity for the pareto front
    :param quantity_2: the second quantity for the pareto front
    :param title:
    """
    print("\n\n Preparing 2D Pareto front ")
    fig = plt.figure()
    ax = plt.axes()

    legend = []
    i = 0
    for model in model.pareto_models:
        i += 1
        v1 = model.quantities[quantity_1.parent.name + '_' +
                              quantity_1.name]
        v2 = model.quantities[quantity_2.parent.name + '_' +
                              quantity_2.name]
        if v1.vlen > 1:
            print("Be careful, the length of the first quantity is {"
                  "} and is thus summed".format(v1.vlen))
            v1 = sum(v1.get_value()) * model.time.DT
        if v2.vlen > 1:
            print("Be careful, the length of the second quantity is {"
                  "} and is thus summed".format(v2.vlen))
            v2 = sum(v2.get_value()) * model.time.DT

        plt.plot(v1, v2, marker='+')
        if legend_on:
            legend += ['Optimisation {}'.format(i)]

    plt.legend(legend)
    plt.xlabel('{0}_{1}'.format(quantity_1.parent.name, quantity_1.name))
    plt.ylabel('{0}_{1}'.format(quantity_2.parent.name, quantity_2.name))

    if title is None:
        plt.title('Pareto front between {0}_{1} and {2}_{3}'.format(
            quantity_1.parent.name, quantity_1.name,
            quantity_2.parent.name, quantity_2.name))
    elif isinstance(title, str):
        plt.title(title)
    else:
        TypeError('title should be either None or a string')

    plt.show()


def plot_quantity(time, quantity, fig=None, ax=None, color=None, label=None,
                  title=None):
    """
    **Description**

        Function that plots a OMEGAlpes.general.optimisation.elements.Quantity

    **Parameters**

        - time: TimeUnit for the studied horizon as defined in general.time
        - quantity: OMEGAlpes.general.optimisation.elements.Quantity
        - fig: Figure as defined in matplotlib.pyplot.Figure
        - ax: axes as defined in matplotlib.pyplot.Axes
        - color: color of the plot
        - label: label for the quantity
        - title: title of the plot


    **Returns**

        - arg1 the matplotlib.pyplot.Figure handle object
        - arg2 the matplotlib.pyplot.Axes handle object
        - arg3 the matplotlib.pyplot.Line2D handle object

    """

    v = getattr(quantity, 'value')

    if fig is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)

    if isinstance(fig, plt.Figure):
        if ax is None:
            ax = fig.add_subplot(111)
        elif not isinstance(ax, plt.Axes):
            raise ValueError(
                'ax should be either NoneType or matplotlib.pyplot.Axes')

    if isinstance(v, (list, np.ndarray)):
        try:
            ld = ax.plot(time.I * time.DT, v, '-', color=color,
                         label=label)
            fig.canvas.draw()

        except ValueError:
            ld = ax.plot(np.arange(0, len(v) * time.DT, time.DT), v, 'x-',
                         color=color, label=label)

    elif isinstance(v, dict):
        ind = list(v.keys())
        val = list(v.values())
        lst = np.array([ind, val]).transpose()
        # lst = np.array([ind, val], ndmin=2)
        lst = lst[lst[:, 0].argsort()]
        ind = lst[:, 0]
        val = lst[:, 1]
        ld = ax.plot(ind * time.DT, val, 'x-', color=color, label=label)

    else:
        raise TypeError(
            'Type {0} is not supported for the plot'.format(
                type(v)))

    if title is None:
        plt.title('Evolution of {0} over the studied period'.format(
            quantity.name))
    elif isinstance(title, str):
        plt.title(title)
    else:
        TypeError('title should be either None or a string')

    return ld, ax, fig


def plot_quantity_bar(time, quantity, fig=None, ax=None, color=None,
                      label=None, title=None):
    """
    **Description**

        Function that plots a OMEGALPES.general.optimisation.elements.Quantity
        as a bar

    **Attributes**

        - quantity is the OMEGALPES.general.optimisation.elements.Quantity
        - fig could be None, a matplotlib.pyplot.Figure or Axes for multiple
          plots

    **Returns**

        - arg1 the matplotlib.pyplot.Figure handle object
        - arg2 the matplotlib.pyplot.Axes handle object
        - arg3 the matplotlib.pyplot.Line2D handle object

    """

    v = getattr(quantity, 'value')

    if fig is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)

    if isinstance(fig, plt.Figure):
        if ax is None:
            ax = fig.add_subplot(111)
        elif not isinstance(ax, plt.Axes):
            raise ValueError(
                'ax should be either NoneType or matplotlib.pyplot.Axes')

    if isinstance(v, (list, np.ndarray)):
        try:
            ld = ax.bar(time.I * time.DT, v, color=color, label=label)
            fig.canvas.draw()

        except ValueError:
            ld = ax.bar(np.arange(0, len(v) * time.DT, time.DT), v,
                        color=color, label=label)

    elif isinstance(v, dict):
        ind = list(v.keys())
        val = list(v.values())
        lst = np.array([ind, val]).transpose()
        # lst = np.array([ind, val], ndmin=2)
        lst = lst[lst[:, 0].argsort()]
        ind = lst[:, 0]
        val = lst[:, 1]
        ld = ax.bar(ind * time.DT, val, color=color, label=label)

    else:
        raise TypeError(
            'Type {0} is not supported for the plot'.format(
                type(v)))

    if title is None:
        plt.title('Evolution of {0} over the studied period'.format(
            quantity.name))
    elif isinstance(title, str):
        plt.title(title)
    else:
        TypeError('title should be either None or a string')

    return ld, ax, fig


def sum_quantities_in_quantity(quantities_list=[],
                               tot_quantity_name='sum_quantity'):
    """
    **Description**

        Function that creates a new quantity gathering several values of
        quantities
        Should be used in order to plot several quantities in one once the
        optimisation is done

    **Attributes**

        * quantities : a list of Quantities
          (OMEGALPES.general.optimisation.elements.Quantity)
        * tot_quantity_name : string : name of the new quantity

    **Returns**

        - tot_quantity : the new quantity created and filled
    """
    tot_q_value = [0] * quantities_list[0].vlen
    qunit = quantities_list[0].unit

    for q in quantities_list:
        if isinstance(q, Quantity):
            if q.unit == qunit:
                for i in range(q.vlen):
                    tot_q_value[i] = tot_q_value[i] + q.value[i]
            else:
                TypeError("The unit {0} of the quantity {1} is not the same "
                          "as the first quantity {2} which unit is {3}"
                          "".format(q.unit, q.name, quantities_list[0].name,
                                    qunit))
        else:
            TypeError("{0} should be a Quantity and is a {1}".format(q.name,
                                                                     q.__class__))

    tot_quantity = Quantity(value=tot_q_value, name=tot_quantity_name,
                            description='create a new quantity gathering '
                                        'various quantities')
    return tot_quantity
