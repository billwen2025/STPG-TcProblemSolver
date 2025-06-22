#!/usr/bin/python3
import BorderPointDB as BPDB
import pathsSeqGen as pthGen
import sortlinklist as sorLL
import findTailsFHSTtoSHFL as TMgr
import matplotlib.pyplot as plt
import numpy as np
import math,os

def checkDBComplete():
    allprefixs=pthGen.enumerateDBprefix()
    missprefixs=[]
    for prefix in allprefixs:
        tails=BPDB.getTailsofPrefix(prefix)
        if len(tails)==0:
            missprefixs.append(prefix)
    return missprefixs

def insertMissingPrefixbyDeduct():
    missprefixs=checkDBComplete()
    needckprefixs=[]
    newaddedprefixs=[]
    for missprix in missprefixs:
        upperprefix,lowerprefix=BPDB.findUpperAndLowerPrefixInDB(missprix[0],missprix[1],missprix[2],missprix[3],missprix[4])
        uppertails=BPDB.getTailsofPrefix(upperprefix)
        lowertails=BPDB.getTailsofPrefix(lowerprefix)
        if len(uppertails)==len(lowertails):
            #use the uppertails as tail of this prefix
            #id4,id5 is equal
            linksDic={'F1': [0.011,0.011], 'F2': [0.011,0.011], 'F3': [0.011,0.011], 'F4': [0.011,0.011], 'F5': [0.011,0.011],'F6': [0.015,0.015,0.015], 'F7': [0.011,0.011], 'F8':[0.011,0.011], 'F9': [0.011,0.011], 'F10':[0.011,0.011]}
            for value in missprix:
                idx=missprix.index(value)
                key='F%d'%(idx+1)
                link=pthGen.ValuToLinkMapDic[value]
                linksDic[key]=link

            for value in uppertails:
                idx=uppertails.index(value)
                key='F%d'%(idx+6)
                link=pthGen.ValuToLinkMapDic[value]
                linksDic[key]=link
            
            linksStruobj=sorLL.linkArryStru(linksDic)
            BPDB.addLinksToBDDB(linksStruobj,0,BPDB.GOTTYPE_DERIVED,BPDB.TODOACT_SIMUCK)
            newaddedprefixs.append(missprix)
        else:
            needckprefixs.append(missprix)            
    return needckprefixs,newaddedprefixs

def updateDBwithTheMissing(newadded, manualcheck):
    print("The following prefixs need to be checked by manual now! If sofware developped, then replace the following print with functions!")
    for prefix in newadded:
        print("check by Simulation for the prefix in DB:[%d,%d,%d,%d,%d]"%(prefix[0],prefix[1],prefix[2],prefix[3],prefix[4]))
    for prefix in manualcheck:
        print("check by FHST then SHFT with prefix then add to DB:[%d,%d,%d,%d,%d]"%(prefix[0],prefix[1],prefix[2],prefix[3],prefix[4]))
#bplist: (linkdic,tvalue) list
def buildDBwithSimulationResults(bplist):
    for bptup in bplist:
        linksStruobj=sorLL.linkArryStru(bptup[0])
        Tvalue=bptup[1]
        BPDB.addLinksToBDDB(linksStruobj,Tvalue)

#return the tree
#BFT borad first search

#we first search DB wiht prefix, then find tails,
#with tails, we build the search tree. one type of tails one tree.
#so the tree is for tails start id is id6 (idx start from 1), the whole logical need to be rewriten.

def buildSearchTreeWithTails(tails):
    # 初始化根节点
    root = sorLL.treeitm(0)
    
    # 遍历每个路径
    for path in tails:
        current_node = root
        for i, node_id in enumerate(path):
            # 查找当前节点的子节点
            found_child = None
            if current_node.FirstChild:
                current_child = current_node.FirstChild
                while current_child:
                    if current_child.Value == node_id:
                        found_child = current_child
                        break
                    #current_child = current_child.siblingMap.get(current_child.Value, None)
                    current_child = current_child.siblingMap.get(node_id, None)
            
            if found_child is None:
                # 如果子节点不存在，则创建新节点
                new_child = sorLL.treeitm(node_id, current_node)
                if current_node.FirstChild is None:
                    current_node.addfirstChild(new_child, node_id, node_id)
                else:
                    current_node.FirstChild.addSibling(node_id, new_child)
                current_node = new_child
            else:
                # 如果子节点存在，则移动到该子节点
                current_node = found_child
    
    return root

