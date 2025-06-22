#!/usr/bin/python3
import pathsSeqGen as pthG
import sortlinklist as sorLL
import math,time
import BorderPointDB as BPDB
import BPDBCreate as DBCT

TCUPPER_VALUE=0.12005
INFINITYLKVALUE=4860
LINKMAXVALUESETING=466
IDTAILINIFITY=99999999999999

def buildlinkStrufromPrefixTail(prefix,tail):
    linkdic={}
    id=0
    for preValu in prefix:
        id+=1
        key='F%d'%(id)
        link=pthG.ValuToLinkMapDic[preValu]
        linkdic[key]=link
    for tailValu in tail:
        id+=1
        key='F%d'%(id)
        link=pthG.ValuToLinkMapDic[tailValu]
        linkdic[key]=link
    #print("linkdic:%s"%(str(linkdic)))
    linkstru=sorLL.linkArryStru(linkdic)
    
    return linkstru



staticRound=0

#output array Values, same order as LinkStrArray
def getSimuResultsForLinkStrArray(LinkStrArray):
    global staticRound
    print("#get simu Round # %d"%(staticRound))
    staticRound+=1

    dirlist=pthG.genDirlistForArraySimu(LinkStrArray)
    #run simulation
        #for the list, each linkstru make a dir, make a config file for each dir.
        #          copy simualtion code to dir, and record all the dirs
        #run simulation for those dirs
    pthG.runSimulationOnDirlist(dirlist)#wait untill got results
    #collect results
    resultdic=pthG.collectReslutsOnDirlist(dirlist)
    #store to simulation DB
    pthG.StoreSimuResults(resultdic,LinkStrArray)

    #clen the dir
    pthG.cleantheWorkingDir(dirlist)

    resultArray=[]
    for linkStr in LinkStrArray:
        resulValue=resultdic[linkStr.HashValue]
        resultArray.append(resulValue)
    return resultArray

# lklst make different
# return  diffobjlist,  dic: idx:objlistidx
def lkstruDiffIdxGen(lklst):
    hashkeyidx={}
    idx=0
    diffObjlist=[]
    newlisthashkeydix={}
    for lkobj in lklst:
        if lkobj.HashValue not in hashkeyidx.keys():
            hashkeyidx[lkobj.HashValue]=idx
            diffObjlist.append(lkobj)
            newlisthashkeydix[lkobj.HashValue]=len(diffObjlist)-1
        idx+=1
    orglistidxdic={}
    for idx in range(len(lklst)):
        lkobj=lklst[idx]
        hashkey=lkobj.HashValue
        orglistidxdic[idx]=newlisthashkeydix[hashkey]

    return diffObjlist, orglistidxdic



def getRepeatableObjsTailsArray(objlist):
    tails=[]
    for obj in objlist:
        tail=[obj.IDs[5],obj.IDs[6],obj.IDs[7],obj.IDs[8],obj.IDs[9]]
        tails.append(tail)
    return tails


    
#find the next SHFT tails to check, at once   
#currentTail is the last check failed FT
#return the next more flat tails
def getNxtSHFTTailsTocheck(currentFaitTail,orginalTail):

    print("geNxtTails curtail:%s orgtail:%s"%(currentFaitTail,orginalTail))
    
    #find the next possible flatten step
    thenextStep=0
    semisetp=0
    for hop in range(len(currentFaitTail)-2,0,-1):
        hopValue=currentFaitTail[hop]
        nextHopValue=currentFaitTail[hop+1]
        if hopValue>=INFINITYLKVALUE:
            nexValue=INFINITYLKVALUE
        else:
            nexValue=pthG.getNextValue(hopValue)
        print("hop:%d, hopValue:%d nextHopvalue:%d nextvalue:%d"%(hop,hopValue,nextHopValue,nexValue))
        
        if nexValue==nextHopValue:
            semisetp=hop
        if nexValue<nextHopValue:
            thenextStep=hop
            break
    orgTopStep=0
    orgTopNextValue=0
    orgTopValue=0
    for hop in range(len(orginalTail)-2,0,-1):
        orgTopValue=orginalTail[hop]
        orgTopNextValue=orginalTail[hop+1]
        if orgTopValue>=INFINITYLKVALUE:
            continue
        
        print("orghop:%d, orgTopValue:%d orgTopNextValue:%d"%(hop,orgTopValue,orgTopNextValue))
        
        if orgTopValue<orgTopNextValue and orgTopNextValue<INFINITYLKVALUE:
            orgTopStep=hop
            break

    orgTopBegin=0
    for hop in range(len(orginalTail)):
        if orginalTail[hop] ==orgTopValue:
            orgTopBegin=hop
            break


    print("semihop:%d thenextStep:%d nexValue:%d nextvalue:%d"%(semisetp,thenextStep,nexValue,pthG.getPreviousValue(currentFaitTail[thenextStep+1])))
    print("orgTopStep:%d orgTopValue:%d orgTopNextValue:%d"%(orgTopStep,orgTopValue,orgTopNextValue))
    #increase one setp
    if thenextStep>0:
        #found
        rttails=[]
        tailrt=currentFaitTail.copy()
        nextValue=pthG.getPreviousValue(currentFaitTail[thenextStep+1])
        for idx in range(thenextStep,len(currentFaitTail)):
            tailrt[idx]=nextValue
        tailrt.sort()
        if thenextStep<2:
            tailrt[4]=currentFaitTail[thenextStep+1]
            if thenextStep<2:
                tailrt[3]=currentFaitTail[thenextStep+1]
        #else:
            tailrt[thenextStep]=currentFaitTail[thenextStep]
        tailrt.sort()
        rttails.append(tailrt)
        print("tailrt0:%s"%(tailrt))
        
        if nexValue<nextValue:
            tailrt1=tailrt.copy()
            tailrt1[thenextStep]=nexValue  
            #tailrt1[thenextStep]=currentFaitTail[thenextStep]
            tailrt1.sort()
            print("tailrt1:%s"%(tailrt1))
            rttails.append(tailrt1)

        if orgTopNextValue>nextValue:
            tailrt2=currentFaitTail.copy()
            if nexValue<nextValue:
                for idx in range(thenextStep,len(currentFaitTail)):
                    tailrt2[idx]=nexValue
            else:
                tailrt2=tailrt.copy()
            
            for idx in range(orgTopStep+1,len(currentFaitTail)):
                tailrt2[idx]=orgTopNextValue            
            print("tailrt2:%s"%(tailrt2))
            tailrt2.sort()
            rttails.append(tailrt2)

        if orgTopValue>nextValue:
            tailrt3=currentFaitTail.copy()
            if nexValue<nextValue:
                for idx in range(orgTopBegin,len(currentFaitTail)):
                    tailrt3[idx]=orgTopValue
            else:
                tailrt3=tailrt.copy()
            tailrt3[4]=orgTopNextValue
            print("tailrt3:%s"%(tailrt3))
            tailrt3.sort()
            rttails.append(tailrt3)
        return rttails
    elif orginalTail[4]<=466:
        rttails=[]
        addedvalue=pthG.getNextValue(currentFaitTail[semisetp])
        #orgLastValue=orginalTail[4]
        #orgfirstValue=orginalTail[0]

        orgValueArray=[]
        #value=orgfirstValue
        for value in orginalTail:
            if value>addedvalue and (value not in orgValueArray):
                orgValueArray.append(value)
            #value=pthG.getNextValue(value)
        idx=0
        tailrt=currentFaitTail.copy()
        for value in orgValueArray:
            if idx==0:
                #only first value change
                setValue=pthG.getPreviousValue(value)
            else:
                setValue=value   

            thenextStep=orginalTail.index(value)
            for idx in range(thenextStep+1,len(currentFaitTail)):
                tailrt[idx]=setValue
            ###
            idx+=1

        if idx>0:
            tailrt.sort()
            print("tailrt:%s"%(tailrt))
            rttails.append(tailrt)
            return rttails
        
    return None

# the tail[4] bigger the better
def sortTailbyID10(tail):
    id9=tail[4]
    # id9=0
    # if tail[4]==INFINITYLKVALUE:
    #     id9=0
    # else:
    #     id9=tail[4]
    
    id8=0
    if tail[3]==INFINITYLKVALUE:
        id8=0
    else:
        id8=tail[3]
    
    id7=0
    if tail[2]==INFINITYLKVALUE:
        id7=0
    else:
        id7=tail[2]

    #id6=tail[1]
    id6=0
    if tail[1]==INFINITYLKVALUE:
        id6=0
    else:
        id6=tail[1]

    return -(id9*16*16*16+id8*16*16+id7*16+id6)


#all tail to check
def getAllSHFTSteps(FirstFaitTail,orginalTail):
    tails=[]
    tails.append(FirstFaitTail)
    tailAry=getNxtSHFTTailsTocheck(FirstFaitTail,orginalTail)
    while(tailAry):
        newAry=[]
        for tail in tailAry:
            if tail not in tails:
                tails.append(tail)
                tailAryA=getNxtSHFTTailsTocheck(tail,orginalTail)
                if tailAryA:
                    for newtail in tailAryA:
                        if newtail not in newAry:
                            newAry.extend(tailAryA)

        if len(tails)>4:
            break 
        tailAry=newAry   

    #sort tails with the [4] biggest first
    tails.sort(key=sortTailbyID10)       
        
    return tails

#Nobj may duplicate in list
#this func to avoid duplicate obj in list and keep obj' idx consistent
def appendAndFindIdx(objlist,Nobj):
    idx=0
    ridx=-1
    for obj in objlist:
        if obj.HashValue==Nobj.HashValue:
            ridx=idx
            break
        idx+=1
    if ridx<0:
        objlist.append(Nobj)
        ridx=len(objlist)-1
    return ridx

#tail in tails have no inifity link
def verifiedFiniteTailsBorder(prefix,tails):
    nexttailsDic={}#idx same as tails :nexttail
    for idx in range(len(tails)):
        nexttail=getNextTail(tails[idx])
        nexttailsDic[idx]=nexttail
    objlist=[]

    resultOrgIdxDic={}#idx:resultsarrayidx 
    resultNextIdxDic={}#idx: resultsarrayidx 
    taillist=[]
    for keyidx in nexttailsDic.keys():
        obj=buildlinkStrufromPrefixTail(prefix,tails[keyidx])
        oidx=appendAndFindIdx(objlist,obj)
        tail=tails[keyidx]
        if tail not in taillist:
            taillist.append(tail)
        resultOrgIdxDic[keyidx]=oidx
        nobj=buildlinkStrufromPrefixTail(prefix,nexttailsDic[keyidx])
        nidx=appendAndFindIdx(objlist,nobj)
        tail=nexttailsDic[keyidx]
        if tail not in taillist:
            taillist.append(tail)
        resultNextIdxDic[keyidx]=nidx
    
    return objlist, resultOrgIdxDic, resultNextIdxDic, taillist




def cleanTailsofOnePrefix(newtails):
    #clean the tail with overlap
    cleanedTails=[]
    for tail in newtails:
        AlldimSamller=0
        for cktail in newtails:
            if cktail!=tail:
                clean=0
                for idx in range(len(cktail)):
                    if tail[idx]>cktail[idx]:
                        clean=1
                        break
                if clean==0:
                    AlldimSamller=1
                    break
        print("tail:%s  key:%d cleared:%d"%(tail,BPDB.tailMetric(tail),AlldimSamller))
        if AlldimSamller==0:
            cleanedTails.append(tail)  
    return cleanedTails  


###for finding tails of a prefix from 0 knowledge
class tailState:
    def __init__(self,tailValue):
        self.IDValue=tailValue
        self.checkedByNextSFHT=0 # 0, not checked; 1 checked already; 2:the next to check value already been created. 
        self.BorderConfirmed=0 # 0 ,not ; 1 yes
        self.TCCheckedReslt=2 # 0 math border ,1 bigger than smaller, -1 maybe smaller than border，-2 thebiggerTail is smaller
        self.InBorderShadow=0 # no need to check in current borders points Shadows
        self.TailSharpNess=0 # sortby this value as the next best check tail
        self.smallerTailV=0
        self.biggerTailV=0
        pass

