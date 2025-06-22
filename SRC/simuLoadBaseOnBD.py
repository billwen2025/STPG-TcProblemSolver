#!/usr/bin/python3
import DataBaseTestResults as SimTRDB
import sortlinklist as sorLL
import pathsSeqGen as ptGen
import oneDimOrder as oneDOd

#0. assigen the work table.(initial point already been stored in DB)
#1. get work load from DB, and make simulation to update DB and reduce the workload.
# 1.1  get the latest start point from the worktable with IsBorder==1 UpperFineTune==1
#      1. get the slope , initail var tuple, and the tuples
#      2. inclrease the slope (and var) to get a new tuple that is IsBorder==2/-2, base on the increased slope test result
#      3. base on the direction (+/-) of this new tuple. make simulations to check if their results cross the border.
#           3.1 gen linkStrucs
#           3.2 make simulations (if already have reslut in DB, just get reslut and not run simulation)
#           3.3 gether results
#      4.(candidates process) if those results are in/out border( base on direction), those crossed results are IsBorder=1, others are IsBorder==2/-2 and need the one more round simualtions.
#           4.1 collect results and store them in the DB. if the resluts crossed then they are border candidates(IsBorder=1 but UpperFineTune==0). Otherwise IsBorder==2/-2.
#           4.2 for those new created IsBorder==2/-2 records in DB (the probram already checked their creation records--- should this be stored in DB?)
#               4.2.1  border test keys (stored in ckCandidates) : trying keys. Tuples to record: tuple[0] the borderkey, tuple[1] the slope increased key. others the trying keys. If processes are broken, then database keep the track of the process.
#               4.2.2  When the simulation finished. Update result base on simulation results, if result crossed,  points belongs to  candidates. Otherswise,set IsBorder==2/-2  but UpperFineTune==0, and those points need to proceed to next one step test. to change them into border candidates(IsBorder=1 but UpperFineTune==0). 
#               4.2.3  For those pending Outsiders (IsBorder=2/-2 but UpperFineTune==0), make them concreat by one more step test.  if this one more step test fail to cross the border, those pending Outsiders is sure outsider (IsBorder=2/-2 UpperFineTune==1), and new pending ousider points need to check; if that one more step success to cross the border, then the pending Outsiders turned to sure outsider(IsBorder=2/-2 UpperFineTune==1), and no new pending ousider points need to check.
#                       the  pending Outsiders can indenpendenly checked by  (IsBorder=2/-2 but UpperFineTune==0), untill UpperFineTune==1.
#      5.(borders process) for all border candidates(IsBorder=1 but UpperFineTune==0).  verify all dimentions to make them the border point (IsBorder=1 but UpperFineTune==1)
#               each pathi in this candidate should record the checked ones and unchecked.## todo 2 database change to consider how to make this work and trackable.
#               5.1  if all dimentions checked. then it is border point  UpperFineTune==0.
#               5.2  if some dimention failed. then some dimention have an improved candidate, then this old border candidate(IsBorder=1 but UpperFineTune==1) will be IsBorder=2/-2 and a new candidate will be evaluated next.

TVALUE_TC=0.074
TVALUE_DEDUCTUPPER=0.15
TVALUE_DEDUCTLOWER=0.03
TVALUE_DELTA=0.00005

ISBORDER_UNTEST=0
ISBORDER_SET=1
ISBORDER_UPPER=2
ISBORDER_LOWER=-2

UPPERFINETUNE_UNTEST=0
UPPERFINETUNE_SET=1
UPPERFINETUNE_SUB=-1

DIMTTP_DRIVE=0
DIMTTP_SIMU=1
DIMTTP_FIX=2
DIMTTP_FROMUPPER=3
DIMTTP_FROMLOWER=-3

SLOPCOMPARE_RANGE=0.005# update later, not sure now

#operations and process to schedul simulations
# the states of the process have been stored in DB
# the class is to make simulation base on the DB commands

