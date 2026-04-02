#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module includes the optimization elements (quantities, constraints and
objectives) formulated in LP or MILP**

 - Quantity : related to the decision variable or parameter
 - Constraint : related to the optimization problem constraints
   4 categories of constraints :
    - Constraint: to define a constraint object
    - DefinitionConstraint: to calculate and define quantities or for physical
    constraints
    - TechnicalConstraint: linked with technical constraints
    - ActorConstraint: constraint decided by the actors
    2 types of constraints:
    - Constraints : basic constraint
    - DynamicConstraint: basic constraint depending on the time
 - Objective : related to the objective function

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

import datetime
import numpy as np
import pandas as pd
from pulp import LpContinuous

__docformat__ = "restructuredtext en"


class Quantity:
    """
    **Description**

        Class that defines what is a quantity. A quantity can wether be a
        decision variable or a parameter, depending on the opt parameter

    **Attributes**

     - name (str) : the name of the quantity
     - description (str) :  a description of the meaning of the quantity
     - vtype (PuLP) : the variable type, depending on PuLP

        * LpBinary (binary variable)
        * LpInteger (integer variable)
        * LpContinuous (continuous variable)
     - vlen (int) : size of the variable
     - unit (str) : unit of the quantity
     - opt (binary)

        * True: this is an optimization variable
        * False: this is a constant - a parameter
     - value (float, list, dict) : value (unused if opt=True)
     - ub, lb : upper and lower bounds
     - parent (OptObject) : the quantity belongs to this unit

    .. note::
        Make sure that all the modifications on Quantity are made before
        adding the unit to the Model
    """

    def __init__(self, name="var0", opt=True, unit="s.u", vlen=None,
                 value=None, description="", vtype=LpContinuous,
                 lb=None, ub=None, parent=None):
        """

        :param name: (str) name of the quantity
        :param opt: (binary) optimisation parameter
        :param unit: (str) unit of the quantity
        :param vlen: (int) size of the quantity value
        :param value: (float, list or dict) value of the quantity
        :param description: (str) description of the quantity
        :param vtype: (type) the variable type according to PuLP
        :param lb: (float or int) : lower bound of the value of the quantity
        :param ub: (float or int) : upper bound of the value of the quantity
        :param parent: (OptObject) parent unit
        """

        self.name = name
        if vlen is None:
            try:
                vlen = len(value)
            except TypeError:
                vlen = 1

        if parent is None:
            print('Warning : Parent argument of {0} is None'.format(self.name))

        self.vlen = vlen
        self.description = description
        self.unit = unit
        self.lb = lb
        self.ub = ub
        self.vtype = vtype
        self.value = {}

        if not isinstance(vlen, int):
            raise TypeError('vlen should be of type int !')

        if isinstance(opt, bool):
            # The optimisation parameter is a boolean
            if isinstance(value, (int, float)):
                # The value is an int or a float
                self.opt = opt
                if value:
                    # If the value is not None, the opt parameter should be
                    # False
                    self.opt = False
                if vlen <= 1:
                    self.value = value
                else:
                    # vlen should be 1 for ints and floats values
                    raise ValueError(
                        'value\'s size is given as vlen = {0}, but the value '
                        'is actually a {1}'.format(vlen, type(value)))

            elif isinstance(value, list):
                # The value is a list
                if value:
                    # If value is not None, the opt parameter is a list of
                    # False
                    self.opt = []
                    for i in range(vlen):
                        self.opt.append(False)
                if len(value) == vlen:
                    self.value = value
                else:
                    # vlen should be the list length
                    raise ValueError(
                        'value\'s size ({0}) should be vlen ({1})'.format(
                            len(value), vlen))

            elif isinstance(value, dict):
                # The value is a dict
                if any(isinstance(n, (int, float)) for n in list(
                        value.values())):
                    # At least one value of the dict is specified
                    self.opt = {}
                    # The opt parameter is a dict of False
                    self.opt.update({i: False for i in list(value.keys())})
                    print('At least one value is specified in the dict '
                          'value : the opt parameter is set as a dict of '
                          'False with the value keys')
                else:
                    self.opt = {}
                    self.opt.update({i: opt for i in list(value.keys())})

                if len(value) == vlen:
                    self.value = value
                else:
                    # vlen should be the dict value size
                    raise ValueError(
                        'value\'s size ({0}) should be vlen ({1})'.format(
                            len(value), vlen))

            elif value is None:
                if not opt:
                    # The quantity should have a specified value if
                    # opt=False OR opt should be set to True if the Quantity
                    #  is a decision variable
                    raise Exception('If the Quantity.opt == False, '
                                    'Quantity.value cannot be None. '
                                    'Value is required, or opt must be set '
                                    'to True !')
                elif vlen >= 2:
                    # if opt=True, the value is given the default value 0,
                    # or a list of 0 if vlen>=2
                    self.opt = {i: opt for i in range(vlen)}
                    self.value = {i: 0 for i in range(vlen)}

                else:
                    self.opt = opt
                    self.value = 0

            else:
                # Value should be either an int, a float, a list, a dict or
                # None
                raise TypeError('Unknown type for argument \'value\'')

        elif isinstance(opt, (list, dict)):
            raise Exception('Not implemented yet...')

        else:
            # opt should be a boolean, a list or a dict
            raise TypeError('Unknown type for argument \'opt\'')

        self.parent = parent
        self._add_quantity_list()

    def __str__(self):
        # String special method
        return str(self.value)

    def __repr__(self):
        # Repr special method
        if isinstance(self.opt, bool):
            exp = '<OMEGALPES.general.optimisation.elements.Quantity : (' \
                  'name:\'{0}\', opt:{1}, vlen:{1})> \n'.format(self.name,
                                                                self.opt,
                                                                self.vlen)
        elif isinstance(self.opt, list):
            exp = '<OMEGALPES.general.optimisation.elements.Quantity : (' \
                  'name:\'{0}\', opt[0]:{1}, vlen:{2})> \n'.format(self.name,
                                                                   self.opt[0],
                                                                   self.vlen)

        elif isinstance(self.opt, dict):
            exp = '<OMEGALPES.general.optimisation.elements.Quantity : (' \
                  'name:\'{0}\', opt:{1}, vlen:{2})> \n'.format(self.name,
                                                                list(
                                                                    self.opt.values()),
                                                                self.vlen)
        return exp

    def __float__(self):
        # Special method float (only works for int and float values,
        # not list and dict ones)
        return float(self.value)

    def get_value(self):
        """ return the value of the quantity according the type of the value
        in order to be able to use it easily in print and plot methods:
        int -> int
        float -> float
        list -> list
        dict -> list
        ndarray --> list
        """
        if isinstance(self, Quantity):
            if isinstance(self.value, dict):
                return list(self.value.values())

            if isinstance(self.value, np.ndarray):
                return list(self.value.values().tolist())

            else:
                return self.value
        else:
            raise TypeError('you can only use the get_value() method on'
                            'quantities')

    def get_value_with_date(self, unit=None):
        """ return the values of the quantity associated to a date in a
        dataframe if the values are a list or a dict (only).
        """
        if not unit:
            unit = self.unit
        else:
            pass

        if isinstance(self, Quantity):
            if isinstance(self.value, dict):

                df = pd.DataFrame(data=list(self.value.values()),
                                  index=self.parent.time.DATES,
                                  columns=['Value in {}'.format(unit)])
                return df

            if isinstance(self.value, list):
                df = pd.DataFrame(data=list(self.value),
                                  index=self.parent.time.DATES,
                                  columns=['Value in {}'.format(unit)])
                return df

            else:
                raise TypeError(
                    'the value {} should be a list or a dict'.format(
                        self.name))

        else:
            raise TypeError('you can only use the get_value() method on'
                            'quantities')

    def _add_quantity_list(self):
        if self.parent:
            if self not in self.parent._quantities_list:
                self.parent._quantities_list.append(self)
        else:
            Warning("the quantity {} should have a parent otherwise "
                    "the quantity won't be added to the parent "
                    "_quantities_list".format(self.name))


