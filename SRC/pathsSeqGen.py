#!/usr/bin/python3
import os,shutil,time,datetime,math
import threading
import oneDimOrder as oneDOd
import collectData as collData
import sqlite3
#import sortlinklist as sorlk
#import simusrc.linkDelayMdl as lkdly

#RUNNINGDRR="/home/bill/work/STPGPlusSGB/STPGPlusSGBModel"
RUNNINGDRR="/home/bill/Documents/VScode/gitCode/STPGPlusSGBModel"
MINDELAY=0.01
QTPLEN=3
D1=0.011
D2=0.015
D3=0.020
MAXDELAY=[D1,D2, D3]
#retrurn all possible maxDelay arrays.
#len= 3^hops of hopsn array
def Gen1DimSeqc(hopsn):
    if hopsn==1:
        return [[D1],[D2],[D3]]
    if hopsn==2:
        array=[
            [D1,D1],
            [D1,D2],
            [D2,D2], 
            [D1,D3],
            [D2,D3],
            [D3,D3],
        ]
        return array
    if hopsn==3:
        array=[
            [D1,D1,D1],
            [D1,D1,D2],
            [D1,D2,D2],
            [D1,D1,D3],
            [D2,D2,D2],
            [D1,D2,D3],
            [D2,D2,D3],
            [D1,D3,D3],              
            [D2,D3,D3],
            [D3,D3,D3],
        ]
        return array
    if hopsn==4:
        array=[
            [D1,D1,D1,D1],
            [D1,D1,D1,D2],
            [D1,D1,D2,D2],
            [D1,D1,D1,D3],
            [D1,D2,D2,D2],
            [D1,D1,D2,D3],
            [D2,D2,D2,D2],
            [D1,D2,D2,D3],           
            [D1,D1,D3,D3], 
            [D2,D2,D2,D3],             
            [D1,D2,D3,D3],
            [D2,D2,D3,D3],
            [D1,D3,D3,D3],
            [D2,D3,D3,D3],
            [D3,D3,D3,D3],
        ]
        return array
    if hopsn==5:#and more, check the scale
        array=[
            [D1,D1,D1,D1,D1], #hops5            
            [D2,D2,D2,D2,D2],
            [D3,D3,D3,D3,D3],
            [D1,D1,D1,D1,D1,D1], #hops6
            [D2,D2,D2,D2,D2,D2],
            [D3,D3,D3,D3,D3,D3],
            [D1,D1,D1,D1,D1,D1,D1], #hops7
            [D2,D2,D2,D2,D2,D2,D2],
            [D3,D3,D3,D3,D3,D3,D3],
            [D1,D1,D1,D1,D1,D1,D1,D1], #hops8
            [D2,D2,D2,D2,D2,D2,D2,D2],
            [D3,D3,D3,D3,D3,D3,D3,D3],
            [D1,D1,D1,D1,D1,D1,D1,D1,D1], #hops9
            [D2,D2,D2,D2,D2,D2,D2,D2,D2],
            [D3,D3,D3,D3,D3,D3,D3,D3,D3],
            [D3,D3,D3,D3,D3,D3,D3,D3,D3,D3],#hops10
            [D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3],#hops11
            [D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3],#hops12
            [D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3],#hops13
            [D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3],#hops14
            [D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3,D3],#hops15
        ]
        return array