class tailsManager:

    def __init__(self,prefix):
        self.previxValue=BPDB.prefixMetric(prefix)
        self.prefixArray=prefix
        self.tailsBASE={}#tailValue:tailarray
        self.tailsState={}#tailValue:State
        pass

    #get commit time of tail
    # prefix + tail should have been simulated
    def getTc(self,tail):
        obj=buildlinkStrufromPrefixTail(self.prefixArray,tail)
        pthG.simOpenDatabase()
        Tvalue=pthG.checkSimExist(obj.HashValue)
        pthG.simCloseDatabase()
        if Tvalue:
            self.setTailCheckResult(tail,Tvalue)
        else:
            print("Error!! tail %s is not been simulated!"%(tail))        

    def addnewtail(self,tail):
        tail.sort()
        TailValue=BPDB.tailMetric(tail)
        #print("add tailValue:%d tail:%s"%(TailValue,tail))
        if TailValue not in self.tailsBASE.keys():            
            self.tailsBASE[TailValue]=tail
            state=tailState(TailValue)
            state.TailSharpNess=sortTailbyID10(tail)
            self.tailsState[TailValue]=state
            return 1
        return 0

    def addTestedTail(self,tail):
        tail.sort()
        self.addnewtail(tail)        
        self.getTc(tail)

    def getTailTCCState(self,tail):
        tail.sort()
        tValue=BPDB.tailMetric(tail)
        state=self.tailsState[tValue]
        return state.TCCheckedReslt        

    def addBDtail(self,tail):
        tail.sort()
        nexttail=getNextTail(tail,0)
        self.addnewtail(tail)
        self.addnewtail(nexttail)
        self.setBiggerNeighbro(tail,nexttail)
        self.getTc(tail)
        self.getTc(nexttail)

    def dumpTailSates(self,tails):
        for tail in tails:
            tail.sort()
            tValue=BPDB.tailMetric(tail)
            state=self.tailsState[tValue]
            print("[%d] TCCK:%d BDCK:%d CHSHFT:%d SHDOW:%d"%(tValue,state.TCCheckedReslt,state.BorderConfirmed,state.checkedByNextSFHT,state.InBorderShadow))


    def setResultsBatch(self,tails,resutls):
        idx=0
        for tail in tails:
            print("tailidx:%d %s result:%f"%(idx,tail,resutls[idx]))
            self.setTailCheckResult(tail,resutls[idx])
            idx+=1
    
    def setBorderFlag(self,tail):
        tID=BPDB.tailMetric(tail)
        state=self.tailsState[tID]
        state.BorderConfirmed=1
        state.TCCheckedReslt=0

    def setTailCheckResult(self,tail,Tvalue):
        tail.sort()
        TailValue=BPDB.tailMetric(tail)
        mystate=self.tailsState[TailValue]
        if mystate.TCCheckedReslt==2:
            #first time set
            if Tvalue<TCUPPER_VALUE:                
                mystate.TCCheckedReslt=-1
            else:
                mystate.TCCheckedReslt=1  
            #if some bigger Tail linked to this tail          
            if mystate.biggerTailV:
                thepeerState=self.tailsState[mystate.biggerTailV]
                #this tail must have been set value
                if Tvalue<TCUPPER_VALUE:
                    if thepeerState.TCCheckedReslt==1:
                         mystate.TCCheckedReslt=0
                         mystate.BorderConfirmed=1
                    elif thepeerState.TCCheckedReslt==-1:
                        mystate.TCCheckedReslt=-2
                else:
                    # if thepeerState.TCCheckedReslt==1:
                    #      mystate.TCCheckedReslt=0
                    #      mystate.BorderConfirmed=1
                    # el
                    if thepeerState.TCCheckedReslt==-1:
                        mystate.TCCheckedReslt=1
                        thepeerState.BorderConfirmed=1
            if mystate.smallerTailV:
                thepeerState=self.tailsState[mystate.smallerTailV]
                if Tvalue<TCUPPER_VALUE:
                    # if thepeerState.TCCheckedReslt==1:
                    #      mystate.TCCheckedReslt=0
                    #      mystate.BorderConfirmed=1
                    # el
                    if thepeerState.TCCheckedReslt==-1:
                        thepeerState.TCCheckedReslt=-2#nopossible to check border
                else:
                    if thepeerState.TCCheckedReslt==-1:
                        thepeerState.TCCheckedReslt=0
                        thepeerState.BorderConfirmed=1
                        if thepeerState.smallerTailV:
                            nextpeeerState=self.tailsState[thepeerState.smallerTailV]
                            nextpeeerState.TCCheckedReslt=-2#nopossible to check border
    
    def wrapperGetSimuResultWithRepeatableObjs(self,objlist):

        distiincobjlist,orglistidxmap=lkstruDiffIdxGen(objlist)

        checknessaryList=[]
        tochecktails=[]
        for tryobj in distiincobjlist:
            tail=[tryobj.IDs[5],tryobj.IDs[6],tryobj.IDs[7],tryobj.IDs[8],tryobj.IDs[9]]
            tochecktails.append(tail)
        checknessaryList=self.filterTailCandidates(tochecktails)
        nessidxdic={}
        idx=0
        for tail in tochecktails:
            if tail in checknessaryList:
                nessidxdic[idx]=checknessaryList.index(tail)
            else:
                nessidxdic[idx]=-1 
            idx+=1

        realtryobjlist=[]
        for tail in checknessaryList:
            obj=buildlinkStrufromPrefixTail(self.prefixArray,tail)
            realtryobjlist.append(obj)
        realtryresult=getSimuResultsForLinkStrArray(realtryobjlist)

        distresultlist=[]
        for idx in range(len(tochecktails)):
            if nessidxdic[idx]>=0:
                result=realtryresult[nessidxdic[idx]]            
            else:
                result=TCUPPER_VALUE+0.0088 
            distresultlist.append(result)

        #distresultlist=getSimuResultsForLinkStrArray(distiincobjlist)
        resultlist=[]
        for idx in orglistidxmap.keys():
            objidx=orglistidxmap[idx]
            resulValue=distresultlist[objidx]
            resultlist.append(resulValue)
        return resultlist
    
    
    
    #the Tail is the current value to check, and we know prefixary+Tail < TCUPPER_VALUE
    # tailTopValue is the largest possible value of the Tail[tailhops]
    # the value should just checked in tailhops
    def getbestTail(self,Tail,tailhops,tailTopValue):
        if tailhops>4:
            tailhops=4
        BValue=Tail[tailhops]
        EValue=tailTopValue
        searchtable=[]
        nValue=BValue
        while nValue<=EValue:
            searchtable.append(nValue)
            nValue=pthG.getNextValue(nValue)
        Bidx=0# not checked yet, with  Infinity ending
        Bidx1=1
        Bidx2=2
        Eidx=len(searchtable)
        print("Eidx:%d"%(Eidx))
        if Eidx==1:
            midtryArry=[]
            big0Value=searchtable[Bidx]
            #big1Value=searchtable[Bidx1]
            big0Tail=Tail.copy()
            big0Tail[tailhops]=big0Value
            #big1Tail=Tail.copy()
            #big1Tail[tailhops]=big1Value
            for idx in range(tailhops+1,len(Tail)):
                big0Tail[idx]=INFINITYLKVALUE
                #big1Tail[idx]=INFINITYLKVALUE
            print("check1 tail:%s"%(big0Tail))
            big0obj=buildlinkStrufromPrefixTail(self.prefixArray,big0Tail)
            #big1obj=buildlinkStrufromPrefixTail(prefixAry,big1Tail)
            midtryArry.append(big0obj)
            #midtryArry.append(big1obj)
            midreslt=getSimuResultsForLinkStrArray(midtryArry)
            if midreslt[0]<TCUPPER_VALUE:
                return big0Tail
            return None
        elif Eidx==2:
            midtryArry=[]
            big0Value=searchtable[Bidx]
            big1Value=searchtable[Bidx1]
            big0Tail=Tail.copy()
            big0Tail[tailhops]=big0Value
            big1Tail=Tail.copy()
            big1Tail[tailhops]=big1Value
            for idx in range(tailhops+1,len(Tail)):
                big0Tail[idx]=INFINITYLKVALUE
                big1Tail[idx]=INFINITYLKVALUE
            print("check2-1 tail:%s"%(big0Tail))
            print("check2-1 tail:%s"%(big1Tail))
            big0obj=buildlinkStrufromPrefixTail(self.prefixArray,big0Tail)
            big1obj=buildlinkStrufromPrefixTail(self.prefixArray,big1Tail)
            midtryArry.append(big0obj)
            midtryArry.append(big1obj)
            midreslt=getSimuResultsForLinkStrArray(midtryArry)
            if midreslt[1]<TCUPPER_VALUE:
                return big1Tail
            if midreslt[0]<TCUPPER_VALUE:
                return big0Tail
            return None
        elif Eidx==0:
            return None


        while(Eidx-Bidx>1):
            #
            midtryArry=[]
            if (Eidx-Bidx)>=3:
                #check Bidx increase
                big0Value=searchtable[Bidx]
                big1Value=searchtable[Bidx1]
                big2Value=searchtable[Bidx2]
                big0Tail=Tail.copy()
                big0Tail[tailhops]=big0Value
                big1Tail=Tail.copy()
                big1Tail[tailhops]=big1Value
                big2Tail=Tail.copy()
                big2Tail[tailhops]=big2Value
                for idx in range(tailhops+1,len(Tail)):
                    big0Tail[idx]=INFINITYLKVALUE
                    big1Tail[idx]=INFINITYLKVALUE
                    big2Tail[idx]=INFINITYLKVALUE
                print("check3-1 tail:%s"%(big0Tail))
                print("check3-2 tail:%s"%(big1Tail))
                print("check3-3 tail:%s"%(big2Tail))
                big0obj=buildlinkStrufromPrefixTail(self.prefixArray,big0Tail)
                big1obj=buildlinkStrufromPrefixTail(self.prefixArray,big1Tail)
                big2obj=buildlinkStrufromPrefixTail(self.prefixArray,big2Tail)
                midtryArry.append(big0obj)
                midtryArry.append(big1obj)
                midtryArry.append(big2obj)
            elif(Eidx-Bidx)==1:
                midtryArry=[]
                big0Value=searchtable[Bidx]
                #big1Value=searchtable[Bidx1]
                big0Tail=Tail.copy()
                big0Tail[tailhops]=big0Value
                #big1Tail=Tail.copy()
                #big1Tail[tailhops]=big1Value
                for idx in range(tailhops+1,len(Tail)):
                    big0Tail[idx]=INFINITYLKVALUE
                    #big1Tail[idx]=INFINITYLKVALUE
                print("check3-1-1 tail:%s"%(big0Tail))
                big0obj=buildlinkStrufromPrefixTail(self.prefixArray,big0Tail)
                #big1obj=buildlinkStrufromPrefixTail(prefixAry,big1Tail)
                midtryArry.append(big0obj)
                #midtryArry.append(big1obj)
                midreslt=getSimuResultsForLinkStrArray(midtryArry)
                if midreslt[0]<TCUPPER_VALUE:
                    return big0Tail
                return None
            elif (Eidx-Bidx)==2:
                midtryArry=[]
                big0Value=searchtable[Bidx]
                big1Value=searchtable[Bidx1]
                big0Tail=Tail.copy()
                big0Tail[tailhops]=big0Value
                big1Tail=Tail.copy()
                big1Tail[tailhops]=big1Value
                for idx in range(tailhops+1,len(Tail)):
                    big0Tail[idx]=INFINITYLKVALUE
                    big1Tail[idx]=INFINITYLKVALUE
                print("check3-2-1 tail:%s"%(big0Tail))
                print("check3-2-2 tail:%s"%(big1Tail))
                big0obj=buildlinkStrufromPrefixTail(self.prefixArray,big0Tail)
                big1obj=buildlinkStrufromPrefixTail(self.prefixArray,big1Tail)
                midtryArry.append(big0obj)
                midtryArry.append(big1obj)
                midreslt=getSimuResultsForLinkStrArray(midtryArry)
                if midreslt[1]<TCUPPER_VALUE:
                    return big1Tail
                if midreslt[0]<TCUPPER_VALUE:
                    return big0Tail
                return None


            mid=math.floor((Bidx+Eidx)/2)
            if mid<=Bidx2:
                mid=Bidx2+1
            #check mid value
            if mid < Eidx:
                print("mid:%d Eidx:%d"%(mid,Eidx))
                midValue=searchtable[mid]
                tail=Tail.copy()
                tail[tailhops]=midValue
                for idx in range(tailhops+1,len(Tail)):
                    tail[idx]=INFINITYLKVALUE
                print("check3-4 tail:%s"%(tail))
                midlkDic=buildlinkStrufromPrefixTail(self.prefixArray,tail)
                midtryArry.append(midlkDic) 

            last=Eidx-1
            if last>mid:
                ##check if already runned before
                ckobj=midtryArry[-1]
                value=None
                if ckobj:
                    pthG.simOpenDatabase()
                    value=pthG.checkSimExist(ckobj.HashValue)
                    pthG.simCloseDatabase()
                if value==None or value<TCUPPER_VALUE:#not build before or <Tc
                ###
                    lastValue=searchtable[last]
                    tail=Tail.copy()
                    tail[tailhops]=lastValue
                    for idx in range(tailhops+1,len(Tail)):
                        tail[idx]=INFINITYLKVALUE
                    print("check3-5 tail:%s"%(tail))
                    midlkDic=buildlinkStrufromPrefixTail(self.prefixArray,tail)
                    midtryArry.append(midlkDic) 
                else:
                    last=mid #disable last check

            #midreslt=getSimuResultsForLinkStrArray(midtryArry)
            midreslt=self.wrapperGetSimuResultWithRepeatableObjs(midtryArry)
            tailsarray=getRepeatableObjsTailsArray(midtryArry)
            for tail in tailsarray:
                self.addnewtail(tail)
            self.setResultsBatch(tailsarray,midreslt)
            
            print("results:%s Eidx:%d Bidx:%d mid:%d last:%d Bidx1:%d Bidx2:%d"%(midreslt,Eidx,Bidx,mid,last,Bidx1,Bidx2))
            if Eidx>=3:
                
                #if first find some >TC Bidx stop
                if midreslt[0]<TCUPPER_VALUE:
                    Bidx=Bidx
                if (Eidx-Bidx)>1 and midreslt[1]<TCUPPER_VALUE:
                    Bidx=Bidx1
                if (Eidx-Bidx)>2 and midreslt[2]<TCUPPER_VALUE:
                    Bidx=Bidx2
                if (Eidx-Bidx)>3 and midreslt[3]<TCUPPER_VALUE:
                    Bidx=mid
                    
                #if midreslt[Eidx-1]<TCUPPER_VALUE:
                #    Bidx=Eidx-1
                
                #from the last to the first, which idx is > TC, set to Eidx
                if  (Eidx-Bidx)>3 and midreslt[3]>TCUPPER_VALUE:
                    Eidx=mid
                if (Eidx-Bidx)>2 and midreslt[2]>TCUPPER_VALUE:
                    Eidx=Bidx2
                if (Eidx-Bidx)>1 and midreslt[1]>TCUPPER_VALUE:
                    Eidx=Bidx1
                if midreslt[0]>TCUPPER_VALUE:
                    Eidx=Bidx
                
                
                if last>mid:
                    if midreslt[-1]<TCUPPER_VALUE and Bidx<Eidx:
                        Bidx=last
                        break
                    if Eidx>last:
                        Eidx=last
                print("Eidx:%d Bidx:%d last:%d"%(Eidx,Bidx,last))
            else:            
                if midreslt[0]>TCUPPER_VALUE:
                    Eidx=mid
                else:
                    Bidx=mid

            Bidx1=Bidx+1
            Bidx2=Bidx+2

            print("newround: Bidx:%d Bidx1:%d Bidx2:%d Eidx:%d"%(Bidx,Bidx1,Bidx2,Eidx))
        #result is Bidx
        print("Finally: Bidx:%d Bidx1:%d Bidx2:%d Eidx:%d searchTable:%s"%(Bidx,Bidx1,Bidx2,Eidx,searchtable))
        rettail=Tail.copy()   

        rettail[tailhops]=searchtable[Bidx]
        for idx in range(tailhops+1,len(Tail)):
            rettail[idx]=INFINITYLKVALUE
        print("tailhops:%d returned tail:%s"%(tailhops,rettail))
        return rettail
    # return the borderpoint tail
    #  if exist new tail, return that tail with heading same as tail but value in tailidx different
    #  if not exsit, return none
    #  use the improved tail of index tails as the tail.
    #  the tailidx is the last not INIFITY index 
    def checktail(self,tail,endValue): 
        tailidx=0
        for idx in range(len(tail)):
            if tail[idx]<INFINITYLKVALUE:
                tailidx=idx
            else:
                break
        newtail=self.getbestTail(tail,tailidx,endValue)
        return newtail

    def setCheckbySHFT(self,tail):
        tail.sort()
        TailValue=BPDB.tailMetric(tail)
        mystate=self.tailsState[TailValue]
        mystate.checkedByNextSFHT=1
    #
    #tail values in the same link is compariable
    def findBiggerLinkNext(self,headlV,toBtailV):
        if headlV>=toBtailV:
            print("error for value")
            return -1
        
        HeadState=self.tailsState[headlV]
        #newState=self.tailsState[toBtailV]
        if HeadState.biggerTailV==0:
            #first to add
            return headlV
            #newState.smallerTailV=headlV
            #HeadState.biggerTailV=toBtailV
        else:
            #find the pos
            nxtHValue=headlV
            nxtHState=HeadState
            #find the nxtSValue as new header 
            while  toBtailV>nxtHValue:
                nxtTailValue=nxtHState.biggerTailV
                print("curHValue:%d nxtTail:%d"%(nxtHValue,nxtTailValue))                
                nxtTailState=self.tailsState[nxtTailValue]
                if nxtTailState.biggerTailV==0:
                    break
                if toBtailV<nxtTailValue:
                    #find the pos
                    return nxtHValue
                
                nxtHValue=nxtTailValue
                nxtHState=nxtTailState
                
            
            return nxtHValue

    def insertBiggerLink(self,headlV,toBtailV):
        if headlV>=toBtailV:
            print("Error value %d >= %d"%(headlV,toBtailV))
            return -1
        HeadState=self.tailsState[headlV]
        newState=self.tailsState[toBtailV]
        if HeadState.biggerTailV==0:
            #first to add
            newState.smallerTailV=headlV
            HeadState.biggerTailV=toBtailV
        else:
            nextnextTailV=HeadState.biggerTailV
            nextNextTailState=self.tailsState[nextnextTailV]
            newState.smallerTailV=headlV
            HeadState.biggerTailV=toBtailV

            nextNextTailState.smallerTailV=toBtailV
            newState.biggerTailV=nextnextTailV
        return
    
    def findSmallerLinkNext(self,headlV,toStailV):
        if headlV<=toStailV:
            print("Error value")
            return -1
        
        HeadState=self.tailsState[headlV]
        #newState=self.tailsState[toStailV]
        if HeadState.smallerTailV==0:
            #first to add
            return headlV
            #newState.smallerTailV=headlV
            #HeadState.biggerTailV=toBtailV
        else:
            #find the pos
            nxtHValue=headlV
            nxtHState=HeadState
            #find the nxtSValue as new header 
            while  toStailV<nxtHValue:
                nxtTailValue=nxtHState.smallerTailV
                nxtTailState=self.tailsState[nxtTailValue]
                if nxtTailState.smallerTailV==0:
                    break
                if toStailV>nxtTailValue:
                    #find the pos
                    return nxtHValue
                nxtHValue=nxtTailValue
                nxtHState=nxtTailState
            return nxtHValue
                
    def insertSmallerLink(self,headlV,toStailV):
        HeadState=self.tailsState[headlV]
        newState=self.tailsState[toStailV]
        if HeadState.smallerTailV==0:
            #first to add
            newState.biggerTailV=headlV
            HeadState.smallerTailV=toStailV
        else:
            nextnextTailV=HeadState.smallerTailV
            nextNextTailState=self.tailsState[HeadState.smallerTailV]
            newState.biggerTailV=headlV
            HeadState.smallerTailV=toStailV

            nextNextTailState.biggerTailV=toStailV
            newState.smallerTailV=nextnextTailV
        return
    
    def debugPrintBiggerlinks(self,Headv):
        strPint='Head:[%d]<=<'%(Headv)
        headState=self.tailsState[Headv]
        nextV=headState.biggerTailV
        addstr="[%d]<=<"%(nextV)
        strPint=strPint+addstr
        while nextV>0:
            nextState=self.tailsState[nextV]
            nextV=nextState.biggerTailV
            addstr="[%d]<=<"%(nextV)
            strPint=strPint+addstr
            if nextV==Headv:
                strPint=strPint+"Loop"
                break
        print(strPint)

    def debugPrintSmallerlinks(self,Headv):
        strPint='Head:[%d]>=>'%(Headv)
        headState=self.tailsState[Headv]
        nextV=headState.smallerTailV
        addstr="[%d]>=>"%(nextV)
        strPint=strPint+addstr
        while nextV>0:
            nextState=self.tailsState[nextV]
            nextV=nextState.smallerTailV
            addstr="[%d]>=>"%(nextV)
            strPint=strPint+addstr
            if nextV==Headv:
                strPint=strPint+"Loop"
                break
        print(strPint)
    
    # theBTail,tail already added to this manager
    def setBiggerNeighbro(self,tail,theBTail):
        tail.sort()
        theBTail.sort()
        if theBTail[4]<tail[4]:
            print("tail last error")
            return -1
        
        headV=BPDB.tailMetric(tail)
        toBtV=BPDB.tailMetric(theBTail)

        toBState=self.tailsState[toBtV]
        if toBState.smallerTailV>0:
            print("tail [%d] already added to some head"%(toBtV))
            return -2
        #bilink chain manuplicate 
        nextV=self.findBiggerLinkNext(headV,toBtV)  

        #print("[%d]%d <=< %d"%(headV,nextV,toBtV))      
        self.insertBiggerLink(nextV,toBtV)
        #self.debugPrintBiggerlinks(headV)
        

    def setSmallerNeighbro(self,tail,theSTail):
        tail.sort()
        theSTail.sort()
        if theSTail[4]>tail[4]:
            return -1
        headV=BPDB.tailMetric(tail)
        toStV=BPDB.tailMetric(theSTail)
        #bilink chain manuplicate 
        nextV=self.findSmallerLinkNext(headV,toStV)
        self.insertSmallerLink(nextV,toStV)
        self.debugPrintSmallerlinks(headV)

    def getBestSHFTTail(self):
        bestail=None
        candidates=[]
        for key in self.tailsState.keys():
            state=self.tailsState[key]
            thetail=self.tailsBASE[key]
            #print("[%d]TCCK:%d ShaDow:%d CKSFHT:%d"%(key, state.TCCheckedReslt,state.InBorderShadow,state.checkedByNextSFHT))
            if (state.TCCheckedReslt==0 or state.TCCheckedReslt==-1) and state.InBorderShadow==0 and state.checkedByNextSFHT==0:# and thetail[4]<INFINITYLKVALUE:
                candidates.append(state)
        print("numCand:%d"%len(candidates))
        bestValue=0
        bestID=0
        for state in candidates:
            if state.TailSharpNess<bestValue:
                bestValue=state.TailSharpNess
                bestID=state.IDValue
        if bestID>0:
            bestail=self.tailsBASE[bestID]
            bestState=self.tailsState[bestID]
            bestState.checkedByNextSFHT=1
            steps=improvableTailsSteps(bestail)
            if steps==0:
                print("flappest already!!")
                return None
            else:
                print("improveable Steps:%d"%(steps))
        return bestail
    
    def getAllBPTails(self):
        alltails=[]
        candidates=[]
        for key in self.tailsState.keys():
            state=self.tailsState[key]
            if (state.TCCheckedReslt==0 or state.TCCheckedReslt==-1) and state.InBorderShadow==0:
                candidates.append(state)
        for state in candidates:
            tail=self.tailsBASE[state.IDValue]
            alltails.append(tail)
            
        tails=cleanTailsofOnePrefix(alltails)

        for tail in alltails:
            if tail not in tails:
                tValue=BPDB.tailMetric(tail)
                theState=self.tailsState[tValue]
                theState.InBorderShadow=1

        return tails
    
    ##app logic
    def getAllTailsOfPrefix(self):

        #for last finity tail send to getMoreTails
        nextchecktail=None

        firstTail=self.findFirstBPTailOfPrefixFHST()
        print("first Tail:%s"%(str(firstTail)))
        nextail,firstValid,nextslopsearch=self.nextTailsWithInifity(firstTail)
        print("nextTail:%s, firstvalid:%d  lastsposSch:%d"%(nextail,firstValid,nextslopsearch))
        while(nextail and  nextail[4]>=INFINITYLKVALUE):
            if firstValid==0:
                firstTail=nextail
                #allTails.append(firstTail)
                self.addBDtail(firstTail)
                nextchecktail=firstTail
                nextail,firstValid,nextslopsearch=self.nextTailsWithInifity(firstTail)
                if nextail and BPDB.tailMetric(nextail)==BPDB.tailMetric(firstTail):
                    break
                print("nextTail1:%s, firstvalid:%d  lastsposSch:%d"%(nextail,firstValid,nextslopsearch))
            elif nextslopsearch:
                #allTails.append(firstTail)
                self.addBDtail(firstTail)
                nextchecktail=firstTail
                if nextail:
                    #allTails.append(nextail)
                    self.addBDtail(nextail)
                    firstTail=nextail
                    nextchecktail=firstTail
                    nextail,firstValid,nextslopsearch=self.nextTailsWithInifity(firstTail)
                    if nextail and BPDB.tailMetric(nextail)==BPDB.tailMetric(firstTail):
                        break
                    print("nextTail2:%s, firstvalid:%d  lastsposSch:%d"%(nextail,firstValid,nextslopsearch))
        print("from nextchecktail:%s, call getMoreTails"%(nextchecktail))
        rttails=self.getMoreTails(nextchecktail)        

        return rttails
    ##FHST
    #try All Infinity with all starting hops
    #find the cross hops
    #retrun tail array, exact
    def findFirstBPTailOfPrefixFHST(self):
        Lkvalue=self.prefixArray[4]
        #short cut
        # if Lkvalue<=224:
        #     return [380,INFINITYLKVALUE,INFINITYLKVALUE,INFINITYLKVALUE,INFINITYLKVALUE]
        #if Lkvalue<=240:
        #    return [364,INFINITYLKVALUE,INFINITYLKVALUE,INFINITYLKVALUE,INFINITYLKVALUE]
        #else:
        #    Lkvalue=364
        Lkvalue=364
        LkvalueNxt=pthG.getNextValue(Lkvalue)
        #FHST
        tails=[]
        simuResults=[]
        if (self.prefixArray[4]>=348 and  self.prefixArray[3]>=348 or self.prefixArray[4]>348 and  self.prefixArray[3]>=120)  and  (self.prefixArray[2]>=348 or  self.prefixArray[1]>=120 or self.prefixArray[4]>348):
            #go to a smaller range checking
            #the first must > TC and last< TC
            LkvalueN2=pthG.getNextValue(LkvalueNxt)
            LkvalueN3=pthG.getNextValue(LkvalueN2)

            if self.prefixArray[1]>120 or (self.prefixArray[4]>348 and (self.prefixArray[2]>328 or self.prefixArray[0]>=120)):
                tail1=[Lkvalue,Lkvalue,Lkvalue,Lkvalue,INFINITYLKVALUE]
                tails.append(tail1)
                self.addnewtail(tail1)
                tail2=[Lkvalue,Lkvalue,Lkvalue,Lkvalue,LINKMAXVALUESETING]
                tails.append(tail2)
                self.addnewtail(tail2)
                tail3=[Lkvalue,Lkvalue,Lkvalue,Lkvalue,Lkvalue]
                tails.append(tail3)
                self.addnewtail(tail3)
                tail4=[Lkvalue,Lkvalue,Lkvalue,LkvalueN2,LkvalueN2]
                tails.append(tail4)    
                self.addnewtail(tail4)
                tail5=[Lkvalue,Lkvalue,Lkvalue,LkvalueN3,LkvalueN3]
                tails.append(tail5)    
                self.addnewtail(tail5)
                linkDic1=buildlinkStrufromPrefixTail(self.prefixArray,tail1)
                linkDic2=buildlinkStrufromPrefixTail(self.prefixArray,tail2)
                linkDic3=buildlinkStrufromPrefixTail(self.prefixArray,tail3)
                linkDic4=buildlinkStrufromPrefixTail(self.prefixArray,tail4)
                linkDic5=buildlinkStrufromPrefixTail(self.prefixArray,tail5)
            else:
                tail1=[Lkvalue,Lkvalue,Lkvalue,INFINITYLKVALUE,INFINITYLKVALUE]
                tails.append(tail1)
                self.addnewtail(tail1)
                tail2=[Lkvalue,Lkvalue,Lkvalue,Lkvalue,INFINITYLKVALUE]
                tails.append(tail2)
                self.addnewtail(tail2)
                tail3=[Lkvalue,Lkvalue,LkvalueNxt,LkvalueNxt,LkvalueNxt]
                tails.append(tail3)
                self.addnewtail(tail3)
                tail4=[Lkvalue,Lkvalue,LkvalueN2,LkvalueN2,LkvalueN2]
                tails.append(tail4)    
                self.addnewtail(tail4)
                tail5=[Lkvalue,Lkvalue,Lkvalue,LINKMAXVALUESETING,LINKMAXVALUESETING]
                tails.append(tail5)    
                self.addnewtail(tail5)
                linkDic1=buildlinkStrufromPrefixTail(self.prefixArray,tail1)
                linkDic2=buildlinkStrufromPrefixTail(self.prefixArray,tail2)
                linkDic3=buildlinkStrufromPrefixTail(self.prefixArray,tail3)
                linkDic4=buildlinkStrufromPrefixTail(self.prefixArray,tail4)
                linkDic5=buildlinkStrufromPrefixTail(self.prefixArray,tail5)

            #simul and get result
            linkDicArray=[linkDic1,linkDic2,linkDic3,linkDic4,linkDic5]
            simuResults=getSimuResultsForLinkStrArray(linkDicArray)

            tailsarray=[tail1,tail2,tail3,tail4,tail5]
            self.setResultsBatch(tailsarray,simuResults)

        else:

            tail1=[Lkvalue,INFINITYLKVALUE,INFINITYLKVALUE,INFINITYLKVALUE,INFINITYLKVALUE]
            tails.append(tail1)
            self.addnewtail(tail1)
            tail2=[Lkvalue,Lkvalue,INFINITYLKVALUE,INFINITYLKVALUE,INFINITYLKVALUE]
            tails.append(tail2)
            self.addnewtail(tail2)
            tail3=[Lkvalue,Lkvalue,Lkvalue,INFINITYLKVALUE,INFINITYLKVALUE]
            tails.append(tail3)
            self.addnewtail(tail3)
            tail4=[Lkvalue,LkvalueNxt,LkvalueNxt,LkvalueNxt,LINKMAXVALUESETING]
            tails.append(tail4)    
            self.addnewtail(tail4)
            tail5=[Lkvalue,LkvalueNxt,LkvalueNxt,LkvalueNxt,LkvalueNxt]
            tails.append(tail5)
            self.addnewtail(tail5)

            linkDic1=buildlinkStrufromPrefixTail(self.prefixArray,tail1)
            linkDic2=buildlinkStrufromPrefixTail(self.prefixArray,tail2)
            linkDic3=buildlinkStrufromPrefixTail(self.prefixArray,tail3)
            linkDic4=buildlinkStrufromPrefixTail(self.prefixArray,tail4)
            linkDic5=buildlinkStrufromPrefixTail(self.prefixArray,tail5)

            #simul and get result
            linkDicArray=[linkDic1,linkDic2,linkDic3,linkDic4,linkDic5]
            simuResults=getSimuResultsForLinkStrArray(linkDicArray)

            tailsarray=[tail1,tail2,tail3,tail4,tail5]
            self.setResultsBatch(tailsarray,simuResults)

        

        print("Prefix %s first Results:%s"%(self.prefixArray,simuResults))
        

        lasttailidx=0
        for idx in range(len(simuResults)):
            if simuResults[idx]>TCUPPER_VALUE:
                lasttailidx=idx
            else:
                lasttailidx=idx# first idx that is <=TCUPPER_VALUE
                break
        refinetail=tails[lasttailidx]# this value is <=TCUPPER_VALUE
        lkvalu=refinetail[lasttailidx]
        valueinc1=pthG.getNextValue(lkvalu)
        valueinc2=pthG.getNextValue(valueinc1)
        valueinc3=pthG.getNextValue(valueinc2) # 3 is enougth for FHST?
        valueinc4=pthG.getNextValue(valueinc3)


        tailinc1=refinetail.copy()
        tailinc1[lasttailidx]=valueinc1
        #tailinc1[lasttailidx+1]=valueinc1
        self.addnewtail(tailinc1)
        #self.setBiggerNeighbro(refinetail,tailinc1)
        tailinc2=refinetail.copy()
        tailinc2[lasttailidx]=valueinc2
        if lasttailidx<4:
            tailinc2[lasttailidx+1]=valueinc2
        self.addnewtail(tailinc2)
        #self.setBiggerNeighbro(refinetail,tailinc2)
        tailinc3=refinetail.copy()
        tailinc3[lasttailidx]=valueinc3
        if lasttailidx<4:
            tailinc3[lasttailidx+1]=valueinc3
        self.addnewtail(tailinc3)
        #self.setBiggerNeighbro(refinetail,tailinc3)
        # tailinc4=refinetail.copy()
        # tailinc4[lasttailidx]=valueinc4
        # self.addnewtail(tailinc4)
        # self.setBiggerNeighbro(refinetail,tailinc4)
        tailinc2T=refinetail.copy()
        for idx in range(lasttailidx,len(refinetail)):
            tailinc2T[idx]=valueinc3
        tailinc2T[lasttailidx]=valueinc2
        self.addnewtail(tailinc2T)
        tailinc3T=refinetail.copy()
        for idx in range(lasttailidx,len(refinetail)):
            tailinc3T[idx]=valueinc3
        #tailinc3T[lasttailidx]=valueinc3
        self.addnewtail(tailinc3T)
        



        LkDicinc0=buildlinkStrufromPrefixTail(self.prefixArray,refinetail)#aleady tesed so not includ
        LkDicinc1=buildlinkStrufromPrefixTail(self.prefixArray,tailinc1)
        LkDicinc2=buildlinkStrufromPrefixTail(self.prefixArray,tailinc2)
        LkDicinc3=buildlinkStrufromPrefixTail(self.prefixArray,tailinc3)
        LkDicinc2T=buildlinkStrufromPrefixTail(self.prefixArray,tailinc2T)
        LkDicinc3T=buildlinkStrufromPrefixTail(self.prefixArray,tailinc3T)
        finetuneLinkDics=[LkDicinc1,LkDicinc2,LkDicinc3,LkDicinc2T,LkDicinc3T]
        #fintuneresluts=getSimuResultsForLinkStrArray(finetuneLinkDics)
        fintuneresluts=self.wrapperGetSimuResultWithRepeatableObjs(finetuneLinkDics)

        tailsarray=[tailinc1,tailinc2,tailinc3,tailinc2T,tailinc3T]
        self.setResultsBatch(tailsarray,fintuneresluts)

        print("finetune results:%s for %d-%d"%(fintuneresluts,lkvalu,valueinc3))
        resultidx=0
        for idx in range(len(fintuneresluts)):
            if fintuneresluts[idx]>TCUPPER_VALUE:
                break
            resultidx+=1
        if resultidx<=3:
            if resultidx==0:
                return refinetail
            elif resultidx==1:
                return tailinc1
            elif resultidx==2:
                return tailinc2
            elif resultidx==3:
                return tailinc3
                #return finetuneLinkDics[resultidx-1]
        else:
            #big range to search
            valueinc5=pthG.getNextValue(valueinc1)
            tailinc5=refinetail.copy()
            tailinc5[lasttailidx]=valueinc5
            self.addnewtail(tailinc5)
            self.setBiggerNeighbro(refinetail,tailinc5)

            valueinc6=pthG.getNextValue(valueinc5)
            tailinc6=refinetail.copy()
            tailinc6[lasttailidx]=valueinc6
            self.addnewtail(tailinc6)
            self.setBiggerNeighbro(tailinc5,tailinc6)

            #tailinc1.sort()
            #orgtailinc2=tailinc2.copy()   
            tailinc7=refinetail.copy()
            tailinc7[lasttailidx]=420# 0.02 * 3
            self.addnewtail(tailinc7)
            #self.setBiggerNeighbro(orgtailinc2,tailinc2)

            #tailinc2.sort()
            #orgtailinc3=tailinc3.copy()   
            tailinc8=refinetail.copy()
            tailinc8[lasttailidx]=LINKMAXVALUESETING# 0.011 * 4
            self.addnewtail(tailinc8)
            #self.setBiggerNeighbro(orgtailinc3,tailinc3)

            #tailinc3.sort()
            LkDicinc0=buildlinkStrufromPrefixTail(self.prefixArray,tailinc5)
            LkDicinc1=buildlinkStrufromPrefixTail(self.prefixArray,tailinc6)
            LkDicinc2=buildlinkStrufromPrefixTail(self.prefixArray,tailinc7)
            LkDicinc3=buildlinkStrufromPrefixTail(self.prefixArray,tailinc8)
            finetuneLinkDics=[LkDicinc0,LkDicinc1,LkDicinc2,LkDicinc3]

            #fintuneresluts=getSimuResultsForLinkStrArray(finetuneLinkDics)
            fintuneresluts=self.wrapperGetSimuResultWithRepeatableObjs(finetuneLinkDics)

            tailsarray=[tailinc5,tailinc6,tailinc7,tailinc8]
            self.setResultsBatch(tailsarray,fintuneresluts)

            print("bigRange Initial Search:%s"%(fintuneresluts))
            resultidx=0
            for idx in range(len(fintuneresluts)):
                if fintuneresluts[idx]>TCUPPER_VALUE:
                    break
                resultidx+=1
            if resultidx==0:
                return tailinc1
            else:
                if resultidx>3:
                    resultidx=3
                fintuneTails=[refinetail,tailinc1,tailinc2,tailinc3]
                tail=self.binarySearchFHSTInRange(fintuneTails[resultidx-1],fintuneTails[resultidx])
                return tail
            
    #tail1< tail2
    # tail1< TCUPPER_VALUE ,tail2>TCUPPER_VALUE
    # tail1/2 have same ending position,(not infinity hops)
    def binarySearchFHSTInRange(self,tail1,tail2):
        diffHop=0
        for hops in range(len(tail1)):
            if tail1[hops]<tail2[hops]:
                diffHop=hops
                break
        #lkVal1=tail1[diffHop]
        lkVal2=tail2[diffHop]

        rettail=self.getbestTail(tail1,diffHop,lkVal2)
        self.addBDtail(rettail)        
        
        return rettail
    
    def nextTailsWithInifity(self,tailWithInFinity):
        inputValid=1
        poslastSearchInpos=0
        
        laststepPos=0
        
        for pos in range(len(tailWithInFinity)):
            if tailWithInFinity[pos]<INFINITYLKVALUE:
                laststepPos=pos
            else:
                break
        # beginStoppos=0
        # for pos in range(len(tailWithInFinity)):
        #     if tailWithInFinity[pos]==tailWithInFinity[laststepPos]:
        #         beginStoppos=pos
        #         break
        
        # valuelist=[]
        # value=tailWithInFinity[laststepPos]
        # while value and value<=LINKMAXVALUESETING:
        #     valuelist.append(value)
        #     value=pthG.getNextValue(value)
        # mididx=math.floor(len(valuelist)/2)
        
        #1 lastsetp set to LINKMAXVALUE if < 0  begin setp inclreas
        LastValue=tailWithInFinity[laststepPos]
        preposValue=tailWithInFinity[laststepPos-1]
        nxtpreposValue=pthG.getNextValue(preposValue)
        if laststepPos>1 and (LastValue>nxtpreposValue):
            LastValue=nxtpreposValue            
            tailWithInFinity[laststepPos]=LastValue
            tailWithInFinity[laststepPos-1]=LastValue
        self.addnewtail(tailWithInFinity)
        
        obj00=buildlinkStrufromPrefixTail(self.prefixArray,tailWithInFinity)




        print("lastpos:%d oftail%s"%(laststepPos,tailWithInFinity))
        #check this laststepPos hop
        testtail10=tailWithInFinity.copy()
        testtail10[laststepPos]=pthG.getNextValue(LastValue)
        self.addnewtail(testtail10)
        print("org:%s inc%s"%(tailWithInFinity,testtail10))
        self.setBiggerNeighbro(tailWithInFinity,testtail10)

        obj10=buildlinkStrufromPrefixTail(self.prefixArray,testtail10)
        print("tail0:%s"%(testtail10))
        testtail11=tailWithInFinity.copy()
        testtail11[laststepPos]=LINKMAXVALUESETING
        self.addnewtail(testtail11)
        #self.setBiggerNeighbro(testtail10,testtail11)

        obj11=buildlinkStrufromPrefixTail(self.prefixArray,testtail11)
        print("tail1:%s"%(testtail11))
        testtail12=tailWithInFinity.copy()
        testtail12[laststepPos]=INFINITYLKVALUE
        self.addnewtail(testtail12)
        #self.setBiggerNeighbro(testtail11,testtail12)

        obj12=buildlinkStrufromPrefixTail(self.prefixArray,testtail12)
        print("tail2:%s"%(testtail12))

        #2 beginsetp increase
        # check laststepPos+1 hop  tailWithInFinity[laststepPos],tailWithInFinity[laststepPos], must be <TC
        testtail20=tailWithInFinity.copy()
        testtail20[laststepPos]=pthG.getNextValue(LastValue)
        if laststepPos<4:
            testtail20[laststepPos+1]=pthG.getNextValue(LastValue)
        self.addnewtail(testtail20)

        obj20=buildlinkStrufromPrefixTail(self.prefixArray,testtail20)
        print("tail3:%s"%(testtail20))

        testtail21=tailWithInFinity.copy()
        testtail21[laststepPos]=LINKMAXVALUESETING
        if laststepPos<4:
            testtail21[laststepPos+1]=LINKMAXVALUESETING
        self.addnewtail(testtail21)

        obj21=buildlinkStrufromPrefixTail(self.prefixArray,testtail21)
        print("tail4:%s"%(testtail21))

        tailsarray=[testtail10,testtail11,testtail12,testtail20,testtail21,tailWithInFinity]

        objlist=[obj10,obj11,obj12,obj20,obj21,obj00]

        resultlist=self.wrapperGetSimuResultWithRepeatableObjs(objlist)
        
        
        self.setResultsBatch(tailsarray,resultlist)

        print("got results:%s"%(resultlist))

        if resultlist[0]<TCUPPER_VALUE:
            #this link need need fine tune;
            #chck others result for more information
            #but beginHoppos is the smallest already. check the lasthop inclreasing
            inputValid=0

        if resultlist[1]>TCUPPER_VALUE or resultlist[2]>TCUPPER_VALUE:
            poslastSearchInpos=1
        else:
            poslastSearchInpos=0

        if inputValid==0 and poslastSearchInpos:
                    
            if resultlist[1]>TCUPPER_VALUE:
                tail=self.checktail(testtail10,LINKMAXVALUESETING)
            else:#INIFITY<TC LINKMAXVALUESETING<TC
                tail=testtail11
        else:
            #poslast is ok check next slot
            if resultlist[3]>TCUPPER_VALUE:
                #no nee check others,
                #tailWithInFinity is the last one
                tail=None
            elif resultlist[4]>TCUPPER_VALUE:
                #search poslast+1 in range idx
                tail=self.checktail(testtail20,LINKMAXVALUESETING)
            else:
                tail=testtail21 # since INFIINTY,INIFITY is <TC by inputValid==1

            
        return tail,inputValid,poslastSearchInpos
    
    #return the outsiderlist
    def getOusiderTails(self):
        outsiderlist=[]
        for key in self.tailsBASE.keys():
            state=self.tailsState[key]
            if state.TCCheckedReslt==1:
                outsiderlist.append(self.tailsBASE[key])
        
        return outsiderlist


    
    def filterTailCandidates(self,tailsCandiList):
        #clean the tail with overlap
        outsiderlist=self.getOusiderTails()
        innerlist=self.getAllBPTails()
        nooutsider=[]
        cleanedTails=[]
        for tail in tailsCandiList:
            AlldimBigger=0
            for cktail in outsiderlist:
                #if cktail!=tail:
                    clean=0
                    for idx in range(len(cktail)):
                        if tail[idx]<cktail[idx]:
                            clean=1
                            #print("not sure,found smaller than part %d of idx:%d in:%s"%(cktail[idx],idx,cktail))
                            break
                    if clean==0:
                        #all dim >= cktail
                        #print("for sure, tail:%s no smaller dim in cktail:%s"%(tail,cktail))
                        AlldimBigger=1
                        break
            #print("tail:%s cleared:%d"%(tail,AlldimSamller))
            if AlldimBigger==0:                
                nooutsider.append(tail) 
            #else:
            #    print("tail:%s must bigger than TC, so skipped"%(tail))
        # for tail in nooutsider:
        #     AlldimSamller=0
        #     for cktail in innerlist:
        #         if cktail!=tail:
        #             clean=0
        #             for idx in range(len(cktail)):
        #                 if tail[idx]>cktail[idx]:
        #                     clean=1
        #                     break
        #             if clean==0:
        #                 #all dim <= cktail
        #                 AlldimSamller=1
        #                 break
        #     #print("tail:%s cleared:%d"%(tail,AlldimSamller))
        #     if AlldimSamller==0:
        #         cleanedTails.append(tail) 

        cleanedTails=nooutsider.copy()

        return cleanedTails  

    #SHFT
    # return the next tail or None
    # None for loop end
    # we should use the returned value to check the  next tail untill we got None
    def getNextSHFTTail(self,preTail):
        #if tail is infinity, increase the last not infinity hop value 
        diffhop=0
        for hop in range(len(preTail)):
            if hop>0:
                diffhop=hop-1
            if preTail[hop]>=INFINITYLKVALUE:
                break
        
        laststephop=0#step inc >1
        beginghop=0
        print("getNextSHFTTail lastnotinfinty hop:%d"%(diffhop))

        if diffhop<3:# infinity link exist
            laststephop=diffhop+1
            beginghop=diffhop
        else:
            print("search step diffhop:%d"%(diffhop))
            curpos=diffhop+1
            laststephop=diffhop+1
            prepos=curpos-1
            while(prepos>=0):
                curValu=preTail[curpos]
                preValu=preTail[prepos]
                onstepValue=pthG.getPreviousValue(curValu)
                if preValu<onstepValue:
                    beginghop=prepos
                    break
                elif preValu==onstepValue:
                    laststephop=curpos#begin of next step 

                curpos=prepos
                prepos=curpos-1
        print("next beginhop:%d lasthop:%d"%(beginghop,laststephop))


        if beginghop>0:
            
            curValue=preTail[beginghop]
            nextValue=pthG.getNextValue(curValue)
            begintail=preTail.copy()
            for hop in range(len(preTail)):
                if hop>=beginghop:
                    begintail[hop]=nextValue
            if laststephop>3 and preTail[laststephop]==INFINITYLKVALUE:
                # if laststephop<4:
                #     lastNxtValue=466#pthG.getPreviousValue(preTail[laststephop])
                # else:
                    lastNxtValue=LINKMAXVALUESETING#pthG.getPreviousValue(preTail[laststephop])
            else:
                lastNxtValue=preTail[laststephop]


            ##added for the biggest begin step
            for hop in range(len(preTail)):
                if hop>laststephop:
                    begintail[hop]=lastNxtValue

            # endtail=preTail.copy()        
            # if preTail[laststephop]<lastNxtValue: #the last to diffhop can be more flat
            #     curValue=preTail[laststephop]
            #     nextValue=pthG.getNextValue(curValue)
            #     for hop in range(len(preTail)):
            #         if hop>=laststephop:
            #             endtail[hop]=nextValue
            print("begin hops idx:%d diffhop:%d lstnxtValue:%d begintail:%s"%(beginghop,diffhop,lastNxtValue,begintail))
            
            beginSimAry=[]
            tails=[]
            if begintail[4]<INFINITYLKVALUE:
                bestpossibletail=self.getBestSHFTTail()
                if bestpossibletail==None:
                    bestpossibletail=preTail
                
                #generate all possibles
                gentails=getAllSHFTSteps(begintail,bestpossibletail) #preTail
                
                #tails to verifyed 
                #tails=gentails.copy()
                tails=self.filterTailCandidates(gentails)
                

                beginSimAry,orgResultsdic,nextResultdic,newtails=verifiedFiniteTailsBorder(self.prefixArray,tails)
                print("orgobjidx:%s"%(orgResultsdic))
                print("nxtobjidx:%s"%(nextResultdic))
                purifiedList=[] 
                for tail in newtails:
                    new=self.addnewtail(tail)
                    if new:
                        purifiedList.append(tail)

                         

                resultbegin=getSimuResultsForLinkStrArray(beginSimAry)
                print("batchtailscheck:%s orgtails:%d purifiedtails:%d"%(resultbegin,len(newtails), len(purifiedList)))
                self.setResultsBatch(newtails,resultbegin)
                #self.dumpTailSates(purifiedList)


                borderTails=[]
                nextToCheckk=[]
                resultlistNew=[]
                for idx in range(len(tails)):
                    if resultbegin[orgResultsdic[idx]]<TCUPPER_VALUE and resultbegin[nextResultdic[idx]]>TCUPPER_VALUE:
                        borderTails.append(tails[idx])
                        print("got result idx:%d"%(idx))
                    elif resultbegin[nextResultdic[idx]]<TCUPPER_VALUE:
                        nextToCheckk.append(tails[idx])
                        resultlistNew.append(resultbegin[orgResultsdic[idx]])
                        print("need check idx:%d"%(idx))
                if len(borderTails)>0:
                    print("gotBDtailsNum:%d"%(len(borderTails)))
                    return borderTails
                if len(nextToCheckk)==0:                
                    return None                 

                #choose on tail as begin tail and go through the next loop process
                # for finding  more ranges
                begintail=nextToCheckk[0]
                print("next tocheck in this func tail:%s"%(begintail))
                resultbegin=resultlistNew
                
                
                

                    #we can verify the tails here directly
                    # and return directly here
                    #               
            else:
                print("check tail %s"%(begintail))
                
                tails=[begintail]
                self.addnewtail(begintail)
                beginlinkDic=buildlinkStrufromPrefixTail(self.prefixArray,begintail)        
                beginSimAry=[beginlinkDic]
                resultbegin=getSimuResultsForLinkStrArray(beginSimAry)
                self.setResultsBatch(tails,resultbegin)


            
            print("got RTvalue:%s"%(resultbegin))
            if len(resultbegin)==1 and resultbegin[0]>TCUPPER_VALUE:
                return None
            # else:
            #     #find first < TC
            #     begintail=None
            #     bestidx=-1
            #     value=0
            #     for idx in range(len(resultbegin)):
            #         if resultbegin[idx]<TCUPPER_VALUE and value<resultbegin[idx]:
            #             value=resultbegin[idx]
            #             bestidx=idx
            #     if bestidx>=0:
            #         if bestidx>0 and  abs(resultbegin[0]-resultbegin[bestidx])<0.00005:
            #             bestidx=0
            #         begintail=tails[bestidx]
            #     if begintail==None:
            #         return None           

            if preTail[laststephop]==INFINITYLKVALUE:
                diffhop=hopsStepToCheck(begintail)
                nextValue=pthG.getNextValue(nextValue)
                lastNxtValue=LINKMAXVALUESETING
                if begintail[4]<INFINITYLKVALUE:
                    print("case 1 try:%d hops:%d tail:%s lastNxtvalue:%d"%(begintail[diffhop],diffhop,begintail,lastNxtValue))
                    tail=self.getbestTail(begintail,4,lastNxtValue)
                else:
                    print("case 1 try:%d hops:%d tail:%s lastNxtvalue:%d"%(begintail[diffhop],diffhop,begintail,lastNxtValue))
                    tail=self.getbestTail(begintail,diffhop,lastNxtValue)
            elif preTail[laststephop]>=LINKMAXVALUESETING:
                
                valuearray=[]
                moditail=begintail.copy()
                currentValue= moditail[diffhop+1]
                while(currentValue<=LINKMAXVALUESETING):
                    valuearray.append(currentValue)
                    currentValue=pthG.getNextValue(currentValue)
                if len(valuearray)>1:
                    idx=math.floor(len(valuearray)*2/3) 
                    moditail[diffhop]=valuearray[idx]
                #else:
                #    moditail[diffhop]=pthG.getNextValue(moditail[diffhop])
                #    #begintail[diffhop+1]==begintail[diffhop]
                
                    print("case 2 try:%d"%(moditail[diffhop]))

                    tail=self.getbestTail(moditail,diffhop,LINKMAXVALUESETING)
            else:
                diffhop=hopsStepToCheck(begintail)
                print("case 3 try:%d hops:%d tail:%s"%(begintail[diffhop],diffhop,begintail))
                tail=self.getbestTail(begintail,4,lastNxtValue)

            print("got best Tail:%s"%(tail))
            if tail==None:
                begintail.sort()
                return [begintail]
            
            self.addBDtail(tail)
            return [tail]
        else:
            return None
    
    #search only last value [4] with all previous as prefix
    def searchTailsDBforMaxValue(self,tailprefix):
        lkVmax=tailprefix[4]
        #thisValue=BPDB.tailMetric(tailprefix)
        smallestOne=LINKMAXVALUESETING
        for tailID in self.tailsBASE.keys():
            chktail=self.tailsBASE[tailID]
            if chktail[0]==tailprefix[0] and chktail[1]==tailprefix[1] and chktail[2]==tailprefix[2] and chktail[3]==tailprefix[3] and chktail[4]>lkVmax:
                if chktail[4]<smallestOne:
                    smallestOne=chktail[4]
            else:
                continue
        return smallestOne

    ##check borders of possible tails
    def checkBordersOfFinalTails(self):
        tails=self.getAllBPTails()
        tocheck=[]
        for tail in tails:
            #print("ck tail%s"%(tail))
            if self.getTailTCCState(tail)==-1:
                tocheck.append(tail)
        
        nextsetpcheck=[]
        for tail in tocheck:
            lkNxtValue=self.searchTailsDBforMaxValue(tail)
            if tail[4]==INFINITYLKVALUE:
                nextLKV=INFINITYLKVALUE
            else:
                nextLKV=pthG.getNextValue(tail[4])
            if nextLKV<lkNxtValue:
                nextsetpcheck.append(tail)
            else:
                if nextLKV>=LINKMAXVALUESETING or nextLKV==lkNxtValue:
                    self.setBorderFlag(tail)
        tailstoSimu=[]

        for tail in nextsetpcheck:
            smallest=pthG.getNextValue(tail[4])
            lkNxtValue=self.searchTailsDBforMaxValue(tail)
            if lkNxtValue<LINKMAXVALUESETING:
                bigest=pthG.getPreviousValue(lkNxtValue)
            else:
                bigest=LINKMAXVALUESETING
            
            valuelist=[]
            valuetoadd=pthG.getNextValue(smallest)
            while valuetoadd<bigest:
                valuelist.append(valuetoadd)
                valuetoadd=pthG.getNextValue(valuetoadd)
            if len(valuelist)>0:            
                mid=math.floor(len(valuelist)/2)
                midValue=valuelist[mid]
            else:
                midValue=smallest
            
            stail=tail.copy()
            stail[4]=smallest

            mtail=tail.copy()
            mtail[4]=midValue

            btail=tail.copy()
            btail[4]=bigest

            if stail not in tailstoSimu:
                tailstoSimu.append(stail)
            if mtail not in tailstoSimu:
                tailstoSimu.append(mtail)
            if btail not in tailstoSimu:
                tailstoSimu.append(btail)
        
        if len(tailstoSimu)==0:
            return None
        
        simuobjlist=[]
        for tail in tailstoSimu:
            self.addnewtail(tail)
            obj=buildlinkStrufromPrefixTail(self.prefixArray,tail)
            simuobjlist.append(obj)
        simuresults=getSimuResultsForLinkStrArray(simuobjlist)
        self.setResultsBatch(tailstoSimu,simuresults)

        return simuresults


    #check more tails
    # return [] or tails list
    def getMoreTails(self,theLastTail):
        if theLastTail:
            initalTail=theLastTail.copy()#initail
            theCheckingTails=[initalTail]
            while(theCheckingTails):
                theCheckingTail=self.getBestSHFTTail()                
                if theCheckingTail==None:
                    #final fine tune the borders
                    results=self.checkBordersOfFinalTails()
                    while results:
                        results=self.checkBordersOfFinalTails()
                    break
                theCheckingTails=self.getNextSHFTTail(theCheckingTail)                      
        #retrun
        tails=self.getAllBPTails()
        return tails