class Constraint:
    """
    **Description**

        Class that defines a constraint object

    **Attributes**

     - name: name of the constraint
     - description: a description of the constraint
     - active:
       False = non-active constraint;
       True = active constraint
     - exp: (str) : expression of the constraint
     - parent: (unit) : this constraint belongs to this unit

    .. note::
        Make sure that all the modifications on Constraints are made before
        adding the unit to the Model (OptimisationModel.addUnit()).

    """

    def __init__(self, exp, name='CST0', description='', active=True,
                 parent=None):
        """

        :param exp: (str) expression of the constraint
        :param name: (str) name of the constraint
        :param description: (str) description of the constrain
        :param active: (bool) is the constraint active or not
        :param parent: (OptObject) parent unit
        """
        self.name = name
        self.description = description
        self.exp = exp
        self.active = active
        self.parent = parent
        self._add_cst_list()

    def _add_cst_list(self):
        if self.parent:
            if self not in self.parent._constraints_list:
                self.parent._constraints_list.append(self)
        else:
            Warning("the constraint {} should have a parent otherwise "
                    "the constraint won't be added to the parent "
                    "_constraints_list".format(self.name))

    def _deactivate_constraint(self):
        """ An constraint can be deactivated in order to debug (only!)
        """
        self.active = False


class DynamicConstraint(Constraint):
    """
    **Description**

        Class that defines a constraint depending on the time.
        NB : Mandatory for PuLP

    """

    def __init__(self, exp_t, t_range='for t in time.I', name='DCST0',
                 description='dynamic constraint', active=True, parent=None):
        """

        :param exp_t (str): constraint expression time-dependant
        :param t_range (str): time range defining when the constraint is set
        :param name (str): name of the constraint
        :param description (str): description of the constraint
        :param active (bool): is the constraint activated or deactivated
        :param parent: unit containing the constraint
        """
        if t_range[0] == ' ':
            # If the t_range starts with an empty space, it is deleted
            t_range = t_range[1:]
        exp = exp_t + ' ' + t_range

        Constraint.__init__(self, exp, name, description, active, parent)

        self.exp_t = exp_t
        self.t_range = t_range


