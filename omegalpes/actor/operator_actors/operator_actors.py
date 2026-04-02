#! usr/bin/env python3
#  -*- coding: utf-8 -*-


"""
**This module defines the operator_actor and its scope of responsibility**

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


class OperatorActor(Actor):
    """
    **Description**

        OperatorActor class inherits from the the basic class Actor. It
        enables one to model an actor who operates energy units which is part
        of its scope of responsibility.
        An operator actor has objectives and constraints which are
        linked to the energy units he operates.

    **Attributes**

     - name : name of the actor
     - operated_unit_list:  list of the energy units operated by the actor or
       more precisely in its scope of responsibility

    """

    def __init__(self, name, operated_unit_type_tuple,
                 operated_unit_list=None, operated_node_list=None,
                 verbose=True):
        Actor.__init__(self, name=name, verbose=verbose)

        self.description = 'Operator Actor OptObject'
        self.operated_unit_list = operated_unit_list or []
        self.operated_node_list = operated_node_list or []

        for unit in self.operated_unit_list:
            self._check_unit_type(unit, operated_unit_type_tuple)
            unit._set_optobject_as_attr(optobject=self,
                                        attribute_name='operator')

    def _check_operated_unit_list(self, obj_operated_unit_list):
        """
        Check if the objective must be applied to the whole energy units
        under the scope of responsibility (if obj_operated_unit_list is
        empty); or to selected units and in this case, if the units are under
        the scope of responsibility

        :param obj_operated_unit_list: List of units on which the
            objective will be applied. Might be empty.
        :return: the list of the operated energy unit in order to apply
            the objective on these units
        """
        final_operated_unit_list = []
        if not obj_operated_unit_list:
            final_operated_unit_list = self.operated_unit_list
        else:
            if not isinstance(obj_operated_unit_list, list):
                raise TypeError("The operated unit list in order to add an "
                                "objective should be a list")
            else:
                for operated_unit in obj_operated_unit_list:
                    if operated_unit not in self.operated_unit_list \
                            and operated_unit.parent not in \
                            self.operated_node_list:
                        raise ValueError("the unit {0} must be "
                                         "operated by {1}"
                                         .format(operated_unit.name, self.name))
                    else:
                        final_operated_unit_list = obj_operated_unit_list
        return final_operated_unit_list

    def _check_operated_node_list(self, obj_operated_node_list):
        """
        Check if the objective must be applied to the whole energy nodes
        under the scope of responsibility (if obj_operated_node_list is
        empty); or to selected nodes and in this case, check if the nodes are
        under the scope of responsibility

        :param obj_operated_nodes_list: List of nodes on which the
            objective will be applied. Might be empty.
        :return: the list of the operated energy nodes in order to apply
            the objective on these units
        """
        final_operated_node_list = []
        if not obj_operated_node_list:
            final_operated_node_list = self.operated_node_list
        else:
            if not isinstance(obj_operated_node_list, list):
                raise TypeError("The operated unit list in order to add an "
                                "objective should be a list")
            else:
                for operated_node in obj_operated_node_list:
                    if operated_node not in self.operated_node_list:
                        raise ValueError("the node {0} must be "
                                         "operated by {1}"
                                         .format(operated_node.name,
                                                 self.name))
                    else:
                        final_operated_node_list = obj_operated_node_list
        return final_operated_node_list

    def _check_unit_type(self, operated_unit, operated_unit_type_tuple):
        """
        Check if the unit type corresponds to the actor energy unit type
        otherwise it raises a TypeError

        :param operated_unit: operated energy unit on the actor scope of
            responsibility
        :param operated_unit_type_tuple: available type of the energy units
            considering the actor plus energynode type
        """
        if not issubclass(operated_unit.__class__, operated_unit_type_tuple):
            raise TypeError("The operated unit type {0} does not correspond "
                            "to the actor energy unit type {1} ".format(
                operated_unit.__class__, operated_unit_type_tuple))