CONFIGFILE="SimParam.cfg"
SIMUSRCDir="SRC/simusrc/"
CURRENTDIR=os.getcwd()
#
# for each item in array instance, generate a testcase in TopDir
#    generate a config file for this dir
#    copy simulation src to this dir
#    hopsN is the hops num. theArray is the array got by Gen1DimSeqc
# return instance dirpath list
def genInstancesN10Dim1(hopsN, theArray, TopDir):
    dirlist=[]
    strlist=[]
    strHeaderlist=[]
    cfgstr="DimensionOrderTest:1\n"
    strHeaderlist.append(cfgstr)
    cfgstr="Hops:%d\n"%(hopsN)
    strHeaderlist.append(cfgstr)
    cfgstr="ArrayLen:%d\n"%(len(theArray))
    strHeaderlist.append(cfgstr)
    
    instNum=0

    for itm in theArray:
        strlist=strHeaderlist.copy()
        cfgstr="case:%d\n"%(instNum)
        strlist.append(cfgstr)
        cfgstr="PathMaxDelay:%s\n"%(itm)
        strlist.append(cfgstr)
        dirofthiscase="case%d"%(instNum)
        abspath=os.path.join(TopDir,dirofthiscase)
        os.makedirs(abspath)
        dirlist.append(abspath)
        confgfilepath=os.path.join(abspath,CONFIGFILE)
        with open(confgfilepath,"w+") as f:
            f.writelines(strlist)
            f.close()
        #copy the src files from the src orginal dir 
        srcdir=os.path.join(CURRENTDIR,SIMUSRCDir)
        srcMain=os.path.join(srcdir,"SGBDESIntevals.py")
        detMain=os.path.join(abspath,"SGBDESIntevals.py")
        shutil.copy(srcMain,detMain)   
        srclink=os.path.join(srcdir,"linkDelayMdl.py")
        detlink=os.path.join(abspath,"linkDelayMdl.py")
        shutil.copy(srclink,detlink)   
        #end of process
        instNum+=1



    return dirlist

CURRENTDIR=os.getcwd()#/home/bill/Documents/VScode/gitCode/STPGPlusSGBModel
WORKINGDIR="/TestWorkingGDir"#RAM disk


def exeCmd(cmdstr):
    try:
        print("%s start"%(cmdstr))
        retrunmsg=os.system(cmdstr)
        print("%s end"%(cmdstr))
    except:
        print("running failed in %s"%(cmdstr))

TestHops=1

def testonedimension():
    #gen test cases
    thearray=Gen1DimSeqc(TestHops)
    workingdir=os.path.join(CURRENTDIR,WORKINGDIR)
    testdirlist=genInstancesN10Dim1(TestHops,thearray,workingdir)
    # paraller run test cases
    threads=[]
    for testcasedir in testdirlist:
        
        os.chdir(testcasedir)#change to the test case dir 
        detMain=os.path.join(testcasedir,"SGBDESIntevals.py")
        cmdstr="/usr/bin/python3 %s"%(detMain)
        
        thd=threading.Thread(target=exeCmd,args=(cmdstr,))
        thd.start()
        threads.append(thd)
        time.sleep(1)
        
    #wait untill finish
    for thd in threads:
        thd.join()


    os.chdir(CURRENTDIR)#change back to the src dir
    #collect result

#input array of a link upper bound values
#transfor it into a ID value, the value is in order of var.hops
def linkIDValue(link):
    value=0
    hops=len(link)
    value=(hops)*MINDELAY
    if hops>3:
        value+=MINDELAY*(hops-3)*0.5
    if hops>5:
        value+=MINDELAY*(hops-5)*0.9
    if hops>7:
        value+=MINDELAY*(hops-7)*0.9
    if hops>9:
        value+=MINDELAY*(hops-9)*0.9
    range=0
    for val in link:
        range=range+(val-MINDELAY)
    value=range*0.4+value

    valueID=math.ceil(value*10000)

    return valueID

newSimuDB=0 
#newSimuDB=1 #simulation links delay different

if newSimuDB==0:    
    VALUETOLINKMAPFILE="ValuToLinkMapDicObj.txt"
else:
    VALUETOLINKMAPFILE="ValuToLinkMapDicObj2.txt"

ValuToLinkMapDic={}
ValuOrderList=[]

