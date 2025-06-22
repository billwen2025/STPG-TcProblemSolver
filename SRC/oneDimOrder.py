#!/usr/bin/python3
import sortlinklist as sorLL
OrderMapList={}
theorder=0

OneDimOrder={}#key, value---sorted
def initialOrderList():
    global OrderMapList,OneDimOrder,theorder
    theorder=0
    OrderMapList={}
    OneDimOrder={}


    #hop2
    key=tuple([0.011,0.011])
    OneDimOrder[key]=theorder,0.042371
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015])
    OneDimOrder[key]=theorder,0.047370
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011])
    OneDimOrder[key]=theorder,0.047374
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015])
    OneDimOrder[key]=theorder,0.051854
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02,0.011])
    OneDimOrder[key]=theorder,0.053716
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ])
    OneDimOrder[key]=theorder,0.053719
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ])
    OneDimOrder[key]=theorder,0.057973
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015])
    OneDimOrder[key]=theorder,0.057984
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.011])
    OneDimOrder[key]=theorder,0.063448
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ])
    OneDimOrder[key]=theorder,0.063708
    OrderMapList[theorder]=key
    theorder+=1

    #hop3
    key=tuple([0.011,0.015,0.011])
    OneDimOrder[key]=theorder,0.068385
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.015])
    OneDimOrder[key]=theorder,0.068386
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.011])
    OneDimOrder[key]=theorder,0.068402
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.015])
    OneDimOrder[key]=theorder,0.072860
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.015])
    OneDimOrder[key]=theorder,0.072864
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.011])
    OneDimOrder[key]=theorder,0.072865
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.020])
    OneDimOrder[key]=theorder,0.074699
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.011])
    OneDimOrder[key]=theorder,0.074711
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.011])
    OneDimOrder[key]=theorder,0.074732
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.015])
    OneDimOrder[key]=theorder,0.077241
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.011])
    OneDimOrder[key]=theorder,0.078958
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.015])
    OneDimOrder[key]=theorder,0.078964
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.020])
    OneDimOrder[key]=theorder,0.078966
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.015])
    OneDimOrder[key]=theorder,0.078968
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.020])
    OneDimOrder[key]=theorder,0.078969
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.011])
    OneDimOrder[key]=theorder,0.078976
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.015])
    OneDimOrder[key]=theorder,0.083201
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.020])
    OneDimOrder[key]=theorder,0.083213
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.015])
    OneDimOrder[key]=theorder,0.083225
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.011,0.011])
    OneDimOrder[key]=theorder,0.084517
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.020])
    OneDimOrder[key]=theorder,0.084697
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.011])
    OneDimOrder[key]=theorder,0.084699
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.020])
    OneDimOrder[key]=theorder,0.084713
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.020])
    OneDimOrder[key]=theorder,0.088893
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.015])
    OneDimOrder[key]=theorder,0.088907
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.020])
    OneDimOrder[key]=theorder,0.088908
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.011,0.015])
    OneDimOrder[key]=theorder,0.089401
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.011,0.011])
    OneDimOrder[key]=theorder,0.089407
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.015,0.011])
    OneDimOrder[key]=theorder,0.089408
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.011,0.011])
    OneDimOrder[key]=theorder,0.089421
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.015,0.015])
    OneDimOrder[key]=theorder,0.093873
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.011,0.015])
    OneDimOrder[key]=theorder,0.093881
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.015,0.011])
    OneDimOrder[key]=theorder,0.093881
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.011,0.015])
    OneDimOrder[key]=theorder,0.093883
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.015,0.011])
    OneDimOrder[key]=theorder,0.093889
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.011,0.011])
    OneDimOrder[key]=theorder,0.093894
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.020])
    OneDimOrder[key]=theorder,0.094482
    OrderMapList[theorder]=key
    theorder+=1


    #hop4

    key=tuple([0.011,0.02 ,0.011,0.011])
    OneDimOrder[key]=theorder,0.095701
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.011,0.020])
    OneDimOrder[key]=theorder,0.095718
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.020,0.011])
    OneDimOrder[key]=theorder,0.095721
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.011,0.011])
    OneDimOrder[key]=theorder,0.095725
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.015,0.015])
    OneDimOrder[key]=theorder,0.098245
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.015,0.015])
    OneDimOrder[key]=theorder,0.098248
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.011,0.015])
    OneDimOrder[key]=theorder,0.098255
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.015,0.011])
    OneDimOrder[key]=theorder,0.098258
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.015,0.020])
    OneDimOrder[key]=theorder,0.099965
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.020,0.011])
    OneDimOrder[key]=theorder,0.099973
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.011,0.020])
    OneDimOrder[key]=theorder,0.099975
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.011,0.015])
    OneDimOrder[key]=theorder,0.099976
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.011,0.020])
    OneDimOrder[key]=theorder,0.099976
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.020,0.015])
    OneDimOrder[key]=theorder,0.099977
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.020,0.011])
    OneDimOrder[key]=theorder,0.099978
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.015,0.011])
    OneDimOrder[key]=theorder,0.099980
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.011,0.011])
    OneDimOrder[key]=theorder,0.099980
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.011,0.015])
    OneDimOrder[key]=theorder,0.099987
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.011,0.011])
    OneDimOrder[key]=theorder,0.099999
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.015,0.011])
    OneDimOrder[key]=theorder,0.100008
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.015,0.015])
    OneDimOrder[key]=theorder,0.102586
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.015,0.020])
    OneDimOrder[key]=theorder,0.104188,
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.011,0.020])
    OneDimOrder[key]=theorder,0.104196
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.020,0.015])
    OneDimOrder[key]=theorder,0.104199
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.015,0.020])
    OneDimOrder[key]=theorder,0.104207
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.020,0.011])
    OneDimOrder[key]=theorder,0.104210
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.020,0.015])
    OneDimOrder[key]=theorder,0.104215
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.015,0.015])
    OneDimOrder[key]=theorder,0.104215
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.015,0.011])
    OneDimOrder[key]=theorder,0.104217
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.015,0.011])
    OneDimOrder[key]=theorder,0.104221
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.011,0.015])
    OneDimOrder[key]=theorder,0.104226
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.011,0.015])
    OneDimOrder[key]=theorder,0.104229
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.015,0.015])
    OneDimOrder[key]=theorder,0.104242
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.011,0.020])
    OneDimOrder[key]=theorder,0.105691
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.011,0.020])
    OneDimOrder[key]=theorder,0.105716
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.020,0.011])
    OneDimOrder[key]=theorder,0.105725
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.020,0.011])
    OneDimOrder[key]=theorder,0.105726
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.011,0.011])
    OneDimOrder[key]=theorder,0.105731
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.011,0.020,0.020])
    OneDimOrder[key]=theorder,0.105707
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.020,0.015])
    OneDimOrder[key]=theorder,0.108421
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.015,0.020])
    OneDimOrder[key]=theorder,0.108423
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.015,0.015])
    OneDimOrder[key]=theorder,0.108437
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.015,0.015])
    OneDimOrder[key]=theorder,0.108450
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.011,0.020,0.020])
    OneDimOrder[key]=theorder,0.109879
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.015,0.020])
    OneDimOrder[key]=theorder,0.109884
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.015,0.020,0.020])
    OneDimOrder[key]=theorder,0.109885
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.011,0.020])
    OneDimOrder[key]=theorder,0.109892
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.020,0.015])
    OneDimOrder[key]=theorder,0.109894
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.020,0.015])
    OneDimOrder[key]=theorder,0.109900
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.020,0.011])
    OneDimOrder[key]=theorder,0.109906
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.020,0.011])
    OneDimOrder[key]=theorder,0.109908
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.011,0.020])
    OneDimOrder[key]=theorder,0.109910
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.015,0.020])
    OneDimOrder[key]=theorder,0.109919
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.015,0.011])
    OneDimOrder[key]=theorder,0.109921
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.011,0.015])
    OneDimOrder[key]=theorder,0.109924
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple( [0.015,0.02 ,0.020,0.015])
    OneDimOrder[key]=theorder,0.114069
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.015,0.020,0.020])
    OneDimOrder[key]=theorder,0.114078
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.015,0.020])
    OneDimOrder[key]=theorder,0.114086
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.015,0.020])
    OneDimOrder[key]=theorder,0.114098
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.020,0.015])
    OneDimOrder[key]=theorder,0.114099
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.015,0.015])
    OneDimOrder[key]=theorder,0.114114
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.011,0.02 ,0.020,0.020])
    OneDimOrder[key]=theorder,0.115464
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.011,0.020,0.020])
    OneDimOrder[key]=theorder,0.115466
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.011,0.020])
    OneDimOrder[key]=theorder,0.115486
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.020,0.011])
    OneDimOrder[key]=theorder,0.115498
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.015,0.020,0.020])
    OneDimOrder[key]=theorder,0.119634
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.015,0.02 ,0.020,0.020])
    OneDimOrder[key]=theorder,0.119638
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.020,0.015])
    OneDimOrder[key]=theorder,0.119655
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.015,0.020])
    OneDimOrder[key]=theorder,0.119658
    OrderMapList[theorder]=key
    theorder+=1
    key=tuple([0.02, 0.02 ,0.020,0.020])
    OneDimOrder[key]=theorder,0.125173
    OrderMapList[theorder]=key
    theorder+=1


