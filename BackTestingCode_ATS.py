import numpy as np
import matplotlib.pyplot as plt

def MeanCalc(PrVect):
    return (sum(PrVect)/len(PrVect))

def StdDevCalc(PrVect):
    Avg = MeanCalc(PrVect)
    Total = 0
    for i in range(len(PrVect)):
        Total = Total + (PrVect[i]-Avg)**2
    return ((Total/len(PrVect))**0.5)

def HghLowCalc(PrVect,HVect,LVect):
    Start = 0 #index of starting element
    return ((max(HVect)-min(LVect))/PrVect[Start])

def KellyCritCalc(WinTrades, LosTrades, No_Of_WL_KC, PercentageOfEquity):
    Output = PercentageOfEquity
    if len(WinTrades) > No_Of_WL_KC and len(LosTrades) > No_Of_WL_KC:
        TotalWin_Amount = 0
        TotalLossAmount = 0
        for i in range(len(WinTrades)):
            TotalWin_Amount = TotalWin_Amount + abs(WinTrades[i])
        for i in range(len(LosTrades)):
            TotalLossAmount = TotalLossAmount + abs(LosTrades[i])
        if TotalLossAmount != 0 and TotalWin_Amount != 0:
            b = (TotalWin_Amount/len(WinTrades)) / (TotalLossAmount/len(LosTrades))
        else:
            b = 1
        p = len(WinTrades)/(len(WinTrades)+len(LosTrades))      
        q = 1 - p
        Output = (b*p-q)/b
    return Output

def VolatilityCalc(PrVect, HVect, LVect, RtVect, Weights):
    Output = 0
    StdDev = StdDevCalc(RtVect)
    HghLow = HghLowCalc(PrVect, HVect, LVect)
    Output = StdDev*Weights + HghLow*(1-Weights)
    return (Output)

def ReturnVCalc(PrVect, RsWSize):
    ReturnsVect = []
    for k in range(len(PrVect)):
        if k < (RsWSize-1):
            ReturnsVect.append(0)
        else:
            ReturnsVect.append(PrVect[k]/PrVect[k-(RsWSize-1)]-1)    
    return (ReturnsVect)

def Analysis1Calc(WTrades_V, LTrades_V):
    Total_Long_Trades = 0
    Total_Short_Trades = 0
    Total_Long_Won = 0   #
    Total_Short_Won = 0   #
    Total_Long_Profit = 0
    Total_Long_Loss = 0
    Total_Short_Profit = 0
    Total_Short_Loss = 0
    for m in range(len(WTrades_V)):
        for n in range(len(WTrades_V[m])):
            if WTrades_V[m][n] > 0:
                Total_Long_Won = Total_Long_Won + 1
                Total_Long_Trades = Total_Long_Trades + 1
                Total_Long_Profit = Total_Long_Profit + WTrades_V[m][n]
            else:
                Total_Short_Won = Total_Short_Won + 1
                Total_Short_Trades =  Total_Short_Trades + 1
                Total_Short_Profit = Total_Short_Profit + WTrades_V[m][n] * -1
        for n in range(len(LTrades_V[m])):
            if LTrades_V[m][n] > 0:
                Total_Long_Trades = Total_Long_Trades + 1
                Total_Long_Loss = Total_Long_Loss + LTrades_V[m][n]
            else:
                Total_Short_Trades =  Total_Short_Trades + 1
                Total_Short_Loss = Total_Short_Loss + LTrades_V[m][n] * -1
    return (Total_Long_Trades,Total_Short_Trades,Total_Long_Won,Total_Short_Won,Total_Long_Profit,Total_Long_Loss,Total_Short_Profit,Total_Short_Loss)