def loadValuToLinkMapDic():
    global ValuToLinkMapDic,ValuOrderList
    filename=os.path.join(BACKUPRESULTDIR,VALUETOLINKMAPFILE)
    with open(filename,'r') as f:
        strline=f.readline()
        ValuToLinkMapDic=eval(strline)
        f.close()
    for value in ValuToLinkMapDic.keys():
        if value not in ValuOrderList:
            ValuOrderList.append(value)
        link=ValuToLinkMapDic[value]
        #print("value:%d  link:%s"%(value,link))
    ValuOrderList.sort()
    #print("%s"%(ValuToLinkMapDic))


def testValueFunc():
    valuLinkMap={}
    for hops in range(1,6):
        linksarray=Gen1DimSeqc(hops)
        for link in linksarray:
            value=linkIDValue(link)
            print("%s value:%d"%(link,value))
            valuLinkMap[value]=link

    strline=str(valuLinkMap)
    filename=os.path.join(BACKUPRESULTDIR,VALUETOLINKMAPFILE)
    with open(filename,'w') as f:
        f.writelines(strline)
        f.close()
        
#thisValue is in the  ValuOrderList
#return the request value if it reach the end, return None

def getPreviousValue(thisValue):
    idx=ValuOrderList.index(thisValue)
    if idx >0:
        return ValuOrderList[idx-1]
    return None

def getNextValue(thisValue):
    idx=ValuOrderList.index(thisValue)
    if (idx+1) >=len(ValuOrderList):
        return None
    return ValuOrderList[idx+1]

    
###check db integration
# check if the prefix exist in DB, prefix is ID1-ID5
def enumerateDBprefix(startminID=10400,endMaxID=36400):
    # valulist=[]
    # thisID=startminID
    # valulist.append(thisID)
    # nexID=getNextValue(thisID)
    # while(nexID<=endMaxID):
    #     thisID=nexID
    #     valulist.append(thisID)
    #     nexID=getNextValue(thisID)
    prefixs=[]
    id1=startminID
    id2=startminID
    id3=startminID
    id4=startminID
    id5=startminID
    while (id1<=endMaxID and id2<=endMaxID  and id3<=endMaxID  and id4<=endMaxID  and id5<=endMaxID):
        prefixs.append([id1,id2,id3,id4,id5])
        nexid5=getNextValue(id5)
        if nexid5>endMaxID:
            #进位
            nexid4=getNextValue(id4)
            if nexid4>endMaxID:
                #进位
                nexid3=getNextValue(id3)
                if nexid3>endMaxID:
                    #进位
                    nexid2=getNextValue(id2)
                    if nexid2>endMaxID:
                        #进位
                        id1=getNextValue(id1)
                        id2=id1
                    else:
                        id2=nexid2
                    id3=id2
                else:
                    id3=nexid3
                id4=id3
            else:
                id4=nexid4            
            id5=id4
        else:
            id5=nexid5      
    return prefixs

#####################
#    after we already got 1 Dim order, we now want to explore some 2 Dim orders
## two dim  test gen
##  mid is one dim link, upper and lower bound is the one dim link boundary
##  gen arrays that with upper and lower pairs, with mid mid in the middle, and wait simulation to sort them 
#   the return array is 2 dim array ( each item is array is 2 link ). And we focus on increasing by different conbines
#######################

def genDim2Arrays(theMidlinkkey, theUpperBDlinkkey, theLowerBDlinkkey):
    theList=[(theMidlinkkey,theMidlinkkey)]
    #oneDOd.initialOrderList()#called already
    nextGkey=oneDOd.getNextOdLink(theMidlinkkey)
    while oneDOd.greater(theUpperBDlinkkey,nextGkey):
        nextSkey=theLowerBDlinkkey
        while oneDOd.greater(theMidlinkkey,nextSkey):
            newitm=(nextSkey,nextGkey)
            theList.append(newitm)
            nextSkey=oneDOd.getNextOdLink(nextSkey)

        nextGkey=oneDOd.getNextOdLink(nextGkey)

    return theList