#############################
# global instance of TailsMgr
#############################    
TailsMgr=None

def createTailsMgr(prefixAry):
    global TailsMgr
    TailsMgr=tailsManager(prefixAry)        

#### middle prefix check, the tails should be in the ranges
# check the middle prefix tails by simulations, tails will be returned and with tailsevaluation. 
#   So this function just for some key points, not for many. And we can base one the result of this function for next step (man guided procedure, not program).
#   with the pattner (some id increased only) normally ID5,ID0 ID4 ID2 ID3
#
# so we can use this feature to accelarate the cacluationg process
# 
# Input: 
# FullPattner: [Id1Lower,Id1Upper]... [Id5Lower,ID5Upper]; Different from setting pattner, that only have ID1-ID5
# PrefixBegin,PrefixEnd: the range of middleprefix table, if same, the middleprefix is set by input.
# lowerTailsList:  a list of tails to check, as the lower boundary of each dimention
# rangeDistList:  array to set increasing steps of each tail in lowerTailsList to check.  1 for 1 step further, 0 for only the tail in lowerTailsList.
#  rangeDistList  have same  dim as  lowerTailsList
# 
# Output: midprefix, midtails, tailsEvalue
#  midprefix and midtails are the best choose prefix and tails for the middle prefix. 
#  tailsEvalue is the midtails evaluation, have same dim as midtails, each value have the meaning:
#   0, match well;  1,maybe bigger than border; -1, maybe smaller than border

