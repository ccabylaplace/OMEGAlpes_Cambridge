#! usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
**This module enables to model buildings as thermal loads**

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
from pulp import LpContinuous, LpBinary

from ...energy.units.consumption_units import VariableConsumptionUnit
from ...general.optimisation.elements import *
from ...general.optimisation.core import OptObject
from ...general.utils.maths import def_abs_value

__docformat__ = "restructuredtext en"

# Stefan-boltzmann constant
BOLTZMANN = 0.000000056697   # W/m2K4

# Thermal resistance of external surfaces according to ISO 6946
RSE = 0.04
F_F = 0.2

class RCNetwork_1(OptObject):
    #                   H_EA
    #                   ____
    # theta_ea     o---|____|----o    T_int
    #                            |
    #                            _
    #                           | |   H_AC
    #                           |_|
    #                   H_EC     |
    #                   ____     |
    # theta_ec     o---|____|----o    theta_c
    #                            |
    #                            _
    #                           | |   H_MC
    #                           |_|
    #                   H_EM     |
    #                   ____     |
    # theta_em     o---|____|----o    theta_m
    #                            |
    #                           ___
    #                           ___   C_M
    #                            |

    def __init__(self, time, name, T_ext, theta_ec, theta_em,
                 T_int_min=0, T_int_max=50, theta_ea=None, theta_c=None,
                 theta_m=None, h_ea=0, h_ac=0, h_ec=0, h_mc=0, h_em=0, c_m=0,
                 f_im=None, f_r_l=0.7, f_r_p=0.5, f_r_a=0.2, f_sa=0.1,
                 f_sm=None, f_sc=None, f_ic=None, f_hc_cv=None, U_wall=0.2,
                 U_win=1.2, U_roof=0.2, e_wall=0.9, e_win=0.9, e_roof=0.9,
                 a_wall=0.6, a_roof=0.6, A_wall=None, A_win=None, A_roof=None,
                 owner=None):

        OptObject.__init__(self, name, 'Thermal_zone')

        self.time = time
        self.owner = owner

        self.F_DICT = {'F_IM': f_im, 'F_R_L': f_r_l, 'F_R_P': f_r_p,
                       'F_R_A': f_r_a, 'F_SA': f_sa, 'F_SM': f_sm,
                       'F_SC': f_sc, 'F_IC': f_ic, 'F_HC_CV': f_hc_cv}

        self.U_DICT = {'WIN': U_win, 'WALL': U_wall, 'ROOF': U_roof}
        self.E_DICT = {'WIN': e_win, 'WALL': e_wall, 'ROOF': e_roof}
        self.A_DICT = {'WIN': A_win, 'WALL': A_wall, 'ROOF': A_roof}
        self.AB_DICT = {'WALL': a_wall, 'ROOF': a_roof}

        # Calculation simplifications
        # TODO : Check
        try:
            h_1 = 1 / (1 / h_ea + 1 / h_ac)
        except ZeroDivisionError:
            h_1 = 0
            # if h_ea == 0:
            #     h_1 = h_ac
            # else:
            #     h_1 = h_ea

        h_2 = h_1 + h_ec
        h_3 = 1 / (1 / h_2 + 1 / h_mc)

        # Cm: Explanation of /3600 (Wh/K) SIA 2044 unit is Wh/K, ISO unit is J/K

        self.H_C_DICT = {'H_EA': h_ea, 'H_AC': h_ac, 'H_EC': h_ec,
                         'H_MC': h_mc, 'H_EM': h_em, 'H_1': h_1, 'H_2': h_2,
                         'H_3': h_3, 'C_M': c_m / 3600}

        # Creation of all nodes' temperatures
        self.T_int = Quantity(name='T_int', lb=T_int_min,
                              ub=T_int_max, vlen=time.LEN,
                              vtype=LpContinuous, parent=self)

        self.T_ext = Quantity(name='T_ext', value=T_ext, vlen=time.LEN,
                              vtype=LpContinuous, parent=self)

        self.theta_ea = Quantity(name='theta_ea', value=theta_ea, lb=-50,
                                 ub=50, vlen=time.LEN, vtype=LpContinuous,
                                 parent=self)

        self.theta_ec = Quantity(name='theta_ec', value=theta_ec,
                                 vlen=time.LEN, vtype=LpContinuous,
                                 parent=self)

        self.theta_c = Quantity(name='theta_c', value=theta_c, lb=-50,
                                ub=50, vlen=time.LEN, vtype=LpContinuous,
                                parent=self)

        self.theta_em = Quantity(name='theta_em', value=theta_em,
                                 vlen=time.LEN, vtype=LpContinuous,
                                 parent=self)

        self.theta_m = Quantity(name='theta_m', value=theta_m, lb=-50,
                                ub=50, vlen=time.LEN, vtype=LpContinuous,
                                parent=self)

        self.T_op = Quantity(name='T_op', lb=-50, ub=50, vlen=time.LEN,
                             vtype=LpContinuous, parent=self)


