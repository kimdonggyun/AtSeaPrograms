#!/usr/bin/env python

"""
SeaWater_update.py

Recalculate derived parameters (density, salinity, dissolved oxygen)

Visually adjust Temp/Sal => DO and sigmaT
"""
#System Stack
import datetime
import os
import argparse

#Science Stack
from netCDF4 import Dataset
import seawater as sw
import numpy as np

__author__   = 'Shaun Bell'
__email__    = 'shaun.bell@noaa.gov'
__created__  = datetime.datetime(2014, 9, 11)
__modified__ = datetime.datetime(2014, 9, 11)
__version__  = "0.1.0"
__status__   = "Development"
__keywords__ = 'CTD', 'SeaWater', 'Cruise', 'derivations'

"""--------------------------------netcdf Routines---------------------------------------"""

def get_global_atts(nchandle):

    g_atts = {}
    att_names = nchandle.ncattrs()
    
    for name in att_names:
        g_atts[name] = nchandle.getncattr(name)
        
    return g_atts

def get_vars(nchandle):
    return nchandle.variables

def get_var_atts(nchandle, var_name):
    return nchandle.variables[var_name]

def ncreadfile_dic(nchandle, params):
    data = {}
    for j, v in enumerate(params): 
        if v in nchandle.variables.keys(): #check for nc variable
                data[v] = nchandle.variables[v][:]

        else: #if parameter doesn't exist fill the array with zeros
            data[v] = None
    return (data)

def repl_var(nchandle, var_name, val=1e35):
    if len(val) == 1:
        nchandle.variables[var_name][:] = np.ones_like(nchandle.variables[var_name][:]) * val
    else:
        nchandle.variables[var_name][:] = val
    return
    
"""------------------------------------- Recalculations -----------------------------------------"""
def sigmaTheta(user_in, user_out):

    cruiseID = user_in.split('/')[-2]
    leg = cruiseID.lower().split('L')
    if len(leg) == 1:
        cruiseID = leg[0]
        leg = ''
    else:
        cruiseID = leg[0] + 'L' + leg[-1]

    #epic flavored nc files
    nc_path = user_out + cruiseID + '/'
    nc_path = [nc_path + fi for fi in os.listdir(nc_path) if fi.endswith('.nc') and not fi.endswith('_cf_ctd.nc')]

    for ncfile in nc_path:
        print ("Working on sigma-theta for {0}...").format(ncfile)
   
        nchandle = Dataset(ncfile,'a')
        
        global_atts = get_global_atts(nchandle)
        vars_dic = get_vars(nchandle)
        data = ncreadfile_dic(nchandle,vars_dic.keys())

        
        # calculate sigmaTheta at 0db gauge pressure (s, t, p=0)
        sigTh_pri = sw.eos80.dens0(data['S_41'][0,:,0,0],sw.ptmp(data['S_41'][0,:,0,0],data['T_28'][0,:,0,0],data['dep'][:]))-1000
        try:
            sigTh_sec = sw.eos80.dens0(data['S_42'][0,:,0,0],sw.ptmp(data['S_42'][0,:,0,0],data['T2_35'][0,:,0,0],data['dep'][:]))-1000
        except:
            print "No secondary temp and/or salinity in file"
            
        #replace nan with 1e35
        sigTh_pri[np.isnan(sigTh_pri)] = 1e35
        try:
            sigTh_sec[np.isnan(sigTh_sec)] = 1e35
        except:
            pass
            
        #update SigmaT
        repl_var(nchandle, 'STH_71', sigTh_pri)
        try:
            repl_var(nchandle, 'STH_2071', sigTh_sec)
        except:
            print "STH_2071 not in file"        
        nchandle.close()

    processing_complete = True
    return processing_complete 

def sigmaT(user_in, user_out):

    cruiseID = user_in.split('/')[-2]
    leg = cruiseID.lower().split('L')
    if len(leg) == 1:
        cruiseID = leg[0]
        leg = ''
    else:
        cruiseID = leg[0] + 'L' + leg[-1]

    #epic flavored nc files
    nc_path = user_out + cruiseID + '/'
    nc_path = [nc_path + fi for fi in os.listdir(nc_path) if fi.endswith('.nc') and not fi.endswith('_cf_ctd.nc')]

    for ncfile in nc_path:
        print ("Working on density for {0}...").format(ncfile)
   
        nchandle = Dataset(ncfile,'a')
        
        global_atts = get_global_atts(nchandle)
        vars_dic = get_vars(nchandle)
        data = ncreadfile_dic(nchandle,vars_dic.keys())

        
        # calculate sigmaT at 0db gauge pressure (s, t, p=0)
        sigT_pri = sw.eos80.dens0(data['S_41'][0,:,0,0],data['T_28'][0,:,0,0])-1000
        try:
            sigT_sec = sw.eos80.dens0(data['S_42'][0,:,0,0],data['T2_35'][0,:,0,0])-1000
        except:
            print "No secondary temp and/or salinity in file"
            
        #replace nan with 1e35
        sigT_pri[np.isnan(sigT_pri)] = 1e35
        try:
            sigT_sec[np.isnan(sigT_sec)] = 1e35
        except:
            pass
            
        #update SigmaT
        repl_var(nchandle, 'ST_70', sigT_pri)
        try:
            repl_var(nchandle, 'ST_2070', sigT_sec)
        except:
            print "ST_2070 not in file"        
        nchandle.close()

    processing_complete = True
    return processing_complete


