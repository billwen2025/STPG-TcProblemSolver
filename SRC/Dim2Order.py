#/usr/bin/python3
import os,shutil
import csv,re
import pickle


OrderMapListFileName="OrderMapList.serial"
Dim2OrderFileName="Dim2Order.serial"
Dim2Test1Dir="/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/Dim2PartialOrder/test1/"
OrderMapListDim2test1={}
Dim2Ordertest1={}

orderfile=os.path.join(Dim2Ordertest1,OrderMapListFileName)
with open(orderfile,"rb") as f:
    OrderMapListDim2test1=pickle.load(f)

orderfile=os.path.join(Dim2Ordertest1,Dim2OrderFileName)
with open(orderfile,"rb") as f:
    Dim2Ordertest1=pickle.load(f)

#currkey is tuple
# return nextkey or none
def getNextOdLink(currkey):
    if currkey in Dim2Ordertest1.keys():
        ordertup=Dim2Ordertest1[currkey]
        idx=ordertup[0]
        nexidx=idx+1
        if nexidx in OrderMapListDim2test1.keys():
            return OrderMapListDim2test1[nexidx]        
    return None

#currkey is tuple
# return prekey or none
def getPreOdLink(currkey):
    if currkey in Dim2Ordertest1.keys():
        ordertup=Dim2Ordertest1[currkey]
        idx=ordertup[0]
        preidx=idx-1
        if preidx in OrderMapListDim2test1.keys():
            return OrderMapListDim2test1[preidx]        
    return None

def greater(keyA,keyB):
    if (keyA in Dim2Ordertest1.keys()) and (keyB in Dim2Ordertest1.keys()):
        ordertupA=Dim2Ordertest1[keyA]
        oda=ordertupA[0]
        ordertupB=Dim2Ordertest1[keyB]
        odb=ordertupB[0]

        return oda>odb
    return False