#currkey is tuple
# return nextkey or none
def getNextOdLink(currkey,keepsize=1):
    if currkey in OneDimOrder.keys():
        currValue=sorLL.linkTupleValue(currkey)
        ordertup=OneDimOrder[currkey]
        idx=ordertup[0]
        nexidx=idx+1
        while nexidx in OrderMapList.keys():
            while keepsize and len(OrderMapList[nexidx])!=len(currkey):
                nexidx=nexidx+1
                if nexidx not in OrderMapList.keys():
                    return None
            newvalue=sorLL.linkTupleValue(OrderMapList[nexidx])
            if (newvalue-currValue)<0.001:
                nexidx=nexidx+1
            else:
                if nexidx in OrderMapList.keys():
                    return OrderMapList[nexidx]
                else:
                    return None
    return None

def getLinkValue(currkey):
    if currkey in OneDimOrder.keys():
        ordertup=OneDimOrder[currkey]
        value=ordertup[1]
        return value      
    return None

#currkey is tuple
# return prekey or none
def getPreOdLink(currkey,keepsize=1):
    if currkey in OneDimOrder.keys():
        currValue=sorLL.linkTupleValue(currkey)
        ordertup=OneDimOrder[currkey]
        idx=ordertup[0]
        preidx=idx-1
        while preidx in OrderMapList.keys():
            while keepsize and len(OrderMapList[preidx])!=len(currkey):
                preidx=preidx-1
                if preidx not in OrderMapList.keys():
                    return None
            newvalue=sorLL.linkTupleValue(OrderMapList[preidx])
            if (currValue-newvalue)<0.001:
                preidx=preidx-1
            else:
                if preidx in OrderMapList.keys():
                    return OrderMapList[preidx]
                else:
                    return None     
    return None

def greater(keyA,keyB):
    if (keyA in OneDimOrder.keys()) and (keyB in OneDimOrder.keys()):
        ordertupA=OneDimOrder[keyA]
        oda=ordertupA[0]
        ordertupB=OneDimOrder[keyB]
        odb=ordertupB[0]

        return oda>odb
    return False