class ZEA_RCNetwork_1(RCNetwork_1):
    def __init__(self, time, name, T_ext, A_f, A_win, Aext_v, A_roof,
                 footprint, U_win, U_wall, U_roof, U_base, floors, e_wall=0.9,
                 e_win=0.9, e_roof=0.9, a_wall=0.6, a_roof=0.6,
                 construction='heavy', height_bg=0, perimeter=0, f_hc_cv=1,
                 void=0, hvac_prop=None, T_int_min=0, T_int_max=50, owner=None):

        """
            Copyright 2015, Architecture and Building Systems - ETH Zurich

        :param time:
        :param name:
        :param T_ext:
        :param A_f:
        :param A_win:
        :param Aext_v:
        :param A_roof:
        :param footprint:
        :param U_win:
        :param U_wall:
        :param U_roof:
        :param U_base:
        :param floors:
        :param construction:
        :param height_bg:
        :param perimeter:
        :param f_hc_cv:
        :param void:
        :param hvac_prop:
        :param T_int_min:
        :param T_int_max:
        :param owner:
        """

        # Import functions from City Energy Analyst - ETH Zurich
        from ...demand.rc_model_SIA import calc_h_ea, calc_h_ac, calc_h_ec, \
            calc_h_mc, calc_h_em, \
            calc_h_op_m, calc_f_im, calc_f_sm, calc_f_sc, calc_f_ic, f_r_a, \
            f_r_l, f_r_p, f_sa

        if hvac_prop is not None:
            m_v_sys = hvac_prop.vent_param['M_VE_MECH']
            m_v_w = hvac_prop.vent_param['M_VE_W']
            m_v_inf = hvac_prop.vent_param['M_VE_INF']
        else:
            m_v_sys = 0
            m_v_w = 0
            m_v_inf = 1.23 * 0.1 ** (2/3) * A_f * 0.000277778 * 3
            Warning("You didn't enter any HVAC property for the thermal"
                    " zone properties {}.".format(name))

        # Calculation of the fraction of windows on walls
        window_to_wall_ratio = A_win / Aext_v

        Aop_sup = calc_Aop_sup(Awall_all=Aext_v, void=void,
                               window_to_wall_ratio=window_to_wall_ratio)
        Aop_bel = calc_Aop_bel(height_bg=height_bg, perimeter=perimeter,
                               footprint=footprint)

        A_tot = A_win + Aop_sup + footprint + Aop_bel + A_roof * (floors - 1)

        Htr_op = calc_Htr_op(Aop_bel=Aop_bel, Aop_sup=Aop_sup,
                             footprint=footprint, U_base=U_base, U_wall=U_wall,
                             U_roof=U_roof)
        Htr_w = A_win * U_win

        Cm_Af = get_Cm_Af(construction)

        # Af: conditioned floor area (heated/cooled) in [m2]
        A_m = calc_Am(Cm_Af=Cm_Af, Af=A_f)
        C_m = calc_cm(Cm_Af=Cm_Af, Af=A_f)

        h_ea = calc_h_ea(m_v_sys, m_v_w, m_v_inf)
        h_ac = calc_h_ac(A_tot)
        h_ec = calc_h_ec(Htr_w)
        h_mc = calc_h_mc(A_m)
        h_op_m = calc_h_op_m(Htr_op)
        h_em = calc_h_em(h_op_m, h_mc)

        f_im = calc_f_im(A_tot, A_m)
        f_sm = calc_f_sm(A_tot, A_m, A_win)
        f_sc = calc_f_sc(A_tot, A_m, A_win, h_ec)
        f_ic = calc_f_ic(A_tot, A_m, h_ec)

        RCNetwork_1.__init__(self, time, name, T_ext=T_ext, theta_ec=T_ext,
                             theta_em=T_ext, T_int_min=T_int_min,
                             T_int_max=T_int_max, theta_ea=T_ext,
                             theta_c=None, theta_m=None, h_ea=h_ea,
                             h_ac=h_ac, h_ec=h_ec, h_mc=h_mc, h_em=h_em,
                             c_m=C_m, f_im=f_im, f_r_l=f_r_l, f_r_p=f_r_p,
                             f_r_a=f_r_a, f_sa=f_sa, f_sm=f_sm, f_sc=f_sc,
                             f_ic=f_ic, f_hc_cv=f_hc_cv, U_wall=U_wall,
                             U_win=U_win, U_roof=U_roof, e_wall=e_wall,
                             e_win=e_win, e_roof=e_roof, a_wall=a_wall,
                             a_roof=a_roof, A_wall=Aop_sup, A_win=A_win,
                             A_roof=A_roof, owner=owner)


