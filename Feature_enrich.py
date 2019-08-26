# -*- coding: utf-8 -*-
"""
Created on Sat May 18 20:28:20 2019

@author: hydra li
"""

import numpy as np
exec(open("indicators.py").read())

def Generate_pool(price1):
    MACD_Signal(price1)
    Bollinger_Band(price1)
    RSI(price1)
    TechnicalIndicators(price1)
    
    price1 = price1.drop(price1.index[0:28])
    price1 = price1.dropna()
    
    return price1


def MACD_Signal(price1, fast = 12, slow = 26, sig_period = 9):
    price = price1.copy()
    price.loc[:,'MACD'] = price['<CLOSE>'].rolling(5).mean() - price['<CLOSE>'].rolling(13).mean()
    price.loc[:,'signal_line'] = price['MACD'].rolling(9).mean()
    
    price.loc[:,'diff'] = np.sign(price['signal_line'] - price['MACD'])
    price['sign'] = int(0)
    price['sign'].loc[price['diff']*price['diff'].shift(1) == -1] = 1    
    price.loc[:,'sign'] = price['diff'].shift(1)*price['sign']
    price['signal'] = int(0)
    price.loc[(price['MACD'] > 0) & (price['sign'] == -1), 'signal'] = -1
    price.loc[(price['MACD'] < 0) & (price['sign'] == 1), 'signal'] = 1
    price = price.dropna()
    
    price1['MACD'] = price['signal']
    return price1

def Bollinger_Band(price1, MA_period = 20, Band_width = 2):
    price = price1.copy()
    price['Boll_mid'] = price['<CLOSE>'].rolling(MA_period).mean()
    price['Boll_Upper'] = price['Boll_mid'] + Band_width*price['<CLOSE>'].rolling(20).std()
    price['Boll_Lower'] = price['Boll_mid'] - Band_width*price['<CLOSE>'].rolling(20).std()  

    price['signal'] = int(0)
    price['diff'] = np.sign(price['<CLOSE>'] - price['Boll_Upper'])
    price['signal'].loc[(price['diff'].shift(1)*price['diff'] == -1) & (price['diff'].shift(1) > 0)] = -1
    price['diff1'] = np.sign(price['<CLOSE>'] - price['Boll_Lower'])
    price['signal'].loc[(price['diff1'].shift(1)*price['diff1'] == -1) & (price['diff1'].shift(1) < 0)] = 1
    
    price1['Bollinger'] = price['signal']
    return price1


def RSI(price1, period = 14, low = 30, high = 70):
    price = price1.copy()

    price['return'] = price['<CLOSE>'].pct_change()*100
    price['positive'] = price['return'] * (price['return'] > 0)
    price['negative'] = price['return'] * (price['return'] < 0)
    price['win'] = 0
    price.iloc[period,-1] = price['positive'][:period].sum()/period
    price['loss'] = 0
    price.iloc[period,-1] = price['negative'][:period].sum()/period
    price = price.iloc[period::]
    win = [price['win'][0]]
    loss = [price['loss'][0]]
    for i in range(1, price.shape[0]):
        win.append((win[-1]*(period - 1) + price['positive'][i])/period)
        loss.append((loss[-1]*(period - 1) + price['negative'][i])/period)    
    price['win'] = win
    price['loss'] = loss
    price['RSI'] = 100 - 100/(1- price['win']/price['loss'])
    
    price['signal'] = 0
    price.loc[price['RSI'] >= high, 'signal'] = -1
    price.loc[price['RSI'] <= low, 'signal'] = 1
    
    price1['RSI'] = price['signal']
    price1['RSI_level'] = price['RSI']
    return price1

## ADMI does not give a trading signal, instead it only tells you if a trend is strong or weak, so we generate no signal from it
## but return its value instead
## There is a mistake in the formula of calculating the William's R, add -1/+1 to the end of index
## Ultimate_Oscilator requires remove 28 days before first data is generated


def TechnicalIndicators(price1):
    price = price1.copy()
    price.index = range(price1.shape[0])
    momentum(price)
    Look_back = 30
    trix(price)
    ema(price, 10)
    ema(price, 40)
    price['ema_diff'] = np.sign(price['ema10'] - price['ema40'])
    price['ema_Signal'] = int(0)
    
    price['ema_Signal'].loc[price['ema_diff']*price['ema_diff'].shift(1) == -1] = 1    
    price.loc[:,'ema_Signal'] = price['ema_diff'].shift(1)*price['ema_Signal']
    price = price.drop('ema_diff', axis=1)
            
    price['trix_sign'] = np.sign(price['trix'] - price['trix_signal'])
    price['TRIX_signal'] = 0
    price['TRIX_signal'][price['trix_sign']*price['trix_sign'].shift(1) == -1] = 1    
    price.loc[:,'TRIX_signal'] = price['trix_sign'].shift(1)*price['TRIX_signal']
    price.index = price1.index
    
    
    price1['momentum'] = price['momentum']
    price1['TRIX'] = price['TRIX_signal']
    price1['ema_Signal'] = price['ema_Signal']
    
    return price1
    
