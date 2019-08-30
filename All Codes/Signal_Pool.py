# -*- coding: utf-8 -*-
"""
Created on Tue Aug  6 23:21:45 2019

@author: hydra li
"""

import pandas as pd
import numpy as np
import copy
from sklearn.linear_model import Lasso, ElasticNet
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor


class Generate_Signal():
    def __init__(self, Price_Data, Factor_Pool = None):
        self.Price = Price_Data
        self.Factor_Pool = Factor_Pool
        self.Signal_Pool = pd.DataFrame(index = self.Price.index)
        
        
    def MACD(self, Short = 12, Long = 26, Signal_period = 9):
        temp = pd.DataFrame(index = self.Price.index)
        temp['MACD'] = self.Price['close'].rolling(Short).mean() - self.Price['close'].rolling(Long).mean()
        temp['Signal_line'] = temp['MACD'].rolling(Signal_period).mean()
        temp = temp.fillna(0)

        temp['diff'] = np.sign(temp['Signal_line'] - temp['MACD'])
        temp['Crossing'] = (temp['diff'] * temp['diff'].shift(1) == -1) * temp['diff'].shift(1)
        temp['Signal'] = 0
        temp.loc[(temp['MACD'] > 0) & (temp['Crossing'] == -1), 'Signal'] = -1
        temp.loc[(temp['MACD'] < 0) & (temp['Crossing'] == 1), 'Signal'] = 1
        
        self.Signal_Pool['MACD'] = temp['Signal']
        
        
    def Bollinger_Band(self, MA_period = 20, Band_Width = 2):
        temp = pd.DataFrame(index = self.Price.index)
        temp['close'] = self.Price['close']
        temp['Boll_Mid'] = self.Price['close'].rolling(MA_period).mean()
        temp['Boll_Upper'] = temp['Boll_Mid'] + Band_Width * self.Price['close'].rolling(MA_period).std()        
        temp['Boll_Lower'] = temp['Boll_Mid'] - Band_Width * self.Price['close'].rolling(MA_period).std()
        temp = temp.fillna(0)

        temp['Cross_Upper'] = np.sign(self.Price['close'] - temp['Boll_Upper'])        
        temp['Cross_Lower'] = np.sign(self.Price['close'] - temp['Boll_Lower'])

        temp['Signal'] = 0
        temp['Signal'].loc[(temp['Cross_Upper'].shift(1) * temp['Cross_Upper'] == -1) & (temp['Cross_Upper'].shift(1) > 0)] = -1
        temp['Signal'].loc[(temp['Cross_Lower'].shift(1) * temp['Cross_Lower'] == -1) & (temp['Cross_Lower'].shift(1) < 0)] = 1
        
        self.Signal_Pool['Boll_Band'] = temp['Signal']
  
    
    def RSI(self, MA_period = 14, low = 30, high = 70):
        temp = pd.DataFrame(index = self.Price.index)
        temp['ret'] = self.Price['close'].pct_change()*100
        temp = temp.fillna(0)
        temp['Total_Gain'] = temp['ret'] * (temp['ret'] > 0)
        temp['Total_Loss'] = temp['ret'] * (temp['ret'] < 0)
        gain = copy.deepcopy(temp['Total_Gain'].values)
        loss = copy.deepcopy(temp['Total_Loss'].values)
        gain[MA_period + 1] = gain[1:(MA_period+1)].sum()/MA_period
        loss[MA_period + 1] = loss[1:(MA_period+1)].sum()/MA_period    
        for i in range(MA_period + 2, temp.shape[0]):
            gain[i] = (gain[i-1]*(MA_period - 1) + gain[i])/MA_period             
            loss[i] = (loss[i-1]*(MA_period - 1) + loss[i])/MA_period 
        
        temp['RSI'] = 100 - 100/(1 - gain/loss)
        temp['RSI'][:MA_period] = 50
        temp['Signal'] = 0
        temp.loc[temp['RSI'] >= high, 'Signal'] = -1
        temp.loc[temp['RSI'] <= low, 'Signal'] = 1
        
        self.Signal_Pool['RSI'] = temp['Signal']


    def EMA(self, fast = 10, slow = 30):
        temp = pd.DataFrame(index = self.Price.index)
        temp['price'] = self.Price['close']
        temp['Fast'] = temp['price'].ewm(ignore_na = True, com = fast, min_periods = fast, adjust = True).mean()        
        temp['Slow'] = temp['price'].ewm(ignore_na = True, com = slow, min_periods = slow, adjust = True).mean()  
        temp = temp.fillna(0)
        temp['FMS'] = np.sign(temp['Fast'] - temp['Slow'])
        temp['Signal'] = 0
        temp['Signal'].loc[temp['FMS'] * temp['FMS'].shift(1) == -1]= 1
        
        self.Signal_Pool['EMA'] = temp['Signal']*temp['FMS'].shift(1)
        
    
    def Accum_Dist(self, Period = 14, threshold = 2.5):
        temp = copy.deepcopy(self.Price)
        for index, row in temp.iterrows():
            if row['high'] != row['low']:
                ac = (row['close']*2 - row['high'] - row['low'])/(row['high'] - row['low'])*row['volume']
            else:
                ac = 0
            temp.set_value(index, 'acc_dist', ac)
        temp = temp.fillna(0)
        temp['acc_dist_ema'] = temp['acc_dist'].ewm(ignore_na = True, com = Period, min_periods = Period, adjust = True).mean()
        temp['change'] = temp['acc_dist_ema'] - temp['acc_dist_ema'].shift(1)
        temp['Benchmark'] = temp['acc_dist_ema'].rolling(Period).std()
        temp['Signal'] = 0
        temp['Signal'].loc[temp['change']/temp['Benchmark'] > threshold] = 1
        temp['Signal'].loc[temp['change']/temp['Benchmark'] < -threshold] = -1                

        self.Signal_Pool['Acc_Dis'] = temp['Signal']
        
    def Machine_Learning_Models(self, Buffer = None, refit = 50, use_length = 200, Look_Forward = 3, feature_period = 5):
        if Buffer is None:
            Buffer = self.Factor_Pool
        temp = self.Price['close'].pct_change(Look_Forward).shift(-Look_Forward)
        temp = temp.rename('Y')
        if temp.shape[0] < use_length:
            print('Not Enough Data in the Buffer Yet')
        else:
            N = (temp.shape[0] - use_length)//refit
        self.Signal_Pool['LASSO'] = 0
        self.Signal_Pool['Elastic_Net'] = 0
        self.Signal_Pool['Neural_Net'] = 0
        self.Signal_Pool['Support_Vector'] = 0
        self.Signal_Pool['Random_Forest'] = 0
        self._LASSO_Features = []
        self._EN_Features = []
        for i in range(N):
            Train_start = refit * i
            Train_end = refit * i + use_length + feature_period - Look_Forward # Skip a few days data where it's not trainable to avoid data leakage problem
            P_start = refit * i + use_length + feature_period
            P_end = min(refit * (i+1) + use_length + feature_period, temp.shape[0] -1)