class DefinitionConstraint(Constraint):
    """
    **Description**

        Defining a category of constraint: DefinitionConstraint for imposed
        mathematical relation constraints, which may be physical. They are
        used to calculate and define quantities, or to reprensent physical
        phenomenon.
        Must be different from Technical and Actor constraints.
        This kind of constraint is by nature non-negotiable

        Definition constraint: added to the model to calculate a quantity or
        define it considering an other.
            example: the definition of e_tot: calc_e_tot (e_tot = LpSum(e))
        Physical constraint: to model a constraint which is linked to the
        physics.
            example: not implemented yet, see DefinitionDynamicConstraint
    """

    def __init__(self, exp, name='DefCST0', description='Constraint for '
                                                        'definitions',
                 active=True,
                 parent=None):
        Constraint.__init__(self, exp=exp, name=name,
                            description=description, active=active,
                            parent=parent)


class DefinitionDynamicConstraint(DynamicConstraint, DefinitionConstraint):
    """
    **Description**

        Defining a category of constraint: DefinitionDynamicConstraint
        on the time.  (see: DynamicConstraint, DefinitionConstraint)
        Must be different from Technical and Actor constraints.
        This kind of constraint is by nature non-negotiable

        DefinitionDynamicConstraint: to calculate a quantity
        or define it considering an other quantity and depending on the time.
            example: the definition of a capacity def_capacity
            (energy[t] <= capacity at each time step t)
        Physical constraint: to model physical constraints.
            example: the power balance in an Energy node: power_balance
           (LpSum(p_production_unit[t] for the set of production units
           connected to the energy node) = LpSum(p_consumption_unit[t] for the
           consumption units connected to the energy node at each time step t)
    """

    def __init__(self, exp_t, t_range='for t in time.I', name='DefDynCST0',
                 description='dynamic constraint for definition',
                 active=True, parent=None):
        DefinitionConstraint.__init__(self, exp='', name=name,
                                      description=description, active=active,
                                      parent=parent)
        DynamicConstraint.__init__(self, exp_t=exp_t,
                                   t_range=t_range, name=name,
                                   description=description,
                                   active=active, parent=parent)


class TechnicalConstraint(Constraint):
    """
    **Description**

        Defining a category of constraint: TechnicalConstraint.
        To model a constraint which is linked to
        technical issues
        Must be different from Definition and Actor constraints.
        This kind of constraint is mainly a negotiable constraint.


            example: not implemented yet, see TechnicalDynamicConstraints

    """

    def __init__(self, exp, name='TechCST0', description='Technical '
                                                         'constraint',
                 active=True,
                 parent=None):
        Constraint.__init__(self, exp, name, description, active, parent)
        self._add_tech_cst_list()

    def _add_tech_cst_list(self):
        if self.parent:
            if self not in self.parent._technical_constraints_list:
                self.parent._technical_constraints_list.append(self)
            else:
                Warning("the technical constraint {} should have a parent "
                        "otherwise the constraint won't be added to the "
                        "parent "
                        "_technical_constraints_list".format(self.name))

    def deactivate_constraint(self):
        """ An technical constraint can be deactivated :
             - To compare scenarios
             - To try a less constrained problem
        """
        self.active = False


