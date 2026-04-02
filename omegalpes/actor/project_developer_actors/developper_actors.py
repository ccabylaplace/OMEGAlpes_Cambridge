#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module defines the operator_actor and its scope of responsibility**

 One constraint is available :
    - co2_emission_maximum

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
from ..actor import Actor
from ...general.optimisation.elements import *


class ProjectDeveloper(Actor):
    """
    **Description**

        RegulatorActor class inherits from the the basic class Actor. It
        enables one to model an actor who can add constraints on all
        energy units of the study case.

    **Attributes**

     - name : name of the actor
    """

    def __init__(self, name, built_unit_list=None, built_node_list=None,
                 verbose=True):
        Actor.__init__(self, name=name, verbose=verbose)

        self.description = 'Project Developer Actor OptObject'
        self.built_unit_list = built_unit_list or []
        self.built_node_list = built_node_list or []

        for unit in self.built_unit_list:
            unit._set_optobject_as_attr(optobject=self,
                                        attribute_name='developer')

    def _check_built_unit_list(self, obj_built_unit_list):
        """
        Check if the objective must be applied to the whole energy units
        under the scope of responsibility (if obj_built_unit_list is
        empty); or to selected units and in this case, if the units are under
        the scope of responsibility

        :param obj_built_unit_list: List of units on which the
            objective will be applied. Might be empty.
        :return: the list of the built energy unit in order to apply
            the objective on these units
        """
        final_built_unit_list = []
        if not obj_built_unit_list:
            final_built_unit_list = self.built_unit_list
        else:
            if not isinstance(obj_built_unit_list, list):
                raise TypeError("The built unit list in order to add an "
                                "objective should be a list")
            else:
                for built_unit in obj_built_unit_list:
                    if built_unit not in self.built_unit_list \
                            and built_unit.parent not in \
                            self.built_node_list:
                        raise ValueError("the unit {0} must be "
                                         "built by {1}"
                                         .format(built_unit.name, self.name))
                    else:
                        final_built_unit_list = obj_built_unit_list
        return final_built_unit_list

    def _check_built_node_list(self, obj_built_node_list):
        """
        Check if the objective must be applied to the whole energy nodes
        under the scope of responsibility (if obj_built_node_list is
        empty); or to selected nodes and in this case, check if the nodes are
        under the scope of responsibility

        :param obj_built_nodes_list: List of nodes on which the
            objective will be applied. Might be empty.
        :return: the list of the built energy nodes in order to apply
            the objective on these units
        """
        final_built_node_list = []
        if not obj_built_node_list:
            final_built_node_list = self.built_node_list
        else:
            if not isinstance(obj_built_node_list, list):
                raise TypeError("The built unit list in order to add an "
                                "objective should be a list")
            else:
                for built_node in obj_built_node_list:
                    if built_node not in self.built_node_list:
                        raise ValueError("the node {0} must be "
                                         "built by {1}"
                                         .format(built_node.name, self.name))
                    else:
                        final_built_node_list = obj_built_node_list
        return final_built_node_list