def CheckMidOfRangeWithSameTailsLen(FullPattner,PrefixBegin,PrefixEnd,lowerTailsList,rangeDistList):
    #Step is increase only
    PrefixValBegin=BPDB.prefixMetric(PrefixBegin)
    PrefixValuEnd=BPDB.prefixMetric(PrefixEnd)
    prefixArray=[]
    prefix=[]
    #if some reauslt outside the range, step++ and loop again,but results of all tails fail to fit, exit.
    if PrefixValuEnd>PrefixValBegin:
        BPDB.OpenDatabase()
        prefixArray=BPDB.getPrefixArrayByRange(FullPattner,PrefixValBegin,PrefixValuEnd)
        BPDB.CloseDatabase()
        mididx=math.floor(len(prefixArray)/2)
        prefix=prefixArray[mididx]
    else:
        prefix=PrefixBegin.copy()    

    tailsChoose, tailsEvalue=checkthePrefixPoint(prefix,lowerTailsList,rangeDistList)

    return prefix,tailsChoose, tailsEvalue

def checkthePrefixPoint(prefix,lowerTailsList,rangeDistList):
    print("CK midprefix:%s"%(prefix))
    #check middle only
    OurRangeTailValues=[]#list of idc  hops:linkvaluelist
    idx=-1
    for rglen in rangeDistList:
        idx+=1
        valudic={}
        valulist=[]
        
        lasthop=0
        tail=lowerTailsList[idx]
        for hop in range(len(tail)):
            if tail[hop]<LINKMAXVALUESETING:
                lasthop=hop
            else:
                break
        value=tail[lasthop]
        count=0
        while count<rglen:
            value=pthG.getNextValue(value)                
            valulist.append(value)
            count+=1
             
        valudic[lasthop]=valulist
        OurRangeTailValues.append(valudic)

    linkidx=-1
    SimuIdxDic={}#linkidx:list of indexes in resultsarray, index = keyvalue index * 2 
    simuArray=[]
    tailsArray=[]
    for trydic in OurRangeTailValues:
        linkidx+=1
        orgtial=lowerTailsList[linkidx]
        lkobj=buildlinkStrufromPrefixTail(prefix,orgtial)
        simuArray.append(lkobj)
        print("addtail:%s"%(orgtial))
        tailsArray.append(orgtial)
        resultlist=[]
        resultlist.append(len(simuArray)-1)
        lasthops=0
        for hop in trydic.keys():
            lasthops=hop
        if len(trydic[lasthops])>0:
            for newVal in trydic[lasthops]:
                newtail=orgtial.copy()
                newtail[lasthops]=newVal
                lkobj=buildlinkStrufromPrefixTail(prefix,newtail)
                simuArray.append(lkobj)
                tailsArray.append(newtail)
                print("addtail:%s"%(newtail))
                resultlist.append(len(simuArray)-1)
        #
        SimuIdxDic[linkidx]=resultlist    
            
    resultArray=getSimuResultsForLinkStrArray(simuArray)
    print("results:%s"%(resultArray))

    tailsChoose, tailsEvalue=paserResultsCkMidWthSTLen(tailsArray,resultArray,SimuIdxDic)

    return tailsChoose,tailsEvalue