def Analysis2Calc(Inp):
    TLT = Inp[0]          # Total_Long_Trades
    TST = Inp[1]          # Total_Short_Trades
    TLW = Inp[2]          # Total_Long_Won
    TSW = Inp[3]          # Total_Short_Won
    TLP = Inp[4]          # Total_Long_Profit
    TLL = Inp[5]          # Total_Long_Profit
    TSP = Inp[6]          # Total_Long_Loss
    TSL = Inp[7]          # Total_Short_Profit
    Long_Rate = TLT / (TLT+TST)
    ShortRate = 1 - Long_Rate
    if TLT != 0:
        Long_Win_Rate = TLW / TLT
    else:    
        Long_Win_Rate = 0
    if TST != 0:
        ShortWin_Rate = TSW / TST
    else:    
        ShortWin_Rate = 0
    if TLW != 0:
        Avg_Long_Win = TLP / TLW
    else:    
        Avg_Long_Win = 0
    if TSW != 0:
        Avg_ShortWin = TSP / TSW
    else:    
        Avg_ShortWin = 0
    if (TLT-TLW) != 0:   
        Avg_Long_Los = TLL / (TLT-TLW)
    else:    
        Avg_Long_Los = 0
    if (TST-TSW) != 0:
        Avg_ShortLos = TSL / (TST-TSW)
    else:
        Avg_ShortLos = 0
    if (TLT + TST) != 0:
        TotalWinRate = (TLW+TSW)/(TLT + TST)
    else:
        TotalWinRate = 0
    if (TLW+TSW) != 0: 
        AverageWinAmount = (TLP+TSP) / (TLW+TSW)
    else:
        AverageWinAmount = 0
    if ((TLT+TST)-(TLW+TSW)) != 0:
        AverageLossAmount = (TLL+TSL) / ((TLT+TST)-(TLW+TSW))
    else:
        AverageLossAmount = 0
    return (Long_Rate,ShortRate,Long_Win_Rate,ShortWin_Rate,Avg_Long_Win,Avg_ShortWin,Avg_Long_Los,Avg_ShortLos,TotalWinRate,AverageWinAmount,AverageLossAmount)

def DrawDownCalc(InpNAV_V):
    AbsoluteDrawdown = 0
    MaximalDrawdown = 0
    LowestPoint = InpNAV_V[0]
    HighestPoint = InpNAV_V[0]
    for i in range(len(InpNAV_V)):
        if LowestPoint > InpNAV_V[i]:
            LowestPoint = InpNAV_V[i]
        if HighestPoint < InpNAV_V[i]:
            HighestPoint = InpNAV_V[i]
        if (HighestPoint - InpNAV_V[i]) > MaximalDrawdown:
            MaximalDrawdown = HighestPoint - InpNAV_V[i]
    AbsoluteDrawdown = InpNAV_V[0] - LowestPoint 
    return(AbsoluteDrawdown, MaximalDrawdown)

def PrettyOutput(StrategyResults):
    First = Analysis1Calc(StrategyResults[2],StrategyResults[3])
    Second = Analysis2Calc(First)
    KellyCrit = Second[8] - ( (1-Second[8]) / (Second[9]/Second[10]) )
    plt.plot(StrategyResults[5])
    plt.plot(StrategyResults[7])
    DrawDowns = DrawDownCalc(StrategyResults[5])
    print("Initial Deposit       : ", StrategyResults[0])
    print("Final Equity          : ", StrategyResults[1])
    print("Final Equity 2        : ", StrategyResults[6])
    print("Total NET Profit      : ", StrategyResults[1]-StrategyResults[0])
    print("Total Trades          : ", sum(StrategyResults[4]))
    print(" (%) Long V Short Pos : ", Second[0])
    print(" Total Win Rate       : ", Second[8])
    print(" Avg Win Amount       : ", Second[9])
    print(" Avg Loss Amount      : ", Second[10])
    print(" Kelly Criterion      : ", KellyCrit)
    print(" Absolute Drawdown    : ", DrawDowns[0])
    print(" Maximal Drawdown     : ", DrawDowns[1])
    print("")
    print("Total Long Trades     : ", First[0])
    print("   (%) Long Wins      : ", Second[2])
    print("   Total Long Win Am  : ", First[4])
    print("   Avg Long Win Am    : ", Second[4])
    print("   Total Long Loss Am : ", First[5])
    print("   Avg Long Loss Am   : ", Second[6])
    print("")
    print("Total Short Trades    : ", First[1])
    print("   (%) Short Wins     : ", Second[3])
    print("   Total Short Win Am : ", First[6])
    print("   Avg Short Win Am   : ", Second[5])
    print("   Total Short Loss Am: ", First[7])
    print("   Avg Short Loss Am  : ", Second[7])
    print("")
    return ()