def buildSearchTreeWithDB():
    #the Root node is id0, a virtual id, just used to organize tree
    root=sorLL.treeitm(0)
    id1=0
    id2=0
    id3=0
    id4=0
    id5=0
    id6=0
    id7=0
    id8=0
    id9=0
    id10=0

    id1s=BPDB.getBDPointsNextHopIDs([])
    firstchild=sorLL.treeitm(id1s[0],root)
    root.addfirstChild(firstchild,id1s[-1],id1s[0])    
    for id1 in id1s:
        if id1!=firstchild.Value:
            otherchild=sorLL.treeitm(id1,root)
            firstchild.addSibling(id1,otherchild)
    for id1 in firstchild.siblingMap.keys():
        otherchild=firstchild.siblingMap[id1]
        otherchild.copySiblingfromFirst(firstchild)
    
    id2objects=[]
    for id1 in firstchild.siblingMap.keys():
        id1obj=firstchild.siblingMap[id1]
        id2s=BPDB.getBDPointsNextHopIDs([id1])
        firstChildID1=sorLL.treeitm(id2s[0],id1obj)
        id2objects.append(firstChildID1)
        id1obj.addfirstChild(firstChildID1,id2s[-1],id2s[0])
        for id2 in id2s:
            if id2!=firstChildID1.Value:
                otherchild=sorLL.treeitm(id2,id1obj)
                id2objects.append(otherchild)
                firstChildID1.addSibling(id2,otherchild)
        for id2 in firstChildID1.siblingMap.keys():
            otherchild=firstChildID1.siblingMap[id2]
            otherchild.copySiblingfromFirst(firstChildID1)


    id3objects=[]
    for id2obj in id2objects:
        id1=id2obj.Parent.Value
        id2=id2obj.Value
        prefixary=[id1,id2]
        id3s=BPDB.getBDPointsNextHopIDs(prefixary)
        firstChildID2=sorLL.treeitm(id3s[0],id2obj)
        id3objects.append(firstChildID2)
        id2obj.addfirstChild(firstChildID2,id3s[-1],id3s[0])
        for id3 in id3s:
            if id3!=firstChildID2.Value:
                otherchild=sorLL.treeitm(id3,id2obj)
                id3objects.append(otherchild)
                firstChildID2.addSibling(id3,otherchild)
        for id3 in firstChildID2.siblingMap.keys():
            otherchild=firstChildID2.siblingMap[id3]
            otherchild.copySiblingfromFirst(firstChildID2)

    id4objects=[]
    for id3obj in id3objects:
        id1=id3obj.Parent.Parent.Value
        id2=id3obj.Parent.Value
        id3=id3obj.Value
        prefixary=[id1,id2,id3]
        id4s=BPDB.getBDPointsNextHopIDs(prefixary)
        firstChildID3=sorLL.treeitm(id4s[0],id3obj)
        id4objects.append(firstChildID3)
        id3obj.addfirstChild(firstChildID3,id4s[-1],id4s[0])
        for id4 in id4s:
            if id4!=firstChildID3.Value:
                otherchild=sorLL.treeitm(id4,id3obj)
                id4objects.append(otherchild)
                firstChildID3.addSibling(id4,otherchild)
        for id4 in firstChildID3.siblingMap.keys():
            otherchild=firstChildID3.siblingMap[id4]
            otherchild.copySiblingfromFirst(firstChildID3)
    
    id5objects=[]
    for id4obj in id4objects:
        id1=id4obj.Parent.Parent.Parent.Value
        id2=id4obj.Parent.Parent.Value
        id3=id4obj.Parent.Value
        id4=id4obj.Value
        prefixary=[id1,id2,id3,id4]
        id5s=BPDB.getBDPointsNextHopIDs(prefixary)
        firstChildID4=sorLL.treeitm(id5s[0],id4obj)
        id5objects.append(firstChildID4)
        id4obj.addfirstChild(firstChildID4,id5s[-1],id5s[0])
        for id5 in id5s:
            if id5!=firstChildID4.Value:
                otherchild=sorLL.treeitm(id5,id4obj)
                id5objects.append(otherchild)
                firstChildID4.addSibling(id5,otherchild)
        for id5 in firstChildID4.siblingMap.keys():
            otherchild=firstChildID4.siblingMap[id5]
            otherchild.copySiblingfromFirst(firstChildID4)

    id6objects=[]
    for id5obj in id5objects:
        id1=id5obj.Parent.Parent.Parent.Parent.Value
        id2=id5obj.Parent.Parent.Parent.Value
        id3=id5obj.Parent.Parent.Value
        id4=id5obj.Parent.Value
        id5=id5obj.Value
        prefixary=[id1,id2,id3,id4,id5]
        id6s=BPDB.getBDPointsNextHopIDs(prefixary)
        firstChildID5=sorLL.treeitm(id6s[0],id5obj)
        id6objects.append(firstChildID5)
        id5obj.addfirstChild(firstChildID5,id6s[-1],id6s[0])
        for id6 in id6s:
            if id6!=firstChildID5.Value:
                otherchild=sorLL.treeitm(id6,id5obj)
                id6objects.append(otherchild)
                firstChildID5.addSibling(id6,otherchild)
        for id6 in firstChildID5.siblingMap.keys():
            otherchild=firstChildID5.siblingMap[id6]
            otherchild.copySiblingfromFirst(firstChildID5)

    id7objects=[]
    for id6obj in id6objects:
        id1=id6obj.Parent.Parent.Parent.Parent.Parent.Value
        id2=id6obj.Parent.Parent.Parent.Parent.Value
        id3=id6obj.Parent.Parent.Parent.Value
        id4=id6obj.Parent.Parent.Value
        id5=id6obj.Parent.Value
        id6=id6obj.Value
        prefixary=[id1,id2,id3,id4,id5,id6]
        id7s=BPDB.getBDPointsNextHopIDs(prefixary)
        firstChildID6=sorLL.treeitm(id7s[0],id6obj)
        id7objects.append(firstChildID6)
        id6obj.addfirstChild(firstChildID6,id7s[-1],id7s[0])
        for id7 in id7s:
            if id7!=firstChildID6.Value:
                otherchild=sorLL.treeitm(id7,id6obj)
                id7objects.append(otherchild)
                firstChildID6.addSibling(id7,otherchild)
        for id7 in firstChildID6.siblingMap.keys():
            otherchild=firstChildID6.siblingMap[id7]
            otherchild.copySiblingfromFirst(firstChildID6)

    id8objects=[]
    for id7obj in id7objects:
        id1=id7obj.Parent.Parent.Parent.Parent.Parent.Parent.Value
        id2=id7obj.Parent.Parent.Parent.Parent.Parent.Value
        id3=id7obj.Parent.Parent.Parent.Parent.Value
        id4=id7obj.Parent.Parent.Parent.Value
        id5=id7obj.Parent.Parent.Value
        id6=id7obj.Parent.Value
        id7=id7obj.Value
        prefixary=[id1,id2,id3,id4,id5,id6,id7]
        id8s=BPDB.getBDPointsNextHopIDs(prefixary)
        firstChildID7=sorLL.treeitm(id8s[0],id7obj)
        id8objects.append(firstChildID7)
        id7obj.addfirstChild(firstChildID7,id8s[-1],id8s[0])
        for id8 in id8s:
            if id8!=firstChildID7.Value:
                otherchild=sorLL.treeitm(id8,id7obj)
                id8objects.append(otherchild)
                firstChildID7.addSibling(id8,otherchild)
        for id8 in firstChildID7.siblingMap.keys():
            otherchild=firstChildID7.siblingMap[id8]
            otherchild.copySiblingfromFirst(firstChildID7)

    id9objects=[]
    for id8obj in id8objects:
        id1=id8obj.Parent.Parent.Parent.Parent.Parent.Parent.Parent.Value
        id2=id8obj.Parent.Parent.Parent.Parent.Parent.Parent.Value
        id3=id8obj.Parent.Parent.Parent.Parent.Parent.Value
        id4=id8obj.Parent.Parent.Parent.Parent.Value
        id5=id8obj.Parent.Parent.Parent.Value
        id6=id8obj.Parent.Parent.Value
        id7=id8obj.Parent.Value
        id8=id8obj.Value
        prefixary=[id1,id2,id3,id4,id5,id6,id7,id8]
        id9s=BPDB.getBDPointsNextHopIDs(prefixary)
        firstChildID8=sorLL.treeitm(id9s[0],id8obj)
        id9objects.append(firstChildID8)
        id8obj.addfirstChild(firstChildID8,id9s[-1],id9s[0])
        for id9 in id9s:
            if id9!=firstChildID8.Value:
                otherchild=sorLL.treeitm(id9,id8obj)
                id9objects.append(otherchild)
                firstChildID8.addSibling(id9,otherchild)
        for id9 in firstChildID8.siblingMap.keys():
            otherchild=firstChildID8.siblingMap[id9]
            otherchild.copySiblingfromFirst(firstChildID8)

    for id9obj in id9objects:
        id1=id9obj.Parent.Parent.Parent.Parent.Parent.Parent.Parent.Parent.Value
        id2=id9obj.Parent.Parent.Parent.Parent.Parent.Parent.Parent.Value
        id3=id9obj.Parent.Parent.Parent.Parent.Parent.Parent.Value
        id4=id9obj.Parent.Parent.Parent.Parent.Parent.Value
        id5=id9obj.Parent.Parent.Parent.Parent.Value
        id6=id9obj.Parent.Parent.Parent.Value
        id7=id9obj.Parent.Parent.Value
        id8=id9obj.Parent.Value
        id9=id9obj.Value
        prefixary=[id1,id2,id3,id4,id5,id6,id7,id8,id9]
        id10s=BPDB.getBDPointsNextHopIDs(prefixary)
        firstChildID9=sorLL.treeitm(id10s[0],id9obj)
        
        id9obj.addfirstChild(firstChildID9,id10s[-1],id10s[0])
        for id10 in id10s:
            if id10!=firstChildID9.Value:
                otherchild=sorLL.treeitm(id10,id9obj)
                
                firstChildID9.addSibling(id10,otherchild)
        for id10 in firstChildID9.siblingMap.keys():
            otherchild=firstChildID9.siblingMap[id10]
            otherchild.copySiblingfromFirst(firstChildID9)

    return root



        
