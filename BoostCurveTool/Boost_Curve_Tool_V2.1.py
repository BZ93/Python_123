# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 13:45:04 2020

@author: Z632445
"""

import re
import tkinter as tk
from tkinter import *
import tkinter.messagebox
from tkinter.filedialog import askopenfilename
import numpy as np
from matplotlib import pyplot as plt
import mplcursors
from scipy import interpolate
import xlsxwriter
import os
from random import randint

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from mpldatacursor import datacursor
from mpldatacursor import HighlightingDataCursor

# =================================================================================================
# show an "Open" dialog box
# =================================================================================================

Tq_demand_Max = 0
IpTqRes_User = 0.01
# Column torque values in the range from 0 to 10 with step size of 0.1
# input_torque = np.arange(0, 10, 0.01) # User input values

input_file = "No File Selected/Application Closed"


def interpol(user_input, x_points, y_points):
    tck = interpolate.splrep(x_points, y_points)
    return interpolate.splev(user_input, tck)


# =================================================================================================
# Boost Curve function
# =================================================================================================
def boost_curve(PD, P0, P1, P2, P3, P4, P5, Ip_res):
    # Column torque values in the range from 0 to 10 with step size of 0.1
    global input_torque
    input_torque = np.arange(0, 10, Ip_res)  # User input values
    # To initialize with random values of torque_demand
    torque_demand = np.zeros((len(PD), len(input_torque)), dtype=np.float64)
    # To initialize with random values of torque_assistance
    torque_assistance = np.zeros((len(PD), len(input_torque)), dtype=np.float64)

    # Calculation of Boost Torque based on Linear and Quadratic expressions
    for i in range(len(PD)):
        section_tune0_P1_A = abs(input_torque) * PD[i]
        section_tune0_P2_A = abs(
            (((P2[i] - PD[i]) * (abs(input_torque) - P0[i]) ** 2) / (2 * P1[i])) + (PD[i] * abs(input_torque)))
        section_tune0_P3_A = abs(
            (P2[i] * (abs(input_torque) - P0[i] - P1[i])) + (P2[i] * P1[i] / 2) + (PD[i] * ((P0[i]) + (P1[i] / 2))))
        section_tune0_P4_A = abs(((P5[i] - P2[i]) * ((abs(input_torque) - P3[i]) ** 2) / (2 * P4[i])) + P2[i] * (
                abs(input_torque) - P0[i] - (P1[i] / 2)) + (PD[i] * ((P0[i]) + (P1[i] / 2))))
        section_tune0_P5_A = abs((P5[i] * (abs(input_torque) - P3[i] - (P4[i] / 2))) + (
                P2[i] * (P3[i] + (P4[i] / 2) - (P1[i] / 2) - P0[i])) + (PD[i] * ((P0[i]) + (P1[i] / 2))))

        for j in range(len(input_torque)):
            if (input_torque[j] >= 0) and (input_torque[j] < P0[i]):
                torque_demand[i][j] = section_tune0_P1_A[j]
            elif input_torque[j] >= P0[i] and input_torque[j] < (P0[i] + P1[i]):
                torque_demand[i][j] = section_tune0_P2_A[j]
            elif input_torque[j] >= (P0[i] + P1[i]) and input_torque[j] < P3[i]:
                torque_demand[i][j] = section_tune0_P3_A[j]
            elif input_torque[j] >= P3[i] and input_torque[j] < (P3[i] + P4[i]):
                torque_demand[i][j] = section_tune0_P4_A[j]
            elif input_torque[j] >= (P3[i] + P4[i]):
                torque_demand[i][j] = section_tune0_P5_A[j]
            else:
                torque_demand[i][j] = section_tune0_P5_A[j]

            torque_assistance[i][j] = min((torque_demand[i][j] / float(Tq_demand_Max)) * 100, 100)
            # To limit the maximum output torque Demand for CD
        torque_demand[torque_demand > float(Tq_demand_Max)] = float(Tq_demand_Max)

    return torque_demand, torque_assistance, input_torque


# =================================================================================================
# End of Boost Curve function
# =================================================================================================

# =================================================================================================
# Cursor function for the graph (torque_demand)
# =================================================================================================
class Cursor:
    def __init__(self, ax):
        self.ax = ax
        self.lx = ax.axhline(color='k')  # the horiz line
        self.ly = ax.axvline(color='k')  # the vert line

        # text location in axes coords
        self.txt = ax.text(0.6, 0.9, '', transform=ax.transAxes)
        return

    def mouse_move(self, event):
        if not event.inaxes:
            return
        x, y = event.xdata, event.ydata
        # update the line positions
        self.lx.set_ydata(y)
        self.ly.set_xdata(x)
        self.txt.set_text('Driver Input Torque (Nm) = %1.2f\nAssistance Torque Demand (Nm)= %1.2f' % (x, y))
        self.ax.figure.canvas.draw()
        return


# =================================================================================================
# Cursor function for the graph (torque_assistance)
# =================================================================================================

class Cursor1:
    def __init__(self, ax10):
        self.ax10 = ax10
        self.lx = ax10.axhline(color='k')  # the horiz line
        self.ly = ax10.axvline(color='k')  # the vert line

        # text location in axes coords
        self.txt = ax10.text(0.6, 0.9, '', transform=ax10.transAxes)
        return

    def mouse_move10(self, event):
        if not event.inaxes:
            return
        x, y = event.xdata, event.ydata
        # update the line positions
        self.lx.set_ydata(y)
        self.ly.set_xdata(x)
        self.txt.set_text('Driver Input Torque (Nm) = %1.2f\nAssistance (%%)= %1.2f' % (x, y))
        self.ax10.figure.canvas.draw()
        return


# =================================================================================================
# Tkinter GUI input interface (Max available assist and PAR file selection)
# =================================================================================================

class numOnly:

    def __init__(self, root):
        self.root = root
        self.root.title("Boost Curve Tool")
        self.root.geometry("650x460")
        self.root.configure(bg="#c0ded9")

        # =======================================================================Frame======================================================================================
        Mainframe = Frame(self.root, bd=10)
        Mainframe.grid()

        Tops = Frame(Mainframe, bd=10, width=100, height=350, relief=RIDGE)
        Tops.pack(side=TOP)

        self.lblInfo = Label(Tops, font=('Helvetica', 31, 'bold'), text="Boost Curve Tool", justify=CENTER,
                             bg="#c0ded9")
        self.lblInfo.grid(padx=2)

        MembersName_F = LabelFrame(Mainframe, bd=10, width=466, height=200, font=('Helvetica', 12, 'bold'),
                                   text="Plot Graph", relief=RIDGE)
        MembersName_F.pack(pady=25)

        # =======================================================================Variable===================================================================================

        MaxAvlAssist = StringVar()
        IpTqRes = StringVar()
        VTDPAR = StringVar()

        # =======================================================================Label & Entry==============================================================================
        self.lblMaxAvlAssist = Label(MembersName_F, font=('Helvetica', 16, 'bold'), text="Max Available Assist (Nm)",
                                     justify=CENTER, bd=7)
        self.lblMaxAvlAssist.grid(row=0, column=0, sticky=W)

        self.lblMaxAvlAssist = Label(MembersName_F, font=('Helvetica', 10, 'bold'), text="[Ex: 70, 80]",
                                     justify=CENTER, bd=7)
        self.lblMaxAvlAssist.grid(row=0, column=2, sticky=W)

        self.lblMaxAvlAssist = Label(MembersName_F, font=('Helvetica', 16, 'bold'), text="Input torque Resolution",
                                     justify=CENTER, bd=7)
        self.lblMaxAvlAssist.grid(row=1, column=0, sticky=W)

        self.txtMaxAvlAssist = Entry(MembersName_F, font=('Helvetica', 13, 'bold'), bd=7, textvariable=MaxAvlAssist,
                                     justify=LEFT, width=12)
        self.txtMaxAvlAssist.grid(row=0, column=1)

        self.txtMaxAvlAssist = Entry(MembersName_F, font=('Helvetica', 13, 'bold'), bd=7, textvariable=IpTqRes,
                                     justify=LEFT, width=12)
        self.txtMaxAvlAssist.grid(row=1, column=1)

        self.lblVTDPAR = Label(MembersName_F, font=('Helvetica', 16, 'bold'), text="Select PAR file", justify=CENTER,
                               bd=7)
        self.lblVTDPAR.grid(row=2, column=0, sticky=W)

        self.lblVTDPAR = Label(MembersName_F, font=('Helvetica', 10, 'bold'), text="[*.par files only]", justify=CENTER,
                               bd=7)
        self.lblVTDPAR.grid(row=2, column=2, sticky=W)

        self.ITR1 = Label(MembersName_F, font=('Helvetica', 12, 'bold'),
                          text="*Note: Input torque resolution values are as follows: 1, 0.1, 0.01, 0.001 ... so on,\nlesser the resolution and more the accuracy of Assistance torque values.",
                          justify=CENTER,
                          bd=7)
        self.ITR1.grid(row=4, column=0, sticky=W, columnspan=3)

        # =======================================================================Functions==================================================================================

        def Destory_User_Window():
            root.destroy()
            return

        def error():
            screen1 = Toplevel(self.root)
            screen1.geometry("220x50")
            screen1.title("Warning!")
            tk.Label(screen1, font=('Helvetica', 16, 'bold'), text="All fields required!", justify=CENTER, bd=7,
                     fg="red").grid(row=1, column=0, padx=10, sticky=W)

            return

        def Browse_PAR_File():

            global input_file
            # tk().withdraw()
            input_file = askopenfilename(initialdir=".//", filetypes=(("Text File", "*.PAR"), ("All Files", "*.par")),
                                         title="Select the PAR file")

            try:
                with open(input_file, 'r') as file_handler:
                    file_handler.close()
                    # print("debug:0001")

            except:
                error()
                # input_file = "No File Selected/Application Closed"
                # Destory_User_Window()
            return

        def Display_data():
            global Tq_demand_Max
            Tq_demand_Max = MaxAvlAssist.get()
            if str(Tq_demand_Max) == "":
                error()
            else:
                Destory_User_Window()
            return

        def IpTrq_Res():
            global IpTqRes_User
            IpTqRes_User = float(IpTqRes.get())
            screen2 = Toplevel(self.root)
            screen2.geometry("220x50")
            screen2.title("User Data")
            if IpTqRes_User is None:
                tk.Label(screen2, font=('Helvetica', 16, 'bold'), text="All fields required!", justify=CENTER, bd=7,
                         fg="red").grid(row=1, column=0, padx=10, sticky=W)
            else:
                tk.Label(screen2, font=('Helvetica', 16, 'bold'), text="Values stored!", justify=CENTER, bd=7,
                         fg="green", ).grid(row=1, column=0, padx=30)
            return IpTqRes_User

        # =======================================================================Buttons====================================================================================

        self.btnSearch = tk.Button(MembersName_F, padx=18, bd=7, font=('Helvetica', 13, 'bold'), width=7,
                                   command=Browse_PAR_File, text="Search", bg="#c0ded9").grid(row=2, column=1, pady=12)
        self.btnPlot = tk.Button(MembersName_F, padx=18, bd=7, font=('Helvetica', 13, 'bold'), width=7,
                                 command=Display_data, text="Plot", bg="#F18F49").grid(row=3, column=1, pady=12)
        self.btnPlot1 = tk.Button(MembersName_F, padx=20, bd=7, font=('Helvetica', 13, 'bold'), width=5,
                                  command=IpTrq_Res, text="Load", bg="#F18F49").grid(row=1, column=2, pady=12)
        # tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="AT → DT", variable=IpTqRes, command=switch_at_dt_calc, value =0).grid(row=6, column=2, sticky = tk.W)


if __name__ == '__main__':
    root = Tk()
    application = numOnly(root)
    root.mainloop()

# =================================================================================================
# Import .par file, generate dictionary keys and convert the string values of keys to float values
# =================================================================================================

f = open(input_file, 'r')
tune_dict = {}
l = f.readlines()
i = 0
while i < len(l):
    r = re.search(r"AC\.BC_(\w+)_MAP\.(TUNE\d+)\s+.*?\s+(.*?)\s+", l[i])
    if r is not None:
        # print(r.group(1)+"_"+r.group(2))
        list_name = r.group(1) + "_" + r.group(2)
        tune_dict[list_name] = [float(r.group(3))]
        while i < len(l) - 1:
            i = i + 1
            # print i
            k = re.search(":\s+(.*)\s+;", l[i])
            if k is not None:
                # print k.groups()
                # print l[i]
                tune_dict[list_name].append(float(k.group(1)))
            else:
                i = i - 1
                break
    i = i + 1

# ===================================================================================================================
# Import .par file, generate dictionary keys and convert the string values of keys to float values (Vehicle Speed)
# ===================================================================================================================
tune_dict_veh_spd = {}
p = 0
while p < len(l):
    r = re.search(r"AC\.TUNDAT\.(VEHICLE_SPEED_BREAKPOINTS)\s+.*?\s+(.*?)\s+", l[p])
    if r is not None:
        # print(r.group(1)+"_"+r.group(2))
        list_name_veh = r.group(1)
        tune_dict_veh_spd[list_name_veh] = [int(r.group(2))]
        while p < len(l) - 1:
            p = p + 1
            # print i
            t = re.search(":\s+(.*)\s+;", l[p])
            if t is not None:
                # print k.groups()
                # print l[i]
                tune_dict_veh_spd[list_name_veh].append(int(t.group(1)))
            else:
                p = p - 1
                break
    p = p + 1

VehSpd_BP = tune_dict_veh_spd["VEHICLE_SPEED_BREAKPOINTS"]


# label_name = ["VehSpd_BP_0","VehSpd_BP_5","VehSpd_BP_10","VehSpd_BP_20","VehSpd_BP_30","VehSpd_BP_40","VehSpd_BP_60","VehSpd_BP_80","VehSpd_BP_100","VehSpd_BP_120","VehSpd_BP_140","VehSpd_BP_160"]

# =================================================================================================
# Plot for torque_demand
# =================================================================================================

def plot_graph(ip_torque, tq_demand, fig, ax, cursor):
    # Only Tune 0  will be determined
    for i in range(len(tune_dict["PD_TUNE0"])):
        # Draw all the lines in the same plot, assigning a label for each one to be
        # Plotting the driver input torque and torque demand
        # Initialise the figure and axes.
        # fig,  = plt.subplots(1, figsize=(10, 8))
        ax.plot(ip_torque, tq_demand[i, :], color=color[i], label=(str(VehSpd_BP[i]) + " Kmph"))
        mplcursors.cursor()  # interactive data selection cursors
        # Add a legend, and position it on the lower right (with no box)
        plt.legend(loc="upper left", title="Legend", frameon=False)

        # cursor = Cursor(ax)
        fig.canvas.mpl_connect('motion_notify_event', cursor.mouse_move)
        # plt.xlabel("Driver Input Torque (Nm)")
        # plt.ylabel("Assistance Torque Demand (Nm)")
        plt.xlim([0, 10])
        plt.ylim([0, 130])
        plt.xticks(np.arange(0, 11, 1))
        plt.yticks(np.arange(0, 130, 10))

        # Show the major grid lines with dark grey lines
        plt.grid(b=True, which='major', color='#D3D3D3', linestyle='-')

        # Show the minor grid lines with very faint and almost transparent grey lines
        plt.minorticks_on()
        plt.grid(b=True, which='minor', color='#DCDCDC', linestyle='-', alpha=0.4)
        # plt.show()
    return


# =================================================================================================
# Plot for torque_assistance
# =================================================================================================

def plot_graph10(ip_torque, tq_demand, fig, ax, cursor):
    # Only Tune 0  will be determined
    for i in range(len(tune_dict["PD_TUNE0"])):
        # Draw all the lines in the same plot, assigning a label for each one to be
        # Plotting the driver input torque and torque demand
        # Initialise the figure and axes.
        # fig,  = plt.subplots(1, figsize=(10, 8))
        ax.plot(ip_torque, tq_demand[i, :], color=color[i], label=(str(VehSpd_BP[i]) + " Kmph"))
        mplcursors.cursor()  # interactive data selection cursors
        # Add a legend, and position it on the lower right (with no box)
        plt.legend(loc="upper left", title="Legend", frameon=False)

        # cursor = Cursor(ax)
        fig.canvas.mpl_connect('motion_notify_event', cursor.mouse_move10)
        # plt.xlabel("Driver Input Torque (Nm)")
        # plt.ylabel("Assistance Torque Demand (Nm)")
        plt.xlim([0, 10])
        plt.ylim([0, 120])
        plt.xticks(np.arange(0, 11, 1))
        plt.yticks(np.arange(0, 120, 10))

        # Show the major grid lines with dark grey lines
        plt.grid(b=True, which='major', color='#D3D3D3', linestyle='-')

        # Show the minor grid lines with very faint and almost transparent grey lines
        plt.minorticks_on()
        plt.grid(b=True, which='minor', color='#DCDCDC', linestyle='-', alpha=0.4)
        # plt.show()
    return


# =================================================================================================
# Program to check whether a given key already exists in a dictionary.
# =================================================================================================

key_present = 0
search_key_Tune1 = "PD_TUNE1" or "P0_TUNE1" or "P1_TUNE1" or "P2_TUNE1" or "P3_TUNE1" or "P4_TUNE1" or "P5_TUNE1"
search_key_Tune2 = "PD_TUNE2" or "P0_TUNE2" or "P1_TUNE2" or "P2_TUNE2" or "P3_TUNE2" or "P4_TUNE2" or "P5_TUNE2"
search_key_Tune3 = "PD_TUNE3" or "P0_TUNE3" or "P1_TUNE3" or "P2_TUNE3" or "P3_TUNE3" or "P4_TUNE3" or "P5_TUNE3"
search_key_Tune4 = "PD_TUNE4" or "P0_TUNE4" or "P1_TUNE4" or "P2_TUNE4" or "P3_TUNE4" or "P4_TUNE4" or "P5_TUNE4"

if search_key_Tune4 in tune_dict:
    key_present = 4
elif search_key_Tune3 in tune_dict:
    key_present = 3
elif search_key_Tune2 in tune_dict:
    key_present = 2
elif search_key_Tune1 in tune_dict:
    key_present = 1
else:
    key_present = 0

# ===================================================================================================================
# Interpolation for tune_dict(P0, P1, P2, P3, P4, P5, PD) & Vehicle Speed
# ===================================================================================================================

temp_x = max(VehSpd_BP)
ip = range(0, temp_x + 1)
color = []
if key_present == 0 or key_present == 1 or key_present == 2 or key_present == 3 or key_present == 4:
    parameterPD_T0 = []
    parameterP0_T0 = []
    parameterP1_T0 = []
    parameterP2_T0 = []
    parameterP3_T0 = []
    parameterP4_T0 = []
    parameterP5_T0 = []
if key_present == 1 or key_present == 2 or key_present == 3 or key_present == 4:
    parameterPD_T1 = []
    parameterP0_T1 = []
    parameterP1_T1 = []
    parameterP2_T1 = []
    parameterP3_T1 = []
    parameterP4_T1 = []
    parameterP5_T1 = []
if key_present == 2 or key_present == 3 or key_present == 4:
    parameterPD_T2 = []
    parameterP0_T2 = []
    parameterP1_T2 = []
    parameterP2_T2 = []
    parameterP3_T2 = []
    parameterP4_T2 = []
    parameterP5_T2 = []
if key_present == 3 or key_present == 4:
    parameterPD_T3 = []
    parameterP0_T3 = []
    parameterP1_T3 = []
    parameterP2_T3 = []
    parameterP3_T3 = []
    parameterP4_T3 = []
    parameterP5_T3 = []
if key_present == 4:
    parameterPD_T4 = []
    parameterP0_T4 = []
    parameterP1_T4 = []
    parameterP2_T4 = []
    parameterP3_T4 = []
    parameterP4_T4 = []
    parameterP5_T4 = []

VehSpd_BP_AP = range(0, temp_x + 1)
if key_present == 0 or key_present == 1 or key_present == 2 or key_present == 3 or key_present == 4:
    parameterPD_T0 = np.interp(ip, VehSpd_BP, tune_dict["PD_TUNE0"])
    parameterP0_T0 = np.interp(ip, VehSpd_BP, tune_dict["P0_TUNE0"])
    parameterP1_T0 = np.interp(ip, VehSpd_BP, tune_dict["P1_TUNE0"])
    parameterP2_T0 = np.interp(ip, VehSpd_BP, tune_dict["P2_TUNE0"])
    parameterP3_T0 = np.interp(ip, VehSpd_BP, tune_dict["P3_TUNE0"])
    parameterP4_T0 = np.interp(ip, VehSpd_BP, tune_dict["P4_TUNE0"])
    parameterP5_T0 = np.interp(ip, VehSpd_BP, tune_dict["P5_TUNE0"])
if key_present == 1 or key_present == 2 or key_present == 3 or key_present == 4:
    parameterPD_T1 = np.interp(ip, VehSpd_BP, tune_dict["PD_TUNE1"])
    parameterP0_T1 = np.interp(ip, VehSpd_BP, tune_dict["P0_TUNE1"])
    parameterP1_T1 = np.interp(ip, VehSpd_BP, tune_dict["P1_TUNE1"])
    parameterP2_T1 = np.interp(ip, VehSpd_BP, tune_dict["P2_TUNE1"])
    parameterP3_T1 = np.interp(ip, VehSpd_BP, tune_dict["P3_TUNE1"])
    parameterP4_T1 = np.interp(ip, VehSpd_BP, tune_dict["P4_TUNE1"])
    parameterP5_T1 = np.interp(ip, VehSpd_BP, tune_dict["P5_TUNE1"])
if key_present == 2 or key_present == 3 or key_present == 4:
    parameterPD_T2 = np.interp(ip, VehSpd_BP, tune_dict["PD_TUNE2"])
    parameterP0_T2 = np.interp(ip, VehSpd_BP, tune_dict["P0_TUNE2"])
    parameterP1_T2 = np.interp(ip, VehSpd_BP, tune_dict["P1_TUNE2"])
    parameterP2_T2 = np.interp(ip, VehSpd_BP, tune_dict["P2_TUNE2"])
    parameterP3_T2 = np.interp(ip, VehSpd_BP, tune_dict["P3_TUNE2"])
    parameterP4_T2 = np.interp(ip, VehSpd_BP, tune_dict["P4_TUNE2"])
    parameterP5_T2 = np.interp(ip, VehSpd_BP, tune_dict["P5_TUNE2"])
if key_present == 3 or key_present == 4:
    parameterPD_T3 = np.interp(ip, VehSpd_BP, tune_dict["PD_TUNE3"])
    parameterP0_T3 = np.interp(ip, VehSpd_BP, tune_dict["P0_TUNE3"])
    parameterP1_T3 = np.interp(ip, VehSpd_BP, tune_dict["P1_TUNE3"])
    parameterP2_T3 = np.interp(ip, VehSpd_BP, tune_dict["P2_TUNE3"])
    parameterP3_T3 = np.interp(ip, VehSpd_BP, tune_dict["P3_TUNE3"])
    parameterP4_T3 = np.interp(ip, VehSpd_BP, tune_dict["P4_TUNE3"])
    parameterP5_T3 = np.interp(ip, VehSpd_BP, tune_dict["P5_TUNE3"])
if key_present == 4:
    parameterPD_T4 = np.interp(ip, VehSpd_BP, tune_dict["PD_TUNE4"])
    parameterP0_T4 = np.interp(ip, VehSpd_BP, tune_dict["P0_TUNE4"])
    parameterP1_T4 = np.interp(ip, VehSpd_BP, tune_dict["P1_TUNE4"])
    parameterP2_T4 = np.interp(ip, VehSpd_BP, tune_dict["P2_TUNE4"])
    parameterP3_T4 = np.interp(ip, VehSpd_BP, tune_dict["P3_TUNE4"])
    parameterP4_T4 = np.interp(ip, VehSpd_BP, tune_dict["P4_TUNE4"])
    parameterP5_T4 = np.interp(ip, VehSpd_BP, tune_dict["P5_TUNE4"])

for i in range(0, temp_x + 1):
    color.append('#%06X' % randint(0, 0xFFFFFF))

# def boost_curve_AP(PD, P0, P1, P2, P3, P4, P5, Ip_res):

#     # Column torque values in the range from 0 to 10 with step size of 0.1
#     global input_torque_AP
#     input_torque_AP = np.arange(0, 10, Ip_res) # User input values
#     # To initialize with random values of torque_demand
#     torque_demand_AP = np.zeros((len(parameterPD_T0), len(input_torque_AP)), dtype=np.float64)

#     # Calculation of Boost Torque based on Linear and Quadratic expressions
#     for i in range(len(parameterPD_T0)):
#         section_tune0_P1_AP  = abs(input_torque_AP) * PD[i]
#         section_tune0_P2_AP  = abs((((P2[i] - PD[i]) * (abs(input_torque_AP) - P0[i])**2) / (2*P1[i])) + (PD[i] * abs(input_torque_AP)))
#         section_tune0_P3_AP  = abs((P2[i] * (abs(input_torque_AP)-P0[i]-P1[i])) + (P2[i] * P1[i]/2) + (PD[i] * ((P0[i]) + (P1[i]/2))))
#         section_tune0_P4_AP  = abs(((P5[i]-P2[i])*((abs(input_torque_AP)-P3[i])**2)/(2*P4[i])) + P2[i]*(abs(input_torque_AP)-P0[i]-(P1[i]/2)) + (PD[i] * ((P0[i]) + (P1[i]/2))))
#         section_tune0_P5_AP  = abs((P5[i] * (abs(input_torque_AP)-P3[i]-(P4[i]/2))) + (P2[i] * (P3[i]+(P4[i]/2)-(P1[i]/2)-P0[i])) + (PD[i] * ((P0[i]) + (P1[i]/2))))

#         for j in range(len(input_torque_AP)):
#             if (input_torque_AP[j] >= 0) and (input_torque_AP[j] < P0[i]):
#                 torque_demand_AP[i][j] = section_tune0_P1_AP[j]
#             elif input_torque_AP[j] >= P0[i] and input_torque_AP[j] < (P0[i] + P1[i]):
#                 torque_demand_AP[i][j] = section_tune0_P2_AP[j]
#             elif input_torque_AP[j] >= (P0[i] + P1[i]) and input_torque_AP[j] < P3[i]:
#                 torque_demand_AP[i][j] = section_tune0_P3_AP[j]
#             elif input_torque_AP[j] >= P3[i] and input_torque_AP[j] < (P3[i] + P4[i]):
#                 torque_demand_AP[i][j] = section_tune0_P4_AP[j]
#             elif input_torque_AP[j] >= (P3[i] + P4[i]):
#                 torque_demand_AP[i][j] = section_tune0_P5_AP[j]
#             else:
#                 torque_demand_AP[i][j] = section_tune0_P5_AP[j]

#         # To limit the maximum output torque Demand for CD
#         torque_demand_AP[torque_demand_AP > float(Tq_demand_Max)] = float(Tq_demand_Max)

#     return torque_demand_AP, input_torque_AP


# =================================================================================================
# Final Boost curve and Assistance plots visualization
# =================================================================================================
# Only Tune 0 will be determined
if key_present == 0 or key_present == 1 or key_present == 2 or key_present == 3 or key_present == 4:
    torque_demand0, torque_assist_NR, input_torque = boost_curve(parameterPD_T0, parameterP0_T0, parameterP1_T0,
                                                                 parameterP2_T0, parameterP3_T0, parameterP4_T0,
                                                                 parameterP5_T0, IpTqRes_User)

    fig10 = plt.figure(figsize=(10, 8))
    ax10 = fig10.gca(projection='3d')
    ax10.set_title('Boost Curve - Tune0', fontsize=20)
    ax10.set_xlabel('Driver Input Torque')
    ax10.set_ylabel('Vehicle Speed')
    ax10.set_zlabel('Assistance Torque Demand')
    X1, X2 = np.meshgrid(input_torque, VehSpd_BP_AP)
    surface0 = ax10.plot_surface(X1, X2, torque_demand0, cmap=cm.coolwarm, linewidth=0)
    fig10.colorbar(surface0, shrink=0.5)
    datacursor(surface0)

    # 2D plotting - Assistance torque Demand tune 0
    torque_demand_NR0, torque_assist0, input_torque = boost_curve(tune_dict["PD_TUNE0"], tune_dict["P0_TUNE0"],
                                                               tune_dict["P1_TUNE0"], tune_dict["P2_TUNE0"],
                                                               tune_dict["P3_TUNE0"], tune_dict["P4_TUNE0"],
                                                               tune_dict["P5_TUNE0"], IpTqRes_User)
    fig0, ax0 = plt.subplots(1, figsize=(10, 8))
    # Set the title for the figure
    fig0.suptitle('Boost Curve - Tune0', fontsize=20)
    cursor0 = Cursor(ax0)
    plt.xlabel("Driver Input Torque(Nm)")
    plt.ylabel("Assistance Torque Demand(Nm)")
    plot_graph(input_torque, torque_demand_NR0, fig0, ax0, cursor0)
    plt.savefig('BoostCurve_Tune0.jpg', dpi=300, bbox_inches='tight')


    # Assistance%  tune 0
    fig3, ax3 = plt.subplots(1, figsize=(10, 8))
    # Set the title for the figure
    fig3.suptitle('Assistance % - Tune0', fontsize=20)
    cursor3 = Cursor1(ax3)
    plt.xlabel("Driver Input Torque(Nm)")
    plt.ylabel("Assistance(%)")
    plot_graph10(input_torque, torque_assist0, fig3, ax3, cursor3)
    plt.savefig('Assistance_Tune0.jpg', dpi=300, bbox_inches='tight')

# Only Tune 0 and Tune 1 will be determined
if key_present == 1 or key_present == 2 or key_present == 3 or key_present == 4:
    torque_demand1, torque_assist_NR, input_torque = boost_curve(parameterPD_T1, parameterP0_T1, parameterP1_T1,
                                                                 parameterP2_T1, parameterP3_T1, parameterP4_T1,
                                                                 parameterP5_T1, IpTqRes_User)

    fig20 = plt.figure(figsize=(10, 8))
    ax20 = fig20.gca(projection='3d')
    ax20.set_title('Boost Curve - Tune1', fontsize=20)
    ax20.set_xlabel('Driver Input Torque')
    ax20.set_ylabel('Vehicle Speed')
    ax20.set_zlabel('Assistance Torque Demand')
    X3, X4 = np.meshgrid(input_torque, VehSpd_BP_AP)
    surface1 = ax20.plot_surface(X3, X4, torque_demand1, cmap=cm.coolwarm, linewidth=0)
    fig20.colorbar(surface1, shrink=0.5)
    datacursor(surface1)

    # 2D plotting - Assistance torque Demand tune 1
    torque_demand_NR1, torque_assist1, input_torque = boost_curve(tune_dict["PD_TUNE1"], tune_dict["P0_TUNE1"],
                                                                 tune_dict["P1_TUNE1"], tune_dict["P2_TUNE1"],
                                                                 tune_dict["P3_TUNE1"], tune_dict["P4_TUNE1"],
                                                                 tune_dict["P5_TUNE1"], IpTqRes_User)
    fig1, ax1 = plt.subplots(1, figsize=(10, 8))
    # Set the title for the figure
    fig1.suptitle('Boost Curve - Tune1', fontsize=20)
    cursor1 = Cursor(ax1)
    plt.xlabel("Driver Input Torque(Nm)")
    plt.ylabel("Assistance Torque Demand(Nm)")
    plot_graph(input_torque, torque_demand_NR1, fig1, ax1, cursor1)
    plt.savefig('BoostCurve_Tune1.jpg', dpi=300, bbox_inches='tight')


    # Assistance% tune 1
    fig4, ax4 = plt.subplots(1, figsize=(10, 8))
    # Set the title for the figure
    fig4.suptitle('Assistance % - Tune1', fontsize=20)
    cursor4 = Cursor1(ax4)
    plt.xlabel("Driver Input Torque(Nm)")
    plt.ylabel("Assistance(%)")
    plot_graph10(input_torque, torque_assist1, fig4, ax4, cursor4)
    plt.savefig('Assistance_Tune1.jpg', dpi=300, bbox_inches='tight')

# Only Tune 0, Tune 1  and Tune 2 will be determined
if key_present == 2 or key_present == 3 or key_present == 4:
    torque_demand2, torque_assist_NR, input_torque = boost_curve(parameterPD_T2, parameterP0_T2, parameterP1_T2,
                                                               parameterP2_T2, parameterP3_T2, parameterP4_T2,
                                                               parameterP5_T2, IpTqRes_User)
    fig30 = plt.figure(figsize=(10, 8))
    ax30 = fig30.gca(projection='3d')
    ax30.set_title('Boost Curve - Tune2', fontsize=20)
    ax30.set_xlabel('Driver Input Torque')
    ax30.set_ylabel('Vehicle Speed')
    ax30.set_zlabel('Assistance Torque Demand')
    X5, X6 = np.meshgrid(input_torque, VehSpd_BP_AP)
    surface2 = ax30.plot_surface(X5, X6, torque_demand2, cmap=cm.coolwarm, linewidth=0)
    fig30.colorbar(surface2, shrink=0.5)
    datacursor(surface2)

    # 2D plotting - Assistance torque Demand tune 2
    torque_demand_NR2, torque_assist2, input_torque = boost_curve(tune_dict["PD_TUNE2"], tune_dict["P0_TUNE2"],
                                                                 tune_dict["P1_TUNE2"], tune_dict["P2_TUNE2"],
                                                                 tune_dict["P3_TUNE2"], tune_dict["P4_TUNE2"],
                                                                 tune_dict["P5_TUNE2"], IpTqRes_User)

    fig2, ax2 = plt.subplots(1, figsize=(10, 8))
    # Set the title for the figure
    fig2.suptitle('Boost Curve - Tune2', fontsize=20)
    cursor2 = Cursor(ax2)
    plt.xlabel("Driver Input Torque(Nm)")
    plt.ylabel("Assistance Torque Demand(Nm)")
    plot_graph(input_torque, torque_demand_NR2, fig2, ax2, cursor2)
    plt.savefig('BoostCurve_Tune2.jpg', dpi=300, bbox_inches='tight')


    # Assistance% tune 2
    fig5, ax5 = plt.subplots(1, figsize=(10, 8))
    # Set the title for the figure
    fig5.suptitle('Assistance % - Tune2', fontsize=20)
    cursor5 = Cursor1(ax5)
    plt.xlabel("Driver Input Torque(Nm)")
    plt.ylabel("Assistance(%)")
    plot_graph10(input_torque, torque_assist2, fig5, ax5, cursor5)
    plt.savefig('Assistance_Tune2.jpg', dpi=300, bbox_inches='tight')

# Only Tune 0, Tune 1, Tune 2  and Tune 3 will be determined
if key_present == 3 or key_present == 4:
    torque_demand3, torque_assist_NR, input_torque = boost_curve(parameterPD_T3, parameterP0_T3, parameterP1_T3,
                                                               parameterP2_T3, parameterP3_T3, parameterP4_T3,
                                                               parameterP5_T3, IpTqRes_User)
    fig40 = plt.figure(figsize=(10, 8))
    ax40 = fig40.gca(projection='3d')
    ax40.set_title('Boost Curve - Tune3', fontsize=20)
    ax40.set_xlabel('Driver Input Torque')
    ax40.set_ylabel('Vehicle Speed')
    ax40.set_zlabel('Assistance Torque Demand')
    X7, X8 = np.meshgrid(input_torque, VehSpd_BP_AP)
    surface3 = ax40.plot_surface(X7, X8, torque_demand3, cmap=cm.coolwarm, linewidth=0)
    fig40.colorbar(surface3, shrink=0.5)
    datacursor(surface3)

    torque_demand_NR3, torque_assist3, input_torque = boost_curve(tune_dict["PD_TUNE3"], tune_dict["P0_TUNE3"],
                                                                 tune_dict["P1_TUNE3"], tune_dict["P2_TUNE3"],
                                                                 tune_dict["P3_TUNE3"], tune_dict["P4_TUNE3"],
                                                                 tune_dict["P5_TUNE3"], IpTqRes_User)
    # 2D plotting - Assistance torque Demand tune 3
    fig6, ax6 = plt.subplots(1, figsize=(10, 8))
    # Set the title for the figure
    fig6.suptitle('Boost Curve - Tune3', fontsize=20)
    cursor6 = Cursor(ax6)
    plt.xlabel("Driver Input Torque(Nm)")
    plt.ylabel("Assistance Torque Demand(Nm)")
    plot_graph(input_torque, torque_demand_NR3, fig6, ax6, cursor6)
    plt.savefig('BoostCurve_Tune3.jpg', dpi=300, bbox_inches='tight')

    # Assistance% tune 3
    fig7, ax7 = plt.subplots(1, figsize=(10, 8))
    # Set the title for the figure
    fig7.suptitle('Assistance % - Tune3', fontsize=20)
    cursor7 = Cursor1(ax7)
    plt.xlabel("Driver Input Torque(Nm)")
    plt.ylabel("Assistance(%)")
    plot_graph10(input_torque, torque_assist3, fig7, ax7, cursor7)
    plt.savefig('Assistance_Tune3.jpg', dpi=300, bbox_inches='tight')

# All tunes are determined
if key_present == 4:
    torque_demand4, torque_assist_NR, input_torque = boost_curve(parameterPD_T4, parameterP0_T4, parameterP1_T4,
                                                               parameterP2_T4, parameterP3_T4, parameterP4_T4,
                                                               parameterP5_T4, IpTqRes_User)
    fig50 = plt.figure(figsize=(10, 8))
    ax50 = fig50.gca(projection='3d')
    ax50.set_title('Boost Curve - Tune4', fontsize=20)
    ax50.set_xlabel('Driver Input Torque')
    ax50.set_ylabel('Vehicle Speed')
    ax50.set_zlabel('Assistance Torque Demand')
    X9, X10 = np.meshgrid(input_torque, VehSpd_BP_AP)
    surface4 = ax50.plot_surface(X9, X10, torque_demand4, cmap=cm.coolwarm, linewidth=0)
    fig50.colorbar(surface4, shrink=0.5)
    datacursor(surface4)

    torque_demand_NR4, torque_assist4, input_torque = boost_curve(tune_dict["PD_TUNE4"], tune_dict["P0_TUNE4"],
                                                                 tune_dict["P1_TUNE4"], tune_dict["P2_TUNE4"],
                                                                 tune_dict["P3_TUNE4"], tune_dict["P4_TUNE4"],
                                                                 tune_dict["P5_TUNE4"], IpTqRes_User)
    # 2D plotting - Assistance torque Demand tune 4
    fig8, ax8 = plt.subplots(1, figsize=(10, 8))
    # Set the title for the figure
    fig8.suptitle('Boost Curve - Tune4', fontsize=20)
    cursor8 = Cursor(ax8)
    plt.xlabel("Driver Input Torque(Nm)")
    plt.ylabel("Assistance Torque Demand(Nm)")
    plot_graph(input_torque, torque_demand_NR4, fig8, ax8, cursor8)
    plt.savefig('BoostCurve_Tune4.jpg', dpi=300, bbox_inches='tight')

    # Assistance% tune 4
    fig9, ax9 = plt.subplots(1, figsize=(10, 8))
    # Set the title for the figure
    fig9.suptitle('Assistance % - Tune4', fontsize=20)
    cursor9 = Cursor1(ax9)
    plt.xlabel("Driver Input Torque(Nm)")
    plt.ylabel("Assistance(%)")
    plot_graph10(input_torque, torque_assist4, fig9, ax9, cursor9)
    plt.savefig('Assistance_Tune4.jpg', dpi=300, bbox_inches='tight')

plt.show()

# =================================================================================================
# End of boost-curve plotting
# =================================================================================================

# =================================================================================================
# Writing data to excel (Driver Torque & Assistance Torque)
# =================================================================================================
workbook = xlsxwriter.Workbook(os.path.join(os.path.expanduser("~"), 'Desktop') +"\\Test.xlsx")
row = 0
col = 0
header_format = workbook.add_format({
    'bold': True,
    'fg_color': '#118dff',
    'border': 1})
input_format = workbook.add_format({
    'bold': True,
    'fg_color': '#f1c716',
    'border': 1})
output_format = workbook.add_format({
    'bold': True,
    'fg_color': '#426871',
    'border': 1})
# title = []

# print(len(tune_dict["PD_TUNE0"]))
# print(len(VehSpd_BP))
# for i in range(len(tune_dict["PD_TUNE0"])):
#     title[i] = ['Driver Torque', ("Assist Trq- " + str(VehSpd_BP[i]) + " Kmph")]
# print(title)
title = ['Driver Torque', ("Assist Trq- " + str(VehSpd_BP[0]) + " Kmph"),
         ("Assist Trq- " + str(VehSpd_BP[1]) + " Kmph"), ("Assist Trq- " + str(VehSpd_BP[2]) + " Kmph"),
         ("Assist Trq- " + str(VehSpd_BP[3]) + " Kmph"), ("Assist Trq- " + str(VehSpd_BP[4]) + " Kmph"),
         ("Assist Trq- " + str(VehSpd_BP[5]) + " Kmph"),
         ("Assist Trq- " + str(VehSpd_BP[6]) + " Kmph"), ("Assist Trq- " + str(VehSpd_BP[7]) + " Kmph"),
         ("Assist Trq- " + str(VehSpd_BP[8]) + " Kmph"),
         ("Assist Trq- " + str(VehSpd_BP[9]) + " Kmph"), ("Assist Trq- " + str(VehSpd_BP[10]) + " Kmph"),
         ("Assist Trq- " + str(VehSpd_BP[11]) + " Kmph")]

# Only Tune 0 data will be created in excel
if key_present == 0 or key_present == 1 or key_present == 2 or key_present == 3 or key_present == 4:
    worksheet = workbook.add_worksheet('Tune0')
    # Setting the width of the columns to 17
    worksheet.set_column('A:M', 17)
    # Setting the height of the first row to 16
    # worksheet.set_row(0, 16)

    # worksheet.set_default_row(4)
    for j, t in enumerate(title):
        worksheet.write(row, col + j, t, header_format)

    row = 1
    worksheet.write_column(row, 0, input_torque, input_format)
    for col, value in enumerate(torque_demand0):
        worksheet.write_column(row, col + 1, value, output_format)

    # Only Tune 0 and Tune 1 data will be created in excel
if key_present == 1 or key_present == 2 or key_present == 3 or key_present == 4:
    worksheet = workbook.add_worksheet('Tune1')
    worksheet.set_column('A:M', 17)
    row = 0
    col = 0
    for j, t in enumerate(title):
        worksheet.write(row, col + j, t, header_format)

    row = 1
    worksheet.write_column(row, 0, input_torque, input_format)
    for col, value in enumerate(torque_demand1):
        worksheet.write_column(row, col + 1, value, output_format)

# Only Tune 0, Tune 1 and Tune 2 data will be created in excel
if key_present == 2 or key_present == 3 or key_present == 4:
    worksheet = workbook.add_worksheet('Tune2')
    worksheet.set_column('A:M', 17)
    row = 0
    col = 0
    for j, t in enumerate(title):
        worksheet.write(row, col + j, t, header_format)

    row = 1
    worksheet.write_column(row, 0, input_torque, input_format)
    for col, value in enumerate(torque_demand2):
        worksheet.write_column(row, col + 1, value, output_format)

# Only Tune 0, Tune 1, Tune 2 and Tune 3 data will be created in excel
if key_present == 3 or key_present == 4:
    worksheet = workbook.add_worksheet('Tune3')
    worksheet.set_column('A:M', 17)
    row = 0
    col = 0
    for j, t in enumerate(title):
        worksheet.write(row, col + j, t, header_format)

    row = 1
    worksheet.write_column(row, 0, input_torque, input_format)
    for col, value in enumerate(torque_demand3):
        worksheet.write_column(row, col + 1, value, output_format)

# All tune's data will be created in excel
if key_present == 4:
    worksheet = workbook.add_worksheet('Tune4')
    worksheet.set_column('A:M', 17)
    row = 0
    col = 0
    for j, t in enumerate(title):
        worksheet.write(row, col + j, t, header_format)

    row = 1
    worksheet.write_column(row, 0, input_torque, input_format)
    for col, value in enumerate(torque_demand4):
        worksheet.write_column(row, col + 1, value, output_format)

workbook.close()

# =================================================================================================
# End of writing data to excel (Driver Torque & Assistance Torque)
# =================================================================================================

# =================================================================================================
# Tkinter GUI interface 2 (Driver Torque and Assistance Torque Calculator)
# =================================================================================================

VehSpd_range = [(str(VehSpd_BP[0]) + " Kmph"),
                (str(VehSpd_BP[1]) + " Kmph"),
                (str(VehSpd_BP[2]) + " Kmph"),
                (str(VehSpd_BP[3]) + " Kmph"),
                (str(VehSpd_BP[4]) + " Kmph"),
                (str(VehSpd_BP[5]) + " Kmph"),
                (str(VehSpd_BP[6]) + " Kmph"),
                (str(VehSpd_BP[7]) + " Kmph"),
                (str(VehSpd_BP[8]) + " Kmph"),
                (str(VehSpd_BP[9]) + " Kmph"),
                (str(VehSpd_BP[10]) + " Kmph"),
                (str(VehSpd_BP[11]) + " Kmph")
                ]


class BoostCurveCalc(tk.Tk):

    # __init__ function for class BoostCurveCalc
    def __init__(self, *args, **kwargs):
        # root = tk.Tk
        # root.title("Boost Curve")
        # root.geometry('960x720')
        # root.configure(bg="#c0ded9")
        # self.title("Boost Curve")
        # self.geometry("720x680+600+300")
        # self.configure(bg="#c0ded9")

        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)

        self.title("Boost Curve")
        self.geometry("1060x620")
        self.configure(bg="#4b8bbe")

        # creating a container
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # initializing frames to an empty array
        self.frames = {}

        # iterating through a tuple consisting
        # of the different page layouts
        for F in (MainPage, Page1, Page2, Page3, Page4, Page5):
            frame = F(container, self)

            # initializing frame of that object from
            # MainPage, page1, page2 respectively with
            # for loop
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(MainPage)

        # to display the current frame passed as

    # parameter
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    # first window frame MainPage


class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        def openexcel():
            os.system("start " + os.path.join(os.path.expanduser("~"), 'Desktop') +"\\Test.xlsx")

            return

        Mainframe = Frame(self, bd=10)
        Mainframe.grid()

        Tops = Frame(Mainframe, bd=10, width=620, height=200, relief=GROOVE)
        Tops.pack(side=TOP)

        lblInfo = Label(Tops, font=('Helvetica', 31, 'bold'), text="Boost Curve Calculator", justify=CENTER,
                        bg="#c0ded9", width=25).grid(padx=170, pady=10)

        MembersName2v_F = tk.LabelFrame(Mainframe, bd=10, width=300, height=200, font=('Helvetica', 14, 'bold'),
                                        text="Select the Tune mode", fg="#006666", relief=GROOVE)
        MembersName2v_F.pack(side=TOP, padx=40, pady=20)

        MembersName3v_F = tk.LabelFrame(Mainframe, bd=10, width=300, height=100, font=('Helvetica', 14, 'bold'),
                                        text="Tune(s) data in Excel", fg="#006666", relief=GROOVE)
        MembersName3v_F.pack(side=TOP, pady=20)
        # # label of frame Layout 2
        # label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="Boost Curve Calculation", justify=CENTER, bg= "#c0ded9", highlightthickness=2, highlightbackground="#111")
        # # putting the grid in its place by using
        # # grid
        # label.grid(padx = 170, pady = 10)

        # label = tk.Label(self, font=('Helvetica', 20, 'bold'), text="Select the Tune mode to analyze the boost curve", justify=CENTER, bg= "#c0ded9")

        # # putting the grid in its place by using
        # # grid
        # label.grid(padx = 170, pady = 20)

        button1 = tk.Button(MembersName2v_F, bd=7, font=('Helvetica', 14, 'bold'), width=7,
                            command=lambda: controller.show_frame(Page1), text="Tune 0", bg="#c0ded9")
        # button1 = Button(MembersName_F, text ="Tune 0", command = lambda : controller.show_frame(Page1), font=('Helvetica', 16, 'bold'), justify=CENTER, bg= "#c0ded9")

        # # putting the button in its place by
        # # using grid
        button1.pack(padx=150, pady=6)
        if key_present == 1 or key_present == 2 or key_present == 3 or key_present == 4:
            ## button to show frame 2 with text layout2
            button2 = tk.Button(MembersName2v_F, bd=7, text="Tune 1", command=lambda: controller.show_frame(Page2),
                                width=7, font=('Helvetica', 14, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button2.pack(padx=150, pady=6)
        if key_present == 2 or key_present == 3 or key_present == 4:
            button3 = tk.Button(MembersName2v_F, bd=7, width=7, text="Tune 2",
                                command=lambda: controller.show_frame(Page3), font=('Helvetica', 14, 'bold'),
                                bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button3.pack(padx=150, pady=6)

        if key_present == 3 or key_present == 4:
            button5 = tk.Button(MembersName2v_F, bd=7, width=7, text="Tune 3",
                                command=lambda: controller.show_frame(Page4), font=('Helvetica', 14, 'bold'),
                                bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button5.pack(padx=150, pady=6)

        if key_present == 4:
            button6 = tk.Button(MembersName2v_F, bd=7, width=7, text="Tune 4",
                                command=lambda: controller.show_frame(Page5), font=('Helvetica', 14, 'bold'),
                                bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button6.pack(padx=150, pady=6)

        button4 = tk.Button(MembersName3v_F, bd=7, width=10, text="Open Excel", command=openexcel,
                            font=('Helvetica', 16, 'bold'), bg="#00af00")

        # putting the button in its place by
        # using grid
        button4.pack(padx=126, pady=6)

# second window frame page1
class Page1(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        # Reset for Tune 0
        Assist_Tq_Dmd_user = tk.StringVar()
        Driver_Tq_user = tk.StringVar()

        def Reset():
            VehSpd.set(" ")
            Assist_Tq_Dmd_user.set("")
            Driver_Tq_user.set("")
            Output_At_Dt.set("")
            Output_Dt_At.set("")
            Switch_AT_DT.set(" ")
            rad1.set(0)

            # =================================================================================================
            # Default selection & calculation of AT to DT
            # =================================================================================================
            tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(row=7,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=4,
                                                                                                               sticky=tk.W)
            tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(row=9,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=15,
                                                                                                               sticky=tk.W)
            tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_At_Dt, width=15,
                     state=DISABLED).grid(row=9, column=2, pady=12)
            Assist_Tq_Dmd_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7,
                                             textvariable=Assist_Tq_Dmd_user, width=15).grid(row=7, column=2)
            tk.Button(self, text='Convert', command=assist_torque, font=('Helvetica', 13, 'bold'), width=10,
                      bg="#c0ded9").grid(row=8, column=2, pady=4)
            # =================================================================================================
            # End of Default selection & calculation of AT to DT
            # =================================================================================================
            return

        def VehSpdData(speed):  # pass new scale value
            global VehSpd_Data
            self.VehSpd_Data = int(VehSpd.get())
            return self.VehSpd_Data

        # global assist_value
        def assist_torque():

            global assist_value
            assist_value = Assist_Tq_Dmd_user.get()
            if str(assist_value) == "":
                error()
            else:
                output = np.interp(assist_value, torque_demand0[self.VehSpd_Data], input_torque)
                Output_At_Dt.set(output)
            return

        # global driver_value
        def driver_torque():

            global driver_value
            driver_value = Driver_Tq_user.get()
            if str(driver_value) == "":
                error()
            else:
                output = np.interp(driver_value, input_torque, torque_demand0[self.VehSpd_Data])
                Output_Dt_At.set(output)
            return

        def switch_at_dt_calc():

            global switch_value
            switch_value = Switch_AT_DT.get()

            if switch_value == 0:
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=7, column=0, padx=10, pady=4, sticky=tk.W)
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=9, column=0, padx=10, pady=15, sticky=tk.W)
                tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_At_Dt, width=15,
                         state=DISABLED).grid(row=9, column=2, pady=12)
                Assist_Tq_Dmd_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7,
                                                 textvariable=Assist_Tq_Dmd_user, width=15).grid(row=7, column=2)
                tk.Button(self, text='Convert', command=assist_torque, font=('Helvetica', 13, 'bold'), width=10,
                          bg="#c0ded9").grid(row=8, column=2, pady=4)
                tk.Label(self, font=('Helvetica', 10, 'bold'), text="*Note: Conversion from Assist Torque to Driver Torque", justify=CENTER,\
                         bd=7).grid(row=7, column=3, sticky=tk.W, columnspan=3)

            else:
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=7, column=0, padx=10, pady=4, sticky=tk.W)
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=9, column=0, padx=10, pady=15, sticky=tk.W)
                tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_Dt_At, width=15,
                         state=DISABLED).grid(row=7, column=2, pady=12)
                Driver_Tq_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Driver_Tq_user,
                                             width=15).grid(row=9, column=2)
                tk.Button(self, text='Convert', command=driver_torque, font=('Helvetica', 13, 'bold'), width=10,
                          bg="#c0ded9").grid(row=8, column=2, pady=4)
                tk.Label(self, font=('Helvetica', 10, 'bold'), text="*Note: Conversion from Driver Torque to Assist Torque", justify=CENTER,\
                         bd=7).grid(row=7, column=3, sticky=tk.W, columnspan=3)

            return

        def error():
            screen1 = Toplevel(self)
            screen1.geometry("220x50")
            screen1.title("Warning!")
            Label(screen1, font=('Helvetica', 16, 'bold'), text="All fields required!", justify=CENTER, bd=7,
                  fg="red").grid(row=1, column=0, padx=10, sticky=W)

            return

        label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="Tune 0", bg="#c0ded9")
        label.grid(row=0, column=3, padx=10, pady=10, sticky=tk.W)

        # label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="***********************", bg= "#c0ded9")
        # label.grid(row = 11, column = 0, padx = 10, pady = 10)
        tk.Label(self, font=('Helvetica', 16, 'bold'), text="Vehicle Speed Breakpoints", bd=7, justify=LEFT).grid(row=2,
                                                                                                                  column=0,
                                                                                                                  padx=10,
                                                                                                                  pady=4)
        tk.Label(self, font=('Helvetica', 16, 'bold'), text="Switch b/w AT & DT", bd=7).grid(row=6, column=0, padx=10,
                                                                                             pady=4, sticky=W)

        # button to show frame 2 with text
        # layout2
        button1 = tk.Button(self, text="MainPage", command=lambda: controller.show_frame(MainPage),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place
        # by using grid
        button1.grid(row=16, column=2, padx=10, pady=10)

        if key_present == 1 or key_present == 2 or key_present == 3 or key_present == 4:
            # button to show frame 2 with text
            # layout2
            button2 = tk.Button(self, text="Tune 1", command=lambda: controller.show_frame(Page2),
                                font=('Helvetica', 16, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button2.grid(row=16, column=3, sticky=tk.W)
        if key_present == 2 or key_present == 3 or key_present == 4:
            # button to show frame 3 with text
            # layout2
            button3 = tk.Button(self, text="Tune 2", command=lambda: controller.show_frame(Page3),
                                font=('Helvetica', 16, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button3.grid(row=16, column=3, sticky=tk.W, padx=100)

        if key_present == 3 or key_present == 4:
            # button to show frame 3 with text
            # layout2
            button5 = tk.Button(self, text="Tune 3", command=lambda: controller.show_frame(Page4),
                                font=('Helvetica', 16, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button5.grid(row=17, column=3, sticky=tk.W)

        if key_present == 4:
            # button to show frame 3 with text
            # layout2
            button6 = tk.Button(self, text="Tune 4", command=lambda: controller.show_frame(Page5),
                                font=('Helvetica', 16, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button6.grid(row=17, column=3, sticky=tk.W, padx=100)

        VehSpd = tk.DoubleVar()
        # Uncheck the radio buttons when the program starts
        # VehSpd.set(" ")
        VehSpd_Data = VehSpd.set(0)

        Output_At_Dt = tk.StringVar()
        Output_Dt_At = tk.StringVar()
        Switch_AT_DT = tk.IntVar()
        # Uncheck the radio buttons when the program starts
        Switch_AT_DT.set(" ")

        rad1 = Scale(self, orient=HORIZONTAL, resolution=1, length=550, width=15, variable=VehSpd, sliderlength=10,
                     from_=0, to=200, tickinterval=30, font=('Helvetica', 10, 'bold'), command=VehSpdData)
        rad1.grid(row=2, column=3, sticky=tk.W)
        # print(rad1)
        # Vehicle speed alignments
        # for val, data in enumerate(VehSpd_range):
        #     rad1 = tk.Radiobutton(self, text=data, variable=VehSpd, command=VehSpdData, value=val, justify=CENTER)
        #     if val > 7:
        #         if val == 11:
        #             rad1.grid(row=4, column = val-6, sticky = tk.W, padx = 50, pady = 10)
        #         else:
        #             rad1.grid(row=4, column = val-6, sticky = tk.W, pady = 10)
        #     elif val > 3:
        #         if val == 7:
        #             rad1.grid(row=3, column = val-2, sticky = tk.W, padx = 50, pady = 10)
        #         else:
        #             rad1.grid(row=3, column = val-2, sticky = tk.W)
        #     else:
        #         if val == 3:
        #             rad1.grid(row=2, column = val+2, sticky = tk.W, padx = 50, pady = 10)
        #         else:
        #             rad1.grid(row=2, column = val+2, sticky = tk.W)

        # tk.Button(self,text='Enter',command=assist_torque,font=('Helvetica', 13, 'bold'),width=10,bg= "#c0ded9").grid(row=8,column=2,pady=4)
        tk.Button(self, padx=18, bd=7, font=('Helvetica', 13, 'bold'), width=7, command=Reset, text="Reset",
                  bg="#F18F49").grid(row=18, column=2, pady=12)
        tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="AT → DT", variable=Switch_AT_DT,
                       command=switch_at_dt_calc, value=0).grid(row=6, column=2, sticky=tk.W)
        tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="DT → AT", variable=Switch_AT_DT,
                       command=switch_at_dt_calc, value=1).grid(row=6, column=3, sticky=tk.W)


# third window frame page2
class Page2(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        # Reset for Tune 1
        Assist_Tq_Dmd_user = tk.StringVar()
        Driver_Tq_user = tk.StringVar()

        def Reset():
            VehSpd.set(" ")
            Assist_Tq_Dmd_user.set("")
            Driver_Tq_user.set("")
            Output_At_Dt.set("")
            Output_Dt_At.set("")
            Switch_AT_DT.set(" ")

            # =================================================================================================
            # Default selection & calculation of AT to DT
            # =================================================================================================
            tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(row=7,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=4,
                                                                                                               sticky=tk.W)
            tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(row=9,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=15,
                                                                                                               sticky=tk.W)
            tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_At_Dt, width=15,
                     state=DISABLED).grid(row=9, column=2, pady=12)
            Assist_Tq_Dmd_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7,
                                             textvariable=Assist_Tq_Dmd_user, width=15).grid(row=7, column=2)
            tk.Button(self, text='Convert', command=assist_torque, font=('Helvetica', 13, 'bold'), width=10,
                      bg="#c0ded9").grid(row=8, column=2, pady=4)
            # =================================================================================================
            # End of Default selection & calculation of AT to DT
            # =================================================================================================

            return

        # global VehSpd_Data
        def VehSpdData(speed):
            global VehSpd_Data
            self.VehSpd_Data = int(VehSpd.get())
            return self.VehSpd_Data

        # global assist_value
        def assist_torque():

            global assist_value
            assist_value = Assist_Tq_Dmd_user.get()
            if str(assist_value) == "":
                error()
            else:
                output = np.interp(assist_value, torque_demand1[self.VehSpd_Data], input_torque)
                Output_At_Dt.set(output)
            return

        # global driver_value
        def driver_torque():

            global driver_value
            driver_value = Driver_Tq_user.get()
            if str(driver_value) == "":
                error()
            else:
                output = np.interp(driver_value, input_torque, torque_demand1[self.VehSpd_Data])
                Output_Dt_At.set(output)
            return
            # global assist_value

        def switch_at_dt_calc():

            global switch_value
            switch_value = Switch_AT_DT.get()

            if switch_value == 0:
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=7, column=0, padx=10, pady=4, sticky=tk.W)
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=9, column=0, padx=10, pady=15, sticky=tk.W)
                tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_At_Dt, width=15,
                         state=DISABLED).grid(row=9, column=2, pady=12)
                Assist_Tq_Dmd_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7,
                                                 textvariable=Assist_Tq_Dmd_user, width=15).grid(row=7, column=2)
                tk.Button(self, text='Convert', command=assist_torque, font=('Helvetica', 13, 'bold'), width=10,
                          bg="#c0ded9").grid(row=8, column=2, pady=4)
                tk.Label(self, font=('Helvetica', 10, 'bold'),
                         text="*Note: Conversion from Assist Torque to Driver Torque", justify=CENTER, \
                         bd=7).grid(row=7, column=3, sticky=tk.W, columnspan=3)

            else:
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=7, column=0, padx=10, pady=4, sticky=tk.W)
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=9, column=0, padx=10, pady=15, sticky=tk.W)
                tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_Dt_At, width=15,
                         state=DISABLED).grid(row=7, column=2, pady=12)
                Driver_Tq_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Driver_Tq_user,
                                             width=15).grid(row=9, column=2)
                tk.Button(self, text='Convert', command=driver_torque, font=('Helvetica', 13, 'bold'), width=10,
                          bg="#c0ded9").grid(row=8, column=2, pady=4)
                tk.Label(self, font=('Helvetica', 10, 'bold'),
                         text="*Note: Conversion from Driver Torque to Assist Torque", justify=CENTER, \
                         bd=7).grid(row=7, column=3, sticky=tk.W, columnspan=3)

            return

        def error():
            screen1 = Toplevel(self)
            screen1.geometry("220x50")
            screen1.title("Warning!")
            Label(screen1, font=('Helvetica', 16, 'bold'), text="All fields required!", justify=CENTER, bd=7,
                  fg="red").grid(row=1, column=0, padx=10, sticky=W)
            return

        label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="Tune 1", bg="#c0ded9")
        label.grid(row=0, column=3, padx=10, pady=10, sticky=tk.W)

        # label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="***********************", bg= "#c0ded9")
        # label.grid(row = 11, column = 0, padx = 10, pady = 10)
        tk.Label(self, font=('Helvetica', 16, 'bold'), text="Vehicle Speed Breakpoints", bd=7, justify=LEFT).grid(row=2,
                                                                                                                  column=0,
                                                                                                                  padx=10,
                                                                                                                  pady=4)
        tk.Label(self, font=('Helvetica', 16, 'bold'), text="Switch b/w AT & DT", bd=7).grid(row=6, column=0, padx=10,
                                                                                             pady=4, sticky=W)

        # button to show frame 2 with text
        # layout2
        button1 = tk.Button(self, text="MainPage", command=lambda: controller.show_frame(MainPage),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place
        # by using grid
        button1.grid(row=16, column=2, padx=10, pady=10)

        # button to show frame 2 with text
        # layout2
        button2 = tk.Button(self, text="Tune 0", command=lambda: controller.show_frame(Page1),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place by
        # using grid
        button2.grid(row=16, column=3, sticky=tk.W)

        if key_present == 2 or key_present == 3 or key_present == 4:
            # button to show frame 3 with text
            # layout2
            button3 = tk.Button(self, text="Tune 2", command=lambda: controller.show_frame(Page3),
                                font=('Helvetica', 16, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button3.grid(row=16, column=3, sticky=tk.W, padx=100)

        if key_present == 3 or key_present == 4:
            # button to show frame 3 with text
            # layout2
            button5 = tk.Button(self, text="Tune 3", command=lambda: controller.show_frame(Page4),
                                font=('Helvetica', 16, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button5.grid(row=17, column=3, sticky=tk.W)

        if key_present == 4:
            # button to show frame 3 with text
            # layout2
            button6 = tk.Button(self, text="Tune 4", command=lambda: controller.show_frame(Page5),
                                font=('Helvetica', 16, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button6.grid(row=17, column=3, sticky=tk.W, padx=100)

        VehSpd = tk.DoubleVar()
        # Uncheck the radio buttons when the program starts
        # VehSpd.set(" ")
        VehSpd_Data = VehSpd.set(0)

        Output_At_Dt = tk.StringVar()
        Output_Dt_At = tk.StringVar()
        Switch_AT_DT = tk.IntVar()
        # Uncheck the radio buttons when the program starts
        Switch_AT_DT.set(" ")

        rad1 = Scale(self, orient=HORIZONTAL, resolution=1, length=550, width=15, variable=VehSpd, sliderlength=10,
                     from_=0, to=200, tickinterval=30, font=('Helvetica', 10, 'bold'), command=VehSpdData)
        rad1.grid(row=2, column=3, sticky=tk.W)
        # print(rad1)
        # Vehicle speed alignment in tkinter window
        # for val, data in enumerate(VehSpd_range):
        #     rad1 = tk.Radiobutton(self, text=data, variable=VehSpd, command=VehSpdData, value=val, justify=CENTER)
        #     if val > 7:
        #         if val == 11:
        #             rad1.grid(row=4, column=val - 6, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=4, column=val - 6, sticky=tk.W, pady=10)
        #     elif val > 3:
        #         if val == 7:
        #             rad1.grid(row=3, column=val - 2, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=3, column=val - 2, sticky=tk.W)
        #     else:
        #         if val == 3:
        #             rad1.grid(row=2, column=val + 2, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=2, column=val + 2, sticky=tk.W)

        # tk.Button(self,text='Enter',command=assist_torque,font=('Helvetica', 13, 'bold'),width=10,bg= "#c0ded9").grid(row=8,column=2,pady=4)
        tk.Button(self, padx=18, bd=7, font=('Helvetica', 13, 'bold'), width=7, command=Reset, text="Reset",
                  bg="#F18F49").grid(row=18, column=2, pady=12)
        tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="AT → DT", variable=Switch_AT_DT,
                       command=switch_at_dt_calc, value=0).grid(row=6, column=2, sticky=tk.W)
        tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="DT → AT", variable=Switch_AT_DT,
                       command=switch_at_dt_calc, value=1).grid(row=6, column=3, sticky=tk.W)


# fourth window frame page3
class Page3(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)

        switch_value = 0
        Assist_Tq_Dmd_user = tk.StringVar()
        Driver_Tq_user = tk.StringVar()

        def Reset():
            VehSpd.set(" ")
            Assist_Tq_Dmd_user.set("")
            Driver_Tq_user.set("")
            Output_At_Dt.set("")
            Output_Dt_At.set("")
            Switch_AT_DT.set(" ")

            # =================================================================================================
            # Default selection & calculation of AT to DT
            # =================================================================================================
            tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(row=7,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=4,
                                                                                                               sticky=tk.W)
            tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(row=9,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=15,
                                                                                                               sticky=tk.W)
            tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_At_Dt, width=15,
                     state=DISABLED).grid(row=9, column=2, pady=12)
            Assist_Tq_Dmd_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7,
                                             textvariable=Assist_Tq_Dmd_user, width=15).grid(row=7, column=2)
            tk.Button(self, text='Convert', command=assist_torque, font=('Helvetica', 13, 'bold'), width=10,
                      bg="#c0ded9").grid(row=8, column=2, pady=4)
            # =================================================================================================
            # End of Default selection & calculation of AT to DT
            # =================================================================================================

            return

        # global VehSpd_Data
        def VehSpdData(speed):
            global VehSpd_Data
            self.VehSpd_Data = int(VehSpd.get())
            return self.VehSpd_Data

        # global assist_value
        def assist_torque():

            global assist_value
            assist_value = Assist_Tq_Dmd_user.get()
            if str(assist_value) == "":
                error()
            else:
                output = np.interp(assist_value, torque_demand2[self.VehSpd_Data], input_torque)
                Output_At_Dt.set(output)
            return

        # global driver_value
        def driver_torque():

            global driver_value
            driver_value = Driver_Tq_user.get()
            if str(driver_value) == "":
                error()
            else:
                output = np.interp(driver_value, input_torque, torque_demand2[self.VehSpd_Data])
                Output_Dt_At.set(output)
            return

        def switch_at_dt_calc():

            global switch_value
            switch_value = Switch_AT_DT.get()

            if switch_value == 0:
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=7, column=0, padx=10, pady=4, sticky=tk.W)
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=9, column=0, padx=10, pady=15, sticky=tk.W)
                tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_At_Dt, width=15,
                         state=DISABLED).grid(row=9, column=2, pady=12)
                Assist_Tq_Dmd_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7,
                                                 textvariable=Assist_Tq_Dmd_user, width=15).grid(row=7, column=2)
                tk.Button(self, text='Convert', command=assist_torque, font=('Helvetica', 13, 'bold'), width=10,
                          bg="#c0ded9").grid(row=8, column=2, pady=4)
                tk.Label(self, font=('Helvetica', 10, 'bold'),
                         text="*Note: Conversion from Assist Torque to Driver Torque", justify=CENTER, \
                         bd=7).grid(row=7, column=3, sticky=tk.W, columnspan=3)

            else:
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=7, column=0, padx=10, pady=4, sticky=tk.W)
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=9, column=0, padx=10, pady=15, sticky=tk.W)
                tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_Dt_At, width=15,
                         state=DISABLED).grid(row=7, column=2, pady=12)
                Driver_Tq_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Driver_Tq_user,
                                             width=15).grid(row=9, column=2)
                tk.Button(self, text='Convert', command=driver_torque, font=('Helvetica', 13, 'bold'), width=10,
                          bg="#c0ded9").grid(row=8, column=2, pady=4)
                tk.Label(self, font=('Helvetica', 10, 'bold'),
                         text="*Note: Conversion from Driver Torque to Assist Torque", justify=CENTER, \
                         bd=7).grid(row=7, column=3, sticky=tk.W, columnspan=3)

            return

        def error():
            screen1 = Toplevel(self)
            screen1.geometry("220x50")
            screen1.title("Warning!")
            Label(screen1, font=('Helvetica', 16, 'bold'), text="All fields required!", justify=CENTER, bd=7,
                  fg="red").grid(row=1, column=0, padx=10, sticky=W)
            return

        label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="Tune 2", bg="#c0ded9")
        label.grid(row=0, column=3, padx=10, pady=10, sticky=tk.W)

        # label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="***********************", bg= "#c0ded9")
        # label.grid(row = 11, column = 0, padx = 10, pady = 10)
        tk.Label(self, font=('Helvetica', 16, 'bold'), text="Vehicle Speed Breakpoints", bd=7, justify=LEFT).grid(row=2,
                                                                                                                  column=0,
                                                                                                                  padx=10,
                                                                                                                  pady=4)
        tk.Label(self, font=('Helvetica', 16, 'bold'), text="Switch b/w AT & DT", bd=7).grid(row=6, column=0, padx=10,
                                                                                             pady=4, sticky=W)

        # button to show frame 2 with text
        # layout2
        button1 = tk.Button(self, text="MainPage", command=lambda: controller.show_frame(MainPage),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place
        # by using grid
        button1.grid(row=16, column=2, padx=10, pady=10)

        # button to show frame 2 with text
        # layout2
        button2 = tk.Button(self, text="Tune 0", command=lambda: controller.show_frame(Page1),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place by
        # using grid
        button2.grid(row=16, column=3, sticky=tk.W)
        # button to show frame 3 with text
        # layout3
        button3 = tk.Button(self, text="Tune 1", command=lambda: controller.show_frame(Page2),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place by
        # using grid
        button3.grid(row=16, column=3, sticky=tk.W, padx=100)

        if key_present == 3 or key_present == 4:
            # button to show frame 3 with text
            # layout2
            button5 = tk.Button(self, text="Tune 3", command=lambda: controller.show_frame(Page4),
                                font=('Helvetica', 16, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button5.grid(row=17, column=3, sticky=tk.W)

        if key_present == 4:
            # button to show frame 3 with text
            # layout2
            button6 = tk.Button(self, text="Tune 4", command=lambda: controller.show_frame(Page5),
                                font=('Helvetica', 16, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button6.grid(row=17, column=3, sticky=tk.W, padx=100)

        VehSpd = tk.DoubleVar()
        # Uncheck the radio buttons when the program starts
        VehSpd.set(" ")
        VehSpd_Data = VehSpd.set(0)
        Output_At_Dt = tk.StringVar()
        Output_Dt_At = tk.StringVar()
        Switch_AT_DT = tk.IntVar()
        # Uncheck the radio buttons when the program starts
        Switch_AT_DT.set(" ")

        # Vehicle speed alignment in tkinter window
        rad1 = Scale(self, orient=HORIZONTAL, resolution=1, length=550, width=15, variable=VehSpd, sliderlength=10,
                     from_=0, to=200, tickinterval=30, font=('Helvetica', 10, 'bold'), command=VehSpdData)
        rad1.grid(row=2, column=3, sticky=tk.W)
        # for val, data in enumerate(VehSpd_range):
        #     rad1 = tk.Radiobutton(self, text=data, variable=VehSpd, command=VehSpdData, value=val, justify=CENTER)
        #     if val > 7:
        #         if val == 11:
        #             rad1.grid(row=4, column=val - 6, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=4, column=val - 6, sticky=tk.W, pady=10)
        #     elif val > 3:
        #         if val == 7:
        #             rad1.grid(row=3, column=val - 2, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=3, column=val - 2, sticky=tk.W)
        #     else:
        #         if val == 3:
        #             rad1.grid(row=2, column=val + 2, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=2, column=val + 2, sticky=tk.W)

        # tk.Button(self,text='Enter',command=assist_torque,font=('Helvetica', 13, 'bold'),width=10,bg= "#c0ded9").grid(row=8,column=2,pady=4)
        tk.Button(self, padx=18, bd=7, font=('Helvetica', 13, 'bold'), width=7, command=Reset, text="Reset",
                  bg="#F18F49").grid(row=18, column=2, pady=12)
        tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="AT → DT", variable=Switch_AT_DT,
                       command=switch_at_dt_calc, value=0).grid(row=6, column=2, sticky=tk.W)
        tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="DT → AT", variable=Switch_AT_DT,
                       command=switch_at_dt_calc, value=1).grid(row=6, column=3, sticky=tk.W)


# Fifth window frame page4
class Page4(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)

        Assist_Tq_Dmd_user = tk.StringVar()
        Driver_Tq_user = tk.StringVar()

        def Reset():
            VehSpd.set(" ")
            Assist_Tq_Dmd_user.set("")
            Driver_Tq_user.set("")
            Output_At_Dt.set("")
            Output_Dt_At.set("")
            Switch_AT_DT.set(" ")

            # =================================================================================================
            # Default selection & calculation of AT to DT
            # =================================================================================================
            tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(row=7,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=4,
                                                                                                               sticky=tk.W)
            tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(row=9,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=15,
                                                                                                               sticky=tk.W)
            tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_At_Dt, width=15,
                     state=DISABLED).grid(row=9, column=2, pady=12)
            Assist_Tq_Dmd_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7,
                                             textvariable=Assist_Tq_Dmd_user, width=15).grid(row=7, column=2)
            tk.Button(self, text='Convert', command=assist_torque, font=('Helvetica', 13, 'bold'), width=10,
                      bg="#c0ded9").grid(row=8, column=2, pady=4)
            # =================================================================================================
            # End of Default selection & calculation of AT to DT
            # =================================================================================================

            return

        # global VehSpd_Data
        def VehSpdData(speed):
            global VehSpd_Data
            self.VehSpd_Data = int(VehSpd.get())
            return self.VehSpd_Data

        # global assist_value
        def assist_torque():

            global assist_value
            assist_value = Assist_Tq_Dmd_user.get()
            if str(assist_value) == "":
                error()
            else:
                output = np.interp(assist_value, torque_demand3[self.VehSpd_Data], input_torque)
                Output_At_Dt.set(output)
            return

        # global driver_value
        def driver_torque():

            global driver_value
            driver_value = Driver_Tq_user.get()
            if str(driver_value) == "":
                error()
            else:
                output = np.interp(driver_value, input_torque, torque_demand3[self.VehSpd_Data])
                Output_Dt_At.set(output)
            return

        def switch_at_dt_calc():

            global switch_value
            switch_value = Switch_AT_DT.get()

            if switch_value == 0:
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=7, column=0, padx=10, pady=4, sticky=tk.W)
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=9, column=0, padx=10, pady=15, sticky=tk.W)
                tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_At_Dt, width=15,
                         state=DISABLED).grid(row=9, column=2, pady=12)
                Assist_Tq_Dmd_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7,
                                                 textvariable=Assist_Tq_Dmd_user, width=15).grid(row=7, column=2)
                tk.Button(self, text='Convert', command=assist_torque, font=('Helvetica', 13, 'bold'), width=10,
                          bg="#c0ded9").grid(row=8, column=2, pady=4)
                tk.Label(self, font=('Helvetica', 10, 'bold'),
                         text="*Note: Conversion from Assist Torque to Driver Torque", justify=CENTER, \
                         bd=7).grid(row=7, column=3, sticky=tk.W, columnspan=3)

            else:
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=7, column=0, padx=10, pady=4, sticky=tk.W)
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=9, column=0, padx=10, pady=15, sticky=tk.W)
                tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_Dt_At, width=15,
                         state=DISABLED).grid(row=7, column=2, pady=12)
                Driver_Tq_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Driver_Tq_user,
                                             width=15).grid(row=9, column=2)
                tk.Button(self, text='Convert', command=driver_torque, font=('Helvetica', 13, 'bold'), width=10,
                          bg="#c0ded9").grid(row=8, column=2, pady=4)
                tk.Label(self, font=('Helvetica', 10, 'bold'),
                         text="*Note: Conversion from Driver Torque to Assist Torque", justify=CENTER, \
                         bd=7).grid(row=7, column=3, sticky=tk.W, columnspan=3)

            return

        def error():
            screen1 = Toplevel(self)
            screen1.geometry("220x50")
            screen1.title("Warning!")
            Label(screen1, font=('Helvetica', 16, 'bold'), text="All fields required!", justify=CENTER, bd=7,
                  fg="red").grid(row=1, column=0, padx=10, sticky=W)
            return

        label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="Tune 3", bg="#c0ded9")
        label.grid(row=0, column=3, padx=10, pady=10, sticky=tk.W)

        # label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="***********************", bg= "#c0ded9")
        # label.grid(row = 11, column = 0, padx = 10, pady = 10)
        tk.Label(self, font=('Helvetica', 16, 'bold'), text="Vehicle Speed Breakpoints", bd=7, justify=LEFT).grid(row=2,
                                                                                                                  column=0,
                                                                                                                  padx=10,
                                                                                                                  pady=4)
        tk.Label(self, font=('Helvetica', 16, 'bold'), text="Switch b/w AT & DT", bd=7).grid(row=6, column=0, padx=10,
                                                                                             pady=4, sticky=W)

        # button to show frame 2 with text
        # layout2
        button1 = tk.Button(self, text="MainPage", command=lambda: controller.show_frame(MainPage),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place
        # by using grid
        button1.grid(row=16, column=2, padx=10, pady=10)

        # button to show frame 2 with text
        # layout2
        button2 = tk.Button(self, text="Tune 0", command=lambda: controller.show_frame(Page1),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place by
        # using grid
        button2.grid(row=16, column=3, sticky=tk.W)
        # button to show frame 3 with text
        # layout3
        button3 = tk.Button(self, text="Tune 1", command=lambda: controller.show_frame(Page2),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place by
        # using grid
        button3.grid(row=16, column=3, sticky=tk.W, padx=100)

        # button to show frame 3 with text
        # layout2
        button5 = tk.Button(self, text="Tune 2", command=lambda: controller.show_frame(Page3),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place by
        # using grid
        button5.grid(row=17, column=3, sticky=tk.W)

        if key_present == 4:
            # button to show frame 3 with text
            # layout2
            button6 = tk.Button(self, text="Tune 4", command=lambda: controller.show_frame(Page5),
                                font=('Helvetica', 16, 'bold'), bg="#c0ded9")

            # putting the button in its place by
            # using grid
            button6.grid(row=17, column=3, sticky=tk.W, padx=100)

        VehSpd = tk.DoubleVar()
        # Uncheck the radio buttons when the program starts
        VehSpd.set(" ")
        VehSpd_Data = VehSpd.set(0)
        Output_At_Dt = tk.StringVar()
        Output_Dt_At = tk.StringVar()
        Switch_AT_DT = tk.IntVar()
        # Uncheck the radio buttons when the program starts
        Switch_AT_DT.set(" ")

        rad1 = Scale(self, orient=HORIZONTAL, resolution=1, length=550, width=15, variable=VehSpd, sliderlength=10,
                     from_=0, to=200, tickinterval=30, font=('Helvetica', 10, 'bold'), command=VehSpdData)
        rad1.grid(row=2, column=3, sticky=tk.W)
        # Vehicle speed alignment in tkinter window
        # for val, data in enumerate(VehSpd_range):
        #     rad1 = tk.Radiobutton(self, text=data, variable=VehSpd, command=VehSpdData, value=val, justify=CENTER)
        #     if val > 7:
        #         if val == 11:
        #             rad1.grid(row=4, column=val - 6, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=4, column=val - 6, sticky=tk.W, pady=10)
        #     elif val > 3:
        #         if val == 7:
        #             rad1.grid(row=3, column=val - 2, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=3, column=val - 2, sticky=tk.W)
        #     else:
        #         if val == 3:
        #             rad1.grid(row=2, column=val + 2, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=2, column=val + 2, sticky=tk.W)

        # tk.Button(self,text='Enter',command=assist_torque,font=('Helvetica', 13, 'bold'),width=10,bg= "#c0ded9").grid(row=8,column=2,pady=4)
        tk.Button(self, padx=18, bd=7, font=('Helvetica', 13, 'bold'), width=7, command=Reset, text="Reset",
                  bg="#F18F49").grid(row=18, column=2, pady=12)
        tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="AT → DT", variable=Switch_AT_DT,
                       command=switch_at_dt_calc, value=0).grid(row=6, column=2, sticky=tk.W)
        tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="DT → AT", variable=Switch_AT_DT,
                       command=switch_at_dt_calc, value=1).grid(row=6, column=3, sticky=tk.W)


# Sixth window frame page4
class Page5(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)

        Assist_Tq_Dmd_user = tk.StringVar()
        Driver_Tq_user = tk.StringVar()

        def Reset():
            VehSpd.set(" ")
            Assist_Tq_Dmd_user.set("")
            Driver_Tq_user.set("")
            Output_At_Dt.set("")
            Output_Dt_At.set("")
            Switch_AT_DT.set(" ")
            # =================================================================================================
            # Default selection & calculation of AT to DT
            # =================================================================================================
            tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(row=7,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=4,
                                                                                                               sticky=tk.W)
            tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(row=9,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=15,
                                                                                                               sticky=tk.W)
            tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_At_Dt, width=15,
                     state=DISABLED).grid(row=9, column=2, pady=12)
            Assist_Tq_Dmd_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7,
                                             textvariable=Assist_Tq_Dmd_user, width=15).grid(row=7, column=2)
            tk.Button(self, text='Convert', command=assist_torque, font=('Helvetica', 13, 'bold'), width=10,
                      bg="#c0ded9").grid(row=8, column=2, pady=4)
            # =================================================================================================
            # End of Default selection & calculation of AT to DT
            # =================================================================================================

            return

        # global VehSpd_Data
        def VehSpdData(speed):
            global VehSpd_Data
            self.VehSpd_Data = int(VehSpd.get())
            return self.VehSpd_Data

        # global assist_value
        def assist_torque():

            global assist_value
            assist_value = 0
            assist_value = Assist_Tq_Dmd_user.get()
            if str(assist_value) == "":
                error()
            else:
                output = np.interp(assist_value, torque_demand4[self.VehSpd_Data], input_torque)
                Output_At_Dt.set(output)
            return

        # global driver_value
        def driver_torque():

            global driver_value
            driver_value = 0
            driver_value = Driver_Tq_user.get()
            if str(driver_value) == "":
                error()
            else:
                output = np.interp(driver_value, input_torque, torque_demand4[self.VehSpd_Data])
                Output_Dt_At.set(output)
            return

        def switch_at_dt_calc():

            global switch_value
            switch_value = Switch_AT_DT.get()

            if switch_value == 0:
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=7, column=0, padx=10, pady=4, sticky=tk.W)
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=9, column=0, padx=10, pady=15, sticky=tk.W)
                tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_At_Dt, width=15,
                         state=DISABLED).grid(row=9, column=2, pady=12)
                Assist_Tq_Dmd_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7,
                                                 textvariable=Assist_Tq_Dmd_user, width=15).grid(row=7, column=2)
                tk.Button(self, text='Convert', command=assist_torque, font=('Helvetica', 13, 'bold'), width=10,
                          bg="#c0ded9").grid(row=8, column=2, pady=4)
                tk.Label(self, font=('Helvetica', 10, 'bold'),
                         text="*Note: Conversion from Assist Torque to Driver Torque", justify=CENTER, \
                         bd=7).grid(row=7, column=3, sticky=tk.W, columnspan=3)

            else:
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Assist Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=7, column=0, padx=10, pady=4, sticky=tk.W)
                tk.Label(self, font=('Helvetica', 16, 'bold'), text="Driver Torque (Nm)", bd=7, justify=LEFT).grid(
                    row=9, column=0, padx=10, pady=15, sticky=tk.W)
                tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Output_Dt_At, width=15,
                         state=DISABLED).grid(row=7, column=2, pady=12)
                Driver_Tq_userlvl = tk.Entry(self, font=('Helvetica', 13, 'bold'), bd=7, textvariable=Driver_Tq_user,
                                             width=15).grid(row=9, column=2)
                tk.Button(self, text='Convert', command=driver_torque, font=('Helvetica', 13, 'bold'), width=10,
                          bg="#c0ded9").grid(row=8, column=2, pady=4)
                tk.Label(self, font=('Helvetica', 10, 'bold'),
                         text="*Note: Conversion from Driver Torque to Assist Torque", justify=CENTER, \
                         bd=7).grid(row=7, column=3, sticky=tk.W, columnspan=3)

            return

        def error():
            screen1 = Toplevel(self)
            screen1.geometry("220x50")
            screen1.title("Warning!")
            Label(screen1, font=('Helvetica', 16, 'bold'), text="All fields required!", justify=CENTER, bd=7,
                  fg="red").grid(row=1, column=0, padx=10, sticky=W)
            return

        label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="Tune 4", bg="#c0ded9")
        label.grid(row=0, column=3, padx=10, pady=10,sticky=tk.W)

        # label = tk.Label(self, font=('Helvetica', 31, 'bold'), text="***********************", bg= "#c0ded9")
        # label.grid(row = 11, column = 0, padx = 10, pady = 10)
        tk.Label(self, font=('Helvetica', 16, 'bold'), text="Vehicle Speed Breakpoints", bd=7, justify=LEFT).grid(row=2,
                                                                                                                  column=0,
                                                                                                                  padx=10,
                                                                                                                  pady=4)
        tk.Label(self, font=('Helvetica', 16, 'bold'), text="Switch b/w AT & DT", bd=7).grid(row=6, column=0, padx=10,
                                                                                             pady=4, sticky=W)

        # button to show frame 2 with text
        # layout2
        button1 = tk.Button(self, text="MainPage", command=lambda: controller.show_frame(MainPage),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place
        # by using grid
        button1.grid(row=16, column=2, padx=10, pady=10)

        # button to show frame 2 with text
        # layout2
        button2 = tk.Button(self, text="Tune 0", command=lambda: controller.show_frame(Page1),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place by
        # using grid
        button2.grid(row=16, column=3, sticky=tk.W)
        # button to show frame 3 with text
        # layout3
        button3 = tk.Button(self, text="Tune 1", command=lambda: controller.show_frame(Page2),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place by
        # using grid
        button3.grid(row=16, column=3, sticky=tk.W, padx=100)

        # button to show frame 3 with text
        # layout2
        button5 = tk.Button(self, text="Tune 2", command=lambda: controller.show_frame(Page3),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place by
        # using grid
        button5.grid(row=17, column=3, sticky=tk.W)

        # button to show frame 3 with text
        # layout2
        button6 = tk.Button(self, text="Tune 3", command=lambda: controller.show_frame(Page4),
                            font=('Helvetica', 16, 'bold'), bg="#c0ded9")

        # putting the button in its place by
        # using grid
        button6.grid(row=17, column=3, sticky=tk.W, padx=100)

        VehSpd = tk.DoubleVar()
        # Uncheck the radio buttons when the program starts
        VehSpd.set(" ")
        VehSpd_Data = VehSpd.set(0)
        Output_At_Dt = tk.StringVar()
        Output_Dt_At = tk.StringVar()
        Switch_AT_DT = tk.IntVar()
        # Uncheck the radio buttons when the program starts
        Switch_AT_DT.set(" ")

        rad1 = Scale(self, orient=HORIZONTAL, resolution=1, length=550, width=15, variable=VehSpd, sliderlength=10,
                     from_=0, to=200, tickinterval=30, font=('Helvetica', 10, 'bold'), command=VehSpdData)
        rad1.grid(row=2, column=3, sticky=tk.W)
        # # Vehicle speed alignment in tkinter window
        # for val, data in enumerate(VehSpd_range):
        #     rad1 = tk.Radiobutton(self, text=data, variable=VehSpd, command=VehSpdData, value=val, justify=CENTER)
        #     if val > 7:
        #         if val == 11:
        #             rad1.grid(row=4, column=val - 6, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=4, column=val - 6, sticky=tk.W, pady=10)
        #     elif val > 3:
        #         if val == 7:
        #             rad1.grid(row=3, column=val - 2, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=3, column=val - 2, sticky=tk.W)
        #     else:
        #         if val == 3:
        #             rad1.grid(row=2, column=val + 2, sticky=tk.W, padx=50, pady=10)
        #         else:
        #             rad1.grid(row=2, column=val + 2, sticky=tk.W)

        # tk.Button(self,text='Enter',command=assist_torque,font=('Helvetica', 13, 'bold'),width=10,bg= "#c0ded9").grid(row=8,column=2,pady=4)
        tk.Button(self, padx=18, bd=7, font=('Helvetica', 13, 'bold'), width=7, command=Reset, text="Reset",
                  bg="#F18F49").grid(row=18, column=2, pady=12)
        tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="AT → DT", variable=Switch_AT_DT,
                       command=switch_at_dt_calc, value=0).grid(row=6, column=2, sticky=tk.W)
        tk.Radiobutton(self, font=('Helvetica', 10, 'bold'), text="DT → AT", variable=Switch_AT_DT,
                       command=switch_at_dt_calc, value=1).grid(row=6, column=3, sticky=tk.W)


app = BoostCurveCalc()
app.mainloop()