class ThermalZone(OptObject):

    def __init__(self, rc_network, phi_i_a, phi_i_l, phi_i_p, I_sol_av, Fsh_win,
                 T_mean, T_dew, sky_cover=1, T_ext=None, hvac_prop=None):
        OptObject.__init__(self, rc_network.name, 'Thermal zone with power flows')

        self.time = rc_network.time
        self.owner = rc_network.owner
        self.prop = rc_network
        rc_network.parent = self

        # ++ Creation of energy flows ++
        self.phi_a = Quantity(name='phi_a', vlen=self.time.LEN,
                              vtype=LpContinuous, parent=self)

        self.phi_c = Quantity(name='phi_c', vlen=self.time.LEN,
                              vtype=LpContinuous, parent=self)

        self.phi_m = Quantity(name='phi_m', vlen=self.time.LEN,
                              vtype=LpContinuous, parent=self)

        self.phi_m_tot = Quantity(name='phi_m_tot', vlen=self.time.LEN,
                                  vtype=LpContinuous, parent=self)

        # Internal gains
        self.phi_i_l = Quantity(name='phi_i_l', value=phi_i_l,
                                vlen=self.time.LEN, vtype=LpContinuous,
                                parent=self)

        self.phi_i_p = Quantity(name='phi_i_p', value=phi_i_p,
                                vlen=self.time.LEN, vtype=LpContinuous,
                                parent=self)

        self.phi_i_a = Quantity(name='phi_i_a', value=phi_i_a,
                                vlen=self.time.LEN, vtype=LpContinuous,
                                parent=self)

        # Solar gains
        I_sol = calc_I_sol(I_sol_average=I_sol_av,
                           Aop_sup=self.prop.A_DICT['WALL'],
                           Awin=self.prop.A_DICT['WIN'],
                           Aroof=self.prop.A_DICT['ROOF'],
                           a_wall=self.prop.AB_DICT['WALL'],
                           a_roof=self.prop.AB_DICT['ROOF'],
                           U_wall=self.prop.U_DICT['WALL'],
                           U_roof=self.prop.U_DICT['ROOF'], Fsh_win=Fsh_win)

        self.I_sol = Quantity(name='I_sol', value=I_sol,
                              vlen=self.time.LEN, vtype=LpContinuous,
                              parent=self, unit='kW')

        # Re-irradiated flows
        self.I_rad = Quantity(name='I_rad', vlen=self.time.LEN,
                              vtype=LpContinuous, parent=self)

        # External gains
        self.phi_s = Quantity(name='phi_s', vlen=self.time.LEN,
                              vtype=LpContinuous, parent=self)

        # Heating and cooling
        self.phi_hc_cv = Quantity(name='phi_hc_cv', vlen=self.time.LEN,
                                  vtype=LpContinuous, parent=self)
        self.phi_hc_r = Quantity(name='phi_hc_r', vlen=self.time.LEN,
                                 vtype=LpContinuous, parent=self)
        self.phi_hc = Quantity(name='phi_hc', lb=-10e+8, ub=10e+8,
                               vlen=self.time.LEN, vtype=LpContinuous,
                               parent=self)

        # Get all coefficients from thermal zone properties
        f_im = rc_network.F_DICT['F_IM']
        f_r_l = rc_network.F_DICT['F_R_L']
        f_r_p = rc_network.F_DICT['F_R_P']
        f_r_a = rc_network.F_DICT['F_R_A']
        f_sa = rc_network.F_DICT['F_SA']
        f_sm = rc_network.F_DICT['F_SM']
        f_ic = rc_network.F_DICT['F_IC']
        f_sc = rc_network.F_DICT['F_SC']
        f_hc_cv = rc_network.F_DICT['F_HC_CV']

        h_em = rc_network.H_C_DICT['H_EM']
        h_ea = rc_network.H_C_DICT['H_EA']
        h_ac = rc_network.H_C_DICT['H_AC']
        h_ec = rc_network.H_C_DICT['H_EC']
        h_mc = rc_network.H_C_DICT['H_MC']
        h_1 = rc_network.H_C_DICT['H_1']
        h_2 = rc_network.H_C_DICT['H_2']
        h_3 = rc_network.H_C_DICT['H_3']
        c_m = rc_network.H_C_DICT['C_M']

        if hvac_prop is None:
            hvac_prop = type('HVAC', (), {})()  # a quick empty object
        hvac_prop.vent_param = {
            'M_VE_MECH': 1.62,
            'M_VE_W': 0.13,
            'M_VE_INF': 0.42,
            'THETA_V_SYS': None
        }

        # Get ventilation data from hvac_prop
        if hvac_prop is not None:
            m_v_sys = hvac_prop.vent_param['M_VE_MECH']
            m_v_w = hvac_prop.vent_param['M_VE_W']
            m_v_inf = hvac_prop.vent_param['M_VE_INF']
            theta_v_sys = hvac_prop.vent_param['THETA_V_SYS']
        else:
            m_v_sys = 0
            m_v_w = 0
            m_v_inf = 0
            theta_v_sys = 20
            Warning("You didn't enter any HVAC property for the thermal"
                    " zone properties {}.".format(rc_network.name))

        # Set all equations into constraints
        self.__set_thermal_flows_equations(f_im, f_r_l, f_r_p, f_r_a, f_sa,
                                           f_sm, f_ic, f_sc, f_hc_cv, h_em,
                                           h_3, h_ec, h_1, h_ea, h_2, T_dew,
                                           T_mean, sky_cover)

        self.__set_temperature_flows_equations(h_ac, h_ea, h_mc, h_ec, h_1, h_3,
                                               h_em, c_m, m_v_sys, theta_v_sys,
                                               m_v_w, m_v_inf)

    def __set_thermal_flows_equations(self, f_im, f_r_l, f_r_p, f_r_a, f_sa,
                                      f_sm, f_ic, f_sc, f_hc_cv, h_em, h_3,
                                      h_ec, h_1, h_ea, h_2, Tdew, Tmean,
                                      sky_cover):

        # Calculation of energy flows
        self.calc_phi_m_tot = DefinitionDynamicConstraint(
            name='calc_phi_m_tot',
            exp_t='{0}_phi_m_tot[t] == {0}_phi_m[t] '
                  '+ {h_em} * {0}_theta_em[t] '
                  '+ ({h_3} * ({0}_phi_c[t] + {h_ec} * {0}_theta_ec[t]'
                  '            + {h_1} * ({0}_phi_a[t] * 1 / {h_ea} '
                  '                        + {0}_theta_ea[t]))) / {h_2}'
                                                .format(self.name, h_em=h_em,
                                                        h_3=h_3,
                                                        h_ec=h_ec, h_1=h_1,
                                                        h_ea=h_ea, h_2=h_2))

        self.calc_phi_m = DefinitionDynamicConstraint(name='calc_phi_m',
                                                      exp_t='{0}_phi_m[t] == '
                                                            '{f_im} * ('
                                                  '{f_r_l} * '
                                                  '{0}_phi_i_l[t] + {f_r_p} * '
                                                  '{0}_phi_i_p[t] + '
                                                  '{f_r_a} * {0}_phi_i_a[t] + '
                                                  '{0}_phi_hc_r[t]) '
                                                  '+ (1 - {f_sa}) * {f_sm} * '
                                                  '{0}_phi_s[t]'
                                                      .format(self.name,
                                                              f_im=f_im,
                                                              f_r_l=f_r_l,
                                                              f_r_p=f_r_p,
                                                              f_r_a=f_r_a,
                                                              f_sa=f_sa,
                                                              f_sm=f_sm))

        self.calc_phi_a = DefinitionDynamicConstraint(name='calc_phi_a',
                                                      exp_t='{0}_phi_a[t] == {f_sa} * {'
                                                  '0}_phi_s[t] + '
                                                  '(1 - {f_r_l}) * {'
                                                  '0}_phi_i_l[t] + (1 - '
                                                  '{f_r_p}) * {0}_phi_i_p[t] '
                                                  '+(1 - {f_r_a}) * '
                                                  '{0}_phi_i_a[t] + {'
                                                  '0}_phi_hc_cv[t]'
                                                      .format(self.name,
                                                              f_sa=f_sa,
                                                              f_r_l=f_r_l,
                                                              f_r_p=f_r_p, f_r_a=f_r_a))

        self.calc_phi_c = DefinitionDynamicConstraint(name='calc_phi_c',
                                                      exp_t='{0}_phi_c[t] == {f_ic} * ('
                                                  '{f_r_l} * '
                                                  '{0}_phi_i_l[t] + {f_r_p} * '
                                                  '{0}_phi_i_p[t] + '
                                                  '{f_r_a} * {0}_phi_i_a[t] + '
                                                  '{0}_phi_hc_r[t]) '
                                                  '+ (1 - {f_sa}) * {f_sc} * '
                                                  '{0}_phi_s[t]'
                                                      .format(self.name,
                                                              f_ic=f_ic,
                                                              f_r_l=f_r_l,
                                                              f_r_p=f_r_p, f_r_a=f_r_a,
                                                              f_sa=f_sa,
                                                              f_sc=f_sc))

        self.calc_phi_s = DefinitionDynamicConstraint(name='calc_phi_s',
                                                      exp_t='{0}_phi_s[t] == {0}_I_sol['
                                                  't] - {0}_I_rad[t]'.format(
                                                self.name))

        # Linearization of the irradiated heat rate flow to the sky
        exp_t = write_linerazation_exp(T_dry=self.prop.T_ext.value,
                                       T_dew=Tdew,
                                       Tlin=Tmean, sky_cover=sky_cover,
                                       U_wall=self.prop.U_DICT['WALL'],
                                       U_win=self.prop.U_DICT['WIN'],
                                       U_roof=self.prop.U_DICT['ROOF'],
                                       e_wall=self.prop.E_DICT['WALL'],
                                       e_win=self.prop.E_DICT['WIN'],
                                       e_roof=self.prop.E_DICT['ROOF'],
                                       A_wall=self.prop.A_DICT['WALL'],
                                       A_win=self.prop.A_DICT['WIN'],
                                       A_roof=self.prop.A_DICT['ROOF'],
                                       name=self.name)

        self.calc_I_rad = DefinitionDynamicConstraint(name='calc_I_rad',
                                                      t_range='for t in time.I[72:]',
                                                      exp_t=exp_t)

        self.calc_phi_hc_cv = DefinitionDynamicConstraint(
            name='calc_phi_hc_cv',
            t_range='for t in time.I',
            exp_t='{0}_phi_hc_cv[t] == {'
                                                      'f_hc_cv} * '
                                                      '{0}_phi_hc[t]'.format(
                                                    self.name,
                                                    f_hc_cv=f_hc_cv))

        self.calc_phi_hc_r = DefinitionDynamicConstraint(name='calc_phi_hc_r',
                                                         t_range='for t in time.I',
                                                         exp_t='{0}_phi_hc_r[t] == (1 '
                                                     '-{f_hc_cv}) * '
                                                     '{0}_phi_hc[t]'.format(
                                                   self.name,
                                                   f_hc_cv=f_hc_cv))

    def __set_temperature_flows_equations(self, h_ac, h_ea, h_mc, h_ec, h_1,
                                          h_3, h_em, c_m, m_v_sys, theta_v_sys,
                                          m_v_w, m_v_inf):
        # Calculation of nodes' temperatures
        self.calc_T_int = DefinitionDynamicConstraint(name='calc_T_int',
                                                      t_range='for t in time.I[72:]',
                                                      exp_t='{0}_T_int[t] == '
                                                            '({h_ac} * '
                                                  '{0}_theta_c[t] + '
                                                  '{h_ea} * {0}_theta_ea[t] + '
                                                  '{0}_phi_a[t]) '
                                                  '/ ({h_ac} + {h_ea})'
                                                      .format(self.name,
                                                              h_ac=h_ac,
                                                              h_ea=h_ea))

        self.calc_theta_c = DefinitionDynamicConstraint(name='calc_theta_c',
                                                        t_range='for t in time.I[72:]',
                                                        exp_t='{0}_theta_c[t] == ({'
                                                    'h_mc} * '
                                                    '({0}_theta_m[t] + {'
                                                    '0}_theta_m[t-1])/2 + '
                                                    '{h_ec} * {0}_theta_ec[t] '
                                                    '+ {0}_phi_c[t] +'
                                                    ' {h_1} * (1/{h_ea} * {'
                                                    '0}_phi_a[t] + '
                                                    '{0}_theta_ea[t])) / ({'
                                                    'h_mc} + {h_ec} + '
                                                    '{h_1})'
                                                        .format(self.name,
                                                                h_mc=h_mc,
                                                                h_ec=h_ec, h_1=h_1,
                                                                h_ea=h_ea))

        self.calc_theta_m = DefinitionDynamicConstraint(name='calc_theta_m',
                                                        t_range='for t in time.I[72:]',
                                                        exp_t='{0}_theta_m['
                                                              't] == ({'
                                                    '0}_theta_m[t-1] * '
                                                    '({c_m} - 0.5 * ({h_3} + '
                                                    '{h_em})) + '
                                                    '{0}_phi_m_tot[t]) / ({'
                                                    'c_m} + 0.5 * '
                                                    '({h_3} + {h_em}))'
                                                        .format(self.name,
                                                                c_m=c_m,
                                                                h_em=h_em,
                                                                h_3=h_3))

        self.calc_theta_m_0 = DefinitionConstraint(name='calc_theta_m_0',
                                                   exp='{0}_theta_m[0] == {0}_T_ext[0]'
                                                   .format(self.name), parent=self)

        # Time for dynamics to appear
        # self.calc_operative_temp = DefinitionDynamicConstraint(
        #     t_range='for t in time.I[144:]',
        #     name='calc_operative_temp', exp_t='2 * {0}_T_op[t] == '
        #                                       '{0}_theta_m[t] + {0}_T_int[t]'
        #         .format(self.name), parent=self)
        self.calc_operative_temp = DefinitionDynamicConstraint(
            t_range='for t in time.I[144:]',
            name='calc_operative_temp',
            exp_t='100 * {0}_T_op[t] == 31 * {0}_T_int[t] + 69 * {'
                  '0}_theta_c[t]'
                .format(self.name), parent=self)

        if m_v_sys != 0 and theta_v_sys is not None:
            # Intermediary temperature to calculate theta_ea in case of
            # mechanical ventilation
            self.theta_v_sys = Quantity(name='theta_v_sys', value=theta_v_sys,
                                        lb=0, ub=50,
                                        vlen=self.time.LEN, vtype=LpContinuous,
                                        parent=self)

            self.calc_theta_ea = DefinitionDynamicConstraint(
                name='calc_theta_ea', t_range='for t in time.I[72:]',
                exp_t='{0}_theta_ea[t] == ({m_v_sys} * {0}_theta_v_sys[t] '
                      '+ ({m_v_w} + {m_v_inf}) * {0}_T_ext[t]) '
                      '* 1 / ({m_v_sys} + {m_v_w} + {m_v_inf})'
                                                   .format(self.name,
                                                           m_v_sys=m_v_sys,
                                                           m_v_w=m_v_w,
                                                           m_v_inf=m_v_inf))

        # else:
        #     # If no mechanical ventilation, theta_ea equals the external
        #     # temperature
        #     self.calc_theta_ea = DefinitionDynamicConstraint(
        #         name='calc_theta_ea',
        #         t_range='for t in time.I',
        #         exp_t='{0}_theta_ea[t] == '
        #                                                  '{0}_T_ext[t]'
        #         .format(self.name))

    def split_heating_and_cooling(self, p_max_heating=10e+12,
                                  p_max_cooling=10e+12):
        self.phi_heating = Quantity(name='phi_heating', lb=0, ub=p_max_heating,
                                    vlen=self.time.LEN,
                                    vtype=LpContinuous, parent=self)

        self.phi_cooling = Quantity(name='phi_cooling', lb=0, ub=p_max_cooling,
                                    vlen=self.time.LEN,
                                    vtype=LpContinuous, parent=self)

        self.heating_on = Quantity(name='heating_on', vlen=self.time.LEN,
                                   vtype=LpBinary, parent=self)

        self.split_heat_cool = DefinitionDynamicConstraint(
            exp_t='{0}_phi_hc[t] == {0}_phi_heating[t] - {0}_phi_cooling[t]'
                .format(self.name), t_range='for t in time.I',
            name='split_heat_cool', parent=self)

        self.heating_only = DefinitionDynamicConstraint(
            exp_t='{0}_phi_heating[t] <= {0}_heating_on[t] * {p_max_h}'
                .format(self.name, p_max_h=p_max_heating), name='heating_only')

        self.cooling_only = DefinitionDynamicConstraint(
            exp_t='{0}_phi_cooling[t] <= (1 - {0}_heating_on[t]) * {p_max_c}'
                .format(self.name, p_max_c=p_max_cooling), name='cooling_only')


