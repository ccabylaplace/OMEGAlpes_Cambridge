#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module creates the Time object**

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

import numpy as np
import pandas as pd

__docformat__ = "restructuredtext en"


class TimeUnit:
    """
    **Description**

        Class defining the studied time period.

    **Attributes**

     - DATES : dated list of simulation steps
     - DT : delta t between values in hours (int or float), i.e. 1/6 will
       be 10 minutes.
     - LEN : number of simulation steps (length of DATES)
     - I : index of time ([0 : LEN])

    """

    def __init__(self, start='01/01/2018', end=None, periods=None, dt=1,
                 verbose=True):
        """
        :param start: start of the studied time period. European or DateTime
            format
        :param end: end of the studied time period. European or DateTime format
        :param periods: number of time step between the start and the end of
            the studied time period
        :param dt: time step size i.e. 1 being 1 hour,  1/6 will be 10 minutes.
        :param verbose: printing the studied time period if True
        """
        start = convert_european_format(start)
        end = convert_european_format(end)

        self.DATES = pd.date_range(start=start, end=end, periods=periods,
                                   freq=str(dt) + 'H')
        self.DT = dt
        self.LEN = len(self.DATES)
        self.I = np.arange(self.LEN)
        if verbose:
            self.print_studied_period()

    @property
    def get_days(self):
        """
        Getting days for the studied period

        :return all_days: list of days of the studied period
        """
        all_days = []  # Initialize the list of days

        for date in self.DATES:
            day = date.date()  # Get dates without the hour

            if day not in all_days:
                all_days.append(day)  # Gather all days in a list

        return all_days

    def get_date_for_index(self, index):
        """
        Getting a date for a given index

        :param index: int value for the index of the wanted dated, between 0
            and LEN (it must be in the studied period)
        """
        if isinstance(index, int):
            if index < self.LEN:
                return self.DATES[index]
            else:
                raise ValueError("The index value should be lower than the "
                                 "number of periods")
        else:
            raise TypeError("You should enter an integer value for the index "
                            "in order to get the associated date.")

    def get_index_for_date(self, date='YYYY-MM-DD HH:MM:SS'):
        """
        Getting the index associated with a date

        :param date: date the index of is wanted. Format YYYY-MM-DD
            HH:MM:SS, must be within the studied period and consistent with the
            timestep value
        """
        date = convert_european_format(date)

        date_tstp = pd.Timestamp(date)

        return list(self.DATES).index(date_tstp)

    def get_index_for_date_range(self, starting_date='YYYY-MM-DD HH:MM:SS',
                                 end=None, periods=None):
        """
        Getting a list of index for a date range

        :param starting_date: starting date of the wanted index
        :param end: ending date of the wanted index
        :param periods: number of periods from the starting_date of the
            wanted index
        :return index_list: list of indexes for the given dates
        """
        starting_date = convert_european_format(starting_date)
        index_list = []
        for date in pd.date_range(start=starting_date, end=end, periods=periods,
                                  freq=str(self.DT) + 'H'):
            index_list.append(self.get_index_for_date(date))

        return index_list

    def print_studied_period(self):
        start_date = self.get_date_for_index(0)
        end_date = self.get_date_for_index(-1)
        print(('You are studying the period from {0} to {1}'.format(start_date,
                                                                    end_date)))

    def get_working_days(self, country='France'):
        exec('from workalendar.europe import ' + country)
        cal = eval(country + '()')

        working_days = [day for day in self.get_days if cal.is_working_day(day)]

        return working_days

    def get_working_dates(self, month_range=range(12), hour_range=range(0, 24),
                          country='France'):
        exec('from workalendar.europe import ' + country)
        cal = eval(country + '()')
        working_dates = [date for date in self.DATES
                         if cal.is_working_day(date)
                         if date.hour in hour_range
                         if date.month in month_range]

        return working_dates

    def get_non_working_days(self, country='France'):
        exec('from workalendar.europe import ' + country)
        cal = eval(country + '()')

        working_days = [day for day in self.get_days
                        if not cal.is_working_day(day)]

        return working_days

    def get_non_working_dates(self, month_range=range(12), hour_range=range(24),
                              country='France'):
        exec('from workalendar.europe import ' + country)
        cal = eval(country + '()')
        working_dates = [date for date in self.DATES
                         if not cal.is_working_day(date)
                         if date.hour in hour_range
                         if date.month in month_range]

        return working_dates


def convert_european_format(date):
    """
        Converting a date with an european format DD/MM/YYYY
        into a datetime format YYYY-MM-DD or return

    :param date: date in european format
    :return: date in format datetime
    """

    try:
        # If date format begins with 'XX/XX' consider european date format
        if date[2] == '/':
            new_date = pd.to_datetime(date, dayfirst=True)
        else:
            new_date = date

    except TypeError:
        new_date = date

    return new_date