class SimuOperationsonDB:
    def __init__(self):
        self.startBDPointKey=None
        self.LeftWKPtNum=0
        self.State=0#
        #set by each new BP
        self.CurrentBPkey=None
        self.BorderKeysArray=[]
        self.BordersObjsArray=[]
        self.StartMidLinktuple=None
        self.BPLinkStruObj=None
        self.BPTValue=0
        #candidates check stage
        self.incrSlopeLkobj=None
        self.RawCandidatesLKStrucs=[]
        self.candidatesCkResultsLKStrucs=[]
        #border check state
        self.RawBordersLKStrucs=[]
        self.BorderCkResultsLKStrucs=[]
        pass


    def runsimu(self):

        self.getStatesAndWorkLoads()
        
        if self.State!=0:
            self.pendingStatesCheckAndResume()
        
        self.getTheWorkLoad()


    #from DB
    #get state and the tasks
    def getStatesAndWorkLoads(self):
        self.LeftWKPtNum=SimTRDB.getWorkCountLeft()
        #get states and related mid states if need recorvery   
        #  check the state and the related data 
        self.State=SimTRDB.getWorkState()     
        #read related mid parameters
        #then start the state
        pass    
    #  if it start from the clear work process 
    #  assigne the process and make work secquences normally
    #  otherwise, use the check the pendingStatesAndResume to recover and continue the previous process
    def pendingStatesCheckAndResume(self):
        #if abnormal, set state accordingly
        # base on the abnormal state, preparing the InnerData for that state running
        if self.State==1:
            #recover state1 variables
            self.increaseSlopeAndGetCandidates()#1->2  
            self.checkCandidates()#2->3
            self.updateMiniSlope()#3->4
            self.updateLeftWorkLoad()#4->0          

        elif self.State==2:
            #recover state2 variables
            self.checkCandidates()#2->3
            self.updateMiniSlope()#3->4
            self.updateLeftWorkLoad()#4->0
            
        elif self.State==3:
            #recover state3 variables
            self.updateMiniSlope()#3->4
            self.updateLeftWorkLoad()#4->0
            
        elif self.State==4:
            #recover state4 variables
            self.updateLeftWorkLoad()#4->0 

    def getTheWorkLoadPath1(self):
        self.getTheInitialBorderPoint()#0->1
        self.increaseUpperSlopeFirstLowerSlopFirst()#1->2
    def getTheWorkLoadPath2(self):
        self.getTheInitialBorderPoint()#0->1
        self.increaseUpperSlopeFirstLowerSlopLast()#1->2
    def getTheWorkLoadPath3(self):
        self.getTheInitialBorderPoint()#0->1
        self.increaseUpperSlopeLastLowerSlopFirst()#1->2
    def getTheWorkLoadPath4(self):
        self.getTheInitialBorderPoint()#0->1
        self.increaseUpperSlopeLastLowerSlopLast()#1->2

    #return the Tvalue
    def checklkStruValueBySimu(self,lkStru):
        return 0.0739
    
    def markBorder(self,lkStru):
        return 0.0739

    def increaseUpperSlopeFirstLowerSlopFirst(self):
        Ousider=self.BPLinkStruObj.inCreaseUpperTupleDist(1)
        Ousidercandidate=None
        #if increased successful return new lkstru
        # if reach the top, no room to increase ,return None
        while(Ousider):
            newborder=Ousider.deCreaseLowerTupleDist(1)
            if newborder:
                Tvalue=self.checklkStruValueBySimu(newborder)
            else:
                Tvalue=0
            while Tvalue>(TVALUE_TC+TVALUE_DELTA):            
                newborder=newborder.deCreaseLowerTupleDist(1)
                if newborder:
                    Tvalue=self.checklkStruValueBySimu(newborder)
                else:
                    Tvalue=0
            else:
                if Tvalue>0:
                    self.markBorder(newborder)
                    Ousidercandidate=newborder.inCreaseUpperTupleDist(1)
                    if Ousidercandidate:
                        Tvalue=self.checklkStruValueBySimu(Ousidercandidate)
                    else:
                        Tvalue=TVALUE_TC+TVALUE_DELTA+0.01 #the upper part already reach limit
                    while Tvalue<(TVALUE_TC+TVALUE_DELTA): 
                        self.markBorder(Ousidercandidate)           
                        Ousidercandidate=Ousidercandidate.inCreaseUpperTupleDist(1)
                        if Ousidercandidate:
                            Tvalue=self.checklkStruValueBySimu(Ousidercandidate)
                        else:
                            Tvalue=TVALUE_TC+TVALUE_DELTA+0.01
                else:
                    Ousidercandidate=None #the lower part already reach limit
                Ousider=Ousidercandidate
            
        


        

    def getTheInitialBorderPoint(self):
        #get all (IsBorder=1 and UpperFineTune=1) items
        #compare the slope of them, choose the bigest slope as the 
        # InitialBorderPoint . set self.CurrentBPkey and border keys array
        self.CurrentBPkey,self.BorderKeysArray=SimTRDB.getMostSlopingBorderPointAndAllBorderKey()
        print(f"BPkey:{self.CurrentBPkey} bdkeyarray{str(self.BorderKeysArray)}")
        self.fetchNewBorderPointDatas()#instance objects in class
        self.State=1#begin to cacluate candidates
        #work stage changed
        SimTRDB.UpdateWorkState(self.State)
        SimTRDB.commitChanges()
        pass

    def increaseSlopeAndGetCandidates(self):        
        #inclrease slope of it and set it to be the outsider 
        #store in db
        self.getIncSlopeBPLinkSturKey()
        #generate raw candidates, store them in DB temperary field
        self.getRawLinksStrusforCandidates()
        #run deduct or simulation to get results, updated the temperary field
        self.crystallizeCandidatesLinkStrus()  

        self.State=2#candidate cacluation finished
        SimTRDB.UpdateWorkState(self.State)
        SimTRDB.commitChanges()
     
        pass

    def checkCandidates(self):
        #get candidates to border test set
        self.getRawBordersLinkStruList()
        #run deduct or simulation to get results
        self.crystallizeBordersLinkSturList()

        self.State=3#border cacluation finished
        SimTRDB.UpdateWorkState(self.State)
        SimTRDB.commitChanges()

        pass

    def updateMiniSlope(self):
        #get all (IsBorder=1 and UpperFineTune=0) items
        #check the solpe of them, and choose a increased minial one as new border
        # set the new border's UpperFineTune=1, all others set to -1.
        # UpperFineTune=1 already been set, change some new border to -1
        SimTRDB.getLeastSlopeIncreaseUpdateKey(self.BPLinkStruObj.hops3Slope+SLOPCOMPARE_RANGE)

        self.State=4#database update finished
        SimTRDB.UpdateWorkState(self.State)
        SimTRDB.commitChanges()
        pass

    def updateLeftWorkLoad(self):
        #update the left work load count in db
        # clear the middle data records in db table workload 
        self.LeftWKPtNum-=1
        if self.LeftWKPtNum>0:
            SimTRDB.UpdateLeftWorkCount(self.LeftWKPtNum)
        
        self.State=0#change back initial
        SimTRDB.UpdateWorkState(self.State)
        SimTRDB.commitChanges()
        #reinitialize the global vars
        self.startBDPointKey=None
        #set by each new BP
        self.CurrentBPkey=None
        self.BorderKeysArray=[]
        self.BordersObjsArray=[]
        self.StartMidLinktuple=None
        self.BPLinkStruObj=None
        self.BPTValue=0
        #candidates check stage
        self.incrSlopeLkobj=None
        self.RawCandidatesLKStrucs=[]
        self.candidatesCkResultsLKStrucs=[]
        #border check state
        self.RawBordersLKStrucs=[]
        self.BorderCkResultsLKStrucs=[]

    ###helper funcs
    #the self.CurrentBPkey already been set
    def fetchNewBorderPointDatas(self):
        #read db to get related data for class 
        #base on self.CurrentBPkey, get all realted data
        self.BPLinkStruObj=SimTRDB.getLkStruObjByHkey(self.CurrentBPkey)
    
        for key in self.BorderKeysArray:
            bordobj=SimTRDB.getLkStruObjByHkey(key)
            self.BordersObjsArray.append(bordobj)
        self.StartMidLinktuple=self.BPLinkStruObj.getMidTuple()
        print("middle:%s"%(str(self.StartMidLinktuple)))
        self.BPTValue=SimTRDB.getTvalueByHKey(self.CurrentBPkey)
        pass

    #read only
    def getBPLinkStru(self):
        return self.BPLinkStruObj
    #read only
    def getBPTValue(self):
        return self.BPTValue
    #read and write
    def getTestDim(self,linkStru):
        testDimobj=SimTRDB.getTestDimObjByHkey(linkStru.HashValue)

        return testDimobj
    #write and store to db
    def setTestDim(self,linkStru,testDimobj):
        SimTRDB.updateTestDim(linkStru.HashValue,testDimobj)
        pass

    #gen slope increased linkStru object incrSlopeLkobj base on the current BPobj
    #  set the deduced the Tvalue , store it in the db, the changes made is base one the StartMidLinktuple
    #  in temperory db field store ckcandidates (0,1) as key of BPobj and the incrSlopeLkobj
    def getIncSlopeBPLinkSturKey(self):
        self.incrSlopeLkobj=sorLL.increaseSlope(self.BPLinkStruObj,self.StartMidLinktuple)
        theincSlopTvalue=0
        
        
        if self.incrSlopeLkobj.BorderValueCompare>0:
            theincSlopTvalue=TVALUE_DEDUCTUPPER
            print("Increase BP key:%s"%(self.incrSlopeLkobj.HashValue))
        elif self.incrSlopeLkobj.BorderValueCompare<0:
            theincSlopTvalue=TVALUE_DEDUCTLOWER
            print("Decrease BP key:%s"%(self.incrSlopeLkobj.HashValue))

        testedDims=sorLL.getonestepTestDimention(self.BPLinkStruObj,self.incrSlopeLkobj,self.incrSlopeLkobj.BorderValueCompare,1,self.StartMidLinktuple)

        SimTRDB.InsertResult(self.incrSlopeLkobj,theincSlopTvalue,testedDims)
        if self.incrSlopeLkobj.BorderValueCompare>0:
            SimTRDB.UpdateIsBorder(self.incrSlopeLkobj,2)
            SimTRDB.UpdateUpperFineTune(self.incrSlopeLkobj,1)
        else:
            SimTRDB.UpdateIsBorder(self.incrSlopeLkobj,-2)
            SimTRDB.UpdateUpperFineTune(self.incrSlopeLkobj,1)

        candidatesTuple=(self.CurrentBPkey,self.incrSlopeLkobj.HashValue)
        SimTRDB.UpdateCandidatesCkTempValue(str(candidatesTuple))

        


        SimTRDB.commitChanges()
        pass  
    # base on the new genernerated incrSlopeLkobj, 
    #   generate linkStrus increaeding/decreaseing half links base on self.StartMidLinktuple
    #   store them in the db and keep them is class object RawCandidatesLKstruc for next stage processing
    # testobjclist is just the lkstru objs array
    def getRawLinksStrusforCandidates(self):
        #base on tested dim to make candidates
        listcandiuncheck=sorLL.genCandidates(self.incrSlopeLkobj,self.incrSlopeLkobj.BorderValueCompare,self.StartMidLinktuple)
        print("got Rawcandidates len:%d"%(len(listcandiuncheck)))
        

        #check the db, remove the duplicated RawCandidatesLKStrucs
        newtuples=[]
        for tup in listcandiuncheck:
            inRawCandidates=0
            for rowcandi in self.RawCandidatesLKStrucs:
                if rowcandi[0].HashValue==tup[0].HashValue:
                    inRawCandidates=1
                    break
            if inRawCandidates:
                continue
            if SimTRDB.aleadyInDB(tup[0])==0:
                print("new Rawcandidate key:%s"%(tup[0].HashValue))
                newtuples.append(tup)
        #
        if len(newtuples)>0:
            
            self.RawCandidatesLKStrucs.extend(newtuples)

            candidatesTuple=(self.CurrentBPkey,self.incrSlopeLkobj.HashValue)

            for tup in self.RawCandidatesLKStrucs:
                print("add Rawcandidate key:%s"%(tup[0].HashValue))
                SimTRDB.InsertResult(tup[0],0,tup[1])
                candidatesTuple=candidatesTuple+(tup[0].HashValue,)

            print("self.RawCandidatesLKStrucs len:%d"%(len(self.RawCandidatesLKStrucs)))

            SimTRDB.UpdateCandidatesCkTempValue(str(candidatesTuple))

            SimTRDB.commitChanges()

            return 
        
    def getRawLinksStrusforCandidatesLkStruArray(self):
        arrayreturnlist=[]
        for tup in self.RawCandidatesLKStrucs:
            arrayreturnlist.append(tup[0])
        return arrayreturnlist


    
    # base on the resultdic, classified the linkstrus in RawCandidatesLKStrucs as 
    # furthtestobjs: need furth test , on the same direction
    # gotresultobjs: got reaults already.
    def CheckRawCandidatesforRowBroder(self,resultdic):
        #need further test keys
        furthtestkeys=[]
        gotresultkeys=[]
        #proprocess self.RawCandidatesLKStrucs
        keyidxmap={}
        idx=0
        for tupl in self.RawCandidatesLKStrucs:
            keyidxmap[tupl[0].HashValue]=idx
            idx+=1
        
        #check Raw
        for reskey in resultdic.keys():
            if reskey==self.CurrentBPkey or reskey==self.incrSlopeLkobj.HashValue:
                #ignore and should not happend
                continue
            value=resultdic[reskey]
            if abs(value- TVALUE_TC)<=TVALUE_DELTA:
                #pass the check got the border
                gotresultkeys.append(reskey)
                SimTRDB.UpdateIsBorder(linkobj,1)
                SimTRDB.UpdateUpperFineTune(linkobj,1)
                print("Confirmed border key:%s"%(linkobj.HashValue))
                continue
            idx=keyidxmap[reskey]
            lkstruTestDimtup=self.RawCandidatesLKStrucs[idx]
            testDim=lkstruTestDimtup[1]
            for linkkey in testDim.keys():
                if testDim[linkkey][1]==3:
                    if value > TVALUE_TC:
                        furthtestkeys.append(reskey)  # new candidates later confirm  
                        SimTRDB.UpdateIsBorder(linkobj,2) # outsider 
                        SimTRDB.UpdateUpperFineTune(linkobj,1)#confirmed
                        print("Confirmed +Outsider key:%s"%(linkobj.HashValue))                                            
                    else:
                        gotresultkeys.append(reskey)
                        linkobj=lkstruTestDimtup[0]
                        SimTRDB.UpdateIsBorder(linkobj,1)# crossed ,must be candidates
                        print("Confirmed border candidate key:%s"%(linkobj.HashValue))
                        
                    # in case there are many 3 
                    break
                elif testDim[linkkey][1]==-3:
                    if value < TVALUE_TC:
                        furthtestkeys.append(reskey)  # new candidates later confirm                       
                    else:
                        gotresultkeys.append(reskey)
                        linkobj=lkstruTestDimtup[0]
                        SimTRDB.UpdateIsBorder(linkobj,2) # outsider 
                        SimTRDB.UpdateUpperFineTune(linkobj,1)#confirmed
                        print("Confirmed +Outsider key:%s"%(linkobj.HashValue))
                        
                    # in case there are many -3
                    break
        gotresultobjs=[]
        furthtestobjs=[]
        for key in gotresultkeys:
            idx=keyidxmap[key]
            lkstrucobj=self.RawCandidatesLKStrucs[idx][0]
            gotresultobjs.append(lkstrucobj)

        for key in furthtestkeys:
            idx=keyidxmap[key]
            furthtestobjs.append(self.RawCandidatesLKStrucs[idx][0])

        return gotresultobjs, furthtestobjs
    
    #source node's results updated in the db
    #if some border found, return the bordercandidate list
    def judgeTheSourObjResults(self,sourceNodeobjs,RawCandidatesLKStrucs,gotresultsobjs,furthtestobjs):
        borderCandidatelist=[]
        if len(sourceNodeobjs)>0:
            # match the source and the candidates accroding gotresultsobj spread from this obj    
            indexedSourcobjs={}#idx:obj
            indexedSourcobjs=sorLL.getSourceIdxfromRwoList(sourceNodeobjs,RawCandidatesLKStrucs)
            for lkstrobj in sourceNodeobjs:
                value=SimTRDB.getTvalueByHKey(lkstrobj.HashValue)
                if value>TVALUE_TC:
                    print("Confirmed +Outsider key:%s"%(lkstrobj.HashValue)) 
                    SimTRDB.UpdateIsBorder(lkstrobj,2)
                    SimTRDB.UpdateUpperFineTune(lkstrobj,1)
                else:
                    # and if one of  the gotreasultobjs is border candidate, the mathing source is is outsider.
                    # if all the gotreasultobj is outsider, the  mathing source is candidate
                    oneCandidate=0
                    allOutSider=1
                    for idx in indexedSourcobjs.keys():
                        #different key(idx) may have same source object
                        if indexedSourcobjs[idx].HashValue==lkstrobj.HashValue:
                            tup=RawCandidatesLKStrucs[idx]
                            if tup[0] in gotresultsobjs:
                                isborder,finetune=SimTRDB.getIsBorderFineTuneByHKey(tup[0].HashValue)
                                if isborder==1:
                                    oneCandidate=1                                    
                                    if allOutSider==1:
                                        allOutSider=0
                            if tup[0] in furthtestobjs:
                                oneCandidate=1                                    
                                if allOutSider==1:
                                    allOutSider=0

                    if oneCandidate and allOutSider==0:
                        print("Confirmed -Outsider key:%s"%(lkstrobj.HashValue))
                        SimTRDB.UpdateIsBorder(lkstrobj,-2)
                        SimTRDB.UpdateUpperFineTune(lkstrobj,1)
                    elif oneCandidate==0 and allOutSider:# all outsiders 
                        print("Confirmed border candidate key:%s"%(lkstrobj.HashValue))
                        SimTRDB.UpdateIsBorder(lkstrobj,1)#border candidate
                        borderCandidatelist.append(lkstrobj)


        return borderCandidatelist
    

    #check firstly by deduct, then by simulation
    #for failed , proceed to get the border candidate
    # in this process, the RawCandidatesLKstruc may change,
    #       if the lkstru have been verified and recored in candidatesCkResultsLKstrucs, it will be reoved from RawCandidatesLKstruc
    #       if we need more test in simulation, RawCandidatesLKstruc will add those new test linkstrus
    #result and mid variables stored in db
    def crystallizeCandidatesLinkStrus(self):

        totestlist=self.getRawLinksStrusforCandidatesLkStruArray()
        leftlist=self.checkValidByDeduct(totestlist)#the got result lkstruc is stored in candidatesCkResultsLKstrucs
        resultdic={}
        if len(leftlist)>0:
            #print("to simulation first obj key:%s"%(leftlist[0].HashValue))
            print("crystallizeCandidatesLinkStrus leftlist len:%d"%(len(leftlist)))
            resultdic=self.checkValidBySimu(leftlist)#the got result lkstruc is stored in candidatesCkResultsLKstrucs,  
        sourceNodeobjs=[]
        #first incrSlopeLkobj is ousider for sure
        #if self.incrSlopeLkobj.BorderValueCompare<0:
        #    sourceNodeobjs.append(self.incrSlopeLkobj)


        gotresultsobjs,furthtestobjs=self.CheckRawCandidatesforRowBroder(resultdic)
        self.candidatesCkResultsLKStrucs.extend(gotresultsobjs)
        # if more test needed them new  linkstru added to RawCandidatesLKstruc
        
        while len(furthtestobjs)>0:
            print("furthtest in crystallizeCandidates")
            #the orginal source must not be border
            candilist=self.judgeTheSourObjResults(sourceNodeobjs,self.RawCandidatesLKStrucs,gotresultsobjs,furthtestobjs)
            self.candidatesCkResultsLKStrucs.extend(candilist)
            self.RawCandidatesLKStrucs=[]
            #set new candidates    
            newtuples=[]         
            for obj in furthtestobjs:
                newlist=sorLL.genCandidates(obj,self.incrSlopeLkobj.BorderValueCompare,self.StartMidLinktuple) 
                for newtup in newlist:
                    newinArray=1
                    for tup in newtuples:
                        if newtup[0].HashValue==tup[0].HashValue:
                            #duplicate
                            newinArray=0
                            break
                    if newinArray:
                        newtuples.append(newtup)
                                                     
            for tup in newtuples:
                if SimTRDB.aleadyInDB(tup[0])==0:
                    print("new Rawcandidate key:%s"%(tup[0].HashValue))
                    self.RawCandidatesLKStrucs.append(tup)

            #and new source
            sourceNodeobjs=furthtestobjs.copy()   
            #update temp data in db
            candidatesTuple=(self.CurrentBPkey,self.incrSlopeLkobj.HashValue)
        
            for tup in self.RawCandidatesLKStrucs:
                SimTRDB.InsertResult(tup[0],0,tup[1])
                candidatesTuple=candidatesTuple+(tup[0].HashValue,)

            SimTRDB.UpdateCandidatesCkTempValue(str(candidatesTuple))

            SimTRDB.commitChanges()

            #new round test
            totestlist=self.getRawLinksStrusforCandidatesLkStruArray()
            leftlist=self.checkValidByDeduct(totestlist)#the got result lkstruc is stored in candidatesCkResultsLKstrucs
            resultdic={}
            if len(leftlist)>0:
                print("crystallizeCandidatesLinkStrus leftlist2 len:%d"%(len(leftlist)))
                resultdic=self.checkValidBySimu(leftlist)#the got result lkstruc is stored in candidatesCkResultsLKstrucs, 

            #got new round test results
            gotresultsobjs,furthtestobjs=self.CheckRawCandidatesforRowBroder(resultdic) 
            self.candidatesCkResultsLKStrucs.extend(gotresultsobjs)
        else:
            #set source obj            
            candilist=self.judgeTheSourObjResults(sourceNodeobjs,self.RawCandidatesLKStrucs,gotresultsobjs,furthtestobjs)
            self.candidatesCkResultsLKStrucs.extend(candilist)
            self.RawCandidatesLKStrucs=[]  
   
        # until RawCandidatesLKstruc is empty        
        # all evaluating and results should be strod in db 
        pass
    
    #get candidates to border test set
    #generate initail list and store the list to RawBordersLKStrucs
    #return the borderCheckArrays
    def getRawBordersLinkStruList(self):
        #for the new test results, test them if they are corressed border point.
        #check all recordes with isborder==0 and finetune==0
        #base on the from link relations, set the is isborder, 
        #   for failed border test records, finetune=1(confired outsider) and isborder= +- 2
        #   for success border ,set isborder=1 and finetune===0(not set)-- those are border candidates, and need next further border verify.
        # all of them should be in self.candidatesCkResultsLKStrucs
        print("Border Candidates checking")
        unmarkedLkstrus=SimTRDB.getUnmakedCandidatesLkstru()# should be none if exit; should be border candidates
        if len(unmarkedLkstrus)>0:
            for lkstru in unmarkedLkstrus:
                SimTRDB.UpdateIsBorder(lkstru,1)
                self.candidatesCkResultsLKStrucs.append(lkstru)
                
        #generate RowBordertestset based on left border candidates
        bdCandidatesKeylist=[]        
        for bordercandi in self.candidatesCkResultsLKStrucs:
            testdim=SimTRDB.getTestDimObjByHkey(bordercandi.HashValue)
            bdCandidatesKeylist.append(bordercandi.HashValue)
            newlist=sorLL.genBorderTestset(bordercandi,testdim,self.StartMidLinktuple)
            for itm in newlist:
                inRawAlready=0
                for tup in self.RawBordersLKStrucs:
                    if tup[0].HashValue== itm[0].HashValue:
                        inRawAlready=1
                        break
                if inRawAlready==0: 
                    if SimTRDB.aleadyInDB(itm[0])==0:
                        self.RawBordersLKStrucs.append(itm) #RawBordersLKStrucs make sure no repeated items

        #generate border test sets for border test        

        bdcandidate=tuple(bdCandidatesKeylist)
        SimTRDB.UpdateBordersCkTempValue(str(bdcandidate))

        SimTRDB.commitChanges()
    ##
    ##     
    ##
    def getRawBordersLinkStruListLkStruArray(self):
        testObjlist=[]
        for tup in self.RawBordersLKStrucs:
            if SimTRDB.aleadyInDB(tup[0])==0:
                SimTRDB.InsertResult(tup[0],0,tup[1])
                testObjlist.append(tup[0])
        SimTRDB.commitChanges()
        return testObjlist

    
    def judgeBorderckResults(self,candidateslist,RawBordersLKStrucs):
        #check if the RawBorder is not 2 , it will be the new candidate
        #        find the corresponding candidate and and make it outsider
        indexedSourcobjs={}#idx:obj
        indexedSourcobjs=sorLL.getSourceIdxfromRwoList(candidateslist,RawBordersLKStrucs)
        failedcandidate=[]
        newborderobjs=[]
        for tuple in RawBordersLKStrucs:
            print("check the result for key:%s"%(tuple[0].HashValue))
            isborder,finetune=SimTRDB.getIsBorderFineTuneByHKey(tuple[0].HashValue)
            if isborder!=2:
                for idx in indexedSourcobjs.keys():
                    if indexedSourcobjs[idx].HashValue==tuple[0].HashValue:
                        failedcandidate.append(candidateslist[idx])
                        newborderobjs.append(tuple[0])
        for candidate in candidateslist:
            if candidate not in failedcandidate:
                #confirmed border
                SimTRDB.UpdateUpperFineTune(candidate,1)
                print("confirm border key:%s"%(candidate.HashValue))
                testDim=SimTRDB.getTestDimsByLinkStruc(candidate)
                for key in testDim.keys():
                    if testDim[key][1]!=2:
                        testDim[key][0]=1
                SimTRDB.updateTestDim(candidate.HashValue,testDim)
        return newborderobjs

    #base on the border candidates's generated checkleast results
    #results strored in BorderCkResultsLKStrucs
    # db updated already
    def checkBorderCandidatesforBorders(self):
        #some candidates results may got by deducting
        newbordercandidates=self.judgeBorderckResults(self.candidatesCkResultsLKStrucs,self.RawBordersLKStrucs)
        self.candidatesCkResultsLKStrucs=[]

        if len(newbordercandidates)>0:
            self.candidatesCkResultsLKStrucs.extend(newbordercandidates)

        pass

    #check firstly by deduct, then by simulation
    # result stored in db
    # RawBordersLKStrucs keep the checking lkstrus and BorderCkResultsLKStrucs keep the results
    # RawBordersLKStrucs and BorderCkResultsLKStrucs should synchronized to db
    def crystallizeBordersLinkSturList(self):
        while(len(self.candidatesCkResultsLKStrucs)>0):
            testobjlist=self.getRawBordersLinkStruListLkStruArray()
            leftlist=self.checkValidByDeduct(testobjlist)
            if len(leftlist)>0:
                resultdic=self.checkValidBySimu(leftlist)#update value in db already
                self.checkBorderCandidatesforBorders()
                self.getRawBordersLinkStruList() 
        pass


    #decuct by known borders
    def checkValidByDeduct(self,linkStucArray):
        #check if the linkstru already have result in db

        #check known slopes of border/subborder points, choose one that best fit the slope and in a dist range
        #  if slopes in the range and best fit, compare the mean value with that of the border/subborder point.
        #  otherwise, unknown. for unknown case  need simulation in this table build process.
        UnCheckObjArray=[]
        if linkStucArray and len(linkStucArray)>0:
            for lkstuc in linkStucArray:
                #get Tvalue key of this obj
                tvalueindb=SimTRDB.getTvalueByHKey(lkstuc.HashValue)
                if tvalueindb and abs(tvalueindb)>TVALUE_DELTA:
                    #ready set by some one some time early
                    print("key:%s already got Tvalue"%(lkstuc.HashValue))
                    continue
                setbydeduct=0
                for borderobj in self.BordersObjsArray:#all borderobj have call it already
                    if abs(borderobj.hops3Slope-lkstuc.hops3Slope)<SLOPCOMPARE_RANGE:
                        #compare it with the mean value
                        setbydeduct=1
                        if borderobj.hops3means>lkstuc.hops3means:
                            #valid
                            lkstuc.BorderValueCompare=-1
                            SimTRDB.UpdateTvalueByHKey(lkstuc.HashValue,TVALUE_DEDUCTLOWER)
                        else:
                            lkstuc.BorderValueCompare=1
                            SimTRDB.UpdateTvalueByHKey(lkstuc.HashValue,TVALUE_DEDUCTUPPER)   
                        print("key:%s got Tvalue by deducing"%(lkstuc.HashValue))                 
                    
                if setbydeduct==0:
                    #the uncheck array
                    UnCheckObjArray.append(lkstuc)  
                    print("key:%s will get Tvalue by simulation"%(lkstuc.HashValue))               
            #the left array objects return
            #if len(UnCheckObjArray)>0:
            #    print("returned first obj key:%s "%(UnCheckObjArray[0].HashValue)) 
        return UnCheckObjArray         

    #run simulations and get resluts
    # result stored in db
    def checkValidBySimu(self,lefLinkSturArray):
        #preparing simualtion
        dirlist=ptGen.genDirlistForArraySimu(lefLinkSturArray)
        #run simulation
            #for the list, each linkstru make a dir, make a config file for each dir.
            #          copy simualtion code to dir, and record all the dirs
            #run simulation for those dirs
        ptGen.runSimulationOnDirlist(dirlist)#wait untill got results
        #collect results
        resultdic=ptGen.collectReslutsOnDirlist(dirlist)
        #update db
        for hashkey in resultdic.keys():
            print("get result for key:%s"%(hashkey))
            value=resultdic[hashkey]
            SimTRDB.UpdateTvalueByHKey(hashkey,value)
            if value>(TVALUE_TC+TVALUE_DELTA):
                SimTRDB.UpdateIsBorderByHKey(hashkey,2)
                SimTRDB.UpdateUpperFineTuneByHKey(hashkey,1)

        SimTRDB.commitChanges()
        return resultdic
    

def moduletest():
    SimTRDB.OpenDatabase()
    oneDOd.initialOrderList()
    simuobj=SimuOperationsonDB()
    simuobj.runsimu()
    SimTRDB.CloseDatabase()

if __name__=='__main__':moduletest()   
