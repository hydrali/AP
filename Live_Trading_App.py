# -*- coding: utf-8 -*-#
"""
Created on Wed Aug 14 00:38:21 2019

@author: hydra li
"""

import pandas as pd
import matplotlib.pyplot as plt
from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector
from threading import Thread, Lock
from time import sleep
from Risk_Analytics_App import Risk_Advisor
from Performance_Analytic_App import Performance_Advisor
from IPython.display import clear_output
import random


class Live_Trade_App():
    def __init__(self, Pool_Limit = 100, Update_Frequency = 5, _Time_Out = 4, _Refresh = 0.3, _TimeZone = 1, frequency = ''):
        self.Pool_Limit = Pool_Limit
        self.Update_Frequency = Update_Frequency
        self._Time_Out = _Time_Out
        self._Refresh = _Refresh
        self._TimeZone = _TimeZone
        self._Holding = {}
        self._Price_Buffer = pd.DataFrame()        
        self._Volume_Buffer = pd.DataFrame()
        self._lock = Lock()
        self._Asset_Watchlist = []
        self._Online_Auditor = None
        self._Online_Appraiser = None
        self._Holding_Port = DWX_ZeroMQ_Connector(_verbose= False, _PUSH_PORT= 32001, _PULL_PORT= 32002, _SUB_PORT= 32000)
        self._Data_Port = DWX_ZeroMQ_Connector(_verbose= False, _PUSH_PORT=32553, _PULL_PORT= 32554 ,_SUB_PORT= 32555)
        self._Execution_Port = DWX_ZeroMQ_Connector(_verbose = False)
        self._Check_Connection_status()


    def Run(self):
        self._Holding_Updater = Thread(name = 'Holding Updater', target = self._Current_Holding, args = (self.Update_Frequency, ))
        self._Holding_Updater.daemon = True
        self._Holding_Updater.start()
        
        self._Risk_Updater = Thread(name = 'Risk Updater', target= self._Risk_Monitor, args= (self.Update_Frequency, ))
        self._Risk_Updater.daemon = True
        self._Risk_Updater.start()
        
#        self._Random_Trader = Thread(name = 'Rand Trader', target=self._Baby_Strategy, args= (self.Update_Frequency, ))
#        self._Random_Trader.daemon = True
#        self._Random_Trader.start()
#        
        #Still Need to UPDATE the time of the info fed back!!!!!!!
        #A function that collects new price record while true, this a daemon thread
        #A condition switch to terminate the thread

    
    def _Current_Holding(self, every):
        while self._Market_Open:
            self._Holding_Port._set_response_(None)
            self._Holding_Port._DWX_MTX_GET_ALL_OPEN_TRADES_()
            _wait_start = pd.to_datetime('now')
            #To prevent the case of waiting forever if never hear back for any reason
            while self._Holding_Port._valid_response_('zmq') == False:
                self._Holding_Port._DWX_MTX_GET_ALL_OPEN_TRADES_()
                sleep(self._Refresh)
                if (pd.to_datetime('now') - _wait_start).total_seconds() > (self._Time_Out):
                    print('... Holding Request Never Heard Back')
                    break
            
            if self._Holding_Port._valid_response_('zmq'):
                _Response = self._Holding_Port._get_response_()