def paserResultsCkMidWthSTLen(tailsArray,resultArray,SimuIdxDic):
    tailsChoose=[]
    tailsEvalue=[]# 0 OK, 1 maybe bigger than border, -1 maybe smaller than border
    #print report
    
    for idx in SimuIdxDic.keys():
        resultidxs=SimuIdxDic[idx]
        print("link %d results:%s"%(idx,resultidxs))
        evaluelist=[]
        for ridx in resultidxs:
            if resultArray[ridx]<TCUPPER_VALUE:
                evaluelist.append(-1)
            else:
                evaluelist.append(1)

        bestidx=0
        for residx in range(len(evaluelist)):
            if evaluelist[residx]<TCUPPER_VALUE:
                bestidx=residx
            else:
                break
        tailEvalue=0
        if bestidx==(len(evaluelist)-1) and len(evaluelist)>1:
            tailEvalue=-1
        if evaluelist[bestidx]>0:
            tailEvalue=1
        
        tailsEvalue.append(tailEvalue)
        bestTailidx=resultidxs[bestidx]
        tailsChoose.append(tailsArray[bestTailidx])
        
    
    return tailsChoose, tailsEvalue





    

########
### 已经有了一定变化区间以后需要用到的函数
########
#increase tail one step
def getNextTail(tail,justonesetp=1):
    lstNVidx=-1
    for val in tail:
        if val<INFINITYLKVALUE:
            lstNVidx+=1
        else:
            break
    ValuLst=tail[lstNVidx]
    nextValue=pthG.getNextValue(ValuLst)
    newtail=tail.copy()
    if justonesetp:
        for idx in range(lstNVidx,len(tail)):
            newtail[idx]=nextValue  
    else:
        if nextValue>=LINKMAXVALUESETING:
            nextValue=INFINITYLKVALUE
        newtail[lstNVidx]=nextValue 
    return newtail