def drawIDScatterPointsInDB():
    hopsArray=[]
    linkIDArray=[]
    #build above two array base on DB data
    idDicArray=BPDB.getAllValidIDTuplesInDB()
    for thedic in idDicArray:
        for hop in thedic.keys():
            linkID=thedic[hop]
            if linkID<108000:#otherwise, it is impossible value
                hopsArray.append(hop)
                linkIDArray.append(thedic[hop])
    
    x = np.array(hopsArray)
    y = np.array(linkIDArray)
    plt.scatter(x, y)
    plt.show()

###################################
#############  add tails in db  ##################
##################################

#prefix already in db, tail maybe need to added
#border point need to added
#all border points already have simulation results
def addSimulationsPrefixWithTailsToDB(prefix,tailslist):
    objlist=[]
    resultlist=[]
    BPDB.OpenDatabase()
    
    for tail in tailslist:
        BPDB.addTailtoDB(tail)
        obj=TMgr.buildlinkStrufromPrefixTail(prefix,tail)
        objlist.append(obj)

    tailsValue=BPDB.addTailsToDB(tailslist)
    prefixValue=BPDB.prefixMetric(prefix)
    TMgr.createTailsMgr(prefix)
    #should called aready with those list, just to get sim result by a simple interface
    resultlist=TMgr.TailsMgr.wrapperGetSimuResultWithRepeatableObjs(objlist)
    
    for idx in range(len(objlist)):
        obj=objlist[idx]
        result=resultlist[idx]
        BPDB.addLinksToBDDB(obj,result)

    BPDB.setfixRLOfPrefixWithTails(prefix,tailslist)
    
    print("prefixValue:%d tailsValue:%s"%(prefixValue,tailsValue))
    BPDB.updatePrefixState(prefix)
    BPDB.commitChanges()
    BPDB.CloseDatabase()