class HeatingLoad(VariableConsumptionUnit):
    """

    """

    def __init__(self, time, name, tz, p_max=10e+12, T_set=19, temp_margin=1,
                 no_cooling=True):
        self.tz = tz
        self.T_set = T_set
        self.temp_margin = temp_margin
        tz.parent = self

        if not isinstance(tz, ThermalZone):
            raise TypeError("tz should be a ThermalZone !")

        print('Redefining minimal and maximal air temperatures for '
              'thermal zone {0}'.format(tz.name))
        # if isinstance(T_set, (int, float)):
        self.tz.prop.T_op.lb = min(T_set) - temp_margin
        self.tz.prop.T_op.ub = max(T_set) + temp_margin

        print(self.tz.prop.name)
        

        if no_cooling:
            p_max_cooling = 1e5
        else:
            p_max_cooling = 1e9
        self.tz.split_heating_and_cooling(p_max_heating=1e9,   # p_max
                                          p_max_cooling=p_max_cooling)   # kW

        VariableConsumptionUnit.__init__(self, time, name, energy_type='Thermal',
                                        p_max=p_max,
                                         e_max=10e9)
        # self.calc_e_tot = None
        # self.e_tot = None

        self.def_heat_cons = DefinitionDynamicConstraint(
            exp_t='{0}_p[t] * 1000 == {1}_phi_heating[t]'   # kW / 1000
                .format(self.name, self.tz.name), name='def_heat_cons',
            t_range='for t in time.I[144:]', parent=self)

    def maximize_thermal_comfort(self, T_op=None, weight=1):
        """

        :param T_op: Operative temperature wished for the maximal thermal
            comfort
        :param weight: Weight of the objective
        """
        if T_op is None:
            T_op = self.T_set
            
        # print(self.T_set)
        if isinstance(self.T_set, list):
            print('xxxxxxxxxxxxx')
            self.def_tz_Top_opt_lb = DefinitionDynamicConstraint(
                name='def_tz_Top_opt_lb',
                exp_t='{0}_T_op[t] >= {1}[t] - {2}'.format(
                    self.tz.prop.name, T_op, self.temp_margin), parent=self)
            print('xxxxxxxxxxxxx')
            self.def_tz_Top_opt_ub = DefinitionDynamicConstraint(
                name='def_tz_Top_opt_ub',
                exp_t='{0}_T_op[t] <= {1}[t] + {2}'.format(
                    self.tz.prop.name, T_op, self.temp_margin), parent=self)

        self.diff_Top_opt = Quantity(name='diff_Top_opt', opt=True,
                                     lb=-self.temp_margin,
                                     ub=self.temp_margin,
                                     vlen=self.time.LEN, parent=self)

        if isinstance(T_op, (int, float)):
            self.def_diff_Top_opt = DefinitionDynamicConstraint(
                name='def_diff_Top_opt',
                exp_t='{0}_diff_Top_opt[t] == {1}_T_op[t] - {2}'.format(
                    self.name, self.tz.prop.name, T_op), parent=self)
        elif isinstance(T_op, list):
            self.def_diff_Top_opt = DefinitionDynamicConstraint(
                name='def_diff_Top_opt',
                exp_t='{0}_diff_Top_opt[t] == {1}_T_op[t] - {2}[t]'.format(
                    self.name, self.tz.prop.name, T_op), parent=self)

        diff = def_abs_value(self.diff_Top_opt, q_max=self.temp_margin,
                             q_min=-self.temp_margin)

        self.max_th_comfort = Objective(name='max_th_comfort',
                                        exp='lpSum({0}_{1}[t] for t in '
                                             'time.I[72:])'.format(self.name,
                                                              diff.name),
                                        parent=self)