#decrease tail one step
def getPreTail(tail):
    lstNVidx=len(tail)-1    
    ValuLst=tail[lstNVidx]
    if ValuLst==INFINITYLKVALUE:
        preValue=LINKMAXVALUESETING
    else:
        preValue=pthG.getpreValue(ValuLst)
    newtail=tail.copy()
    newtail[lstNVidx]=preValue
    newtail.sort()    
    return newtail



#
# prefixmid 在 prefixof(begintails) 和 prefixof(endtails) 之间 
#  len(begintails) > len(endtails); 但是 prefixof(begintails) 和 prefixof(endtails) 之间的关系不一定。我们用 changetype 来判断关系。
# changetype: 
#  0: begintails 继续加大 => endtails； 加大合并的趋势。
#  1: begintails 继续减少 => endtails； 减少合并的趋势。 （从endtails 方向看， 是增加分岔）
#  加大或减少都可能改变tails数量，但是我们需要根据变化方向判断。
# return the last index to improve tail; 最后可以继续优化的tail index.
def checkBeginerTailIdx(prefixmid,begintails,endtails,changeType):
    BtailValues=[]
    EtailValues=[]
    
    for tail in begintails:
        value=BPDB.tailMetric(tail)
        BtailValues.append(value)

    startidx=0
    if len(BtailValues)>1:
        startidx=1
    # endidx=len(BtailValues)-1
    # if len(BtailValues)>1:
    #     endidx=len(BtailValues)-2
    # mididx=startidx
    # if endidx-startidx>1:
    #     mididx=startidx+math.floor((endidx-startidx)/2)
    mididx=startidx+1
    if mididx>=len(BtailValues):
        mididx=startidx
    endidx=mididx+1
    if endidx>=len(BtailValues):
        endidx=mididx

    for tail in endtails:
        value=BPDB.tailMetric(tail)
        EtailValues.append(value)

    # find change targets
    NewTailsValue=[]

    if changeType==0:
        # increase 
        NewTailsValue.append(BtailValues[startidx])
        ###
        newtail=getNextTail(begintails[startidx],0) 
        
        StartidxNextTail=None   

        #sortlist=endtails.copy() #End tails search is nosence 

        newStartValue=BPDB.tailMetric(newtail)
        
        bestidx=-1
        # for idx in range(len(sortlist)):
        #     value=BPDB.tailMetric(sortlist[idx])
        #     if value<newStartValue:
        #         newStartValue=value
        #         bestidx=idx

        if bestidx==-1:            
            if newStartValue not in NewTailsValue:
                NewTailsValue.append(newStartValue)
                StartidxNextTail=newtail

        # else:            
        #     if EtailValues[bestidx] not in NewTailsValue:
        #         NewTailsValue.append(EtailValues[bestidx])  
        #         StartidxNextTail=sortlist[bestidx]
        

        
        # 
        MididxNextTail=None  
        if mididx!=startidx:  
            newtail=getNextTail(begintails[mididx],0) 
                
            #sortlist=endtails.copy() 
            
            newStartValue=BPDB.tailMetric(newtail)
            
            bestidx=-1
            # for idx in range(len(sortlist)):
            #     value=BPDB.tailMetric(sortlist[idx])
            #     if value<newStartValue:
            #         newStartValue=value
            #         bestidx=idx
            if bestidx==-1:
                if newStartValue not in NewTailsValue:
                    NewTailsValue.append(newStartValue)
                    MididxNextTail=newtail
            # else:
            #     if EtailValues[bestidx] not in NewTailsValue:
            #         NewTailsValue.append(EtailValues[bestidx])  
            #         MididxNextTail=sortlist[bestidx]

        # 
        EndidxNextTail=None 
        if endidx!=startidx and endidx!=mididx: 
            newtail=getNextTail(begintails[endidx],0)              
            #sortlist=endtails.copy() 
            newStartValue=BPDB.tailMetric(newtail)
            
            bestidx=-1
            # for idx in range(len(sortlist)):
            #     value=BPDB.tailMetric(sortlist[idx])
            #     if value<newStartValue:
            #         newStartValue=value
            #         bestidx=idx
            if bestidx==-1:
                if newStartValue not in NewTailsValue:
                    NewTailsValue.append(newStartValue)
                    EndidxNextTail=newtail
            # else:
            #     if EtailValues[bestidx] not in NewTailsValue:
            #         NewTailsValue.append(EtailValues[bestidx])
            #         EndidxNextTail=sortlist[bestidx]   

        checkTails=[begintails[startidx],StartidxNextTail] #they must be different
        if MididxNextTail:
            checkTails.append(begintails[mididx])
            checkTails.append(MididxNextTail)
        if EndidxNextTail:
            checkTails.append(begintails[endidx])
            checkTails.append(EndidxNextTail)

        numberofsimu=len(checkTails)
        objlist=[]
        for tail in checkTails:
            print("check the tail:%s"%(tail))
            linkobj=buildlinkStrufromPrefixTail(prefixmid,tail)
            objlist.append(linkobj)
        
        results=getSimuResultsForLinkStrArray(objlist)
        print("check results:%s"%(results))
        if numberofsimu<=2:
            if results[0]<TCUPPER_VALUE and results[1]>TCUPPER_VALUE:
                return startidx
            else:
                if startidx>0:
                    startidx=startidx-1
                return startidx
        if numberofsimu<=4:
            if results[2]<TCUPPER_VALUE and results[3]>TCUPPER_VALUE:
                #mid keeped
                if mididx!=startidx:
                    return mididx
                elif endidx!=startidx:
                    return endidx
            elif results[0]<TCUPPER_VALUE and results[1]>TCUPPER_VALUE:
                # mid overflowed, startidx keeped
                nextid=mididx
                if mididx!=startidx:
                    nextid=mididx-1
                elif endidx!=startidx:
                    nextid=endidx-1
                #if mid > start use mid-1
                if nextid!=startidx:
                    return nextid
                else:
                    return startidx
            else:
                if startidx>0:
                    startidx=startidx-1
                return startidx
        if numberofsimu<=6:
            if results[4]<TCUPPER_VALUE and results[5]>TCUPPER_VALUE:
                #end keeped
                return endidx
            elif results[2]<TCUPPER_VALUE and results[3]>TCUPPER_VALUE:
                #mid keeped, end overflow
                nextid=mididx                             
                #if mid > start use mid-1
                return nextid                
            elif results[0]<TCUPPER_VALUE and results[1]>TCUPPER_VALUE:
                # mid overflowed, startidx keeped
                nextid=startidx               
                return nextid
            else:
                if results[0]<TCUPPER_VALUE and results[1]<TCUPPER_VALUE:
                    if startidx>0:
                        startidx=startidx-1
                    return startidx #the first child need to improve
    else:
        #decrease
        NewTailsValue.append(BtailValues[startidx])
        ###
        newtail=getPreTail(begintails[startidx]) 
        StartidxNextTail=None   

        #sortlist=endtails.copy() #End tails search is nosence 

        newStartValue=BPDB.tailMetric(newtail)
        
        bestidx=-1
        # for idx in range(len(sortlist)):
        #     value=BPDB.tailMetric(sortlist[idx])
        #     if value<newStartValue:
        #         newStartValue=value
        #         bestidx=idx

        if bestidx==-1:            
            if newStartValue not in NewTailsValue:
                NewTailsValue.append(newStartValue)
                StartidxNextTail=newtail

        # else:            
        #     if EtailValues[bestidx] not in NewTailsValue:
        #         NewTailsValue.append(EtailValues[bestidx])  
        #         StartidxNextTail=sortlist[bestidx]
        

        
        # 
        MididxNextTail=None  
        if mididx!=startidx:  
            newtail=getPreTail(begintails[mididx]) 
                
            #sortlist=endtails.copy() 
            
            newStartValue=BPDB.tailMetric(newtail)
            
            bestidx=-1
            # for idx in range(len(sortlist)):
            #     value=BPDB.tailMetric(sortlist[idx])
            #     if value<newStartValue:
            #         newStartValue=value
            #         bestidx=idx
            if bestidx==-1:
                if newStartValue not in NewTailsValue:
                    NewTailsValue.append(newStartValue)
                    MididxNextTail=newtail
            # else:
            #     if EtailValues[bestidx] not in NewTailsValue:
            #         NewTailsValue.append(EtailValues[bestidx])  
            #         MididxNextTail=sortlist[bestidx]

        # 
        EndidxNextTail=None 
        if endidx!=startidx and endidx!=mididx: 
            newtail=getPreTail(begintails[endidx])              
            #sortlist=endtails.copy() 
            newStartValue=BPDB.tailMetric(newtail)
            
            bestidx=-1
            # for idx in range(len(sortlist)):
            #     value=BPDB.tailMetric(sortlist[idx])
            #     if value<newStartValue:
            #         newStartValue=value
            #         bestidx=idx
            if bestidx==-1:
                if newStartValue not in NewTailsValue:
                    NewTailsValue.append(newStartValue)
                    EndidxNextTail=newtail
            # else:
            #     if EtailValues[bestidx] not in NewTailsValue:
            #         NewTailsValue.append(EtailValues[bestidx])
            #         EndidxNextTail=sortlist[bestidx]   

        checkTails=[begintails[startidx],StartidxNextTail] #they must be different
        if MididxNextTail:
            checkTails.append(begintails[mididx])
            checkTails.append(MididxNextTail)
        if EndidxNextTail:
            checkTails.append(begintails[endidx])
            checkTails.append(EndidxNextTail)

        numberofsimu=len(checkTails)
        objlist=[]
        for tail in checkTails:
            linkobj=buildlinkStrufromPrefixTail(prefixmid,tail)
            objlist.append(linkobj)
        results=getSimuResultsForLinkStrArray(objlist)
        if numberofsimu<=2:
            if results[0]<TCUPPER_VALUE and results[1]>TCUPPER_VALUE:
                return startidx
            else:
                if startidx>0:
                    startidx=startidx-1
                return startidx
        if numberofsimu<=4:
            if results[2]<TCUPPER_VALUE and results[3]>TCUPPER_VALUE:
                #mid keeped
                if mididx!=startidx:
                    return mididx
                elif endidx!=startidx:
                    return endidx
            elif results[0]<TCUPPER_VALUE and results[1]>TCUPPER_VALUE:
                # mid overflowed, startidx keeped
                nextid=mididx
                if mididx!=startidx:
                    nextid=mididx-1
                elif endidx!=startidx:
                    nextid=endidx-1
                #if mid > start use mid-1
                if nextid!=startidx:
                    return nextid
                else:
                    return startidx
            else:
                if startidx>0:
                    startidx=startidx-1
                return startidx
        if numberofsimu<=6:
            if results[4]<TCUPPER_VALUE and results[5]>TCUPPER_VALUE:
                #end keeped
                return endidx
            elif results[2]<TCUPPER_VALUE and results[3]>TCUPPER_VALUE:
                #mid keeped, end overflow
                nextid=endidx-1                             
                #if mid > start use mid-1
                return nextid                
            elif results[0]<TCUPPER_VALUE and results[1]>TCUPPER_VALUE:
                # mid overflowed, startidx keeped
                nextid=mididx-1                
                return nextid
            else:
                if startidx>0:
                    startidx=startidx-1
                return startidx
