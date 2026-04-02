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


def convert_hourly_data_into_mean_values(h_data, dt):
    """

    :param h_data: list of hourly data
    :param dt: time step < 1 hour
    :return:

    ..
    Example:
        h_date = [A1, A2, A3]
        dt = 0.25
            results: [A1/4, A1/4, A1/4, A1/4, A2/4, A2/4, A2/4, A2/4,
                      A3/4, A3/4, A3/4, A3/4, A4/4, A4/4, A4/4, A4/4]
    """

    if dt == 1:
        print("Your data are already hourly data")
    elif dt < 1:
        new_data = []
        for i, data in enumerate(h_data):
            new_data += [data*dt] * int(1/dt)
    elif dt > 1:
        raise ValueError("Your time step should be lower than 1.")
    else:
        raise TypeError('Please enter dt as an int or a float.')

    return new_data


def convert_hourly_data_into_static_values(h_data, dt, lin=False):
    """

    :param h_date:
    :param dt:
    :return:

    ..
    Example:
        h_date = [A1, A2, A3]
        dt = 0.25
            results: [A1, A1, A1, A1, A2, A2, A2, A2,
                      A3, A3, A3, A3, A4, A4, A4, A4]
    """

    if dt == 1:
        print("Your data are already hourly data")
    elif dt < 1:
        new_data = []
        for i, data in enumerate(h_data):
            if not lin:
                new_data += [data] * int(1/dt)
            else:
                alpha = (h_data[i+1] - data) / (int(1/dt) - 1)
                beta = h_data[i+1]

                new_data += [alpha * k + beta for k in range((int(1/dt)))]
    elif dt > 1:
        raise ValueError("Your time step should be lower than 1.")
    else:
        raise TypeError('Please enter dt as an int or a float.')

    return new_data