def calc_Am(Cm_Af, Af):
    # Am: Effective mass area in [m2]
    Am = lookup_effective_mass_area_factor(Cm_Af) * Af
    return Am


def calc_Aop_bel(height_bg, perimeter, footprint):
    # Aop_bel: Opaque areas below ground (including ground floor,
    # excluding voids and windows) [m2]
    Aop_bel = height_bg * perimeter + footprint
    return Aop_bel


def calc_Aop_sup(Awall_all, void, window_to_wall_ratio):
    # Aop_sup: Opaque wall areas above ground (excluding voids
    # and windows) [m2]
    Aop_sup = Awall_all * (1 - void) * (1 - window_to_wall_ratio)
    return Aop_sup


def calc_cm(Cm_Af, Af):
    # Cm: internal heat capacity in [J/k]
    Cm = Cm_Af * Af
    return Cm


def calc_Hg(Aop_bel, U_base):
    # Hg: steady-state thermal transmission coefficient to the ground
    # in [W/K]
    Hg = 0.7 * Aop_bel * U_base

    return Hg


def calc_Hd(Aop_sup, U_wall, footprint, U_roof):
    # HD: direct thermal transmission  coefficient to  the
    # external environment in [W/K])

    Hd = Aop_sup * U_wall + footprint * U_roof

    return Hd