#                print('Hear Back Success')
                if ('_trades' in _Response.keys() and len(_Response['_trades']) > 0):
                    New_Holding = pd.DataFrame(_Response['_trades']).transpose()
                    Asset = list(pd.unique(New_Holding['_symbol']))
                    self._Asset_Watchlist = list(set(Asset + self._Asset_Watchlist))
                    self._Holding = {}
                    self._Volume_Multiplier = {}
                    self._Holding['Cash'] = _Response['_Equity']
                    for idx, row in New_Holding.iterrows():
                        ls = 1 if row['_type'] == 0 else -1
                        quantity = row['_Units_lot'] * row['_lots'] * ls
                        if row['_symbol'] not in self._Holding:
                            self._Holding[row['_symbol']] = quantity
                            self._Volume_Multiplier[row['_symbol']] = row['_Units_lot']
                        else:
                            self._Holding[row['_symbol']] += quantity
                        self._Holding['Cash'] -= quantity * row['_open_price']
                    self._HDF = New_Holding
            sleep(every)


    def _Risk_Monitor(self, every):
        Last_Postion = {}
        while self._Market_Open:
            if bool(self._Holding) == False:
                print('Waiting for the first Holding info to be retrieved first')
            else:
                if Last_Postion != self._Holding:
                    Last_Postion = self._Holding.copy()
                    if self._Price_Buffer.shape[0] < 500:
                        self._Online_Auditor = Risk_Advisor(holding_info= Last_Postion, frequency= 'Minutely', Test_day= 'live', Graphic=False)
                    else:
                        self._Online_Auditor = Risk_Advisor(holding_info=Last_Postion, _Price= self._Price_Buffer, _Volume= self._Volume_Buffer, Test_day='live', Graphic= False)
                
                print(self._Holding)
                self._Online_Auditor.All_Live_Printers()
                out3 = self._Online_Auditor.Risk_Contribution(latest= False)
                out3.fillna(0)
                plt.pie(out3.values, labels= list(out3.columns), autopct='%1.1f%%')
                plt.show()
            sleep(every)
            clear_output()

            
    def _Baby_Strategy(self, every):
        while self._Market_Open:
            if bool(self._Holding) == False:
                print('Waiting for the first Holding info to be retrieved first')
            else:
                for idx, row in self._HDF.iterrows():
                    if row['_pnl'] > 20:
                        symbol = row['_symbol']
                        action = 'CLOSE'
                        tkt = idx
                        self.Trade_Execute(action= action, symbol= symbol, tkt = tkt)
                
                Open_Ast = random.sample(self._Asset_Watchlist, 1)[0]
                ls = random.randint(0,1)
                quantity = 0.1
                self.Trade_Execute('OPEN', Open_Ast, _type = ls, lot = quantity)
            sleep(every)

    
    def Trade_Execute(self, action, symbol = None, **kwarg):
        if action =='CLOSE_All':
            _check = '_response_value'
            self._Execution_Port._DWX_MTX_CLOSE_ALL_TRADES_()            
        else:
            self._Execution_Port._set_response_(None)
            if symbol is None:
                print('You forgot to provide a symbol to trade!')
                
            self._Execution_Port._New_Order(action = action, symbol = symbol, **kwarg)
            _wait = pd.to_datetime('now')
            
            if action == 'OPEN':
                _check = '_action'
                
            elif action == 'CLOSE':
                _check = '_response_value'
        
        while self._Execution_Port._valid_response_('zmq') == False:
            sleep(self._Refresh)
            if (pd.to_datetime('now') - _wait).total_seconds() > (self._Time_Out):
                print('...Trade Execution Never Heard Back')
                break

        if self._Execution_Port._valid_response_('zmq'):
            print('... executed successfully')
            if _check in self._Execution_Port._get_response_().keys():
                return self._Execution_Port._get_response_()
        return None


    def _Price_Buffering(self, symbol = None, stop = False):
        if stop:
            self._Data_Port._DWX_MTX_UNSUBSCRIBE_ALL_MARKETDATA_REQUESTS_()
        else:
            self._Data_Port._DWX_MTX_SUBSCRIBE_MARKETDATA_(symbol)
            
    def _Snapshots(self, n, symbol = None):
        if self._Price_Buffer.shape[0] == 0:
            print('Starting to Record Price ... ')
            if symbol == None:
                symbol = self._Asset_Of_Interest
            self._Price_Buffering(symbol= symbol)
            
        for i in range(n):
            if i%20 == 0:
                self._Data_Port._reset_DB_()
            sleep(self._Refresh)
            
            if bool(self._Data_Port._Market_Data_DB):
                snapshot = pd.DataFrame.from_dict(self._Data_Port._Market_Data_DB)
                snapshot.index = pd.to_datetime(snapshot.index).round('1s')
                print('Snapshot Number ', i)
                snapshot = pd.DataFrame(snapshot[symbol].to_list(), index = snapshot.index)
                snapshot.columns = ['Bid', 'Ask', 'Volume']
                self._Price_Buffer = pd.concat([self._Price_Buffer, snapshot]).drop_duplicates()
        self._Price_Buffering(stop= True)
        
    def Print_Price_Buffer(self):
        return self._Price_Buffer
    
    def _Check_Connection_status(self):
        self._Execution_Port._DWX_ZMQ_HEARTBEAT_()
        self._Data_Port._DWX_ZMQ_HEARTBEAT_()
        self._Holding_Port._DWX_ZMQ_HEARTBEAT_()
        _wait_start = pd.to_datetime('now')
        while (pd.to_datetime('now') - _wait_start).total_seconds()< 3:   
            sleep(self._Refresh)
            if self._Execution_Port._valid_response_('zmq'):
                _Response_1 = self._Execution_Port._get_response_()
                Fail = None if _Response_1['_response'] == 'loud and clear!' else 1
            else:
                self._Execution_Port._DWX_ZMQ_HEARTBEAT_()
                Fail = 1
                
            if self._Data_Port._valid_response_('zmq'):
                _Response_2 = self._Data_Port._get_response_()
                if _Response_2['_response'] != 'loud and clear!':
                    Fail = 2
            else:
                self._Data_Port._DWX_ZMQ_HEARTBEAT_()
                Fail = 2
                
            if self._Holding_Port._valid_response_('zmq'):
                _Response_3 = self._Holding_Port._get_response_()
                if _Response_3['_response'] != 'loud and clear!':
                    Fail = 3                
            else:
                self._Holding_Port._DWX_ZMQ_HEARTBEAT_()
                Fail = 3
                
            if Fail is None:                
                print('Good morning sir, PARIS is online ')
                self._Market_Open = True
                return None
        
        if Fail == 1:   
            print('Please Check the configuration of the Execution port')            
        elif Fail == 2:
            print('Please Check the configuration of the Data port')            
        elif Fail == 3:
            print('Please Check the configuration of the Holding port')            
            

    def _Set_Asset(self, Names):
        self._Asset_Watchlist.extend(Names)
        
    def _Close_Market(self):
        self._Market_Open = False
        
    
    
    
    
    
    
    
    