def genInstancesDim2SomePairs(TopDir):
    dirlist=[]
    strlist=[]
    strHeaderlist=[]
    #setting range
    middkey=tuple([0.015,0.015,0.011])
    upperkey=tuple([0.02, 0.015 ,0.011])
    lowerkey=tuple([0.015,0.02])
    #inital Dim1
    oneDOd.initialOrderList()
    theArray=genDim2Arrays(middkey,upperkey,lowerkey)

    cfgstr="DimensionOrderTest:2\n"    
    strHeaderlist.append(cfgstr)
    cfgstr="MiddleKey:%s\n"%(list(middkey))
    strHeaderlist.append(cfgstr)
    cfgstr="UpperKey:%s\n"%list((upperkey))
    strHeaderlist.append(cfgstr)
    cfgstr="LowerKey:%s\n"%(list(lowerkey))
    strHeaderlist.append(cfgstr)


    cfgstr="ArrayLen:%d\n"%(len(theArray))
    strHeaderlist.append(cfgstr)
    
    instNum=0

    for itm in theArray:
        strlist=strHeaderlist.copy()
        cfgstr="case:%d\n"%(instNum)
        strlist.append(cfgstr)
        cfgstr="PathPairs0:%s\n"%(list(itm[0]))
        strlist.append(cfgstr)
        cfgstr="PathPairs1:%s\n"%(list(itm[1]))
        strlist.append(cfgstr)
        dirofthiscase="case%d"%(instNum)
        abspath=os.path.join(TopDir,dirofthiscase)
        os.makedirs(abspath)
        dirlist.append(abspath)
        confgfilepath=os.path.join(abspath,CONFIGFILE)
        with open(confgfilepath,"w+") as f:
            f.writelines(strlist)
            f.close()
        #copy the src files from the src orginal dir 
        srcdir=os.path.join(CURRENTDIR,SIMUSRCDir)
        srcMain=os.path.join(srcdir,"SGBDESIntevals.py")
        detMain=os.path.join(abspath,"SGBDESIntevals.py")
        shutil.copy(srcMain,detMain)   
        srclink=os.path.join(srcdir,"linkDelayMdl.py")
        detlink=os.path.join(abspath,"linkDelayMdl.py")
        shutil.copy(srclink,detlink)   
        #end of process
        instNum+=1

    return dirlist

def testdimension2():
    #gen test cases    
    workingdir=os.path.join(CURRENTDIR,WORKINGDIR)
    testdirlist=genInstancesDim2SomePairs(workingdir)
    ###paraller run test cases
    threads=[]
    for testcasedir in testdirlist:
        
        os.chdir(testcasedir)#change to the test case dir 
        detMain=os.path.join(testcasedir,"SGBDESIntevals.py")
        cmdstr="/usr/bin/python3 %s"%(detMain)
        
        thd=threading.Thread(target=exeCmd,args=(cmdstr,))
        thd.start()
        threads.append(thd)
        time.sleep(1)
        
    #wait untill finish
    for thd in threads:
        thd.join()


    os.chdir(CURRENTDIR)#change back to the src dir


def testGenD2():
    oneDOd.initialOrderList()
    middlekey=tuple([0.015,0.015,0.011])
    upperkey=tuple([0.02, 0.015 ,0.011])
    lowerkey=tuple([0.015,0.02])
    testArray=genDim2Arrays(middlekey,upperkey,lowerkey)
    print("the test 2dim array len:%d"%(len(testArray)))


####################################################################################
# use absoluate dirs to process for simuLoadBaseOnDB 
####################################################################################

ABSSIMULDIR=RUNNINGDRR+'/TestWorkingGDir/'


staticNewSimuKeys=[]