#the range have been confirm by checking both end points
#some prefix in the range may already have been in DB
def addDeductPrefixRangeWithSameTailsToDB(prefixlist,tails):
    result=0.0199885
    BPDB.OpenDatabase()
    for prefix in prefixlist:
        #TMgr.createTailsMgr(prefix)
        #objlist=[]
        for tail in tails:
            BPDB.addTailtoDB(tail)
            obj=TMgr.buildlinkStrufromPrefixTail(prefix,tail)
            #objlist.append(obj)
            BPDB.addLinksToBDDB(obj,result,gotType=BPDB.GOTTYPE_DERIVED,todoType=BPDB.TODOACT_NONE)

        BPDB.updatePrefixState(prefix,State=BPDB.PREFIX_STATE_DEDUC_TAILS)
    BPDB.commitChanges()
    BPDB.CloseDatabase()
    pass
        
#########
### work plan related
########
CKTYPE_MID1=1
CKTYPE_MID3=2
CKTYPE_LOOP1=3

def insertWorkPlans():
    BPDB.OpenDatabase()
    ## plan range 1
    StartPrefixV=000
    EndPrefixV=111
    PreFixPattern=[0,0,1,1,2,2,3,3,4,4]
    tails0=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    tails1=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    CKtype=CKTYPE_MID1
    CKparam0=0
    CKparam1=0
    BPDB.addWorkPlanItem(StartPrefixV,EndPrefixV,PreFixPattern,tails0,tails1,CKtype,CKparam0,CKparam1)
    ## plan range 2
    StartPrefixV=000
    EndPrefixV=111
    PreFixPattern=[0,0,1,1,2,2,3,3,4,4]
    tails0=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    tails1=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    CKtype=CKTYPE_MID1
    CKparam0=0
    CKparam1=0
    BPDB.addWorkPlanItem(StartPrefixV,EndPrefixV,PreFixPattern,tails0,tails1,CKtype,CKparam0,CKparam1)
    ## plan range 3
    StartPrefixV=000
    EndPrefixV=111
    PreFixPattern=[0,0,1,1,2,2,3,3,4,4]
    tails0=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    tails1=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    CKtype=CKTYPE_MID1
    CKparam0=0
    CKparam1=0
    BPDB.addWorkPlanItem(StartPrefixV,EndPrefixV,PreFixPattern,tails0,tails1,CKtype,CKparam0,CKparam1)
    ## plan range 4
    StartPrefixV=000
    EndPrefixV=111
    PreFixPattern=[0,0,1,1,2,2,3,3,4,4]
    tails0=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    tails1=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    CKtype=CKTYPE_MID1
    CKparam0=0
    CKparam1=0
    BPDB.addWorkPlanItem(StartPrefixV,EndPrefixV,PreFixPattern,tails0,tails1,CKtype,CKparam0,CKparam1)
    ## plan range 5
    StartPrefixV=000
    EndPrefixV=111
    PreFixPattern=[0,0,1,1,2,2,3,3,4,4]
    tails0=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    tails1=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    CKtype=CKTYPE_MID1
    CKparam0=0
    CKparam1=0
    BPDB.addWorkPlanItem(StartPrefixV,EndPrefixV,PreFixPattern,tails0,tails1,CKtype,CKparam0,CKparam1)
    ## plan range 6
    StartPrefixV=000
    EndPrefixV=111
    PreFixPattern=[0,0,1,1,2,2,3,3,4,4]
    tails0=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    tails1=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    CKtype=CKTYPE_MID1
    CKparam0=0
    CKparam1=0
    BPDB.addWorkPlanItem(StartPrefixV,EndPrefixV,PreFixPattern,tails0,tails1,CKtype,CKparam0,CKparam1)
    ## plan range 7
    StartPrefixV=000
    EndPrefixV=111
    PreFixPattern=[0,0,1,1,2,2,3,3,4,4]
    tails0=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    tails1=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    CKtype=CKTYPE_MID1
    CKparam0=0
    CKparam1=0
    BPDB.addWorkPlanItem(StartPrefixV,EndPrefixV,PreFixPattern,tails0,tails1,CKtype,CKparam0,CKparam1)
    ## plan range 8
    StartPrefixV=000
    EndPrefixV=111
    PreFixPattern=[0,0,1,1,2,2,3,3,4,4]
    tails0=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    tails1=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    CKtype=CKTYPE_MID1
    CKparam0=0
    CKparam1=0
    BPDB.addWorkPlanItem(StartPrefixV,EndPrefixV,PreFixPattern,tails0,tails1,CKtype,CKparam0,CKparam1)
    ## plan range 9
    StartPrefixV=000
    EndPrefixV=111
    PreFixPattern=[0,0,1,1,2,2,3,3,4,4]
    tails0=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    tails1=[
        [364, 364, 4860, 4860, 4860],
        [364, 380, 384, 4860, 4860],
        [364, 380, 400, 420, 4860],
        [364, 380, 400, 466, 466],
        [364, 384, 420, 420, 466]
    ]
    CKtype=CKTYPE_MID1
    CKparam0=0
    CKparam1=0
    BPDB.addWorkPlanItem(StartPrefixV,EndPrefixV,PreFixPattern,tails0,tails1,CKtype,CKparam0,CKparam1)
    BPDB.commitChanges()
    BPDB.CloseDatabase()