def calc_Htr_op(Aop_bel, Aop_sup, footprint, U_base, U_wall, U_roof):
    Hg = calc_Hg(Aop_bel=Aop_bel, U_base=U_base)
    Hd = calc_Hd(Aop_sup=Aop_sup, U_wall=U_wall, footprint=footprint,
                 U_roof=U_roof)
    Htr_op = Hg + Hd

    return Htr_op


def get_Cm_Af(construction):
    """
        Description	       code	    Cm_Af
        Light construction	T1	    110000
        Medium construction	T2	    165000
        Heavy construction	T3	    300000

    ..
        Copyright 2015, Architecture and Building Systems - ETH Zurich
    """
    if construction == 'light':
        cm_af = 110000
    elif construction == 'medium':
        cm_af = 165000
    elif construction == 'heavy':
        cm_af = 300000
    else:
        raise ValueError('The construction should be "light", "medium" or '
                         '"heavy", but equals {}'.format(construction))

    return cm_af


def lookup_effective_mass_area_factor(cm):
    """
        Look up the factor to multiply the conditioned floor area by to get
        the effective mass area by building
        construction type.
        This is used for the calculation of the effective mass area "Am" in
        `get_prop_RC_model`.
        Standard values can be found in the Annex G of ISO EN13790

        :param: cm: The internal heat capacity per unit of area [J/m2].

        :return: Effective mass area factor (0, 2.5 or 3.2 depending on cm
            value).

    ..
        Copyright 2015, Architecture and Building Systems - ETH Zurich
    """

    if cm == 0:
        return 0
    elif 0 < cm <= 165000.0:
        return 2.5
    else:
        return 3.2