#helper function for simulation
# use the hashkey as dirname
# gen config file
# copy src code to dir
# return the dir
def genconfigfileforsimulation(linkstru,parentdir):
    hashkey=linkstru.HashValue
    newdir=os.path.join(parentdir,hashkey)
    os.makedirs(newdir)
    configfile=os.path.join(newdir,CONFIGFILE)

    ###
    global staticNewSimuKeys
    if hashkey not in staticNewSimuKeys:   
        staticNewSimuKeys.append(hashkey)
    ###
    
    strHeaderlist=[]
    cfgstr="DimensionOrderTest:3\n"    
    strHeaderlist.append(cfgstr)
    cfgstr="UseTheLink:%s\n"%(linkstru.outPutToLinksDicStr())
    strHeaderlist.append(cfgstr)

    with open(configfile,'w') as f:
        f.writelines(strHeaderlist)
        f.close()
    
    #copy src codes to dir
    #copy the src files from the src orginal dir 
    srcdir=os.path.join(CURRENTDIR,SIMUSRCDir)
    srcMain=os.path.join(srcdir,"SGBDESIntevals.py")
    detMain=os.path.join(newdir,"SGBDESIntevals.py")
    shutil.copy(srcMain,detMain)   
    srclink=os.path.join(srcdir,"linkDelayMdl.py")
    detlink=os.path.join(newdir,"linkDelayMdl.py")
    shutil.copy(srclink,detlink)   

    return newdir

def genDirlistForArraySimu(linkStruArray):
    dirlist=[]
    for linkstru in linkStruArray:
        print("genconfig for key:%s"%(linkstru.HashValue))
        dir=genconfigfileforsimulation(linkstru,ABSSIMULDIR)
        dirlist.append(dir)

    return dirlist
backupresultdir={
    # '5b1aebff09c9ebd486e99d32c393217c':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-16-00/5b1aebff09c9ebd486e99d32c393217c/result.log',
    # '9403eba6d713550a1083d0917b6ac85d':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-16-00/9403eba6d713550a1083d0917b6ac85d/result.log',
    # '710172dcc949a3f5ac9b6c188da28a3c':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-19-56/710172dcc949a3f5ac9b6c188da28a3c/result.log',
    # '72829651a056ac08590bbb7f6b4217fc':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-19-56/72829651a056ac08590bbb7f6b4217fc/result.log',
    # 'ce11745aa3b6bbe0ef297c5ea01e29d3':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-19-56/ce11745aa3b6bbe0ef297c5ea01e29d3/result.log',
    # '1a0ad1a161e6cac68280142803938b42':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-23-51/1a0ad1a161e6cac68280142803938b42/result.log',
    # 'fd5652f9779dafee666a80a72323abaa':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-23-51/fd5652f9779dafee666a80a72323abaa/result.log',
    # 'cce5c03181ca940e8884b98d95cdcc13':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-27-43/cce5c03181ca940e8884b98d95cdcc13/result.log',
    # '15319e1e310525c02bb0834c9a507156':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-31-48/15319e1e310525c02bb0834c9a507156/result.log',
    # '572023b174f7e249a64663ce58002d42':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-31-48/572023b174f7e249a64663ce58002d42/result.log',
    # '707652799b0b7a4acfab1430bae7c5c8':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-31-48/707652799b0b7a4acfab1430bae7c5c8/result.log',
    # 'f856a16bc71cbc3b9c239040ba7e0ed0':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-18-31-48/f856a16bc71cbc3b9c239040ba7e0ed0/result.log',
    # '3a18a74e729bc8bf7cf59ee5a2973e02':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-19-56-30/3a18a74e729bc8bf7cf59ee5a2973e02/result.log',
    # '029841bb6799b40269f54facc76b2182':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-19-56-30/029841bb6799b40269f54facc76b2182/result.log', 
    # 'a90c551bfb8da1ee205654f8d154fb8b':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-20-00-24/a90c551bfb8da1ee205654f8d154fb8b/result.log', 
    # 'e77bb570a5109533318ba3431e1622ff':'/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/cacheDir/2025-01-15-20-00-24/e77bb570a5109533318ba3431e1622ff/result.log', 
}

