#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module includes the following utils for output data management**

 It contains the following methods:
    - save_energy_flows() : Save the optimisation results in a .csv file

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

import csv

__docformat__ = "restructuredtext en"


def save_energy_flows(*nodes, file_name=None, sep='\t', decimal_sep='.'):
    """
    Save the optimisation results in a .csv file

    :param nodes: one or several nodes from which should be collected the data
    :param file_name: name of the file to save the data
    :param sep: separator for the data
    :param decimal_sep: separator dor the decimals of the data
    """

    if decimal_sep != '.' and decimal_sep != ',':
        raise ValueError("The decimal separator should be either a dot "
                         "or a comma but is {0}".format(decimal_sep))
    if file_name is None:
        file_name = 'energy_flows_results.csv'
    else:
        file_name += '.csv'

    time = getattr(nodes[0], 'time')

    energy_flows = [
        ['date'] + [date.to_pydatetime() for date in time.DATES] + ['hour']]
    for node in nodes:
        for energy_flow in node.get_flows:
            v = getattr(energy_flow, 'value')
            parent = getattr(energy_flow, 'parent')
            name = getattr(parent, 'name')

            if isinstance(v, list):
                # Using european format
                if decimal_sep == ',':
                    v_euro = [str(el).replace('.', ',')
                              if isinstance(el, float) else el for el in v]
                    energy_flows.append([name] + v_euro)
                else:
                    energy_flows.append([name] + v)
            elif isinstance(v, dict):
                if decimal_sep == ',':
                    v_values_euro = [str(el).replace('.', ',')
                                     if isinstance(el, float) else el for el
                                     in list(v.values())]
                    energy_flows.append([name] + v_values_euro)
                else:
                    energy_flows.append([name] + list(v.values()))
            else:
                pass

    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=sep)
        writer.writerows(zip(*energy_flows))
