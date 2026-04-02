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

from utils import \
    convert_hourly_data_into_mean_values, convert_hourly_data_into_static_values


def import_weather_data(time, weather_path='.\data\weather_data.csv'):
    print('Warning, weather beginning at 1st of January')
    dt = time.DT
    end = int(time.LEN * time.DT)
    # weather_df = pd.read_csv(weather_path, sep=';')[0:end]
    weather_df = pd.read_csv(weather_path, sep=',')[0:time.LEN]
    T_ext = list(weather_df['AirTemp_Avg'][0::6])
    T_dew = list(weather_df['Trosee_Avg'][0::6])
    I_rad = list(weather_df['Ray_Global_RSR2_Avg'][0::6])
    # T_ext = list(weather_df['#C2 Dry bulb temperature in Celsius at indicated '
    #                         'time'])
    # T_dew = list(weather_df['#C3 Dew point temperature in Celsius at '
    #                         'indicated time'])
    # I_rad = list(weather_df['#C9 Global horizontal radiation in Wh/m2'])
    # T_sky = calc_T_sky(T_dry=T_ext, T_dew=T_dew)

    # Convert the values
    T_ext = convert_hourly_data_into_static_values(T_ext, dt)
    T_dew = convert_hourly_data_into_static_values(T_dew, dt)
    I_rad = convert_hourly_data_into_mean_values(I_rad, dt)

    return T_ext, T_dew, I_rad



