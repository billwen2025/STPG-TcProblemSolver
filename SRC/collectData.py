#/usr/bin/python3
import os,shutil
import csv,re
import pickle

RESULTFILE='result.log'
CONFIGFILE='SimParam.cfg'

SimulationDir="/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/Dim2PartialOrder/test1/"

def extract_floats(string):  
  pattern = r"[-+]?\d*\.\d+"  # Regular expression to match float numbers
  matches = re.findall(pattern, string)
  return [float(match) for match in matches]

#return DimN number of arrays in tuple form
def paserCfgtoGetKey(DimN,testcasedir):
    testcasedir=os.path.join(SimulationDir,testcasedir)
    cfgpath=os.path.join(testcasedir,CONFIGFILE)
    delaylist0=None
    delaylist1=None
    with open(cfgpath,'r') as f:
        for line in f:
            #print("paser fileline:%s"%(line))
            match =re.search(r'DimensionOrderTest:(\d+)', line)
            if match:
                type=int(match.group(1))
                if type!=DimN:#type may extend in future
                    return
                
            if DimN==2:              

                match =re.search(r'PathPairs0:(.*?)', line)
                if match:
                    #print(match.groups())
                    #timekeytitle=match.group(1)
                    numberstr=line              
                    delaylist0= extract_floats(numberstr)
                match =re.search(r'PathPairs1:(.*?)', line)
                if match:
                    #print(match.groups())
                    #timekeytitle=match.group(1)
                    numberstr=line              
                    delaylist1= extract_floats(numberstr)

                if delaylist0 and delaylist1:
                    return tuple(delaylist0),tuple(delaylist1)

def getResultValue(testcasedir):
    testcasedir=os.path.join(SimulationDir,testcasedir)
    resultfile=os.path.join(testcasedir,RESULTFILE)
    with open(resultfile,'r') as f:
        for line in f:
            match =re.search(r'Percent95Value:(.*?)', line)
            if match:
                numberstr=line              
                data1array= extract_floats(numberstr)
                return data1array[0]

class dirStru:
    def __init__(self,name,value,key1,key2=None,key3=None,key4=None,key5=None):
        self.dirname=name
        self.key1=key1
        self.key2=key2
        self.key3=key3
        self.key4=key4
        self.key5=key5
        self.value=value


def sortbyvalue(itm):
    return itm.value


OrderMapListFileName="OrderMapList.serial"
Dim2OrderFileName="Dim2Order.serial"

def collectDataFromDir(DimN):
    OrderMapList={}
    Dim2Order={}
    
    dirlist=[]
    filenamelist=os.listdir(SimulationDir)
    for filename in filenamelist:
        dir=os.path.join(SimulationDir,filename)
        if os.path.isdir(dir):
            keytuple=paserCfgtoGetKey(DimN,filename)
            #print("got keytuple:%s"%(list(keytuple)))
            value=getResultValue(filename)
            if DimN==2:
                diritm=dirStru(filename,value,keytuple[0],keytuple[1])
            dirlist.append(diritm)

    dirlist.sort(key=sortbyvalue)
    theOrder=0
    for tdir in dirlist:
        if DimN==2:
            keytuple=(tdir.key1,tdir.key2)
        Dim2Order[keytuple]=(theOrder,tdir.value)
        OrderMapList[theOrder]=keytuple 
        theOrder+=1 

    ##save dic to file
    ordermappath=os.path.join(SimulationDir,OrderMapListFileName)
    with open(ordermappath,'wb') as f:
        pickle.dump(OrderMapList,f)      

    dim2orderpath=os.path.join(SimulationDir,Dim2OrderFileName)
    with open(dim2orderpath,'wb') as f:
        pickle.dump(Dim2Order,f)  

def moduletest():
    collectDataFromDir(2)              

if __name__=='__main__':moduletest()        



