#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module defines inputs and outputs of as poles**

The poles module includes :
 - FlowPole :  this class defines a pole with a directed flow (in or out)
 - EPole : this class define an energy pole

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

__docformat__ = "restructuredtext en"


class FlowPole(dict):
    """
    **Description**

        Interface for basics flux poles
    """

    def __init__(self, flow='flow', direction='in'):
        """

        :param flow: name of the flow
        :type flow: str
        :param direction: direction of the flow : 'in' or 'out'
        :type direction: str
        """
        dict.__init__(self)

        self.flow = flow
        self.direction = direction


class Epole(FlowPole):
    """
    **Description**

        Definition of an energetic pole, power and power
        flow direction convention 'in' or 'out'
    """

    def __init__(self, p, direction, energy_type=None):
        FlowPole.__init__(self, flow='p', direction='direction')
        self.energy_type = energy_type
        self.update({self.flow: p, self.direction: direction})