#terminaltion contidion is step==0            
def improvableTailsSteps(tail):
    idx=hopsStepToCheck(tail)
    step=0
    value=tail[idx]
    endValue=tail[idx+1]
    nxtValue=pthG.getNextValue(value)
    while nxtValue<endValue:
        step+=1
        nxtValue=pthG.getNextValue(nxtValue)
    print("tail:%s idx%d  steps:%d"%(tail,idx,step))
    return step

def hopsStepToCheck(tail):
    idx=0
    lastvalu=tail[4]
    for hop in range(len(tail)-1,0,-1):
        nexValue=INFINITYLKVALUE
        if tail[hop]==INFINITYLKVALUE:
            nexValue=INFINITYLKVALUE
        else:
            nexValue=pthG.getNextValue(tail[hop])
        if  nexValue<lastvalu:
            lastvalu=tail[hop]
        else:
            break
    for hop in range(len(tail)):
        if tail[hop]<lastvalu:
            idx=hop
        else:
            break
    return idx
#
#BeginPrefix < EndPrefix
# BeginTails and EndTails may have different dimentions
# wight of prefix id1> id2> id3,  and id4,id5 fixed, same
#return midprefix and tails
def getMiddlePrefixTailsWithVaryTailsLen(BeginPrefix, BeginTails, EndPrefix, EndTails):
    changeType=0
    # if len(BeginTails)<len(EndTails):
    #     #beginTails and Edntails will swith
    #     changeType=1
    # if len(BeginTails)>len(EndTails):
    #     changeType=0
    
    #BeginPrefixValue=BPDB.prefixMetric(BeginPrefix[0],BeginPrefix[1],BeginPrefix[2],BeginPrefix[3],BeginPrefix[4])
    #EndPrefixValue=BPDB.prefixMetric(EndPrefix[0],EndPrefix[1],EndPrefix[2],EndPrefix[3],EndPrefix[4])
    BPDB.OpenDatabase()
    midprefix=BPDB.getMidPrefix(BeginPrefix,EndPrefix)
    BPDB.CloseDatabase()
    print("get midprefix:%s"%(midprefix))

    newtails=[]

    if changeType==0:
        tailsidx=checkBeginerTailIdx(midprefix,BeginTails,EndTails,changeType)              
        thetail=getNextTail(BeginTails[tailsidx]) 
        rendtail=getNextTail(BeginTails[tailsidx],0)
        print("first idx:%d  nexttrytail:%s rangeTail:%s"%(tailsidx,thetail,rendtail))   
        #checked already
        lkobj=buildlinkStrufromPrefixTail(midprefix,thetail)
        lkrogj=buildlinkStrufromPrefixTail(midprefix,rendtail)

        lkres=getSimuResultsForLinkStrArray([lkobj,lkrogj])
        print("rsl:%s"%(lkres)) 
        MaxValue=LINKMAXVALUESETING
        if lkres[0]<TCUPPER_VALUE and lkres[1]>TCUPPER_VALUE:
            thetail=BeginTails[tailsidx]
            hopidx=hopsStepToCheck(rendtail)
            MaxValue=rendtail[hopidx]
            print("hopidxcheck:%d, MaxValue=%d"%(hopidx,MaxValue))
        elif lkres[1]<TCUPPER_VALUE:# x < <
            thetail=rendtail #it should be same as Endtail[0],if it still small, range error
            hopidx=hopsStepToCheck(rendtail)
            MaxValue=rendtail[hopidx]
        else:#x > >
            if tailsidx>0:
                thetail=BeginTails[tailsidx-1]

       
        if tailsidx==0:
            endtaildix=0
            for idx in range(len(EndTails[0])):
                if EndTails[0][idx]<INFINITYLKVALUE:
                    endtaildix=idx
                else:
                    break
            MaxValue=EndTails[0][endtaildix]
        
         

        createTailsMgr(midprefix) 

        print("begintails idx:%d MaxValue:%d nexttrytail:%s"%(tailsidx,MaxValue,thetail))       
        newtail=TailsMgr.checktail(thetail,MaxValue)
        print("got newtail:%s"%(newtail))  
        #got headings         

        for idx in range(len(BeginTails)):
            if idx<tailsidx:
                #newtails.append(BeginTails[idx])
                TailsMgr.addBDtail(BeginTails[idx])
            break
        #for this new tail we got the rest tails
        TailsMgr.addBDtail(newtail)       
                  
        newtails=TailsMgr.getMoreTails(newtail)

        TailsMgr.checkBordersOfFinalTails()
        cleanedTails=TailsMgr.getAllBPTails()   
 
    return midprefix, cleanedTails



