#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module includes the following maths utils**

 It contains the following methods:
    - def_abs_value() : Define easily absolute value for quantity

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
from ..optimisation.elements import *

__docformat__ = "restructuredtext en"


def def_abs_value(quantity, q_min, q_max):
    """

    :param quantity: Quantity whose absolute value is wanted
    :param q_min: Minimal value of the quantity (negative value)
    :param q_max: Maximal value of the quantity (positive value)

    :return: A new Quantity whose values equal absolute values of the
        initial Quantity
    """

    if q_max <= 0:
        raise ValueError('If q_max <= 0, the absolute value of your quantity '
                         'is -1 * quantity.')
    if q_min >= 0:
        raise ValueError('If q_min >= 0, the absolute value of your quantity '
                         'is your quantity.')

    q_name = getattr(quantity, 'name')
    q_len = getattr(quantity, 'vlen')
    parent = getattr(quantity, 'parent')

    abs_value = Quantity(name='{}_abs'.format(q_name), opt=True, lb=0,
                         ub=q_max, vlen=q_len, parent=parent)
    value_pos = Quantity(name='{}_pos'.format(q_name), opt=True, lb=0, ub=q_max,
                         vlen=q_len, parent=parent)
    value_neg = Quantity(name='{}_neg'.format(q_name), opt=True, lb=0,
                         ub=-q_min, vlen=q_len, parent=parent)
    is_pos = Quantity(name='is_{}_pos'.format(q_name), opt=True, vtype=LpBinary,
                      vlen=q_len, parent=parent)

    setattr(parent, '{}_abs'.format(q_name), abs_value)
    setattr(parent, '{}_pos'.format(q_name), value_pos)
    setattr(parent, '{}_neg'.format(q_name), value_neg)
    setattr(parent, 'is_{}_pos'.format(q_name), is_pos)

    if q_len == 1:
        set_decomp = DefinitionConstraint(
            exp='{0}_{1} == {0}_{1}_pos - {0}_{1}_neg'.format(parent.name,
                                                              q_name),
            name='set_{}_decomp'.format(q_name), parent=parent)

        set_if_pos = DefinitionConstraint(
            exp='{0}_{1}_pos <= {2} * {0}_is_{1}_pos'.format(parent.name,
                                                             q_name, q_max),
            name='set_if_{}_pos'.format(q_name), parent=parent)

        set_if_neg = DefinitionConstraint(
            exp='{0}_{1}_neg <= {2} * ({0}_is_{1}_pos - 1)'.format(parent.name,
                                                                   q_name,
                                                                   q_min),
            name='set_if_{}_neg'.format(q_name), parent=parent)
        set_abs = DefinitionConstraint(
            exp='{0}_{1}_abs == {0}_{1}_pos + {0}_{1}_neg'.format(parent.name,
                                                                  q_name),
            name='set_{}_abs'.format(q_name), parent=parent)

    elif q_len > 1:
        set_decomp = DefinitionDynamicConstraint(
            exp_t='{0}_{1}[t] == {0}_{1}_pos[t] - {0}_{1}_neg[t]'.format(
                parent.name, q_name),
            name='set_{}_decomp'.format(q_name), parent=parent)

        set_if_pos = DefinitionDynamicConstraint(
            exp_t='{0}_{1}_pos[t] <= {2} * {0}_is_{1}_pos[t]'.format(
                parent.name, q_name, q_max),
            name='set_if_{}_pos'.format(q_name), parent=parent)

        set_if_neg = DefinitionDynamicConstraint(
            exp_t='{0}_{1}_neg[t] <= {2} * ({0}_is_{1}_pos[t] - 1)'.format(
                parent.name, q_name, q_min),
            name='set_if_{}_neg'.format(q_name), parent=parent)

        set_abs = DefinitionDynamicConstraint(
            exp_t='{0}_{1}_abs[t] == {0}_{1}_pos[t] + {0}_{1}_neg[t]'.format(
                parent.name, q_name),
            name='set_{}_abs'.format(q_name), parent=parent)

    setattr(parent, 'set_{}_decomp'.format(q_name), set_decomp)
    setattr(parent, 'set_if_{}_pos'.format(q_name), set_if_pos)
    setattr(parent, 'set_if_{}_neg'.format(q_name), set_if_neg)
    setattr(parent, 'set_{}_abs'.format(q_name), set_abs)

    return abs_value