class TechnicalDynamicConstraint(DynamicConstraint, TechnicalConstraint):
    """
    **Description**

        Defining a category of constraint: TechnicalDynamicConstraint
        depending on the time. (see: DynamicConstraint, TechnicalConstraint)
        Must be different from Definition and Actor constraints.
        This kind of constraint is mainly a negotiable constraint.

            example: an energy unit may not be able to stop in one time
            step, but several. The power decreases as a ramp shape:
            set_max_ramp_down

    """

    def __init__(self, exp_t, t_range='for t in time.I', name='TechCST0',
                 active=True,
                 description='Technical and dynamic constraint',
                 parent=None):
        TechnicalConstraint.__init__(self, exp='', name=name,
                                     description=description,
                                     active=active, parent=parent)
        DynamicConstraint.__init__(self, exp_t=exp_t, t_range=t_range,
                                   name=name,
                                   description=description, active=active,
                                   parent=parent)


class ActorConstraint(Constraint):
    """
    **Description**

        Defining a category of constraint: ActorConstraint
        (see: DynamicConstraint, TechnicalConstraint)
        To model a constraint which is due to actor decisions.
        Must be different from Definition and Technical constraints.
        This kind of constraint is mainly a negotiable constraint.

            example: to have a minimal level of energy consumption
            over a period. Constraint : min_energy

    """

    def __init__(self, exp, name='ActCST0', description='', active=True,
                 parent=None):
        Constraint.__init__(self, exp, name, description, active, parent)
        self._add_actor_cst_list()

    def _add_actor_cst_list(self):
        if self.parent:
            if self not in self.parent._actor_constraints_list:
                self.parent._actor_constraints_list.append(self)
            else:
                Warning("the actor's constraint {} should have a parent "
                        "otherwise the constraint won't be added to the "
                        "parent "
                        "_actor_constraints_list".format(self.name))

    def deactivate_constraint(self):
        """ An actor's constraint can be deactivated :
             - To compare scenarios
             - To try a less constrained problem
        """
        self.active = False


class ActorDynamicConstraint(DynamicConstraint, ActorConstraint):
    """
    **Description**

        Defining a category of constraint: ActorDynamicConstraint
        (see: DynamicConstraint, ActorConstraint)
        Must be different from Definition and Technical constraints.
        This kind of constraint is mainly a negotiable constraint.

            example: to operate an energy unit only on defined
            periods. Constraint: daily_dynamic_constraint

    """

    def __init__(self, exp_t, t_range='for t in time.I', name='ActDynCST0',
                 active=True,
                 description='Actor and dynamic constraint',
                 parent=None):
        ActorConstraint.__init__(self, exp='', name=name,
                                 description=description,
                                 active=active, parent=parent)
        DynamicConstraint.__init__(self, exp_t=exp_t, t_range=t_range,
                                   name=name,
                                   description=description, active=active,
                                   parent=parent)


class ExternalConstraint(Constraint):
    """
    **Description**

        +++++++++++++++++++++++++++++++++++++++++++++
          **DEPRECATED: please use ActorConstraint**
        +++++++++++++++++++++++++++++++++++++++++++++

        Defining a special type of constraint: the external constraint
         - This constraint does not translate a physical constraint
         - This constraint defines an external constraint, which could be
           relaxed
 """

    def __init__(self, exp, name='ExCST0', description='', active=True,
                 parent=None):
        Constraint.__init__(self, exp, name, description, active, parent)

        import warnings
        deprecated_msg = "DEPRECATED: HourlyDynamicConstraint is deprecated " \
                         "and will be removed in omegalpes version 0.4 " \
                         "Please use DailyDynamicConstraint that allows to " \
                         "use hour and minutes in the daily constraint " \
                         "definition"
        warnings.warn(deprecated_msg, DeprecationWarning)

        self._add_ext_cst_list()

    def _add_ext_cst_list(self):
        if self.parent:
            if self not in self.parent._external_constraints_list:
                self.parent._external_constraints_list.append(self)
            else:
                Warning("the external constraint {} should have a parent "
                        "otherwise the constraint won't be added to the "
                        "parent "
                        "_external_constraints_list".format(self.name))

    def deactivate_constraint(self):
        """ An external constraint can be deactivated :
             - To compare scenarios
             - To try a less constrained problem
        """
        self.active = False