#check one point is one mid point of the prefix range
#check 3 points is lowermid mid uppermid of the prefix range
def dotheCheckWrokAndSetResult(startprefixValue,endPrefixFalue,prefixPattner,tails1,tails2,CkType,CKparam0,CKparam1):
    BPDB.OpenDatabase()
    prefixlist=BPDB.getPrefixArrayByRange(prefixPattner,startprefixValue,endPrefixFalue)
    totallen=len(prefixlist)
    mid=math.floor(totallen/2)
    lowermid=math.floor(mid/2)
    uppermid=math.floor((mid+totallen)/2)
    if CkType==CKTYPE_MID1:
        #check one mid point
        #just use the tails1
        prefix=prefixlist[mid]
        rangelist=[]
        if CKparam0==0:
            for tail in tails1:
                rangelist.append(1) #just check one step for each tail
        tailsChoose, tailsEvalue=TMgr.checkthePrefixPoint(prefix,tails1,rangelist)
        result=BPDB.WORK_VERRES_OK
        for taileva in tailsEvalue:
            if taileva<0:
                if result==BPDB.WORK_VERRES_OK:
                    result=BPDB.WORK_VERRES_LOWER
                elif result==BPDB.WORK_VERRES_UPPER:
                    result=BPDB.WORK_VERRES_MIX
            elif taileva>0:
                if result==BPDB.WORK_VERRES_OK:
                    result=BPDB.WORK_VERRES_UPPER
                elif result==BPDB.WORK_VERRES_LOWER:
                    result=BPDB.WORK_VERRES_MIX
        chkprefixvalue=BPDB.prefixMetric(prefix) 

        if result!=BPDB.WORK_VERRES_OK:
            BPDB.UpdateWorkPlanItem(startprefixValue,result,chkprefixvalue)
        else:
            BPDB.UpdateWorkPlanItem(startprefixValue,result,BPDB.WORK_LOCKFLAG)         
        pass
    if CkType==CKTYPE_MID3:
        # check lowermid mid uppermid 3 points

        prefix=prefixlist[mid]
        rangelist=[]
        if CKparam0==0:
            for tail in tails1:
                rangelist.append(1) #just check one step for each tail
        tailsChoose, tailsEvalue=TMgr.checkthePrefixPoint(prefix,tails1,rangelist)
        result1=BPDB.WORK_VERRES_OK
        for taileva in tailsEvalue:
            if taileva<0:
                if result1==BPDB.WORK_VERRES_OK:
                    result1=BPDB.WORK_VERRES_LOWER
                elif result1==BPDB.WORK_VERRES_UPPER:
                    result1=BPDB.WORK_VERRES_MIX
            elif taileva>0:
                if result1==BPDB.WORK_VERRES_OK:
                    result1=BPDB.WORK_VERRES_UPPER
                elif result1==BPDB.WORK_VERRES_LOWER:
                    result1=BPDB.WORK_VERRES_MIX
        chkmidprefixvalue=BPDB.prefixMetric(prefix)

        prefix=prefixlist[lowermid]
        rangelist=[]
        if CKparam0==0:
            for tail in tails1:
                rangelist.append(1) #just check one step for each tail
        tailsChoose, tailsEvalue=TMgr.checkthePrefixPoint(prefix,tails1,rangelist)
        result2=BPDB.WORK_VERRES_OK
        for taileva in tailsEvalue:
            if taileva<0:
                if result2==BPDB.WORK_VERRES_OK:
                    result2=BPDB.WORK_VERRES_LOWER
                elif result2==BPDB.WORK_VERRES_UPPER:
                    result2=BPDB.WORK_VERRES_MIX
            elif taileva>0:
                if result2==BPDB.WORK_VERRES_OK:
                    result2=BPDB.WORK_VERRES_UPPER
                elif result2==BPDB.WORK_VERRES_LOWER:
                    result2=BPDB.WORK_VERRES_MIX
        chklowmidprefixvalue=BPDB.prefixMetric(prefix)

        prefix=prefixlist[uppermid]
        rangelist=[]
        if CKparam0==0:
            for tail in tails1:
                rangelist.append(1) #just check one step for each tail
        tailsChoose, tailsEvalue=TMgr.checkthePrefixPoint(prefix,tails1,rangelist)
        result3=BPDB.WORK_VERRES_OK
        for taileva in tailsEvalue:
            if taileva<0:
                if result3==BPDB.WORK_VERRES_OK:
                    result3=BPDB.WORK_VERRES_LOWER
                elif result3==BPDB.WORK_VERRES_UPPER:
                    result3=BPDB.WORK_VERRES_MIX
            elif taileva>0:
                if result3==BPDB.WORK_VERRES_OK:
                    result3=BPDB.WORK_VERRES_UPPER
                elif result3==BPDB.WORK_VERRES_LOWER:
                    result3=BPDB.WORK_VERRES_MIX
        chkuppermidprefixvalue=BPDB.prefixMetric(prefix)
        prefixvalue=BPDB.WORK_VERRES_OK
        prefixvalue=chkmidprefixvalue
        if result1==BPDB.WORK_VERRES_OK and result2==BPDB.WORK_VERRES_OK and result3==BPDB.WORK_VERRES_OK:
            result=BPDB.WORK_VERRES_OK
            prefixvalue=chkmidprefixvalue
        elif result1==BPDB.WORK_VERRES_MIX:
            result=BPDB.WORK_VERRES_MIX
            prefixvalue=chkmidprefixvalue
        elif result2==BPDB.WORK_VERRES_MIX:
            result=BPDB.WORK_VERRES_MIX
            prefixvalue=chklowmidprefixvalue
        elif result3==BPDB.WORK_VERRES_MIX:
            result=BPDB.WORK_VERRES_MIX
            prefixvalue=chkuppermidprefixvalue
        elif result1==BPDB.WORK_VERRES_UPPER:
            result=BPDB.WORK_VERRES_UPPER
            prefixvalue=chkmidprefixvalue
        elif result2==BPDB.WORK_VERRES_UPPER:
            result=BPDB.WORK_VERRES_UPPER
            prefixvalue=chklowmidprefixvalue
        elif result3==BPDB.WORK_VERRES_UPPER:
            result=BPDB.WORK_VERRES_UPPER
            prefixvalue=chkuppermidprefixvalue
        elif result1==BPDB.WORK_VERRES_LOWER:
            result=BPDB.WORK_VERRES_LOWER
            prefixvalue=chkmidprefixvalue
        elif result2==BPDB.WORK_VERRES_LOWER:
            result=BPDB.WORK_VERRES_LOWER
            prefixvalue=chklowmidprefixvalue
        elif result3==BPDB.WORK_VERRES_LOWER:
            result=BPDB.WORK_VERRES_LOWER
            prefixvalue=chkuppermidprefixvalue

        
        if result!=BPDB.WORK_VERRES_OK:
            BPDB.UpdateWorkPlanItem(startprefixValue,result,prefixvalue)
        else:
            BPDB.UpdateWorkPlanItem(startprefixValue,result,BPDB.WORK_LOCKFLAG)  
        pass

    if CkType==CKTYPE_LOOP1:
        # check with tails1 and tail2 in a loop pattner,check 3 points
        # CKparam0: 0: patter is 1212...
        mideven=0
        uppermideven=0
        lowermideven=0
        if CKparam0==0:
            if mid%2==0:
                mideven=1
            else:
                mideven=0
            
            if uppermid%2==0:
                uppermideven=1
            else:
                uppermideven=0
            
            if lowermid%2==0:
                lowermideven=1
            else:
                lowermideven=0
            
            
        prefix=prefixlist[mid]
        rangelist=[]
        if CKparam0==0:
            for tail in tails1:
                rangelist.append(1) #just check one step for each tail
        if mideven:
            tailsChoose, tailsEvalue=TMgr.checkthePrefixPoint(prefix,tails1,rangelist)
        else:
            tailsChoose, tailsEvalue=TMgr.checkthePrefixPoint(prefix,tails2,rangelist)
        result1=BPDB.WORK_VERRES_OK
        for taileva in tailsEvalue:
            if taileva<0:
                if result1==BPDB.WORK_VERRES_OK:
                    result1=BPDB.WORK_VERRES_LOWER
                elif result1==BPDB.WORK_VERRES_UPPER:
                    result1=BPDB.WORK_VERRES_MIX
            elif taileva>0:
                if result1==BPDB.WORK_VERRES_OK:
                    result1=BPDB.WORK_VERRES_UPPER
                elif result1==BPDB.WORK_VERRES_LOWER:
                    result1=BPDB.WORK_VERRES_MIX
        chkmidprefixvalue=BPDB.prefixMetric(prefix)

        prefix=prefixlist[lowermid]
        rangelist=[]
        if CKparam0==0:
            for tail in tails1:
                rangelist.append(1) #just check one step for each tail
        if lowermideven:
            tailsChoose, tailsEvalue=TMgr.checkthePrefixPoint(prefix,tails1,rangelist)
        else:
            tailsChoose, tailsEvalue=TMgr.checkthePrefixPoint(prefix,tails2,rangelist)
        result2=BPDB.WORK_VERRES_OK
        for taileva in tailsEvalue:
            if taileva<0:
                if result2==BPDB.WORK_VERRES_OK:
                    result2=BPDB.WORK_VERRES_LOWER
                elif result2==BPDB.WORK_VERRES_UPPER:
                    result2=BPDB.WORK_VERRES_MIX
            elif taileva>0:
                if result2==BPDB.WORK_VERRES_OK:
                    result2=BPDB.WORK_VERRES_UPPER
                elif result2==BPDB.WORK_VERRES_LOWER:
                    result2=BPDB.WORK_VERRES_MIX
        chklowmidprefixvalue=BPDB.prefixMetric(prefix)

        prefix=prefixlist[uppermid]
        rangelist=[]
        if CKparam0==0:
            for tail in tails1:
                rangelist.append(1) #just check one step for each tail
        if uppermideven:
            tailsChoose, tailsEvalue=TMgr.checkthePrefixPoint(prefix,tails1,rangelist)
        else:
            tailsChoose, tailsEvalue=TMgr.checkthePrefixPoint(prefix,tails2,rangelist)
        result3=BPDB.WORK_VERRES_OK
        for taileva in tailsEvalue:
            if taileva<0:
                if result3==BPDB.WORK_VERRES_OK:
                    result3=BPDB.WORK_VERRES_LOWER
                elif result3==BPDB.WORK_VERRES_UPPER:
                    result3=BPDB.WORK_VERRES_MIX
            elif taileva>0:
                if result3==BPDB.WORK_VERRES_OK:
                    result3=BPDB.WORK_VERRES_UPPER
                elif result3==BPDB.WORK_VERRES_LOWER:
                    result3=BPDB.WORK_VERRES_MIX
        chkuppermidprefixvalue=BPDB.prefixMetric(prefix)
        prefixvalue=BPDB.WORK_VERRES_OK
        prefixvalue=chkmidprefixvalue
        if result1==BPDB.WORK_VERRES_OK and result2==BPDB.WORK_VERRES_OK and result3==BPDB.WORK_VERRES_OK:
            result=BPDB.WORK_VERRES_OK
            prefixvalue=chkmidprefixvalue
        elif result1==BPDB.WORK_VERRES_MIX:
            result=BPDB.WORK_VERRES_MIX
            prefixvalue=chkmidprefixvalue
        elif result2==BPDB.WORK_VERRES_MIX:
            result=BPDB.WORK_VERRES_MIX
            prefixvalue=chklowmidprefixvalue
        elif result3==BPDB.WORK_VERRES_MIX:
            result=BPDB.WORK_VERRES_MIX
            prefixvalue=chkuppermidprefixvalue
        elif result1==BPDB.WORK_VERRES_UPPER:
            result=BPDB.WORK_VERRES_UPPER
            prefixvalue=chkmidprefixvalue
        elif result2==BPDB.WORK_VERRES_UPPER:
            result=BPDB.WORK_VERRES_UPPER
            prefixvalue=chklowmidprefixvalue
        elif result3==BPDB.WORK_VERRES_UPPER:
            result=BPDB.WORK_VERRES_UPPER
            prefixvalue=chkuppermidprefixvalue
        elif result1==BPDB.WORK_VERRES_LOWER:
            result=BPDB.WORK_VERRES_LOWER
            prefixvalue=chkmidprefixvalue
        elif result2==BPDB.WORK_VERRES_LOWER:
            result=BPDB.WORK_VERRES_LOWER
            prefixvalue=chklowmidprefixvalue
        elif result3==BPDB.WORK_VERRES_LOWER:
            result=BPDB.WORK_VERRES_LOWER
            prefixvalue=chkuppermidprefixvalue

        if result!=BPDB.WORK_VERRES_OK:
            BPDB.UpdateWorkPlanItem(startprefixValue,result,prefixvalue)
        else:
            BPDB.UpdateWorkPlanItem(startprefixValue,result,BPDB.WORK_LOCKFLAG)
        ##wait for update  BorderDB in range


    BPDB.commitChanges()
    BPDB.CloseDatabase()