###
def MainFunc(Signal_V, Price_V, High_V, Low_V, IntInv = 1000000, RsWSize = 5, SDWSize = 20, VolWeight = 1, No_Lots = 1, BCap = 3, SCap = 3, IntVRun = 0, CloseOffset = 0, PercOfEq = 0.01, No_Of_WL_KC = 20, cap = 0.2, StopProfit = 0.02, Stop__Loss = 0.02):
    NAV = IntInv
    NAV2 = IntInv
    RunningNAV = []
    RunningNAV2 = []
    InactiveEquity = NAV
    AmountOfAssets = len(Signal_V)
    AmountOfData = len(Signal_V[0])
    EntryPrice = []
    No_ContractsinTr = []
    LongShort = []
    Limit_Hit = []
    TotTrades = []
    WinTrades = []
    LosTrades = []
    Ret_V = [] 

    for i in range(AmountOfAssets):
        Ret_V.append(ReturnVCalc(Price_V[i], RsWSize))
        EntryPrice.append([])
        No_ContractsinTr.append([])
        WinTrades.append([])
        Limit_Hit.append([])
        LosTrades.append([])
        LongShort.append(0)
        TotTrades.append(0)
    for i in range(AmountOfData):
        if i > (RsWSize+SDWSize-1):
            NAV2 = InactiveEquity
            for j in range(AmountOfAssets):
                # Updates NAV with new prices
                if EntryPrice[j] != []:
                    NAV = NAV + ((sum(No_ContractsinTr[j]) * (Price_V[j][i] - Price_V[j][i-1])) * LongShort[j])
                    NAV2 = NAV2 + sum(No_ContractsinTr[j]) * (Price_V[j][i] * LongShort[j])
                    # CHECK STOP PROFIT / LOSS
                    RemoveCounter = 0
                    for k in range(len(EntryPrice[j])):
                        TradePercentMove = ((Price_V[j][i]/EntryPrice[j][k - RemoveCounter]) - 1) * LongShort[j]
                        if (TradePercentMove < -abs(Stop__Loss)) or (TradePercentMove > StopProfit):
                            ###
                            RemTradeVal = (Price_V[j][i])*No_ContractsinTr[j][k - RemoveCounter] * LongShort[j]
                            InactiveEquity = InactiveEquity + RemTradeVal
                            PNL = (Price_V[j][i]-EntryPrice[j][k - RemoveCounter])*No_ContractsinTr[j][k - RemoveCounter] * LongShort[j]
                            if PNL > 0:
                                WinTrades[j].append(PNL * LongShort[j])
                            else:
                                LosTrades[j].append(PNL * LongShort[j] * -1)
                            del EntryPrice[j][k - RemoveCounter]
                            del No_ContractsinTr[j][k - RemoveCounter]
                            RemoveCounter = RemoveCounter + 1
                            ###
            for j in range(AmountOfAssets):      
                # Signal Change Procedure
                ZeroSafetyCheck = np.array(Price_V[j][(i - (RsWSize+SDWSize)):i])
                if (Signal_V[j][i] == -1 or Signal_V[j][i] == 1) and (sum(np.unique(ZeroSafetyCheck)==0) == 0):
                    # Below closes positions
                    if (LongShort[j] == 1 and Signal_V[j][i] == -1) or (LongShort[j] == -1 and Signal_V[j][i] == 1):
                        RemoveCounter = 0
                        for k in range(len(EntryPrice[j])):
                            ###
                            RemTradeVal = (Price_V[j][i])*No_ContractsinTr[j][k - RemoveCounter] * LongShort[j]
                            InactiveEquity = InactiveEquity + RemTradeVal
                            PNL = (Price_V[j][i]-EntryPrice[j][k - RemoveCounter])*No_ContractsinTr[j][k - RemoveCounter] * LongShort[j]
                            if PNL > 0:
                                WinTrades[j].append(PNL * LongShort[j])
                            else:
                                LosTrades[j].append(PNL * LongShort[j] * -1)
                            del EntryPrice[j][k - RemoveCounter]
                            del No_ContractsinTr[j][k - RemoveCounter]
                            RemoveCounter = RemoveCounter + 1
                            ###
                    
                    # Checks criterium if we are required to add a new position
                    AddPosition = False
                    AddPosition = AddPosition or (LongShort[j] == 1 and Signal_V[j][i] == 1 and len(EntryPrice[j]) < BCap)   # Continued Buy Signal, less than cap
                    AddPosition = AddPosition or (LongShort[j] == -1 and Signal_V[j][i] == -1 and len(EntryPrice[j]) < SCap) # Continued Sell Signal, less than cap
                    AddPosition = AddPosition or (LongShort[j] == -1 and Signal_V[j][i] == 1 and CloseOffset == 1)        # Opposite Buy Signal and creates offset trade straight away
                    AddPosition = AddPosition or (LongShort[j] == 1 and Signal_V[j][i] == -1 and CloseOffset == 1)        # Opposite Sell Signal and creates offset trade straight away
                    AddPosition = AddPosition or (LongShort[j] == 0 and (Signal_V[j][i] == -1 or Signal_V[j][i] == 1))       # New Signal with no current positions
                    
                    # Adds new positions
                    if AddPosition == True:
                        Vol = 0
                        NewContracts = 0
                        i2 = i + 1
                        Vol = VolatilityCalc(Price_V[j][(i2-SDWSize):i2],High_V[j][(i2-SDWSize):i2],Low_V[j][(i2-SDWSize):i2],Ret_V[j][(i2-SDWSize):i2],VolWeight)
                        EquityAllocation = KellyCritCalc(WinTrades[j], LosTrades[j], No_Of_WL_KC, PercOfEq)
                        if Vol == 0:
                            Vol = 1
                        if np.abs(EquityAllocation/Vol) > cap:
                            Portion = cap * np.sign(EquityAllocation)
                        else:
                            Portion = EquityAllocation/Vol
                        if IntVRun == 0: 
                            NewContracts = int(Portion* IntInv/Price_V[j][i]/No_Lots)
                        else:
                            NewContracts = int(Portion* NAV/Price_V[j][i]/No_Lots)

                        if (InactiveEquity - NewContracts*Price_V[j][i]*Signal_V[j][i]) >= 0:   # Trade only executed if there is enough capital
                            EntryPrice[j].append(Price_V[j][i])
                            No_ContractsinTr[j].append(NewContracts)
                            InactiveEquity = InactiveEquity - NewContracts*Price_V[j][i]*Signal_V[j][i]
                            TotTrades[j] = TotTrades[j] + 1
                        
                    # Update Long/Short indicator
                    if LongShort[j] == 0:
                        LongShort[j] = Signal_V[j][i]
                    else:
                        if (LongShort[j] == 1 and Signal_V[j][i] == -1) or (LongShort[j] == -1 and Signal_V[j][i] == 1):
                            if CloseOffset == 0:
                                LongShort[j] = 0
                            else:
                                LongShort[j] = Signal_V[j][i]      
        RunningNAV.append(NAV)
        RunningNAV2.append(NAV2)
    Analytics = [IntInv, NAV, WinTrades, LosTrades, TotTrades,RunningNAV,NAV2,RunningNAV2]
    return Analytics