def manualCheck(prefixs,tails,dosimu=1):
    simuAry=[]
    for prefix in prefixs:
        for tail in tails:
            linkobj=buildlinkStrufromPrefixTail(prefix,tail)
            simuAry.append(linkobj)
        prefixValue=BPDB.prefixMetric(prefix)
        print("prefixValue:%d"%(prefixValue))

    if dosimu:    
        resutls=getSimuResultsForLinkStrArray(simuAry)
        print("got sim results:%s"%(resutls))

    #
    arrayValues=[]
    for tail in tails:        
        tvalu=BPDB.tailMetric(tail)
        arrayValues.append(tvalu)
    arrayValues.sort()
    TailsValue=BPDB.tailsMetric(arrayValues)
    
    print("tailsValue:%d"%(TailsValue))
    

def moduletest():
    pthG.loadValuToLinkMapDic() 
    # testPrefixlist=[
    #      #[104, 224, 245, 280, 328] ,
    #      #[104, 104, 120, 348, 348],
    #      #[120, 120, 120, 120, 348],
    #      #[328, 328, 328, 328, 348],
    #      #[280, 280, 280, 328, 348],
    #      [364, 364, 364, 364, 364]
    # ]
    testPrefixlist=[
        #[140, 140, 140, 140, 260],
        [104,280,280,280,364],
        # [104,104,104,348,360],         
        #  [104,104,120,348,360],
        #  [104,104,348,348,360],
        #  [104,120,120,348,360],
        #  [104,348,348,348,360],
        #  [120,120,120,348,360],
        #  [328,328,328,348,360],
        #  [348,348,348,348,360],
        #  #
        #  [104,104,104,328,360],
        #  [104,104,120,328,360],
        #  [104,104,328,328,360],
        #  [104,120,120,328,360],
        #  [104,328,328,328,360],
        #  [120,120,120,328,360],
        #  [280,280,280,328,360],
        #  [328,328,328,328,360],
        #  #
        #  [104,104,104,280,360],
        #  [104,104,120,280,360],
        #  [104,104,280,280,360],
        #  [104,120,120,280,360],
        #  [104,280,280,280,360],
        #  [120,120,120,280,360],
        #  [208,208,208,280,360],
        #  [280,280,280,280,360],
        #  #
        #  [104,104,104,208,360],
        #  [104,104,120,208,360],
        #  [104,104,208,208,360],
        #  [104,120,120,208,360],
        #  [104,208,208,208,360],
        #  [120,120,120,208,360],
        #  [140,140,140,208,360],
        #  [208,208,208,208,360],
        #  #
        #  [104,104,104,120,360],
        #  [104,104,120,120,360],
        #  [104,120,120,120,360],
        #  [120,120,120,120,360],
        #  #
        #  [104,104,104,104,360],

         

          
    ]
    for prefix in testPrefixlist:
        #prefix=[120,120,120,360,364]
        createTailsMgr(prefix)
        tails=TailsMgr.getAllTailsOfPrefix()
        print("Prefix## %s got %d tails"%(prefix,len(tails)))
        idx=0
        for tail in tails:
            idx+=1
            print("tail-%d:%s"%(idx,tail))
        
        DBCT.addSimulationsPrefixWithTailsToDB(prefix,tails)

    ##GLOBAL STATICS
    print("total Round:%d total simulation:%d"%(staticRound,len(pthG.staticNewSimuKeys)))
    
def checksomePoints():
    pthG.loadValuToLinkMapDic() 
    prefixs=[  
            #[140, 140, 140, 208, 328],
            #[140, 140, 240, 280, 328],
            #[120, 328, 328, 328, 328],
            #[328, 328, 328, 328, 328],
            #[208, 208, 208, 208, 328],
            #[328, 328, 328, 344, 344],
            #[120, 120, 120, 280, 280],
            #[104, 120, 120, 208, 280],
            #[140, 140, 208, 280, 280],
            #[208, 208, 208, 280, 280]#
            #[140, 208, 208, 260, 280]
            #[312, 312, 312, 312, 312],
            #[104, 120, 120, 120, 312],
            #[104, 208, 208, 208, 312],
            #[208, 208, 348, 348, 360],
            #[120, 120, 120, 120, 120],
            #[104, 140, 140, 140, 208],
            #[104, 208, 208, 208, 208],
            #[120, 120, 120, 240, 328],
            #[104, 104, 120, 120, 328],
            #[104, 104, 140, 328, 328],
            #[104, 104, 344, 344, 344],
            #[104, 104, 208, 208, 224],
            #[120, 120, 120, 140, 224],
            #[120, 344, 344, 344, 344],
            #[140, 140, 140, 328, 344],
            #[104, 104, 104, 104, 344],
            #[104, 104, 104, 104, 120],
            #[104, 104, 104, 104, 348], 
            #[120, 120, 120, 140, 348],
            #[208, 208, 208, 208, 348], 
            #[140, 140, 140, 140, 348], 
            #[104, 140, 140, 280, 348],
            #[104, 240, 245, 280, 348],
            #[104, 104, 120, 328, 348],
            #[344, 344, 344, 344, 348],
            #[104, 104, 344, 344, 348],
            #[208, 328, 328, 348, 348],
            #[120, 120, 120, 348, 348],
            #[104, 104, 104, 120, 120],
            #[104, 104, 120, 120, 360],
            #[104, 120, 120, 140, 348],
            #[104, 344, 348, 348, 348],
            #[344, 344, 344, 344, 360],
            #[104, 104, 104, 344, 360],
            #[104, 104, 104, 104, 360],
            #[104, 120, 140, 348, 360],
            #[120, 120, 348, 348, 360],
            #[120, 120, 348, 348, 348],
            #[104, 120, 120, 360, 360],
            #[104, 104, 120, 360, 360],
            #[120, 312, 312, 312, 312],
            #[140, 208, 245, 280, 312],
            #[328, 328, 328, 328, 328],
            #[104, 312, 328, 328, 328],
            #[104, 104, 348, 348, 348],
            #[104, 120, 120, 140, 348],
            #distributions
            #A
            #[208, 208, 208, 208, 208],
            ###
            #[224, 280, 328, 348, 364],
            #[140, 140, 140, 140, 140],
            # #mononicity check
            #[360, 364, 364, 364, 364],
            # [104, 104, 104, 104, 104],
            # [120, 120, 120, 120, 120],
            #[120, 120, 120, 140, 140],
            # [208, 208, 208, 208, 208],
            # [224, 224, 224, 224, 224],
            #[240, 240, 240, 240, 240],
            #[245, 245, 245, 245, 245],
            
            #[260, 260, 260, 260, 260],
            #[280, 280, 280, 280, 280],
            #[312, 312, 312, 312, 312],
            [328, 328, 328, 328, 344],
            [344, 344, 344, 344, 348],
            [348, 348, 348, 348, 360],
            #[328, 360, 360, 360, 360],
            # [364, 364, 364, 364, 364],
            # [380, 380, 380, 380, 380],
            # [384, 384, 384, 384, 384],
            # [400, 400, 400, 400, 400],
            # [420, 420, 420, 420, 420],
            # [466, 466, 466, 466, 466],
            # [482, 482, 482, 482, 482],
            # [498, 498, 498, 498, 498],
            # [4860, 4860, 4860, 4860, 4860],
        ]

    tails=[
        #[348, 4860, 4860, 4860, 4860],        
        #[384, 400, 400, 400, 400],
        #[384, 384, 400, 400, 400],
        ####
        #[360, 364, 364, 380, 380],
        #[4860, 4860, 4860, 4860, 4860],
        #[701, 4860, 4860, 4860, 4860],
        #[514, 4860, 4860, 4860, 4860],
        #[502, 4860, 4860, 4860, 4860],
        [360, 360, 364, 420, 466],
        [360, 360, 384, 384, 400],
        [360, 360, 400, 420, 420],
        [360, 360, 364, 384, 400],
        [360, 360, 420, 420, 420],
        [360, 360, 364, 400, 420],
        [360, 360, 364, 364, 538],
        [360, 360, 364, 534, 534],
        #[482, 4860, 4860, 4860, 4860],
        # [312, 364, 364, 364, 364],
       #[348, 364, 364, 364, 364], 
       #[364, 364, 364, 364, 364],
       #[384, 400, 400, 400, 400],
       # Distribution 
       # A
       #[360,400,420,420,4860],  
       #[360, 360, 360, 360, 360],  
#[364, 364, 380, 4860, 4860],
#[364, 364, 400, 400, 4860],
#[364, 364, 384, 420, 4860],
#[364, 364, 400, 420, 420],
#[364, 380, 384, 400, 420],
#[360, 400, 400, 400, 420],
#[360, 384, 400, 420, 420],
#[360, 380, 400, 420, 4860],
#[348, 380, 466, 4860, 4860],
#[348, 384, 420, 4860, 4860],
#[348, 400, 420, 420, 4860],
#[348, 420, 420, 420, 420],

]
    timestart=time.time()
    manualCheck(prefixs,tails)
    #manualCheck(prefixs,tails,0)
    print("time used:%f"%(time.time()-timestart))

def checkSerachBaseOnExistingPoints():
    pthG.loadValuToLinkMapDic() 

    beginPrefix=[104, 120, 120, 280, 328]
    #endPrefix=[120, 120, 140, 280, 328]
    #endPrefix=[120, 120, 208, 280, 328]
    #endPrefix=[120, 120, 240, 280, 328]
    #endPrefix=[140, 208, 260, 280, 328]
    endPrefix=[104, 280, 280, 280, 328]
    beginTails=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 574, 4860],
        [364, 380, 400, 590, 1080],
    ]
    endTails=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 1080, 4860],
    ]
    
    newprefix,newtails=getMiddlePrefixTailsWithVaryTailsLen(beginPrefix,beginTails,endPrefix,endTails)
    print("midPrefix## %s got %d tails"%(newprefix,len(newtails)))
    idx=0
    for tail in newtails:
        idx+=1
        print("tail-%d:%s"%(idx,tail))
    #BPDB.addSimulationsPrefixWithTailsToDB()

def checkRangeMidOfsameDimTails():
    pthG.loadValuToLinkMapDic() 
    beginPrefix=[104, 260, 280, 280, 364] 
    endPrefix=[104, 260, 280, 280, 364] 
    beginTails=[
        [364, 364, 364, 400, 4860],
        [364, 364, 364, 420, 420],
        [364, 364, 380, 380, 420],
        [364, 364, 380, 384, 400],
    ]
    endTails=[
        [364, 364, 364, 380, 4860],
        [364, 364, 364, 384, 420],
        [364, 364, 364, 400, 400],
        [364, 364, 380, 380, 384],
    ]
    pattner=[104,104,120,120,120,280,280,280,364,364]
    rangelist=[2,2,2,2]
    prefix,tails,evalues=CheckMidOfRangeWithSameTailsLen(pattner,beginPrefix,endPrefix,endTails,rangelist)
    print("mid prefix:%s with tailsEvalues:%s"%(prefix,evalues))
    idx=0
    for tail in tails:
        print("<%d> %s"%(idx,tail))
        idx+=1


#if __name__=='__main__':moduletest()
if __name__=='__main__':checksomePoints()  
#if __name__=='__main__':checkSerachBaseOnExistingPoints()
#if __name__=='__main__':checkRangeMidOfsameDimTails()




        








    








    




