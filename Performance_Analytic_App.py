# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 16:00:40 2019

@author: hydra li
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from Risk_Analytics_App import Risk_Advisor

#Performance Advisor inherits from the Risk Advisor as they share most commonly used datas and Performance assessments built on top of that
class Performance_Advisor(Risk_Advisor):  
    def __init__(self, Graphic, **kwarg):
        super().__init__(**kwarg)
        self._Graphic = False
        self._PGraphic = Graphic        
        self._Factor_Loadings = None
    
    def Basic_chart(self):
        fig100, ax100 = plt.subplots()
        ax100.set_title('Portfolio  vs  Bench')
        ax100.set_xlabel('time')
        ax100.plot(self.Equity, color = 'orange')
        ax100.set_ylabel('Portfolio', color = 'orange')
        ax99 = ax100.twinx()
        PLT_B = self._Bench_Mark[self.Equity.index]
        ax99.plot(PLT_B, color = 'blue')
        ax99.set_ylabel('Benchmark_Level', color = 'blue')        
        
        
    def Exposure_vs_Benchmark(self, style = 'line'):
         Expo = self.gross_exp()       
         N_Expo = self.net_exp()
         PLT_B = self._Bench_Mark[Expo.index]
         if style == 'line':
             use = '-'
         elif style == 'dot':
             use = 'o'
         fig101, ax101 = plt.subplots()
         ax101.set_title('Exposure  vs  Benchmark')
         ax101.set_xlabel ('time')
         ax101.plot(Expo.index, Expo, use, color = 'orange', markersize = 2, label = 'Gross')
         ax101.plot(N_Expo.index, N_Expo, use, color = 'green',markersize = 2, label = 'Net')
         ax101.legend(loc = 'upper left')
         ax101.set_ylabel('Exposure', color = 'orange')
         ax102 = ax101.twinx()
         ax102.plot(Expo.index, PLT_B, '--', color = 'blue')
         ax102.set_ylabel('Benchmark_Level', color = 'blue')        
     
        
    def  Fully_Invest_Performance(self, Check = 'Gross', show_current = False):
         if Check == 'Gross':
             Expo = self.gross_exp()
         elif Check == 'Net':
             Expo = self.net_exp()
        
         Port_ret = self.Equity.pct_change().fillna(0)
         Starting_Equity = self.Equity[0]
         Fully_Lever = Port_ret/Expo * 100
         Fully_Lever.replace([np.inf, -np.inf, np.nan], 0, inplace = True)
         Fully_Lever = Fully_Lever + 1
         Port = Starting_Equity * Fully_Lever.cumprod()
         PLT_B = self._Bench_Mark[Expo.index]

         fig103, ax103 = plt.subplots()
         ax103.set_title('Our Mix fully levered  vs  Benchmark')
         ax103.set_xlabel ('time')
         ax104 = ax103.twinx()
         ax103.plot(Port.index, Port, '--', color = 'orange')
         ax103.set_ylabel('Our Pick', color = 'orange')
         ax104.plot(Port.index, PLT_B, '--', color = 'blue')
         ax104.set_ylabel('Benchmark', color = 'blue')
         if show_current:
             ax103.plot(Port.index, self.Equity, '--', color = 'green')
        

    def _Calculate_Factor_Loadings(self, use_bars = 80, rolling = 10):
        if self._Factors is None:
            print('Please provide factors in order to calculate factor loadings :(')
        Factor_ret = self._Factors.pct_change().fillna(0)
        time1 = Factor_ret.index.sort_values()
        time2 = self.portfolio.index.sort_values()
        time3 = self.ret.index.sort_values()
        Common_Time = list(set(time1).intersection(time3))
        if (len(Common_Time) < len(time3) * 0.8) and (len(Common_Time) < len(time1) * 0.5):
            print('Please double check your factor is same frequency as your trading signal!! ')
            return None
        Factor_ret = Factor_ret.loc[pd.Index(Common_Time)]
        ret = self.ret.loc[pd.Index(Common_Time)].drop('Cash', axis = 1)
        time1 = Factor_ret.index.sort_values()
        #compare if we have enough bars to do first regression when portfolio info started, if not we wait untill we have enough bars to do first regression
        N = min(self.portfolio.shape[0]//rolling + 1, (Factor_ret.shape[0] - use_bars)//rolling)
        T_end = use_bars if N< (self.portfolio.shape[0]//rolling + 1) else list(time1).index(time2[0])
        _Beta_idx = []
        _Beta_record = None

        for i in range(N):
            idx = time1[(T_end-use_bars):T_end]
            temp = list(time2).index(idx[-1])
            idx1 = time2[temp:(temp + rolling)]
            _Beta_idx.extend(list(idx1))
            Y = ret.loc[idx].values
            X = Factor_ret.loc[idx].values
            weight = self.weights.drop('Cash', axis=1).loc[idx1].values
            _Paritial_Betas = np.matmul(np.matmul(np.linalg.inv(np.matmul(X.transpose(), X)),X.transpose()),Y)
            _Total_Beta = np.matmul(_Paritial_Betas, weight.transpose()).transpose()
            if _Beta_record is None:
                _Beta_record = np.array(_Total_Beta)
            else:
                _Beta_record = np.concatenate((_Beta_record, _Total_Beta))
            T_end+=rolling
            
        self._Factor_ret = Factor_ret
        self._Factor_Loadings = pd.DataFrame(_Beta_record, columns = self._Factors.columns, index = _Beta_idx)
        self._Factor_Loadings.reindex(self.portfolio.index, method = 'ffill')
        self._Factor_Loadings.fillna(0)
        
        
    def Return_Attribution(self):
        if self._Factor_Loadings is None:
            self._Calculate_Factor_Loadings()
        
        Port_ret = self.Equity.pct_change()
        Factor_RET = self._Factor_Loadings * self._Factor_ret    
        Factor_RET['Alpha'] = Port_ret - Factor_RET.sum(axis = 1)
        Factor_RET['Portfolio'] = Port_ret
        Factor_RET = Factor_RET.dropna()
        summary = pd.DataFrame(Factor_RET.sum(axis = 0)).transpose()*100
        summary.index = ['Total_Return']
        
        if self._PGraphic:
            Factor_RET.plot(title = 'Factor returns')
            print('Summary of Performance Attributed to each factor is: ')
            return summary
        else:
            return Factor_RET
 
    
    def Show_Loading(self):
        if self._Factor_Loadings is None:
            self._Calculate_Factor_Loadings()

        if self._PGraphic:
            self._Factor_Loadings.plot(title = 'Betas over time')
        else:
            return self._Factor_Loadings
        
        
        
        
        
        
        
        
        
        
    
        
        