def calc_I_sol(I_sol_average, Aop_sup, Aroof, Awin, a_wall, a_roof, U_wall,
               U_roof, Fsh_win):
    """

    :param I_sol_average: W/m2
    :param Aop_sup: Opaque wall areas above ground (excluding voids and
        windows) [m2]
    :param Aroof: Roof area [m2]
    :param Awin: Windows area [m2]
    :param a_wall: Absorption coefficient of the walls [0..1]
    :param a_roof: Absorption coefficeint of the roof [0..1]
    :param U_wall:
    :param U_roof:
    :param Fsh_win: Shading factor for windows
    :return: I_sol [kW]
    """

    # from cea.demand.constants import RSE, F_F

    Asol_wall = Aop_sup * a_wall * RSE * U_wall
    Asol_roof = Aroof * a_roof * RSE * U_roof

    if isinstance(I_sol_average, list):
        if isinstance(Fsh_win, list):
            Asol_win = [Fsh_w * Awin * (1 - F_F) for Fsh_w in Fsh_win]
            I_sol = [I_sol_av * (Asol_wall + Asol_roof + Asol_w) for
                     I_sol_av, Asol_w in zip(I_sol_average, Asol_win)]
        elif isinstance(Fsh_win, (int, float)):
            Asol_win = Fsh_win * Awin * (1 - F_F)
            I_sol = [I_sol_av * (Asol_wall + Asol_roof + Asol_win) for
                     I_sol_av in I_sol_average]
        else:
            raise TypeError('Fsh_win should be an int, a float or a list.')

    elif isinstance(I_sol_average, (int, float)):
        if isinstance(Fsh_win, list):
            Asol_win = [Fsh_w * Awin * (1 - F_F) for Fsh_w in Fsh_win]
            I_sol = [I_sol_average * (Asol_wall + Asol_roof + Asol_w)
                     for Asol_w in Asol_win]
        elif isinstance(Fsh_win, (int, float)):
            Asol_win = [Fsh_win * Awin * (1 - F_F)]
            I_sol = I_sol_average * (Asol_wall + Asol_roof + Asol_win)
        else:
            raise TypeError('Fsh_win should be an int, a float or a list.')
    else:
        raise TypeError('I_sol_average should be an int, a float or a list.')

    return I_sol


