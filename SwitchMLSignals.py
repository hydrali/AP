# -*- coding: utf-8 -*-
"""
Created on Thu May 23 18:22:50 2019

@author: Charlie
"""

import random as rnd
import numpy as np

def AllocateSignals(InpList, ClassOrReg = 0):
    
    OutputList = [0] * len(InpList) 
    
    ### PROCESS REGRESSION INPUT LISTS ###
    if ClassOrReg != 0 :   # 0 = Regression Input
        for i in range(len(InpList)):
            if InpList[i] > ClassOrReg:
                OutputList[i] = 1
            elif InpList[i] < -ClassOrReg:
                OutputList[i] = -1

    
    ### PROCESS CLASSIFICATION INPUT LISTS ###
    elif ClassOrReg == 0: # 1 = Classification Input        
        
        InpList = np.array(InpList)
        All_Poss_Classifiers = np.unique(InpList)
        High_Am = All_Poss_Classifiers[-1:]
        Low__Am = All_Poss_Classifiers[:1]
        High_Am2 = All_Poss_Classifiers[-2:-1]
        Low__Am2 = All_Poss_Classifiers[1:2]
        High_n_idx = np.where(InpList == High_Am)[0]
        Low__n_idx = np.where(InpList == Low__Am)[0]
        High_n_idx2 = np.where(InpList == High_Am2)[0]
        Low__n_idx2 = np.where(InpList == Low__Am2)[0]
        for i in range(len(High_n_idx)):
            OutputList[High_n_idx[i]] = 1
        for i in range(len(Low__n_idx)):
            OutputList[Low__n_idx[i]] = -1
        for i in range(len(High_n_idx)):
            OutputList[High_n_idx2[i]] = 1
        for i in range(len(Low__n_idx)):
            OutputList[Low__n_idx2[i]] = -1           
    return OutputList