def checkOnWrokItems():
    #fetchItem that have not be done
    BPDB.OpenDatabase()
    work=BPDB.getFirstUntouchedWorkItems()
    BPDB.CloseDatabase()

    dotheCheckWrokAndSetResult(work[0],work[1],work[2],work[3],work[4],work[5],work[6],work[7])

def buildTreeWithTailsInDB():
    searchTreeObjDic={}
    
    tailsDic=BPDB.getTailsDicInDB()
    for tailsV in tailsDic:
        tails=tailsDic[tailsV]
        if tailsV==0:
            treeobj=None
        else:
            treeobj=buildSearchTreeWithTails(tails)
        searchTreeObjDic[tailsV]=treeobj  
        #print("tailsV:%d set"%(tailsV))  
    
    return searchTreeObjDic

checkhistOneInst=[] #clear for each problem instance
checkhisAll=[]

def savechkHisToDir(DirPath):
    global checkhistOneInst,checkhisAll
    fileOneInstName="checkhistOneInst.txt"
    fileAllInstName="checkhisAll.txt"
    fileOneInstPath=os.path.join(DirPath,fileOneInstName)
    fileAllInstPath=os.path.join(DirPath,fileAllInstName)

    with open(fileOneInstPath,'w') as f:
        strline=str(checkhistOneInst)
        f.writelines(strline)
        f.flush()
    with open(fileAllInstPath,'w') as f:
        strline=str(checkhisAll)
        f.writelines(strline)
        f.flush()
        
    return fileOneInstPath,fileAllInstPath