def calc_T_sky(T_dry, T_dew, sky_cover=1):
    """

    :param T_dry: Dry bulb temperature in Celsius
    :param T_dew: Dew point temperature in Celsius
    :param sky_cover: Sky cover
    """
    sky_T = np.vectorize(calc_skytemp)(T_dry, T_dew, 1)

    return sky_T  # sky temperature in C


def calc_I_rad_linearization_coef(Tdry, Tdew, Tlin, sky_cover=1):
    """

    :param T_dry: Dry bulb temperature in Celsius
    :param T_dew: Dew point temperature in Celsius
    :param sky_cover:
    :return: list(A), list(B):
    """
    temp_df = pd.DataFrame()
    temp_df['T_sky (C)'] = calc_T_sky(T_dry=Tdry, T_dew=Tdew,
                                      sky_cover=sky_cover)
    temp_df['T_sky (K)'] = temp_df['T_sky (C)'] + 273
    temp_df['T_lin (C)'] = Tlin
    temp_df['T_lin (K)'] = temp_df['T_lin (C)'] + 273

    A = 3 * temp_df['T_lin (K)'] ** 4 + temp_df['T_sky (K)'] ** 4 + 4 * \
        temp_df['T_sky (K)'] * temp_df['T_lin (K)'] ** 3

    B = - 4 * temp_df['T_lin (K)'] ** 3 - 6 * temp_df['T_sky (K)'] * temp_df[
        'T_lin (K)'] ** 2 + 2 * temp_df['T_sky (K)'] ** 3

    return list(A), list(B)


def write_linerazation_exp(T_dry, T_dew, sky_cover, Tlin, U_win, U_wall,
                           U_roof, e_win, e_wall, e_roof, A_win, A_wall,
                           A_roof, name):
    A, B = calc_I_rad_linearization_coef(Tdry=T_dry, Tdew=T_dew, Tlin=Tlin,
                                         sky_cover=sky_cover)

    alpha = RSE * BOLTZMANN / 2

    win_coef = 0.5 * U_win * A_win * e_win
    wall_coef = 0.5 * U_wall * A_wall * e_wall
    roof_coef = U_roof * A_roof * e_roof

    coef_tot = alpha * (win_coef + wall_coef + roof_coef)

    A = [a * coef_tot for a in A]
    B = [b * coef_tot for b in B]

    exp_t = '{A}[t] + {B}[t] * ({0}_theta_c[t-1] + 273)'.format(name, A=A, B=B)

    exp_tot = '{0}_I_rad[t] == '.format(name) + exp_t

    return exp_tot


def calc_skytemp(Tdrybulb, Tdewpoint, N=1):
    """

        Copyright 2014, Architecture and Building Systems - ETH Zurich

    :param Tdrybulb: Drybuld temperature [°C]
    :param Tdewpoint: Dewpoint temperature [°C]
    :param N: Sky cover

    :return: Sky temperature in °C

    """

    import math
    sky_e = (0.787 + 0.764 * math.log((Tdewpoint + 273) / 273)) * 1 \
            + 0.0224 * N + 0.0035 * N ** 2 + 0.00025 * N ** 3
    hor_IR = sky_e * BOLTZMANN * (Tdrybulb + 273) ** 4
    sky_T = ((hor_IR / BOLTZMANN) ** 0.25) - 273

    return sky_T  # sky temperature in C