def O2PercentSat(user_in, user_out):

    cruiseID = user_in.split('/')[-2]
    leg = cruiseID.lower().split('L')
    if len(leg) == 1:
        cruiseID = leg[0]
        leg = ''
    else:
        cruiseID = leg[0] + 'L' + leg[-1]

    #epic flavored nc files
    nc_path = user_out + cruiseID + '/'
    nc_path = [nc_path + fi for fi in os.listdir(nc_path) if fi.endswith('.nc') and not fi.endswith('_cf_ctd.nc')]
    
    for ncfile in nc_path:
        print ("Working on oxygen for {0}...").format(ncfile)
        nchandle = Dataset(ncfile,'a')
        
        vars_dic = get_vars(nchandle)
        data = ncreadfile_dic(nchandle,vars_dic.keys())
    
        
        # calculate oxygen saturation
        # Garcia and Gorden 1992 - from Seabird Derived Parameter Formulas
        GG_A0 = 2.00907
        GG_A1 = 3.22014
        GG_A2 = 4.0501
        GG_A3 = 4.94457
        GG_A4 = -0.256847
        GG_A5 = 3.88767
        GG_B0 = -0.00624523
        GG_B1 = -0.00737614
        GG_B2 = -0.010341
        GG_B3 = -0.00817083
        GG_C0 = -0.000000488682
        Ts_pri = np.log((298.15 - data['T_28'][0,:,0,0]) / (273.15 + data['T_28'][0,:,0,0]))
        Oxsol_pri = np.exp(GG_A0 + GG_A1 * Ts_pri + GG_A2 * (Ts_pri) ** 2 + \
                    GG_A3 * (Ts_pri) ** 3 + GG_A4 * (Ts_pri) ** 4 + \
                    GG_A5 * (Ts_pri) ** 5 + data['S_41'][0,:,0,0] * (GG_B0 + GG_B1 * Ts_pri +\
                    GG_B2 * (Ts_pri) ** 2 + GG_B3 * (Ts_pri) ** 3) + GG_C0 * (data['S_41'][0,:,0,0]) ** 2)
        try:
            Ts_sec = np.log((298.15 - data['T2_35'][0,:,0,0]) / (273.15 + data['T2_35'][0,:,0,0]))
            Oxsol_sec = np.exp(GG_A0 + GG_A1 * Ts_sec + GG_A2 * (Ts_sec) ** 2 + \
                        GG_A3 * (Ts_sec) ** 3 + GG_A4 * (Ts_sec) ** 4 + \
                        GG_A5 * (Ts_sec) ** 5 + data['S_42'][0,:,0,0] * (GG_B0 + GG_B1 * Ts_sec +\
                        GG_B2 * (Ts_sec) ** 2 + GG_B3 * (Ts_sec) ** 3) + GG_C0 * (data['S_42'][0,:,0,0]) ** 2)
        except:
            pass        
        #determine sigmatheta and convert Oxygen from micromoles/kg to ml/l
        #calculate new oxygen saturation percent using derived oxsol
        sigmatheta_pri = sw.eos80.pden(data['S_41'][0,:,0,0], data['T_28'][0,:,0,0], data['dep'][:])
        OxPerSat_pri = ( (data['O_65'][0,:,0,0] * sigmatheta_pri / 44660) / Oxsol_pri ) * 100.
        try:
            sigmatheta_sec = sw.eos80.pden(data['S_42'][0,:,0,0], data['T2_35'][0,:,0,0], data['dep'][:])
            OxPerSat_sec = ( (data['CTDOXY_4221'][0,:,0,0] * sigmatheta_sec / 44660) / Oxsol_sec ) * 100.
        except:
            print "No secondary sensor"
             
        #replace nan/1e35 with 1e35, >1e10
        OxPerSat_pri[np.isnan(OxPerSat_pri)] = 1e35
        OxPerSat_pri[data['O_65'][0,:,0,0] == 1e35] = 1e35
        OxPerSat_pri[data['O_65'][0,:,0,0] >= 1e10] = 1e35
        try:
            OxPerSat_sec[np.isnan(OxPerSat_sec)] = 1e35
            OxPerSat_sec[data['CTDOXY_4221'][0,:,0,0] == 1e35] = 1e35
            OxPerSat_sec[data['CTDOXY_4221'][0,:,0,0] >= 1e10] = 1e35
        except:
            print "No secondary sensor"
            
        #update Oxygen
        repl_var(nchandle, 'OST_62', OxPerSat_pri)
        try:
            repl_var(nchandle, 'CTDOST_4220', OxPerSat_sec)
        except:
            print "CTDOST_4220 not in file"
        nchandle.close()
    
    processing_complete = True
    return processing_complete, data

"""------------------------------------- Main -----------------------------------------"""


parser = argparse.ArgumentParser(description='seawater recalculation of sigmat or oxygen')
parser.add_argument('inputpath', metavar='inputpath', type=str, help='path to .nc file')
parser.add_argument('-st','--sigmat', action="store_true", help='recalculate sigmat')
parser.add_argument('-oxy','--oxygen', action="store_true", help='recalculate oxygen conc')
parser.add_argument('-stheta','--sigmatheta', action="store_true", help='calculate sigmatheta')

args = parser.parse_args()

#read in netcdf data file
user_in = args.inputpath
user_out = "/".join(user_in.split('/')[:-2]) + '/'

if args.sigmat:
    sigmaT(user_in, user_out)

if args.oxygen:
    O2PercentSat(user_in, user_out)

if args.sigmatheta:
    sigmaTheta(user_in, user_out)
        