#            print('(', i, temp.index[P_start], temp.index[P_end], ')')
            Train_and_Pred = temp.iloc[Train_start:P_end]
            Features_pool = self._Get_ML_Features(Train_and_Pred.index, Buffer, feature_period)
            
            #Training period
            Training_Feature = Features_pool.loc[temp.index[Train_start: Train_end]].dropna()
            Train_Mean = Training_Feature.mean()
            Train_Std = Training_Feature.std()
            Training_Feature = (Training_Feature - Train_Mean)/Train_Std
            Training_Y = temp.loc[temp.index[Train_start: P_start]] * 100
            Merged = pd.merge(Training_Y, Training_Feature, left_index = True, right_index = True, how = 'inner')
            #LASSO
            self._LASSO_Model = Lasso(alpha= 0.01)
            self._LASSO_Model.fit(Merged.drop('Y', axis = 1), Merged['Y'])
            self._LASSO_Features.append(Training_Feature.columns.get_level_values(1)[self._LASSO_Model.coef_ != 0])
            #EN
            self._Elastic_Net = ElasticNet(alpha = 0.001, l1_ratio= 0.5, normalize= True)
            self._Elastic_Net.fit(Merged.drop('Y', axis = 1), Merged['Y'])            
            self._EN_Features.append(Training_Feature.columns.get_level_values(1)[self._Elastic_Net.coef_ != 0])
            #NN
            self._Neural_Net = MLPRegressor(hidden_layer_sizes=(32,16,8), activation= 'tanh', alpha= 0.001)
            self._Neural_Net.fit(Merged.drop('Y', axis = 1), Merged['Y'])
            #SVM
            self._SVR = SVR()
            self._SVR.fit(Merged.drop('Y', axis = 1), Merged['Y'])
            #RF
            self._Random_Forest = RandomForestRegressor(n_estimators= 30, max_depth= 6)
            self._Random_Forest.fit(Merged.drop('Y', axis = 1), Merged['Y'])
            
            #Use Model to trade in the following period
            Prediction = Features_pool.loc[temp.index[P_start: P_end]]
            Prediction = (Prediction - Train_Mean)/Train_Std
            #LASSO
            Y_hat = self._LASSO_Model.predict(Prediction)
            self.Signal_Pool['LASSO'].loc[Prediction.index] = Y_hat
            #Elastic Net
            Y_hat = self._Elastic_Net.predict(Prediction)
            self.Signal_Pool['Elastic_Net'].loc[Prediction.index] = Y_hat
            #Neural Net
            Y_hat = self._Neural_Net.predict(Prediction)
            self.Signal_Pool['Neural_Net'].loc[Prediction.index] = Y_hat
            #SVM
            Y_hat = self._SVR.predict(Prediction)
            self.Signal_Pool['Support_Vector'].loc[Prediction.index] = Y_hat
            #RF            
            Y_hat = self._Random_Forest.predict(Prediction)
            self.Signal_Pool['Random_Forest'].loc[Prediction.index] = Y_hat
        
    
    def Generate_All_Signals(self, Buffer, Refit_freq):
        self.MACD()
        self.Bollinger_Band()
        self.RSI()
        self.EMA()
        self.Accum_Dist()
        self.Machine_Learning_Models(Buffer, refit = Refit_freq)
        return self.Signal_Pool
    
    
    
    def _Get_ML_Features(self, period, Buffer, feature_time):
        use = ['close', 'volume', 'Asset']
        Pool = Buffer.loc[period, use]
        Pool = Pool.set_index([Pool.index, 'Asset'])
        Pool = Pool.unstack('Asset')
        NA_Count = Pool.isnull().sum()
        Columns = [name for name in NA_Count.index if NA_Count[name] <= 10]     # Only use the factors wgere we have fewer than 10 missig data
        Pool = Pool[Columns].fillna(method = 'ffill')                           # Clean the data and prepare for other feature generatings
        Pool = Pool.stack(level = 1)                                            # Stack Backup to generate features
        Pool['return'] = Pool['close'].sort_index().groupby(level = 1).pct_change() #Get Return
        Pool['cum_ret'] = Pool['return'].rolling(feature_time).sum()                #Get Cumulative Return
        Pool = Pool.unstack('Asset')                                                #Form the features into table 
        Pool = Pool.dropna(axis = 1)
        return Pool
    
    
    
    