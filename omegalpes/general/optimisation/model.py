#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module enables to fill the optimization model and formulate it in
LP or MILP based on the package PuLP (LpProblem)**

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

import os
import warnings
import glob
import collections
import time as pytime
import numpy as np
import copy
from pulp import PULP_CBC_CMD

from pulp import LpProblem, LpStatus, LpVariable, lpSum
from pulp.apis import LpSolver

from ..optimisation.core import OptObject
from ..optimisation.elements import *
from ..time import TimeUnit
from ...energy.energy_nodes import EnergyNode
from ...actor.actor import Actor
from ...energy.units.energy_units import AssemblyUnit

from lpfics.lpfics import find_infeasible_constraint_set

__docformat__ = "restructuredtext en"


class OptimisationModel(LpProblem):
    """
    **Description**

        This class includes the optimization model formulated in LP or MILP
        based on the package PuLP (LpProblem)

    """

    def __init__(self, time, name='optimisation_model', verbose = True):
        """
        :param time:
        :param name:
        """
        LpProblem.__init__(self, name)
        self.verbose = verbose
        self.noOverlap = False
        self.time = time
        self.quantities = collections.OrderedDict()
        self._model_units_list = []
        self._model_quantities_list = []
        self._model_constraints_list = []
        self._model_objectives_list = []
        self._model_pareto_objectives_list = []

    def add_nodes(self, *nodes):
        """
        Add nodes and all connected units to the model
        Check that the time is the same for the model and all the units

        :param nodes: EnergyNode
        """
        for node in nodes:
            if not isinstance(node, EnergyNode):
                raise TypeError(
                    'You have to add nodes from type "EnergyNode".')
            if node not in self._model_units_list:
                self._model_units_list.append(node)
                node.set_power_balance()

            for unit in node.get_connected_energy_units:
                if unit not in self._model_units_list:
                    self._model_units_list.append(unit)

            for unit in self._model_units_list:
                if hasattr(unit, 'time'):
                    if len(self.time.DATES) == len(unit.time.DATES):
                        for i in range(len(self.time.DATES)):
                            if not self.time.DATES[i] == unit.time.DATES[i]:
                                raise ValueError(
                                    'The unit {} does not operate on the '
                                    'same time of the model'.format(
                                        unit.name))
                    else:
                        raise ValueError('The unit {} does not operate on the '
                                         'same time of the model'.format(
                            unit.name))

                self._add_unit_parent(unit)
                self._add_unit_attributes(unit)

        self._add_quantities()
        self._add_objectives(nodes[0].time)
        self._add_constraints(nodes[0].time)

    def add_nodes_and_actors(self, *nodes_or_actors):
        """
        Add nodes, actors and all connected units to the model
        Check that the time is the same for the model and all the units

        :param nodes_or_actors: EnergyNode or Actor type
        """
        init_time = pytime.time()
        for node_or_actor in nodes_or_actors:
            if isinstance(node_or_actor, Actor):
                if node_or_actor not in self._model_units_list:
                    self._model_units_list.append(node_or_actor)

            elif isinstance(node_or_actor, EnergyNode):
                if node_or_actor not in self._model_units_list:
                    self._model_units_list.append(node_or_actor)
                    node_or_actor.set_power_balance()

                for unit in node_or_actor.get_connected_energy_units:
                    if unit not in self._model_units_list:
                        self._model_units_list.append(unit)

            else:
                raise TypeError('You have to add actors or nodes from type '
                                '"Actor" or "EnergyNode".')

            for unit in self._model_units_list:
                if hasattr(unit, 'time'):
                    if len(self.time.DATES) == len(unit.time.DATES):
                        for i in range(len(self.time.DATES)):
                            if not self.time.DATES[i] == unit.time.DATES[i]:
                                raise ValueError(
                                    'The unit {} does not operate on the '
                                    'same time of the model'.format(
                                        unit.name))
                    else:
                        raise ValueError('The unit {} does not operate on the '
                                         'same time of the model'.format(
                            unit.name))

                self._add_unit_parent(unit)
                self._add_unit_attributes(unit)

        self._add_quantities()
        self._add_objectives(self.time)
        self._add_constraints(self.time)
        print('Generation duration =', pytime.time() - init_time,
              'seconds.')

    def _add_unit_parent(self, unit: OptObject) -> None:
        """
        If the parent of the unit is a OptObject, the method adds it to the
        list of units : self._model_units_list
        Else : nothing happens

        :param unit: OptObject whose parent will be added to the list of units
        if also a OptObject
        """

        try:
            parent = getattr(unit, 'parent')
            if isinstance(parent,
                          OptObject) and parent not in self._model_units_list:
                self._model_units_list.append(parent)
        except AttributeError:
            check_if_unit_could_have_parent(unit)

    def _add_unit_attributes(self, unit: OptObject) -> None:
        """
        Adds :
            - The OptObject elements contained in the unit to the list of units
                self._model_units_list
            - The Quantity elements contained in the unit to the list of
                quantities self._model_quantities_list
            - The Constraint elements contained in the unit to the list of
                constraints self._model_constraints_list
            - The Objective elements contained in the unit to the list of
                objectives self._model_objectives_list

        :param unit: OptObject whose attributes (OptObject, Quantity,
        Constraint
        and Objective) will be added to the respective lists
        """
        try:
            for key in list(unit.__dict__.keys()):
                child = getattr(unit, key)
                if isinstance(child,
                              OptObject) and child not in \
                        self._model_units_list:
                    self._model_units_list.append(child)
                elif isinstance(child, Quantity) and child not in \
                        self._model_quantities_list:
                    child.parent = unit
                    self._model_quantities_list.append(child)
                elif isinstance(child, Constraint) and child.active and child \
                        not in self._model_constraints_list:
                    child.parent = unit
                    self._model_constraints_list.append(child)
                elif isinstance(child, Objective) and child not in \
                        self._model_objectives_list:
                    child.parent = unit
                    self._model_objectives_list.append(child)

        except AttributeError:
            pass

    def _add_quantities(self) -> None:
        """
        Adds all quantities as LpVariable to the list self.variables_list
        """

        print('\n--- Adding all variables to the model ---')
        for quantity in self._model_quantities_list:
            q_name = getattr(quantity, 'name')
            val = getattr(quantity, 'value')
            opt = getattr(quantity, 'opt')
            vtyp = getattr(quantity, 'vtype')
            lb, ub = getattr(quantity, 'lb'), getattr(quantity, 'ub')
            try:
                parent = getattr(quantity, 'parent')
                p_name = parent.name
            except AttributeError:
                raise ValueError('Each Quantity object should have a parent')

            new_name = p_name + '_' + q_name

            self._add_quantity(q_name=new_name, q_val=val, q_type=vtyp,
                               q_lb=lb, q_ub=ub, q_opt=opt,
                               parent=quantity.parent)

            # Add the whole variable as an attribute of Variable
            # added in the optimization model
            self.quantities[new_name] = quantity

    def _add_quantity(self, q_name, q_val, q_type, q_lb, q_ub, q_opt,
                      parent=None):
        """
        Adds a quantity as LpVariable to the list self.variables_list
        """
        if self.verbose:
            print('Adding variable : {0}'.format(q_name))

        # Static or dynamic bounds
        if isinstance(q_lb, list):
            lb_cst_exp = q_name + '[t] >= ' + str(q_lb) + '[t]'
            setattr(parent, 'set_lb', DefinitionDynamicConstraint(
                exp_t=lb_cst_exp,
                name='set_lb',
                parent=parent))
            q_lb = min(q_lb)

        if isinstance(q_ub, list):
            ub_cst_exp = q_name + '[t] <= ' + str(q_ub) + '[t]'
            setattr(parent, 'set_ub', DefinitionDynamicConstraint(
                exp_t=ub_cst_exp,
                name='set_ub',
                parent=parent))
            q_ub = max(q_ub)

        # If the values are stored in a dictionary
        if isinstance(q_val, dict):
            if any(i for i in q_opt.values()):
                globals()[q_name] = LpVariable.dict(name=q_name,
                                                    indices=q_val.keys(),
                                                    lowBound=q_lb,
                                                    upBound=q_ub,
                                                    cat=q_type)

            else:
                globals()[q_name] = q_val

        # If the values are stored in a list
        elif isinstance(q_val, list):
            for ind, opt in enumerate(q_opt):
                if opt:
                    var_name = q_name + '_{0}'.format(ind)
                    globals()[var_name] = LpVariable(name=var_name,
                                                     lowBound=q_lb,
                                                     upBound=q_ub,
                                                     cat=q_type)
                else:
                    if ind == 0:
                        globals()[q_name] = q_val

        # If the values are stored in a int/float
        elif isinstance(q_val, (int, float)):
            if q_opt:
                globals()[q_name] = LpVariable(name=q_name,
                                               lowBound=q_lb,
                                               upBound=q_ub,
                                               cat=q_type)
            else:
                globals()[q_name] = q_val

        else:
            raise TypeError('Value type of the quantity {0} of unit {1} '
                            'is not taken into account'.format(q_name,
                                                               parent.name))

    def _add_constraints(self, time: TimeUnit) -> None:
        """
        Add all constraints to the model

        :param time: TimeUnit
        """
        print('\n--- Adding all constraints to the model ---')
        for cst in self._model_constraints_list:
            cst_name = cst.parent.name + '_' + cst.name
            cst_exp = cst.exp

            # Print the constraint expression
            if self.verbose:
                print('Adding constraint : {0} , exp = {1}'.format(cst_name,
                                                                   cst_exp))

            if isinstance(cst, DynamicConstraint):
                loop_exp = "".join([cst.t_range, ':\n'
                                                 '\ttry:\n'
                                                 '\t\tself += {0}, '
                                                 ''.format(cst.exp_t),
                                    '"{0}_{1}".format(cst_name, t)\n'
                                    '\t\tself.constraints[ "{0}_{1}".format('
                                    'cst_name, t)].cst = cst\n'
                                    '\texcept TypeError:\n'
                                    '\t\twarnings.warn("Possible error")'])
                exec(loop_exp)

            else:
                try:
                    # Add the constraint to the optimization model
                    self += eval(cst_exp), cst_name
                    # self.addConstraint(eval(cst_exp), cst_name)

                    # Add the whole constraint as an attribute of constraint
                    # added in the optimization model
                    self.constraints[cst_name].cst = cst

                except TypeError:
                    warnings.warn('Possible error')

    def _add_objectives(self, time: TimeUnit) -> None:
        """
        Adds all objectives to the model

        :param time: TimeUnit
        """
        print('\n--- Adding all objectives to the model ---')
        objective = 0
        for obj in self._model_objectives_list:
            obj_name = obj.parent.name + '_' + obj.name
            obj_exp = obj.exp
            obj_weight = str(obj.weight)

            if self.verbose:
                print('Adding objective : {0}'.format(obj_name))

            if obj.pareto:
                self._model_pareto_objectives_list.append(obj)
            else:
                objective += eval(obj_weight + ' * (' + obj_exp + ')')
        self += objective, "obj_tot"

    def _pareto_and_solve(self, solver=None, pareto_step=0.1):
        """
        Solves the optimization model to produce a pareto front.

        """
        pareto_models = []
        time = self.time
        i = 0

        if pareto_step > 1 or pareto_step <= 0:
            raise ValueError('The pareto step should be positive and its'
                             'value should be less than 1')
        if len(self._model_pareto_objectives_list) == 2:
            for alpha in np.arange(0.0, 1.00001, pareto_step):
                i = i + 1
                print("\n - - - - RUN OPTIMIZATION {0} - - - - ".format(i))
                pareto_model = None
                pareto_model = copy.deepcopy(self)
                pareto_model.objective += \
                    eval(str(alpha) + ' * (' +
                         pareto_model._model_pareto_objectives_list[
                             0].exp + ')')
                pareto_model.objective += \
                    eval(str(1 - alpha) + ' * (' +
                         pareto_model._model_pareto_objectives_list[
                             1].exp + ')')
                print('{0} * {1} + {2} * {3}'.format(
                    alpha, pareto_model._model_pareto_objectives_list[0].exp,
                    1 - alpha,
                    pareto_model._model_pareto_objectives_list[1].exp))

                if solver is None:
                    pareto_model.solve(solver=PULP_CBC_CMD(timeLimit=60), use_mps=False)
                else:
                    pareto_model.solve(solver=solver, use_mps=False)

                if LpStatus[pareto_model.status] != 'Optimal':
                    print('Your problem should have solution before launching'
                          'the method pareto_solve()')
                else:
                    print("\n- - UPDATE RESULTS IN PARETO MODEL {}"
                          " - - ".format(i))
                    pareto_model.update_units()
                    pareto_models.append(copy.deepcopy(pareto_model))
                    del pareto_model
            self.pareto_models = pareto_models
            print("\n- - WARNING - -")
            print(" A time limit has been set at 60 seconds")
            print(" A way to change it is to change the solve method of the model with the following script")
            print("\n (solver=PULP_CBC_CMD(timeLimit = T ), use_mps=False)")
            print("\n with T the number of seconds you need to perform your pareto assessment")
            print("\n- - WARNING - -")
        else:
            print('Your problem should have exactly 2 pareto objectives and '
                  'not {}'.format(len(self._model_pareto_objectives_list)))

    def update_units(self):
        """
        Updates all units values with optimization results
        """
        var_dict = self.variablesDict()
        for unit in self._model_units_list:
            print("Updating unit : {0}".format(unit.name))
            for key in list(unit.__dict__.keys()):
                quantity = getattr(unit, key)
                if isinstance(quantity, Quantity):
                    q_name = getattr(quantity, 'name')
                    q_opt = getattr(quantity, 'opt')
                    q_value = getattr(quantity, 'value')

                    print("\tQuantity : {0}".format(q_name))

                    if isinstance(q_value, (float, int)) and q_opt:
                        quantity.value = var_dict[
                            "{0}_{1}".format(unit.name, q_name)].varValue

                    elif isinstance(q_value, list):
                        for i, _ in enumerate(q_opt):
                            if quantity.opt[i]:
                                quantity.value[i] = var_dict[
                                    "{0}_{1}_{2}".format(unit.name,
                                                         q_name, i)].varValue

                    elif isinstance(q_value, dict):
                        for i in list(q_value.keys()):
                            try:
                                quantity.value[i] = var_dict[
                                    "{0}_{1}_{2}".format(unit.name,
                                                         q_name, i)].varValue
                            except KeyError:
                                pass

    def solve_and_update(self, solver: LpSolver = None,
                         find_infeasible_cst_set=False, pareto_step=0.1) -> \
            None:
        """
        Solves the optimization model and updates all variables values.

        :param solver: Optimization solver
        :type solver: LpSolver
        :param pareto_step: if there are pareto objectives, you can change
            the step to calculate the pareto front
        """
        if not self._model_pareto_objectives_list:
            print("\n - - - - - RUN OPTIMIZATION - - - - - ")
            if solver is None:
                start_time = pytime.time()
                self.solve(solver=solver, use_mps=False)
                print('Resolution duration =', pytime.time() - start_time,
                      'seconds.')
            else:
                self.solve(solver=solver)

            if LpStatus[self.status] == 'Optimal':
                print("\n - - - - - UPDATE RESULTS - - - - - ")
                self.update_units()
            else:
                # warnings.warn("Your optimization failed with status : {
                # }.".format(
                #     LpStatus[self.status]))
                print("\n\n/!\ Your optimization FAILED with status : {} "
                      "/!\.".format(
                    LpStatus[self.status]))
                if LpStatus[self.status] == 'Infeasible':
                    print(
                        '\nIf you want to catch the source of infeasibility:\n'
                        '* Please download LPFICS and use the method '
                        'find_infeasible_constraint_set(your_model)\n'
                        'You can also use according to your needs:\n'
                        '- '
                        'find_definition_and_actor_infeasible_constraints_set('
                        'your_model)\n'
                        '- find_definition_and_technical_'
                        'infeasible_constraints_set(your_model)')
                    print(
                        '* If you are a Gurobi user, you can also refer to '
                        'the '
                        'method "compute_gurobi_IIS()" in '
                        'general\optimation\model.')
                    if find_infeasible_cst_set:
                        find_infeasible_constraint_set(self)
                if LpStatus[self.status] == 'Not Solved':
                    print('You can maybe try with another solver')
        else:
            self._pareto_and_solve(solver=solver,
                                   pareto_step=pareto_step)

    def get_model_constraints_list(self):
        """ Gets constraints of the model """
        return self._model_constraints_list

    def get_model_constraints_name_list(self):
        """ Gets the names of the constraints of the model """
        constraints_name_list = []
        for constraint in self._model_constraints_list:
            new_objective_name = constraint.parent.name + '_' + constraint.name
            constraints_name_list.append(new_objective_name)
        return constraints_name_list

    def get_model_quantities_list(self):
        """ Gets quantities of the model """
        return self._model_quantities_list

    def get_model_quantities_name_list(self):
        """ Gets the names of the quantities of the model """
        quantities_name_list = []
        for quantity in self._model_quantities_list:
            new_objective_name = quantity.parent.name + '_' + quantity.name
            quantities_name_list.append(new_objective_name)
        return quantities_name_list

    def get_model_objectives_list(self):
        """ Gets objectives of the model """
        return self._model_objectives_list

    def get_model_objectives_name_list(self):
        """ Gets the names of the objectives of the model """
        objectives_name_list = []
        for objective in self._model_objectives_list:
            new_objective_name = objective.parent.name + '_' + objective.name
            objectives_name_list.append(new_objective_name)
        return objectives_name_list