def saveResult(filepath,Tvalue):
    resultfile=os.path.join(filepath,"result.log")
    with open(resultfile,'w') as f:
        linestringts=[]
        strtoWrite="Percent95Value:%f\n"%(Tvalue)
        linestringts.append(strtoWrite)
        f.writelines(linestringts)
        f.close()

def runSimulationOnDirlist(dirlist):
    threads=[]
    for testcasedir in dirlist:
        pardir,thisdir=os.path.split(testcasedir)

        simOpenDatabase()
        value=checkSimExist(thisdir)
        simCloseDatabase()
        
        if value:
           saveResult(testcasedir,value)
           # time.sleep(2)#otherwise the dirname will be same
        else:
            os.chdir(testcasedir)#change to the test case dir 
            detMain=os.path.join(testcasedir,"SGBDESIntevals.py")
            cmdstr="/usr/bin/python3 %s"%(detMain)
            
            thd=threading.Thread(target=exeCmd,args=(cmdstr,))
            thd.start()
            threads.append(thd)
            time.sleep(1)        
    #wait untill finish
    for thd in threads:
        thd.join()


    os.chdir(CURRENTDIR)#change back to the src dir
    return

def StoreSimuResults(resultdic,LinkStrArray):
    simOpenDatabase()

    for key in resultdic.keys():
        tvalue=resultdic[key]

        for lkstuobj in LinkStrArray:
            if lkstuobj.HashValue==key:
                sortedValue=checkSimExist(key)
                if sortedValue==None:
                    addSimuResultToDB(lkstuobj,tvalue)
                break


    simCommitChanges()
    simCloseDatabase()

def cleantheWorkingDir(dirlist):
    #return #keepthedir for paper data gethering
    for dir in dirlist:
        shutil.rmtree(dir,ignore_errors=True)
    pass

BACKUPRESULTDIR=RUNNINGDRR+"/ResultDataHis/"
#collect dir value and set to db
#if cleardir==1, clean the dir
#   otherwise move to dir with timestr as dir
#   dirlist


#return dic of result hashkey:value
def collectReslutsOnDirlist(dirlist,cleandir=0):
    # collect result from dirs
    arrayResults={}
    for dir in dirlist:
        dirtuple=os.path.split(dir)
        hashkey=dirtuple[1]
        value=collData.getResultValue(dir)
        arrayResults[hashkey]=value
     
    # clearance processing
    # if cleandir:
    #     for dir in dirlist:
    #         os.removedirs(dir)
    # else:
    #     currenttime=datetime.datetime.now()
    #     strTime=currenttime.strftime("%Y-%m-%d-%H-%M-%S")        
    #     destPardir=os.path.join(BACKUPRESULTDIR,strTime)
    #     os.makedirs(destPardir)
    #     for dir in dirlist:            
    #         shutil.move(dir,destPardir)

    return arrayResults

def testloadValutoLinksMap():
    global ValuOrderList
    loadValuToLinkMapDic()
    for value in ValuToLinkMapDic.keys():
        if value not in ValuOrderList:
            ValuOrderList.append(value)
        link=ValuToLinkMapDic[value]
        print("value:%d  link:%s"%(value,link))
    ValuOrderList.sort()
#new links added to ValuToLinkMapDic then update the ValuOrderList
def updateValuToLinkMapDic():
    global ValuOrderList
    ValuOrderList=[]
    for value in ValuToLinkMapDic.keys():
        if value not in ValuOrderList:
            ValuOrderList.append(value)
        link=ValuToLinkMapDic[value]
        #print("value:%d  link:%s"%(value,link))
    ValuOrderList.sort()

#######
#all simulated DB
######


if newSimuDB==0:
    SimuDBFilepath=BACKUPRESULTDIR+'SimuResultsDB.db'
else:
    SimuDBFilepath=BACKUPRESULTDIR+'SimuResultsDB2.db'
