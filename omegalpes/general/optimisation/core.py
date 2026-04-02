#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module define the main Core object on which the energy units and actors
will be based**

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

from .elements import Quantity, Constraint, Objective, \
    TechnicalConstraint, TechnicalDynamicConstraint

__docformat__ = "restructuredtext en"


class OptObject:
    """
    **Description**

        OptObject class is used as an "abstract class", i.e. it defines some
        general attributes and methods but doesn't contain variable,
        constraint nor objective. In the OMEGAlpes package, all the
        subsystem models are represented by a unit. A model is then
        generated adding OptObject to it.
        Variable, objective and constraints declarations are usually done
        using the __init__ method of the OptObject class.

    **Attributes**

     - name
     - description
     - _quantities_list : list of the quanitities of the OptObject
       (active or not)
     - _constraints_list : list of the constraints of the OptObject(active or
       not)
     - _technical_constraints_list : list of the constraints of the OptObject
       (active or not)
     - _objectives_list : list of the objectives of the OptObject
       (active or not)


    **Methods**

     - __str__: defines the
     - __repr__: defines the unit with its name
     - get_constraints_list
     - get_constraints_name_list
     - get_external_constraints_list
     - get_external_constraints_name_list
     - get_objectives_list
     - get_objectives_name_list
     - get_quantities_list
     - get_quantities_name_list
     - deactivate_optobject_external_constraints


    .. note::
        The OptObject class shouldn't be instantiated in a python script,
        except if you want to create your own model from the beginning.
        In this case, one should consider creating a new class
        NewModel(OptObject).
    """

    def __init__(self, name='U0', description="Optimization object",
                 verbose=True):
        self.name = name
        self.description = description
        self.units_list = []
        self._quantities_list = []
        self._constraints_list = []  # all constraints are in this list
        self._technical_constraints_list = []  # only for technical constraints
        self._actor_constraints_list = []  # only for actor's constraints
        self._objectives_list = []
        self._pareto_objectives_list = []

        if verbose:
            print(("Creating the {0}.".format(name)))

    def __str__(self):
        """"
        Add in the expression of the unit the variables, constraints and
        objectives

        :return: string
        """
        import numpy
        var = {}
        cst = {}
        cstr = {}
        obj = {}
        exp = '<OMEGALPES.general.units.OptObject: \nname: {0} \ndescription: {1}' \
              '\n'.format(self.name, self.description)
        for u_key in list(self.__dict__.keys()):
            key: (Quantity, Constraint, Objective) = getattr(self, u_key)
            if isinstance(key, Quantity):
                if isinstance(key.opt, bool):
                    if key.opt:
                        var[u_key] = key
                    else:
                        cst[u_key] = key
                elif isinstance(key.opt, dict):
                    if numpy.array(list(key.opt.values())).all():
                        var[u_key] = key
                    else:
                        cst[u_key] = key
            elif isinstance(key, Constraint):
                cstr[u_key] = key
            elif isinstance(key, Objective):
                obj[u_key] = key
        exp += '\nOptimization variables:\n'
        for u_key in list(var.keys()):
            exp += 'name: ' + getattr(self, u_key).name + '\n'
        exp += '\nConstants:\n'
        for u_key in list(cst.keys()):
            exp += 'name: ' + getattr(self, u_key).name + ',  value: ' + \
                   str(getattr(self, u_key).value) + '\n'
        exp += '\nConstraints:\n'
        for u_key in list(cstr.keys()):
            exp += '[' + str(getattr(self, u_key).active) + ']' + ' name: ' + \
                   getattr(self, u_key).name + ' exp: ' + \
                   str(getattr(self, u_key).exp) + '\n'
        exp += '\nObjective:\n'
        for u_key in list(obj.keys()):
            exp += '[' + str(getattr(self, u_key).active) + ']' + 'name: ' \
                   + getattr(self, u_key).name + ' exp: ' + \
                   str(getattr(self, u_key).exp) + '\n'
        return exp

    def __repr__(self):
        """
        Return the description of the unit considering the name

        :return: string
        """
        return "<OMEGALPES.general.optimisation.units.OptObject: name:\'{0}\'>" \
            .format(self.name)

    def get_constraints_list(self):
        """ Get the constraints associated with the unit
        as a dictionary shape ['constraint_name' , constraint]
        """
        cst_dict = {}
        for cst in self._constraints_list:
            cst_dict[cst.name] = cst
        return cst_dict

    def get_constraints_name_list(self):
        """ Get the names of the constraints associated with the unit """
        constraints_name_list = []
        for constraint in self._constraints_list:
            constraints_name_list.append(constraint.name)
        return constraints_name_list

    def get_technical_constraints_list(self):
        """ Get the technical constraints associated with the unit
        as a dictionary shape ['constraint_name' , constraint]
        """
        tech_cst_dict = {}
        for tech_cst in self._technical_constraints_list:
            tech_cst_dict[tech_cst.name] = tech_cst
        return tech_cst_dict

    def get_technical_constraints_name_list(self):
        """ Get the names of the external constraints associated with the
        unit """
        tech_csts_name_list = []
        for tech_cst in self._technical_constraints_list:
            tech_csts_name_list.append(tech_cst.name)
        return tech_csts_name_list

    def get_actor_constraints_list(self):
        """ Get the technical constraints associated with the unit
        as a dictionary shape ['constraint_name' , constraint]
        """
        actor_cst_dict = {}
        for actor_cst in self._actor_constraints_list:
            actor_cst_dict[actor_cst.name] = actor_cst
        return actor_cst_dict

    def get_actor_constraints_name_list(self):
        """ Get the names of the external constraints associated with the
        unit """
        actor_csts_name_list = []
        for actor_cst in self._actor_constraints_list:
            actor_csts_name_list.append(actor_cst.name)
        return actor_csts_name_list

    def get_objectives_list(self):
        """ Get objectives associated with the unit
        as a dictionary shape ['objective_name' , objective]
        """
        obj_dict = {}
        for obj in self._objectives_list:
            obj_dict[obj.name] = obj
        return obj_dict

    def get_objectives_name_list(self):
        """ Get the names of the objectives associated with the unit """
        objectives_name_list = []
        for objective in self._objectives_list:
            objectives_name_list.append(objective.name)
        return objectives_name_list

    def get_quantities_list(self):
        """ Get the quantities associated with the unit
        as a dictionary shape ['quantity_name' , quantity]
        """
        quantity_dict = {}
        for quantity in self._quantities_list:
            quantity_dict[quantity.name] = quantity
        return quantity_dict

    def get_quantities_name_list(self):
        """ Get the names of the quantities associated with the unit """
        quantities_name_list = []
        for quantity in self._quantities_list:
            quantities_name_list.append(quantity.name)
        return quantities_name_list

    def deactivate_optobject_external_constraints(self, ext_cst_name_list=None):
        """
        Enable to remove an external constraint linked with an OptObject

        :param ext_cst_name_list: list of external constraint that would be
            removed
        """
        if not ext_cst_name_list:
            cst_dict = self.get_constraints_list()
            for key in cst_dict:
                if isinstance(cst_dict[key],
                              TechnicalConstraint or
                              TechnicalDynamicConstraint):
                    cst_dict[key].deactivate_constraint()
                else:
                    Warning('Only external constraints can be removed')
        else:
            cst_dict = self.get_constraints_list()
            for cst_name in ext_cst_name_list:
                for key in cst_dict:
                    if cst_name == key:
                        if isinstance(cst_dict[key],
                                      TechnicalConstraint or TechnicalDynamicConstraint):
                            cst_dict[key].deactivate_constraint()
                        else:
                            Warning('Only external constraints can be removed')
                    else:
                        pass

    def _deactivate_optobject_constraints(self, cst_name_list=None):
        """
        /!\ Should only be used for debug
        Enable to remove all kind of constraints (internal and external) linked
        with an OptObject.
        The constraint can be selected if cst_name_list is filled
        Warning, up and low limits are not constraints

        :param cst_name_list: list of external constraint that would be
            removed
        """
        if not cst_name_list:
            cst_dict = self.get_constraints_list()
            for key in cst_dict:
                cst_dict[key]._deactivate_constraint()

        else:
            cst_dict = self.get_constraints_list()
            for cst_name in cst_name_list:
                for key in cst_dict:
                    if cst_name == key:
                        cst_dict[key]._deactivate_constraint()
                    else:
                        pass
