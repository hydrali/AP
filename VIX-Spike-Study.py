# -*- coding: utf-8 -*-
"""
Created on Fri May 17 16:35:48 2019

@author: Charlie
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def ReturnVCalc(PrVect, RsWSize):
    ReturnsVect = []
    for k in range(len(PrVect)):
        if k < (RsWSize-1):
            ReturnsVect.append(0)
        else:
            ReturnsVect.append(PrVect[k]/PrVect[k-(RsWSize-1)]-1)    
    return (ReturnsVect)

def MeanCalc(PrVect):
    return (sum(PrVect)/len(PrVect))

def StdDevCalc(PrVect):
    Avg = MeanCalc(PrVect)
    Total = 0
    for i in range(len(PrVect)):
        Total = Total + (PrVect[i]-Avg)**2
    return ((Total/len(PrVect))**0.5)

def ReturnSpikePositions(PrVect, RtVect, Threshold,DaysAfterJump):
    OutputVect = []
    ReturnsVect = []
    VolatilityVect =[]
    NoOfSpikes = 0
    for i in range(len(RtVect)):
        if abs(RtVect[i]) <= Threshold:
            OutputVect.append(0)
        else:
            j = 0
            endOfArr = False
            ReturnsVect.append([0])
            VolatilityVect.append([0])
            while ((j) < DaysAfterJump) and endOfArr != True:
                j = j + 1
                Returns = ((PrVect[(i+j)]/PrVect[i])-1)*100
                Vols = StdDevCalc(PrVect[i:(i+j)])
                ReturnsVect[NoOfSpikes].append(Returns)
                VolatilityVect[NoOfSpikes].append(Vols)
                if (j + i + 1) >= len(RtVect) :
                    endOfArr = True
            if (RtVect[i]) <= -Threshold:
                OutputVect.append(-1)
            else:
                OutputVect.append(1)
            NoOfSpikes = NoOfSpikes + 1
    return OutputVect, ReturnsVect, VolatilityVect

def PrettyOutput1(InpVect,DaysConcerned):
    OutputVect = []
    for j in range(len(DaysConcerned)):
        OutputVect.append([])
        Position = (DaysConcerned[j])
        ZerozVect = []
        for i in range(len(InpVect)):
            if len(InpVect[i]) > Position:
                ZerozVect.append(0)
                OutputVect[j].append(InpVect[i][Position])
        plt.scatter(OutputVect[j],ZerozVect)
        plt.ylabel(str(Position+1) + ' Days Return')
        plt.show()
        #print(str(Position+1) + ' Days Mean Return: ' + str(MeanCalc(OutputVect[j])))
    return OutputVect

def PrettyOutput2(InpVect):
    for i in range(len(InpVect)):
        if len(InpVect[0])== len(InpVect[i]):
            plt.plot(InpVect[i])
    plt.ylabel('Daily returns after spike')
    plt.show()
    return 0

def MainFunc(ticker1,weeklyPercentJumpThreshold,StdDev_WindowSize,StartDate,DaysAfterJump):
    Df = yf.download(tickers = ticker1, start = StartDate)
    
    plt.plot(Df['Close'])
    plt.ylabel(ticker1)
    plt.show()
    
    Ticker_WeeklyReturns = ReturnVCalc(Df['Close'],StdDev_WindowSize)
    
    plt.plot(Ticker_WeeklyReturns)
    plt.ylabel(ticker1 + ' Weekly Returns')
    plt.show()
    
    Ticker_SpikePositions, ReturnsReport, VolatilityReport = ReturnSpikePositions(Df['Close'],Ticker_WeeklyReturns,weeklyPercentJumpThreshold, DaysAfterJump)
    NumberOfJumps = Ticker_SpikePositions.count(1) + Ticker_SpikePositions.count(-1)
    
    print("Amount of Spikes above",weeklyPercentJumpThreshold*100, "% occurs",round(NumberOfJumps *100/len(Ticker_SpikePositions),2) , "% of the time")
    return ReturnsReport , VolatilityReport

ticker1 = "^VIX"
weeklyPercentJumpThreshold = 0.3
StdDev_WindowSize = 5
StartDate = "2017-04-01"
DaysAfterJump = 20
DaysConcerned = [1,5,DaysAfterJump]

SpikeReturns, SpikeStdDevs = MainFunc(ticker1,weeklyPercentJumpThreshold,StdDev_WindowSize,StartDate,DaysAfterJump)
x = PrettyOutput1(SpikeReturns,DaysConcerned)
x = PrettyOutput2(SpikeReturns)
print(x)