def checkLinksValid(prefix,tail,searchDic):
    prefixValue=BPDB.prefixMetric(prefix)
    print("prefixValue:%d"%prefixValue)
    if prefixValue<=978670:
       global checkhistOneInst,checkhisAll
    
       TailsV=BPDB.getTailsVByPrefix(prefix)       
       if TailsV<0:
           print("prefix:%s TailsV:%d ?<0 !!!"%(prefix,TailsV))       
           return 1
       if prefixValue not in checkhistOneInst:
           checkhistOneInst.append(prefixValue)

       if prefixValue not in checkhisAll:
           checkhisAll.append(prefixValue)

       searchobj=searchDic[TailsV]
       if searchobj==None:
           print("searchobj is None")
           return 1
       else:
           #print("TailsValue:%d"%(TailsV))
           #searchobj.print_tree()
           result=searchobj.compare_tail(tail)
           return result
    else:
        return 1
def moduletest():
    pthGen.loadValuToLinkMapDic()

    tails = [
        [1, 2, 3, 4, 5],
        [1, 2, 3, 6, 7],
        [1, 8, 9, 10, 11],
        [1, 2, 3, 4, 8],
        [1, 2, 3, 6, 9],
        [1, 8, 9, 10, 12],
    ]
    root=buildSearchTreeWithTails(tails)
    root.print_tree()
    checktail=[1, 8, 10, 10, 10]
    result=root.compare_tail(checktail)
    print("compare result:%d"%result)



if __name__=='__main__':moduletest()
