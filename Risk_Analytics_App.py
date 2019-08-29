# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 16:33:59 2019

@author: hydra li
"""
from scipy.stats import norm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from Database_Interactions import DB_Operator
from itertools import combinations

class Risk_Advisor():       
    def __init__(self, Portfolio = None, _Price = None, _Volume = None, Graphic = True, Benchmark = ['SPX500USD'],
                 Factors = None, holding_info = None, Test_day = None, frequency = 'Daily', Volume_Multiplier = None):
                
        self._single_day = True
        self._Graphic = Graphic
        self._Factors = None
        DB_Worker = DB_Operator('MT4_Database')
        self._Bench_Mark = DB_Worker.Select_rows(frequency, Benchmark)
        self._Bench_Mark = self._Bench_Mark.set_index(pd.to_datetime(self._Bench_Mark['open_time']))
        self._Bench_Mark = self._Bench_Mark['close']          
        self._Bench_Mark = self._Bench_Mark.fillna(method = 'ffill').dropna()
        
        if Factors is not None:
            if isinstance(Factors, list):
                self._Factors = DB_Worker.Select_rows(frequency, Factors)
                self._Factors = self._Factors.set_index(['Asset', pd.to_datetime(self._Factors['open_time'])])
                self._Factors = self._Factors.unstack(level = 0)['close']
                self._Factors = self._Factors.fillna(method = 'ffill').dropna()
            elif isinstance(Factors, pd.DataFrame):
                self._Factors = Factors
            else: 
                print(''' sorry I don't understand the data type you provide, please provide a list of factors' names or a dataframe of factors' data''')
        #When we call RA separately we generally provide just partial information and then use historical database to ensure Risk advisor runs smooth
        #if Portfolio information is not provided to us directly then we check if holding and time are provided instead
        if Portfolio is None:
        #if holding is provided then we read the price data from the database to do analysis
        #Only in the case of static one day entry we would use a dictionary, otherwise pandas df would be used 
            if holding_info != None:
                if isinstance(holding_info, dict):
                    self.Units = pd.DataFrame(holding_info, index = [Test_day])
                    self.Assets = list(holding_info.keys())
                else:
                    self._single_day = False
                    self.Units = holding_info
                    self.Assets = list(pd.unique(self.Units['Asset']))
            #if neither portfolio nor holdings are provided we assume we'd be analysing our historical trades then we read the trade history
            else:
                self._single_day = False
                Holding = DB_Worker.read_entire_table('Historical_Holdings')
                Holding = Holding.set_index(pd.to_datetime(Holding['open_time']))  
                self.Assets = list(pd.unique(Holding['Asset']))
                Holding =  Holding.set_index([Holding.index, 'Asset']).drop('open_time', axis = 1)
                self.Units = Holding['Amount'].unstack(level = 1).fillna(0)
                
        # After we have holdings we read the corresponding price information to form the portfolio
            if 'Cash' in self.Assets:
                self.Assets.remove('Cash')             
            if _Price is None:  
                self._DB = DB_Worker.Select_rows(frequency, self.Assets) 
                self._DB = self._DB.set_index(['Asset', pd.to_datetime(self._DB['open_time'])])
                self._Close = self._DB.unstack(level= 0)['close']
                self._Volume =  self._DB.unstack(level= 0)['volume'].dropna()
                self._Close['Cash'] = 1
                self._Volume['Cash'] = 0
                self._Close = self._Close.fillna(method = 'ffill')
            else:
                self._Close = _Price
                self._Volume = _Volume

            if self._single_day:
                if Test_day != 'live':
                    self.Prices = self._Close.loc[Test_day]
                else:
                    self.Prices = self._Close.iloc[-1,:]
                self.portfolio = self.Prices*self.Units

            else:
                self.portfolio = self.Units * self._Close
            self.portfolio = self.portfolio.dropna()
            
        # When Performance advisor is connected to the Back_Testor we generally just pass all the portfolio information into the advisor straight away without above hassels
        else:
            self.portfolio = Portfolio
            self._single_day = False
            self._Close = _Price
            self._Volume = _Volume
            self.Assets = list(Portfolio.columns)
            self.Assets.remove('Cash')
            
        self.ret = self._Close.fillna(method= 'ffill').pct_change().dropna()
        self.vcv = self.ret.cov().values

        #When we have portfolio we calculate the equity level, weights and variance etc.
        if self._single_day == False:
            self.Equity = self.portfolio.sum(axis = 1)
            self.weights = self.portfolio.div(self.Equity, axis = 0)
            self.variance = []
            for index, row in self.portfolio.iterrows():
                self.variance.append(np.matmul(np.matmul(row.values, self.vcv), np.transpose(row.values)))
            
        if self._single_day:
            self.Equity = self.portfolio.sum().sum()    
            self.weights = self.portfolio/self.Equity
            temp = np.matmul(self.portfolio.values, self.vcv)
            self.variance = np.matmul(temp, np.transpose(self.portfolio.values))
        
        self.portfolio = self.portfolio[self.Assets + ['Cash']]
        self.weights = self.weights[self.Assets + ['Cash']]
        self._Port_Exc_Cash = self.portfolio.drop('Cash', axis = 1)
        self._frequency = frequency
        DB_Worker.disconnect()
        if Volume_Multiplier is not None:
            for Asset in Volume_Multiplier:
                self._Volume[Asset] *= Volume_Multiplier[Asset]


    def gross_exp(self):
        if self._single_day:
            outcome = self._Port_Exc_Cash.abs().sum().sum()
            outcome = round(outcome)
            printer = 'The Gross Exposure of the portfolio is $' + str(outcome)
            print(printer)
            
        else:
            outcome = self._Port_Exc_Cash.abs().sum(axis = 1)
            outcome = outcome.div(self.Equity, axis = 0)*100
            if self._Graphic:
                fig1, ax0 = plt.subplots()
                ax0.plot(outcome.index, outcome)
                ax0.set_xlabel('time')
                ax0.set_ylabel('percentage')
                ax0.set_title('Gross Exposure')

            if self._Graphic == False:
                return outcome
            
    def net_exp(self):
        if self._single_day:
            outcome = self._Port_Exc_Cash.sum().sum()
            outcome = round(outcome)
            printer = 'The Net Exposure of the portfolio is $' + str(outcome)
            print(printer)
            
        else:
            outcome = self._Port_Exc_Cash.sum(axis = 1)
            outcome = outcome.div(self.Equity, axis = 0)*100
            if self._Graphic:
                fig2, ax2 = plt.subplots()
                ax2.plot(outcome.index, outcome)
                ax2.set_xlabel('time')
                ax2.set_ylabel('percentage')                
                ax2.set_title('Net Exposure')

            if self._Graphic == False:
                return outcome
        
    def corr_table(self):
        return self.ret.corr().fillna(0)
    
    def corr_history(self, window = 50):
        cor_DF_ = self.ret.drop('Cash', axis = 1)
        All_Combs = combinations(self.Assets, 2)
        Corr_Table = pd.DataFrame(index = self.portfolio.index)
        for pairs in All_Combs:
            Corr_Table[pairs] = cor_DF_[pairs[0]].rolling(window).corr(cor_DF_[pairs[1]])
        Corr_Table = Corr_Table.dropna()
        if self._Graphic:
            PLT_B = self._Bench_Mark[Corr_Table.index]
            ax = Corr_Table.plot(subplots = True, color = 'blue')
            for axe in ax:
                axe1 = axe.twinx()
                axe1.plot(Corr_Table.index, PLT_B, color = 'orange')
        else:
            return Corr_Table
    
    def port_vol_monetary(self):
        if self._single_day:
            x = np.asscalar(self.variance**0.5)
            outcome = round(x)
            printer = 'The Monetary volatility of the portfolio is $' + str(outcome)
            print(printer)
            
        else:
            outcome = [Bar**0.5 for Bar in self.variance]
            outcome = pd.Series(outcome, index = self.portfolio.index)
            if self._Graphic:
                fig2, ax3 = plt.subplots()
                ax3.plot(outcome.index, outcome)
                ax3.set_xlabel('time')
                ax3.set_ylabel('Volatility in $')                
                ax3.set_title('Monetary Volatility')

            if self._Graphic == False:
                return outcome
        
    def port_vol_percentage(self):
        if self._single_day:
            x = np.asscalar(self.variance**0.5/self.Equity * 100)
            outcome = np.round(x, 2)
            printer = 'The Percentage volatility of the portfolio is ' + str(outcome) + '%'
            print(printer)   
        
        else:
            outcome = [Bar**0.5*100 for Bar in self.variance]
            outcome = pd.Series(outcome, index = self.portfolio.index)
            outcome = outcome.div(self.Equity, axis = 0)
            if self._Graphic:
                fig4, ax4 = plt.subplots()
                ax4.plot(outcome.index, outcome, 'bo')
                ax4.set_xlabel('time')
                ax4.set_ylabel('Volatility in Percent')                
                ax4.set_title('Percentage Volatility')
                
            if self._Graphic == False:
                return outcome            
    
    def Calculate_VaR(self, percentile = 95):
        multiplier = norm.ppf(percentile/100)
        if self._single_day:
            x = np.asscalar(self.variance**0.5 * multiplier)
            outcome = round(x)
            printer = 'The ' + str(percentile) + ' % VaR of the portfolio is $' + str(outcome)
            print(printer)
            
        else:
            outcome = [Bar**0.5*multiplier for Bar in self.variance]
            outcome = pd.Series(outcome, index = self.portfolio.index)
            if self._Graphic:
                fig5, ax5 = plt.subplots()
                ax5.plot(outcome.index, outcome, 'bo')
                ax5.set_xlabel('time')
                ax5.set_ylabel('VaR in $')                
                ax5.set_title('Value at Risk')
                
            if self._Graphic == False:
                return outcome                
    
    def Empirical_VaR(self, percentile = 95):
        temp = np.matmul(self.ret.values, self.weights.transpose().values)
        n = int(len(temp) * (1- percentile / 100) )
        outcome = temp[temp.argsort(0)][n] * self.Equity
        outcome = np.asscalar(outcome)
        outcome = round(outcome)
        printer = 'The percentile ' +str(percentile) +'% worst historical days with same portfolio holdings have a loss of $' + str(outcome)
        print(printer)
    
    
    def Get_Top_Positions(self, number = 5):
        if self._single_day:
            temp = self.portfolio.abs().values
            rank = np.argsort(temp)[0][::-1]
            idx = rank[:number]
            Assets = self.portfolio.columns[idx]
            Assets = list(Assets)
            printer = 'The top ' +str(number) +' assets by absolute value in our portfolio are ' + str(Assets)
            print(printer)
            
        else:
            outcome = self.weights.drop('Cash', axis = 1)
            outcome*=100
            if outcome.shape[1] > number:
                avg = outcome.abs().sum(axis = 0).values
                rank = np.argsort(avg)[::-1]
                idx = rank[:number]
                Assets = outcome.columns[idx]                
                outcome = outcome[Assets]                
            if self._Graphic:
                ax6 = outcome.plot()
                ax6.set_xlabel('time')
                ax6.set_ylabel('Weights in %')                
                ax6.set_title('Top '+str(number)+' positions')
                
            if self._Graphic == False:
                return outcome
            
            
    def Expected_Shortfall(self, percentile = 95):
        Z = norm.ppf(percentile/100)
        pdf = norm.pdf(Z)
        multiplier = pdf/(1-(percentile/100))
        if self._single_day:
            outcome = np.asscalar(self.variance**0.5*multiplier)
            outcome = round(outcome)
            printer = 'The Expected shortfall if a ' + str(100 - percentile)+' % case happen is $' + str(outcome)
            print(printer)
            
        else:
            outcome = [Bar**0.5*multiplier for Bar in self.variance]
            outcome = pd.Series(outcome, index = self.portfolio.index)
            if self._Graphic:
                fig7, ax7 = plt.subplots()
                ax7.plot(outcome.index, outcome, 'bo')
                ax7.set_xlabel('time')
                ax7.set_ylabel('Loss in $')                
                ax7.set_title('Shortfall with '+str(percentile)+'% confidence')
     
            if self._Graphic == False:
                return outcome                
            
    
    def Liquidity(self, days = 100):
        if self._single_day:
            n = self._Volume.shape[0]
            use = self._Volume.iloc[(n-days):, ]
            out = self.Units.abs()/use.mean()*100
            out = out.sort_values(by = out.index[0], axis =1, ascending = False)
            print('The liquidity of', days, self._frequency, ' in terms of %')
            print(out)
        
        else:
            V_Roll_Mean = self._Volume.rolling(days).mean()
            V_Roll_Mean.iloc[:(days+1), :] = self._Volume.iloc[:(days+1), :]
            V_Roll_Mean = V_Roll_Mean.drop('Cash', axis = 1)
            Denominator = V_Roll_Mean * self._Close.drop('Cash', axis = 1)
            outcome = self._Port_Exc_Cash.div(Denominator).dropna().abs() * 100
            if self._Graphic:
                ax8 = outcome.plot()
                ax8.set_xlabel('time')
                ax8.set_ylabel('% Liquidity')                
                ax8.set_title('% of '+str(days)+' '+ self._frequency + ' average volume')
            if self._Graphic == False:
                return outcome                
  
    
    def Liquidity_Dry_Case(self, percentage = 5):
        n = self._Volume.shape[0]
        pick = int(n*percentage/100)
        df1 = pd.DataFrame(np.sort(self._Volume.values, axis=0), index = range(n), columns=self._Volume.columns)
        Worst_case = df1.iloc[pick, :]
        out = self.Units/Worst_case*100
        out = out.sort_values(by = out.index[0], axis =1, ascending = False)
        print('If the liquidity dries to ', percentage,'% worst case in history then our position compares to market volumes are: %')
        print(out)


    def Risk_Contribution(self, latest = True):
        if latest:
            now = self.weights.iloc[-1, :]
            port_var = np.matmul(np.matmul(now.values, self.vcv),np.transpose(now.values))
            Cont = np.matmul(now.values, self.vcv)/port_var
            Cont = Cont * now
            plt.pie(Cont, labels= self.Assets + ['Cash'], autopct='%1.1f%%')
            return None
        if self._single_day:
            port_var = np.matmul(np.matmul(self.weights.values, self.vcv), np.transpose(self.weights.values))
            Cont = np.matmul(self.weights.values, self.vcv)/port_var
            Cont = Cont *self.weights
            if self._Graphic:
                plt.pie(Cont, labels= self.Assets + ['Cash'], autopct='%1.1f%%')
                plt.show()
            else:
                return Cont
        else:
            Cont_Collect = []
            for i in range(self.portfolio.shape[0]):
                now = self.weights.iloc[i, :]
                port_var = np.matmul(np.matmul(now.values, self.vcv),np.transpose(now.values))
                if port_var != 0:
                    Cont = np.matmul(now.values, self.vcv)/port_var
                else:
                    Cont = [0]*len(now)
                Cont = Cont * now
                Cont_Collect.append(Cont)
            Cont = pd.DataFrame(Cont_Collect, index = self.portfolio.index, columns = self.Assets + ['Cash'])
            return Cont
            
    
    def All_Live_Printers(self):
        if self._single_day:
            self.gross_exp()
            self.net_exp()
            self.port_vol_monetary()
            self.port_vol_percentage()
            self.Calculate_VaR()
            self.Empirical_VaR()
            self.Get_Top_Positions()
            self.Expected_Shortfall()
            print(" ")
            self.Liquidity()
            print("")
            self.Liquidity_Dry_Case()
            
    
    
    
    
    
    
        
        