# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 00:15:06 2019

@author: User
"""
import numpy as np
import pandas as pd
import copy
import matplotlib.pyplot as plt

from Database_Interactions import DB_Operator
from Risk_Analytics_App import Risk_Advisor
from Performance_Analytic_App import Performance_Advisor

class Backtestor():
    def __init__(self, Asset, Frequency = 'Daily', Signal_use ='All', start = None, end = None, Starting_Equity = 100000, threshold = 1):
        Price_Worker = DB_Operator('MT4_Database')
        Signal_Worker = DB_Operator('Signal_DB')
        Temp = Price_Worker.Select_rows(tablename= Frequency, find= Asset, by = 'Asset')
        Temp = Temp.set_index([pd.to_datetime(Temp['open_time']), Temp['Asset']])
        self.Prices = pd.DataFrame(Temp['close'].unstack(level = 1)).sort_index()
        self.Prices['Cash'] = 1
        self.Prices = self.Prices.fillna(method = 'ffill')
        self.time = list(self.Prices.index)
        
        #Volume is only used for the internal Risk Manager
        self._Volume = pd.DataFrame(Temp['volume'].unstack(level = 1)).sort_index().dropna()
        self._Volume['Cash'] = 0
        self._frequency = Frequency
        
        if start != None:
            temp = np.array(self.time)
            if end == None:
                new_time = temp[np.where(temp > pd.to_datetime(start))]
            else: 
                new_time = temp[np.where((temp > pd.to_datetime(start)) & (temp < pd.to_datetime(end)))]
            self.time = list(new_time)
        
        if start == None and end != None:
            temp = np.array(self.time)
            self.time = list(temp[np.where(temp < pd.to_datetime(end))])
            
        All_Signals = Signal_Worker.Select_rows(tablename= Frequency, find= Asset).fillna(0)       
        if Signal_use == 'All':
            self.Signal = All_Signals
        else:
            Signal_use.extend(['open_time', 'Asset'])
            self.Signal = All_Signals[Signal_use]
        self.Signal = self.Signal.set_index([pd.to_datetime(self.Signal['open_time']), self.Signal['Asset']])
        self.Signal = self.Signal.drop(['open_time', 'Asset'], axis = 1)
        
        ML_Signals = ['LASSO', 'Elastic_Net', 'Neural_Net', 'Support_Vector', 'Random_Forest']
        for sig in Signal_use:
            if sig in ML_Signals:
                self.Signal[sig] = np.sign(self.Signal[sig])*(self.Signal[sig].abs() > threshold)
        
        Asset.append('Cash')
        self.Asset = Asset
        self.Holdings = [[0] * len(Asset)]
        self.Holdings[0][-1] = Starting_Equity
        self._Holding_Mapper = {}
        self._Margin_Rate = {}
        for loc, items in enumerate(Asset):
            self._Holding_Mapper[items] = loc
            self._Margin_Rate[items] = 0.2            
            
        self.Prices = self.Prices[self.Asset]
        self._Margin_Rate['Cash'] = 0
        self._Primary_Signal = None
        self._Signal_Agree = 2
        self._Weight_Method = 'Equal_Weight'
        self.Wealth = Starting_Equity
        self._Risk_Cap = None

        self._ret = self.Prices.dropna().pct_change().dropna()
        self._Period_Price = self.Prices.loc[pd.Index(self.time)]
        self.Equity = [Starting_Equity]
        self.Margin = [Starting_Equity]
    
    def run(self, **kwarg):
        if self.Signal.shape[1] != 1:
            Combined_Signal = self._Signal_Combine().sort_index()
        else:
            Combined_Signal = self.Signal.sort_index()
            Combined_Signal.columns = ['Combined_Signal']
                                
        Combined_Signal = Combined_Signal.unstack(level = 1)['Combined_Signal']
        Combined_Signal = Combined_Signal[self.Asset[:-1]].fillna(0)
        self._Period_Signal = Combined_Signal.loc[pd.Index(self.time)]
        self._margin_vals = np.array(list(self._Margin_Rate.values()))
        
        for count, day in enumerate(self.time[1:]):
            daily_signal = Combined_Signal.loc[day]
            self._day_price = self.Prices.loc[day]
            old = self.Holdings[-1]
            if abs(daily_signal.values).sum() == 0:
                new = old
                self.Holdings.append(new)
            else:
                new = self._Calculate_Weight(daily_signal, day, count, old)
                self.Holdings.append(new)
                
            Value =np.matmul(np.array(new), np.nan_to_num(self._day_price.values))
            self.Equity.append(Value)
            Margin = np.matmul(np.array(new)*self._margin_vals, np.nan_to_num(self._day_price.values))
            self.Margin.append(Value - Margin)
            
        self.Holdings = pd.DataFrame(self.Holdings, index = self.time, columns = self.Asset)
        Port_Summary = np.hstack((np.array(self.Equity).reshape(-1,1), np.array(self.Margin).reshape(-1,1)))
        self.Port_Summary = pd.DataFrame(Port_Summary, index = self.time, columns = ['Equity','Margin'])        
        
        self._Port_Val = self._Period_Price.fillna(0) * self.Holdings
        self.Internal_Audit = Risk_Advisor(Portfolio = self._Port_Val, _Price = self.Prices, _Volume = self._Volume, frequency= self._frequency, **kwarg)
        self.Internal_Appraiser = Performance_Advisor(Portfolio = self._Port_Val, _Price = self.Prices, frequency= self._frequency, **kwarg)
        

    def _Signal_Combine(self):
        Signal = copy.deepcopy(self.Signal)
        if self._Primary_Signal != None:
            Signal['Combined_Signal'] = Signal[self._Primary_Signal]
            Signal['Others_Combined'] = Signal.drop(['Combined_Signal', self._Primary_Signal], axis = 1).sum(axis = 1)
        else:
            Signal['Combined_Signal'] = 0
            Signal['Others_Combined'] = Signal.sum(axis = 1)
        
        Signal['Others_Combined'] = (Signal['Others_Combined'].abs() >= self._Signal_Agree).astype(int) * np.sign(Signal['Others_Combined'])
        Signal['Combined_Signal'] = Signal['Combined_Signal'] + Signal['Others_Combined']
        
        return pd.DataFrame(Signal['Combined_Signal'])
        
    
    def _Calculate_Weight(self, Trade_Info, Time, count, Origninal_Holding): 
        New = copy.deepcopy(Origninal_Holding)
        Trades =Trade_Info.to_dict()       

        for items in Trades:
            if Trades[items] == 0:
                continue
            if Trades[items] == 1:
                if Origninal_Holding[self._Holding_Mapper[items]] < 0:
                    units = Origninal_Holding[self._Holding_Mapper[items]]
                    New[self._Holding_Mapper[items]] = 0                  
                else:
                    if self._Weight_Method == 'Equal_Weight':
                        v = self.Wealth/(len(self.Asset)*2)
                        price = self._day_price[items]
                        units = int(v/price)
                        New[self._Holding_Mapper[items]] += units
            if Trades[items] == -1:
                if Origninal_Holding[self._Holding_Mapper[items]] > 0:
                    units = Origninal_Holding[self._Holding_Mapper[items]]
                    New[self._Holding_Mapper[items]] = 0               
                else:    
                    if self._Weight_Method == 'Equal_Weight':
                        v = self.Wealth/(len(self.Asset)*2)                        
                        price = self._day_price[items]              
                        units = int(v/price)*(-1)
                        New[self._Holding_Mapper[items]] += units 
                   
        New = self._Exposure_Control(New, Time, count)
        Delta = [New[o] - Origninal_Holding[o] for o in range(len(New)-1)]
        Delta.append(0)
        cost = np.matmul(np.array(Delta), np.nan_to_num(self._day_price.values))
        New[-1] = Origninal_Holding[-1] - cost
        return New
            
    
    def _Exposure_Control(self, holding, Time, count, period = 25):
        if self._Risk_Cap == None:
            Out = holding
            
        elif self._Risk_Cap:
            Out = holding
            Holding = pd.Series(holding, index = self.Asset)
            Value = Holding * self._day_price
            Equity = self.Equity[count]
            V_dict = Value.to_dict()
            start = max(count - period, 0)
            std = self._ret.iloc[start:count, :-1].std().to_dict()   #Edit this line if we want to consider not daily but weekly or monthly volatilities
            
            for items in self.Asset[:-1]:
                if self._Indiv_Value_Cap != None:
                    if abs(V_dict[items])/Equity > self._Indiv_Value_Cap/100:
                        Out[self._Holding_Mapper[items]] = int(Out[self._Holding_Mapper[items]]*(self._Indiv_Value_Cap * Equity)/V_dict[items]/100)*np.sign(V_dict[items])
  
                if self._Indiv_Vol_Cap != None:
                    if V_dict[items] * std[items]/Equity * 100 > self._Indiv_Vol_Cap:
                        Out[self._Holding_Mapper[items]] = int(Out[self._Holding_Mapper[items]]* self._Indiv_Vol_Cap * Equity/(std[items] * V_dict[items] * 100)*np.sign(V_dict[items]))
                        
            Value = pd.Series(Out, index= self.Asset) * self._day_price
            if self._Port_Value_Cap != None:
                investment = Value[self.Asset[:-1]].abs().sum()
                if investment > self._Port_Value_Cap * Equity/100:
                    multiple = investment*100/(self._Port_Value_Cap * Equity)
                    Out = [int(YYY/multiple) for YYY in Out]
                
            Value = pd.Series(Out, index= self.Asset) * self._day_price
            if self._Port_Vol_Cap != None: 
                vcv = self._ret.iloc[start:count, :].cov().values
                Vol = np.matmul(np.matmul(Value.values, vcv), Value.values.transpose()) ** 0.5
                if Vol > self._Port_Vol_Cap * Equity/100:
                    multiple = Vol * 100 /Equity /self._Port_Vol_Cap
                    Out =[int(XXX/multiple) for XXX in Out]
        return Out
        
        
#---------- User Methods to Adjust Trading Rules     
    def Set_Signal_Rule(self, Primary, Agree):
        self._Primary_Signal = Primary
        self._Signal_Agree = Agree
    
    def Set_Weight_Method(self, Method):
        self._Weight_Method = Method
    
    def Set_Margin_Rate(self, Margin):
        self._Margin_Rate = Margin
        
    def Set_Risk_Cap(self, Value_Cap = None, Indiv_Value_Cap = None, Volatility_Cap = None, Indiv_Vol_Cap = None):
        self._Indiv_Value_Cap = None
        self._Indiv_Vol_Cap = None
        self._Port_Value_Cap = None
        self._Port_Vol_Cap = None
        
        if Indiv_Value_Cap != None:
            self._Indiv_Value_Cap = Indiv_Value_Cap
        if Value_Cap != None:
            self._Port_Value_Cap = Value_Cap
        if Volatility_Cap != None:
            self._Port_Vol_Cap = Volatility_Cap
        if Indiv_Vol_Cap != None:
            self._Indiv_Vol_Cap = Indiv_Vol_Cap    
        if (Indiv_Value_Cap != None) or (Value_Cap != None) or (Volatility_Cap != None) or (Indiv_Vol_Cap != None):
            self._Risk_Cap = True
        
        
#----------Auxiliary Functions     
    def Plot_Trades(self, Investment = 'All'):
        fig, ax1 = plt.subplots()
        if  Investment == 'All':
            Asset_Show = self.Asset[:-1]
        else:
            Asset_Show = Investment
        for Asset in Asset_Show:           
            plt.figure()
            Price = self._Period_Price[Asset]
            plt.plot(Price, 'b-')
            Chart = self._Period_Signal[Asset]
            long = (Chart == 1)*Price
            long = long[long!= 0]
            short = (Chart == -1)*Price
            short = short[short!=0]
            plt.plot(long, 'go')
            plt.plot(short, 'ro')
            plt.title(Asset)
            plt.show()
        

    def Risk_Demos(self):
        self.Internal_Audit._Graphic = True
        self.Internal_Audit.gross_exp()
        self.Internal_Audit.net_exp()
        self.Internal_Audit.port_vol_percentage()
        self.Internal_Audit.Calculate_VaR()
        self.Internal_Audit.Get_Top_Positions()
        self.Internal_Audit.Expected_Shortfall()
        self.Internal_Audit.Liquidity()


    def Performance_Demos(self):
        self.Internal_Appraiser.Basic_chart()
        self.Internal_Appraiser.Exposure_vs_Benchmark()
        self.Internal_Appraiser.Fully_Invest_Performance()
        self.Internal_Appraiser.Show_Loading()
        summary = self.Internal_Appraiser.Return_Attribution()
        return summary