simDBconn=None
simDBcusr=None

def simOpenDatabase():
    global simDBconn,simDBcusr
    simDBconn = sqlite3.connect(SimuDBFilepath)
    simDBcusr=simDBconn.cursor()

def simCloseDatabase():
    global simDBconn,simDBcusr
    simDBconn.commit()
    simDBconn.close()
    simDBcusr=None
    simDBconn=None

def simCommitChanges():
    simDBconn.commit()

if newSimuDB==0:
    SIMU012RESULT='sim012resulttb'
else:
    SIMU012RESULT='simPaperresulttb'

IDX_TVALUE=11

def createSimDB():
    simOpenDatabase()
    sql_text_0 = '''CREATE TABLE %s
           (HashKey TEXT PRIMARY KEY NOT NULL,
            ID1 INTEGER,
            ID2 INTEGER,
            ID3 INTEGER,
            ID4 INTEGER,
            ID5 INTEGER,
            ID6 INTEGER,
            ID7 INTEGER,
            ID8 INTEGER,
            ID9 INTEGER,
            ID10 INTEGER,
            TValue REAL
            );'''%(SIMU012RESULT)
    simDBcusr.execute(sql_text_0)
    simCommitChanges()
    simCloseDatabase()
    pass

def addSimuResultToDB(linkStruObj,Tvalue):
    sqltext=f'''INSERT INTO {SIMU012RESULT} (HashKey,ID1,ID2,ID3,ID4,ID5,ID6,ID7,ID8,ID9,ID10,TValue) VALUES ('{linkStruObj.HashValue}',{linkStruObj.IDs[0]},{linkStruObj.IDs[1]},{linkStruObj.IDs[2]},{linkStruObj.IDs[3]},{linkStruObj.IDs[4]},{linkStruObj.IDs[5]},{linkStruObj.IDs[6]},{linkStruObj.IDs[7]},{linkStruObj.IDs[8]},{linkStruObj.IDs[9]},{Tvalue})'''
    print(sqltext)
    result=simDBcusr.execute(sqltext)

def checkSimExist(hashkey):
    sqltext=f'''SELECT * FROM {SIMU012RESULT} WHERE HashKey='{hashkey}' '''
    result=simDBcusr.execute(sqltext)
    trupl=result.fetchone()
    if trupl:
        return trupl[IDX_TVALUE]
    return None
#######
#### get boundarys points statics
#######

def extract_BPdata_from_db():
    # 连接到数据库
    simOpenDatabase()
    # 查询TValue在0.12 ± 0.00005范围内的记录
    query =f'''SELECT ID1, ID2, ID3, ID4, ID5, ID6, ID7, ID8, ID9, ID10 FROM {SIMU012RESULT} WHERE TValue BETWEEN 0.11995 AND 0.12005'''
    simDBcusr.execute(query)
    results = simDBcusr.fetchall()
    
    # 关闭数据库连接
    simCloseDatabase()
    
    # 构建ValuOrderList：从数据库中提取所有唯一的ID值并排序
    all_ids = set()
    for row in results:
        for id_val in row:
            all_ids.add(id_val)
    IDValuOrderList = sorted(list(all_ids))
    
    # 处理数据，将ID1到ID10的值映射到索引
    id_distributions = [[] for _ in range(10)]
    for row in results:
        for i in range(10):
            index = IDValuOrderList.index(row[i])
            id_distributions[i].append(index)
    
    return id_distributions

########

def getkeyofArray():
    ary=[0.011, 0.011, 0.011, 0.011, 0.011]
    keyid=linkIDValue(ary)
    print("keyid:%d :%s"%(keyid,ary))
def moduletest():
    #testonedimension()
    #testValueFunc()
    #testloadValutoLinksMap()
    #testGenD2()
    #testdimension2()
    #createSimDB()
    getkeyofArray()

if __name__=='__main__':moduletest()