class ExtDynConstraint(DynamicConstraint, ExternalConstraint):
    """
    **Description**

        +++++++++++++++++++++++++++++++++++++++++++++++++++
          **DEPRECATED: please use ActorDynamicConstraint**
        ++++++++++++++++++++++++++++++++++++++++++++++++++++

        Defining a constraint both external and dynamic
        (see: DynamicConstraint, ExternalConstraint)
    """

    def __init__(self, exp_t, t_range='for t in time.I', name='EDCST0',
                 active=True,
                 description='Non-physical and dynamic constraint',
                 parent=None):
        import warnings
        deprecated_msg = "DEPRECATED: HourlyDynamicConstraint is deprecated " \
                         "and will be removed in omegalpes version 0.4 " \
                         "Please use DailyDynamicConstraint that allows to " \
                         "use hour and minutes in the daily constraint " \
                         "definition"
        warnings.warn(deprecated_msg, DeprecationWarning)

        ExternalConstraint.__init__(self, exp='', name=name,
                                    description=description,
                                    active=active, parent=parent)
        DynamicConstraint.__init__(self, exp_t=exp_t, t_range=t_range,
                                   name=name,
                                   description=description, active=active,
                                   parent=parent)


class HourlyDynamicConstraint(ActorDynamicConstraint):
    """
    **Description**

        +++++++++++++++++++++++++++++++++++++++++++++++++
          **DEPRECATED: please use DailyDynamicConstraint**
        +++++++++++++++++++++++++++++++++++++++++++++++++

        Class that defines an dynamic contraint for a time range

        Ex: Constraint applying between 7am and 10pm

        ex_cst = HourlyDynamicConstraint(exp_t, time, init_h=7, final_h=22,
        name='ex_cst')

    **Attributes**

     - name (str) : name of the constraint
     - exp_t (str) : expression of the constraint
     - init_h (int) : hour of beginning of the constraint [0-23]
     - final_h (int) : hour of end of the constraint [1-24]
     - description (str) : description of the constraint
     - active (bool) : defines if the constraint is active or not
     - parent (OptObject) : parent of the constraint
    """

    def __init__(self, exp_t, time, init_h: int = 0, final_h: int = 24,
                 name='HDCST0', description='hourly dynamic constraint',
                 active=True, parent=None):

        import warnings
        deprecated_msg = "DEPRECATED: HourlyDynamicConstraint is deprecated " \
                         "and will be removed in omegalpes version 0.4 " \
                         "Please use DailyDynamicConstraint that allows to " \
                         "use hour and minutes in the daily constraint " \
                         "definition"
        warnings.warn(deprecated_msg, DeprecationWarning)

        if init_h > final_h:
            raise ValueError('final_h {0} should be greater than init_h '
                             '{1}'.format(final_h, init_h))
        if final_h > 24:
            raise ValueError('final_h {} should be lower than '
                             '24'.format(final_h))

        index_list = []  # Initializing the list of index

        # For all days in the time periods, select the hour range
        for day in time.get_days:
            starting_date = datetime.datetime(year=day.year, month=day.month,
                                              day=day.day, hour=init_h)

            if final_h == 24:
                end = day + datetime.timedelta(days=1)

            else:
                end = datetime.datetime(year=day.year, month=day.month,
                                        day=day.day, hour=final_h)

            try:
                index_date = time.get_index_for_date_range(
                    starting_date=starting_date, end=end)
                index_list += index_date

            except ValueError:
                pass  # Exception when no values for the last day for instance

        t_range = 'for t in {}'.format(index_list)

        ActorDynamicConstraint.__init__(self, exp_t, t_range=t_range,
                                        name=name,
                                        description=description, active=active,
                                        parent=parent)