def check_if_unit_could_have_parent(unit):
    """ Checks if the unit has an associated parent

    :param unit: unit which parents will be checked
    """
    import gc
    ref = gc.get_referrers(unit)
    attributes = gc.get_referents(unit)[0]

    for parent in ref:
        try:
            parent_name = parent['name']
            if parent_name not in attributes:
                if not isinstance(unit, (AssemblyUnit, Actor)):
                    warnings.warn('The unit {} seems to have as parent {} '
                                  'which was not declared as '
                                  'parent.'.format(unit.name, parent_name))
                elif isinstance(unit, AssemblyUnit):
                    prod_names = [prod.name for prod in unit.prod_units]
                    cons_name = [cons.name for cons in unit.cons_units]
                    rev_name = [rev.name for rev in unit.rev_units]
                    if (parent_name in prod_names) or (parent_name in
                                                       cons_name) or \
                            parent_name in rev_name:
                        pass
                    else:
                        warnings.warn('The unit {} seems to have as '
                                      'parent {} '
                                      'which was not declared as '
                                      'parent.'.format(unit.name, parent_name))
        except (TypeError, KeyError):
            pass


def compute_gurobi_IIS(gurobi_exe_path=r'C:\gurobi810\win64\bin',
                       opt_model=None, MPS_model=None):
    """
    Identifies the constraints in a .ilp file

    :param gurobi_exe_path: Path to the gurobi solver "gurobi_cl.exe"
    :param opt_model: OptimisationModel to whom compute IIS
    :param MPS_model: name of the mps model
    """
    try:
        # Remove all the existing .mps in your directory
        os.system('"del ' + str('*.mps') + '"')
    except:
        pass

    if MPS_model is None:
        # Create the .mps  in order to get the .mps
        if opt_model is None:
            raise ValueError('You should provide either the OptimisationModel '
                             'or the MPS model')
        opt_model.solve()
        opt_model.writeMPS('{}.mps'.format(opt_model.name))
        MPS_file = glob.glob("*.mps")

    else:
        if MPS_model[-4:] == '.mps':
            MPS_file = [MPS_model]
        else:
            MPS_file = [MPS_model + '.mps']

    # Transform the .mps into a .ilp'
    cmd = '"' + gurobi_exe_path + '\gurobi_cl.exe ResultFile=IISresults.ilp ' \
          + MPS_file[0] + '"'
    os.system(cmd)
