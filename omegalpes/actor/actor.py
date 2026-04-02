#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This modules define the basic Actor object**

 Few methods are available:

    - add_external_constraint
    - add_external_dynamic_constraint
    - add_objective

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
from ..general.optimisation.core import OptObject
from ..general.optimisation.elements import *

class Actor(OptObject):
    """
    **Description**

        Actor class is the basic class to model an actor. The basic actor
        is defined by its name and description.
        An actor is then defined by its constraints and objectives.

    **Attributes**

     - description : description as an Actor OptObject
    """

    def __init__(self, name, no_warn=True, verbose=True):
        OptObject.__init__(self, name=name, verbose=verbose)

        self.description = 'Actor OptObject'

    def add_actor_constraint(self, cst_name, exp):
        """
        Enable to add an external constraint linked with an actor

        :param cst_name: name of the constraint
        :param exp: expression of the constraint

        """
        setattr(self, cst_name, ActorConstraint(exp=exp,
                                                name=cst_name, parent=self))

    def add_actor_dynamic_constraint(self, cst_name, exp_t,
                                     t_range='for t in time.I'):
        """
        Enable to add an external dynamic constraint linked with an actor.
        A dynamic constraint changes over time

        :param cst_name: name of the constraint
        :param exp: expression of the constraint depending on the time
        :param t_range: expression of time for the constraint
        """
        setattr(self, cst_name, ActorDynamicConstraint(exp_t=exp_t,
                                                       name=cst_name,
                                                       t_range=t_range,
                                                       parent=self))

    def remove_actor_constraints(self, ext_cst_name_list=None):
        """
        Enable to remove an external constraint linked with an actor

        :param ext_cst_name_list: list of external constraint that would be
            removed
        """
        if not ext_cst_name_list:
            cst_dict = self.get_constraints_list()
            for key in cst_dict:
                if isinstance(cst_dict[key],
                              ActorConstraint or ActorDynamicConstraint):
                    cst_dict[key].deactivate_constraint()
                else:
                    Warning('Only external constraints can be removed')
        else:
            cst_dict = self.get_constraints_list()
            for cst_name in ext_cst_name_list:
                for key in cst_dict:
                    if cst_name == key:
                        if isinstance(cst_dict[key],
                                      ActorConstraint or
                                      ActorDynamicConstraint):
                            cst_dict[key].deactivate_constraint()
                        else:
                            Warning('Only external constraints can be removed')
                    else:
                        pass

    def add_objective(self, obj_name, exp):
        """
        Enable to add an objective linked with an actor

        :param obj_name: name of the objective
        :param exp: expression of the objective
        """
        setattr(self, obj_name, Objective(exp=exp, name=obj_name, parent=self))