class DailyDynamicConstraint(ActorDynamicConstraint):
    """
    **Description**

        Class that defines a daily dynamic constraint for a time range

        Ex: Constraint applying between 7am and 10:30pm

        ex_cst = DailyDynamicConstraint(exp_t, time, init_h="7:00",
        final_h="10:30", name='ex_cst')

    **Attributes**

     - name (str) : name of the constraint
     - exp_t (str) : expression of the constraint
     - init_time (str) : starting time of the constraint in the format:
     "HH:MM", consistent with the dt value.
     - final_time (str) : ending time of the constraint in the format:
     "HH:MM", consistent with the dt value.
     - description (str) : description of the constraint
     - active (bool) : defines if the constraint is active or not
     - parent (OptObject) : parent of the constraint
    """

    def __init__(self, exp_t, time, init_time: str = "00:00", final_time: str =
    "23:00", name='daily_dynamic_constraint',
                 description='daily dynamic constraint',
                 active=True, parent=None):

        (init_h_str, init_min_str) = init_time.split(":")
        (final_h_str, final_min_str) = final_time.split(":")

        init_h = int(init_h_str)
        init_min = int(init_min_str)
        final_h = int(final_h_str)
        final_min = int(final_min_str)

        if final_h != 00 or final_min != 00:
            if init_h > final_h or (init_h == final_h and init_min >
                                    final_min):
                raise ValueError('The final time {0} should be greater than '
                                 'init_time {1}'.format(final_time, init_time))

        if final_h >= 24:
            raise ValueError('The final hour {} should be lower than '
                             '24'.format(final_h))
        if init_min > 59 or final_min > 59:
            raise ValueError('The defined initial and final minutes should '
                             'have values lower than 60 !')

        index_list = []  # Initializing the list of index
        # For all days in the time periods, select the hour range
        for day in time.get_days:
            starting_date = datetime.datetime(year=day.year, month=day.month,
                                              day=day.day, hour=init_h,
                                              minute=init_min)

            if final_h == 00 and final_min == 00:
                end_date = day + datetime.timedelta(days=1)
            else:
                end_date = datetime.datetime(year=day.year, month=day.month,
                                             day=day.day, hour=final_h,
                                             minute=final_min)

            try:
                index_date = time.get_index_for_date_range(
                    starting_date=starting_date, end=end_date)
                index_list += index_date

            except ValueError:
                # Exception when no values for the last day for instance
                end_date = time.get_date_for_index(time.LEN - 1)
                index_date = time.get_index_for_date_range(
                    starting_date=starting_date, end=end_date)
                index_list += index_date

        t_range = 'for t in {}'.format(index_list)

        ActorDynamicConstraint.__init__(self, exp_t, t_range=t_range,
                                        name=name,
                                        description=description, active=active,
                                        parent=parent)


class Objective:
    """
     **Description**

        Class that defines an optimisation objective

     **Attributes**

      - name (str) :
      - exp (str) :
      - description (str) :
      - active (bool) :
      - weight (float) : weighted factor of the objective
      - parent (unit)
      - unit (str) : unit of the cost expression
      - pareto (str) : if True, OMEGAlpes calculates a pareto front based on
            this objective (two objectives needed)

    **Methods**

    - _add_objectives_list()
    - _add_pareto_objectives_list()

     .. note::
        Make sure that all the modifications on Objectives are made before
        adding the unit to the OptimisationModel, otherwise, it won't be taken
        into account

     """

    def __init__(self, exp, name='OBJ0', description='', active=True, weight=1,
                 unit='s.u.', pareto=False, parent=None):
        self.name = name
        self.exp = exp
        self.description = description
        self.active = active
        self.weight = weight
        self.parent = parent
        self.unit = unit
        self.pareto = pareto
        if pareto:
            self._add_pareto_objectives_list()
        else:
            self._add_objectives_list()

    def _add_objectives_list(self):
        """
        Add the objectives in the _objectives_list of its parent (normally an
        energy_unit or an actor)
        """
        if self.parent:
            if self not in self.parent._objectives_list:
                self.parent._objectives_list.append(self)
        else:
            Warning("the objective {} should have a parent otherwise "
                    "the objective won't be added to the parent "
                    "_objectives_list".format(self.name))

    def _add_pareto_objectives_list(self):
        """
        Add the objectives for the pareto front in the
        _pareto_objectives_list of its parent (normally an
        energy_unit or an actor)
        """
        if self not in self.parent._pareto_objectives_list:
            self.parent._pareto_objectives_list.append(self)
