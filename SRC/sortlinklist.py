#!/usr/bin/python3
import os,csv,shutil,re,math,random
import numpy as np
import oneDimOrder as oneDOd
import pathsSeqGen as pathgen
import xml.etree.ElementTree as ET
import pickle
import hashlib


# 最小二乘 拟合直线
# data_x data_y : 同维度的列表。表示Xy 坐标。
# return  w,b 表示斜率，截距。

def fitline(data_x, data_y):
    m = len(data_y)
    x_bar = np.mean(data_x)
    sum_yx = 0
    sum_x2 = 0
    sum_delta = 0
    for i in range(m):
        x = data_x[i]
        y = data_y[i]
        sum_yx += y * (x - x_bar)
        sum_x2 += x ** 2
    # 根据公式计算w
    w = sum_yx / (sum_x2 - m * (x_bar ** 2))

    for i in range(m):
        x = data_x[i]
        y = data_y[i]
        sum_delta += (y - w * x)
    b = sum_delta / m
    return w, b

def linkTupleValue(lktupl):
    if len(lktupl)==4:
        mean=(0.01+lktupl[0])/2+(0.01+lktupl[1])/2+(0.01+lktupl[2])/2+(0.01+lktupl[3])/2
        var=((lktupl[0]-lktupl[1])*1.2+(lktupl[1]-lktupl[2])+(lktupl[3]-lktupl[2]))/400
        #var=0
        return mean+var
    elif len(lktupl)==3:
        mean=(0.01+lktupl[0])/2+(0.01+lktupl[1])/2+(0.01+lktupl[2])/2
        subv1=(lktupl[0]-lktupl[1])+0.004
        subv2=(lktupl[2]-lktupl[1])+0.004
        if(subv1+subv2)<0:
            var=(subv1+subv2*1.6)/200
        else:
            if subv2<0.0001 or subv1<0.0001:
                var=0.00015+(subv1*1.6+subv2)/200
            else:
                var=(subv1*1.6+subv2)/200
        #print(f"mean:{mean} var:{var} subv1:{subv1} subv2:{subv2}")
        #var=0
        return mean+var
    elif len(lktupl)==2:
        mean=(0.01+lktupl[0])/2+(0.01+lktupl[1])/2
        var=(lktupl[0]-lktupl[1])/100
        #var=0
        return mean+var
    
def sorlink(item):
    #tup=oneDOd.OneDimOrder[item]
    #return tup[0]
    #return linkTupleValue(item)
    value=pathgen.linkIDValue(list(item))
    return value
    
    
    
def linkTuplesSlope(tuplesArry,hops=3):
    if len(tuplesArry)<2:
        return 0
    if hops==3:
        #fit the hops3MeanList
        data_x=[]
        data_y=[]
        x=0.015
        stepx=0.0015
        for lktupl in tuplesArry:
            mean=linkTupleValue(lktupl)
            data_x.append(x)
            data_y.append(mean)
            x+=stepx
        w,b=fitline(data_x,data_y)
        return w        
    elif hops==2:
        #fit the hops3MeanList
        data_x=[]
        data_y=[]
        x=0.0101
        stepx=0.0005
        for lktupl in tuplesArry:
            mean=linkTupleValue(lktupl)
            data_x.append(x)
            data_y.append(mean)
            x+=stepx
        w,b=fitline(data_x,data_y)
        return w
        
# # 模拟数据
# x = np.arange(1, 17, 1)
# y = np.array([4.00, 6.40, 8.00, 8.80, 9.22, 9.50, 9.70, 10.86, 10.00, 10.20, 10.32, 10.42, 10.50, 11.55, 12.58, 13.60])
# # 计算并绘制
# w, b = fit(x, y)
# pred_y = w * x + b
# plt.scatter(x, y)
# plt.plot(x, pred_y, c='r', label='line')
# plt.show()

#search tree define
class treeitm:
    def __init__(self,IDvalue,ParentNode=None):
        self.Value=IDvalue # value is function as key in sibling lookup
        self.childLowerValue=IDvalue
        self.childUpperValue=IDvalue
        #for fast access siblings, child of the same parent have same siblings; 
        # so it is 1-to-1 map with childLow and childUpper of parent
        self.siblingMap={}#value:treeitm obj                  
        self.FirstChild=None # next treeitm
        self.Parent=ParentNode
    #for first child
    def addSibling(self,siblIDvalue,siblobj):
        parNode=self.Parent
        #print(f"Adding sibling {siblIDvalue} to node {self.Value} lower:{parNode.childLowerValue} upper:{parNode.childUpperValue}")
        self.siblingMap[siblIDvalue]=siblobj
        
        if siblIDvalue>parNode.childUpperValue or parNode.childUpperValue==0:
            parNode.childUpperValue=siblIDvalue
        if siblIDvalue<parNode.childLowerValue or parNode.childLowerValue==0:
            parNode.childLowerValue=siblIDvalue

    #for other child
    def copySiblingfromFirst(self,firstItm):
        firstID=firstItm.Value
        self.siblingMap[firstID]=firstItm
        for IDv in firstItm.siblingMap.keys():
            if IDv!=self.Value:
                self.siblingMap[IDv]=firstItm.siblingMap[IDv]


    
    #firstChild choose the lowerIDvalue object； 
    # (upperIDvalue also valid, but we choose the lowerset)
    def addfirstChild(self,firstchildObj,childUpperValue,childlowerValue):
        #print(f"Adding first child {firstchildObj.Value} to node {self.Value}")
        self.FirstChild=firstchildObj
        self.childLowerValue=childlowerValue
        self.childUpperValue=childUpperValue

    # print the tree structure starting from this node
    def print_tree(self, prefix="", last=True):
        indent = "    "
        branch = "└── " if last else "├── "
        print(f"{prefix}{branch}N({self.Value})")
        if self.FirstChild:
            lastTrue=(len(self.FirstChild.siblingMap.values())==0)
            self.FirstChild.print_tree(prefix + indent, last=lastTrue)
            for sibling in self.FirstChild.siblingMap.values():
                if sibling != self.FirstChild:                    
                    sibling.print_tree(prefix + indent, last=True)

    # compare the given tail with the tree
    def compare_tail(self, tail):
        if self.Parent is not None:
            raise ValueError("compare_tail should only be called on the root node (self.Parent == None)")

        current_node = self
        for idx, node_id in enumerate(tail):
            # Check if the current node has a child with the value node_id
            if current_node.FirstChild:
                current_child = current_node.FirstChild
                while current_child:
                    if current_child.Value == node_id:
                        current_node = current_child
                        break
                    current_child = current_child.siblingMap.get(node_id, None)
                else:
                    # No matching child found, compare with the last matched node
                    #parNode=current_node.Parent
                    #print("ckid:%d currnode0:%d, upper:%d, lower:%d"%(node_id,current_node.Value,current_node.childUpperValue,current_node.childLowerValue))
                    if node_id > current_node.childUpperValue:
                        return 1
                    elif node_id < current_node.childLowerValue:
                        return -1
            else:
                # No children, compare with the current node
                #print("currnode1:%d, upper:%d, lower:%d"%(current_node.Value,current_node.childUpperValue,current_node.childLowerValue))
                #parNode=current_node.Parent
                if node_id  > current_node.childUpperValue:
                    return 1
                elif node_id < current_node.childLowerValue:
                    return -1
                else:
                    return 0

        # If all nodes matched
        return 0

class linkArryStru:
    def __init__(self,linkArryDic,midTuple=None):
        self.linkNum=0
        self.linkPlist=[]#tuples
        self.IDs=[]
        for key in linkArryDic:
            plink=linkArryDic[key]
            theID=pathgen.linkIDValue(plink)
            self.IDs.append(theID)
            self.linkPlist.append(tuple(plink))
            self.linkNum+=1
        self.linkPlist.sort(key=sorlink)
        self.IDs.sort()
        self.HashValue=hashlib.md5(str(self.linkPlist).encode('utf-8')).hexdigest()
        #get middle set
        # self.MidTuple=midTuple#None for the first border lkstru have flatest slope, if not none, the upper lower middle is base one this value
        # self.UpperDist=0
        # self.UpperSlope=0
        # self.LowerDist=0
        # self.LowerSlope=0
        # self.middleArray=[]
        # self.upperArray=[]#r 1-m same value with same r 0 for middle:idx in linkPlist
        # self.lowerArray=[]
        # self.getMiddleTupleArray()

        # #get 2hops3 parameters
        # self.hops2means=0
        # self.hops2msdt=0
        # self.hops2mididx=0
        # self.hops2Slope=0
        # self.hops2MeanList=[]
        # self.hops2vvars={0:[0,0,0],1:[0,0,0]}
        # self.getHops2MeansAndVarsArray()

        # self.hops3means=0
        # self.hops3msdt=0
        # self.hops3mididx=0
        # self.hops3Slope=0
        # self.hops3MeanList=[]
        # self.hops3vvars={0:[0,0,0],1:[0,0,0],2:[0,0,0]}# 0.011,0.015,0.02 count just another index, not standard idx

        # #for border find
        # self.BorderValueCompare=0
        
        # self.getHops3MeansAndVarsArray()


    # def getMiddleTupleArray(self):
    #     if self.MidTuple==None:
    #         mididx=math.ceil(self.linkNum/2)
    #         self.MidTuple=self.linkPlist[mididx]
        
    #     middleValue=linkTupleValue(self.MidTuple)
    #     for key in self.linkPlist:
    #         if len(key)==len(self.MidTuple):
    #             value=linkTupleValue(key)
    #             if value == middleValue:
    #                 self.middleArray.append(key)                    
    #             elif value >= middleValue:
    #                 self.upperArray.append(key)
    #             else:
    #                 self.lowerArray.append(key)

    #     for tupl in self.upperArray:
    #         value=linkTupleValue(tupl)
    #         diff=value-middleValue #+
    #         self.UpperDist+=diff
    #     self.UpperSlope=linkTuplesSlope(self.upperArray,len(self.MidTuple))
    #     for tupl in self.lowerArray:
    #         value=linkTupleValue(tupl)
    #         diff=value-middleValue #-
    #         self.LowerDist+=diff
    #     self.LowerSlope=linkTuplesSlope(self.lowerArray,len(self.MidTuple))
        

    # def inCreaseUpperTupleDist(self,SlopeFirst=0):
    #     if SlopeFirst==0:
    #         #increase middle if there exit
    #         #increase the lease upper ,untill the upper all (0.02...) 
    #         pass
    #     else:
    #         #inclreae the largest upper untill it (0.02...)
    #         #increase the next largest upper
    #         pass
    #     #make new struc and return
    #     linkDic={}
    #     #make new link and keep others
    #     newlkStru=linkArryStru(linkDic)
    #     return newlkStru
    
    # def deCreaseLowerTupleDist(self,SlopeFirst=0):
    #     if SlopeFirst==0:
    #         #decrease middle if there exit
    #         #decrease the biggest lower ,untill the lower all (0.011...) 
    #         pass
    #     else:
    #         #decreae the least lower untill it (0.011...)
    #         #decrease the next least lower
    #         pass
    #     #make new struc and return
    #     linkDic={}
    #     #make new link and keep others
    #     newlkStru=linkArryStru(linkDic)
    #     return newlkStru

    
    #revers string to dict is python eval()
    def outPutToLinksDicStr(self):
        linkDic={}
        idx=0
        for lkTuple in self.linkPlist:
            idx+=1
            key="F%d"%(idx)
            linkDic[key]=list(lkTuple)
        return str(linkDic)
    
    #prefix


    #Below for 2hops3 types links
    #
    #mixture link features
    #try to use some simple index to denote those features
    #those features may changed with new algorithm developed

    # now return means, var[2], vvar[2:3] dict
    # def getHops2MeansAndVarsArray(self):
    #     self.hops2means=0
    #     self.hops2msdt=0
    #     self.hops2MeanList=[]
    #     self.hops2vvars={0:[0,0,0],1:[0,0,0]}# 0.011,0.015,0.02 count just another index, not standard idx
    #     count=0
    #     summean=0
    #     for lktupl in self.linkPlist:
    #         if len(lktupl)==2:
    #             count+=1
    #             #vvar statics
    #             if lktupl[0]==0.011:
    #                 self.hops2vvars[0][0]+=1
    #             if lktupl[0]==0.015:
    #                 self.hops2vvars[0][1]+=1
    #             if lktupl[0]==0.02:
    #                 self.hops2vvars[0][2]+=1
    #             if lktupl[1]==0.011:
    #                 self.hops2vvars[1][0]+=1
    #             if lktupl[1]==0.015:
    #                 self.hops2vvars[1][1]+=1
    #             if lktupl[1]==0.02:
    #                 self.hops2vvars[1][2]+=1
                

    #             mean=linkTupleValue(lktupl)
    #             self.hops2MeanList.append(lktupl)
    #             summean+=mean
                

    #     self.hops2means=summean/count
    #     sdtV=0
    #     for lktupl in self.hops2MeanList:
    #         mean=linkTupleValue(lktupl)
    #         sdtV+=abs(mean-self.hops2means)

    #     self.hops2msdt=sdtV/(count-1)

    #     bestidx=0
    #     bestdiff=0.08
    #     idx=-1
    #     for lktupl in self.linkPlist:
    #         idx+=1
    #         if len(lktupl)==3:                
    #             mean=linkTupleValue(lktupl)
    #             diff=abs(mean-self.hops2means)
    #             if diff<bestdiff:
    #                 bestdiff=diff
    #                 bestidx=idx
    #     self.hops2mididx=bestidx

    #     self.hops2Slope=linkTuplesSlope(self.hops2MeanList,2)

    #     return
    
    # # now return means, var[3], vvar[3:3] dict
    # def getHops3MeansAndVarsArray(self):
    #     self.hops3means=0
    #     self.hops3msdt=0
    #     self.hops3mididx=0
    #     self.hops3MeanList=[]
    #     self.hops3vvars={0:[0,0,0],1:[0,0,0],2:[0,0,0]}# 0.011,0.015,0.02 count just another index, not standard idx
    #     count=0
    #     summean=0
    #     for lktupl in self.linkPlist:
    #         if len(lktupl)==3:
    #             count+=1
    #             #vvar statics
    #             if lktupl[0]==0.011:
    #                 self.hops3vvars[0][0]+=1
    #             if lktupl[0]==0.015:
    #                 self.hops3vvars[0][1]+=1
    #             if lktupl[0]==0.02:
    #                 self.hops3vvars[0][2]+=1
    #             if lktupl[1]==0.011:
    #                 self.hops3vvars[1][0]+=1
    #             if lktupl[1]==0.015:
    #                 self.hops3vvars[1][1]+=1
    #             if lktupl[1]==0.02:
    #                 self.hops3vvars[1][2]+=1
    #             if lktupl[2]==0.011:
    #                 self.hops3vvars[2][0]+=1
    #             if lktupl[2]==0.015:
    #                 self.hops3vvars[2][1]+=1
    #             if lktupl[2]==0.02:
    #                 self.hops3vvars[2][2]+=1


    #             mean=linkTupleValue(lktupl)
    #             self.hops3MeanList.append(lktupl)#link already sorted by initial
    #             summean+=mean

        
    #     self.hops3means=summean/count
    #     sdtV=0
    #     for lktupl in self.hops3MeanList:
    #         mean=linkTupleValue(lktupl)
    #         sdtV+=abs(mean-self.hops3means)

    #     self.hops3msdt=sdtV/(count-1)
    #     bestidx=0
    #     bestdiff=0.08
    #     idx=-1
    #     for lktupl in self.linkPlist:
    #         idx+=1
    #         if len(lktupl)==3:                
    #             mean=linkTupleValue(lktupl)
    #             diff=abs(mean-self.hops3means)
    #             if diff<bestdiff:
    #                 bestdiff=diff
    #                 bestidx=idx
    #     self.hops3mididx=bestidx
    #     self.hops3Slope=linkTuplesSlope(self.hops3MeanList,3)
        
    #     return
    # def getMidTuple(self,hops=3):
    #     if hops==3:
    #         return self.linkPlist[self.hops3mididx]
    #     elif hops==2:
    #         return self.linkPlist[self.hops2mididx]


#got the increaded values
def varHops3LinkStuc(linkStruA,linkStruBTuplsArray):
    varvalue=0
    hop3link=linkStruA.linkPlist[linkStruA.hops3mididx]
    middle=linkTupleValue(hop3link)
    for lktupl  in linkStruBTuplsArray: 
        mean=linkTupleValue(lktupl)
        if mean>middle:
            varvalue=varvalue+(mean-middle)
    return varvalue


#return Upper ,Lower parts
def partitionlinks(LinkStruA,middletuple,hops=3):
    UpperPart=[]
    LowerPart=[]
    initMidtupleValue=linkTupleValue(middletuple)
    totaltupls=len(LinkStruA.hops3MeanList)
    midcount=math.floor(totaltupls/2)
        
    for lktuple in LinkStruA.hops3MeanList:        
        mean=linkTupleValue(lktuple)
        if mean<= initMidtupleValue and len(LowerPart)<midcount:
            LowerPart.append(lktuple)
            print("Lower:%s"%(str(lktuple)))
        elif mean>=initMidtupleValue:
            UpperPart.append(lktuple)
            print("Upper:%s"%(str(lktuple)))
    return UpperPart, LowerPart
        
#increase slope,linkStruA is the border point(add or delete will make the new struct not border point),
#  initMidtupleValue is the first opt linkstru middle link
# the returned value linkStruA is sure not valid border, so its need to check later.  And base on the
#  increaded way in this function (Add or Delete), 
#   the later finding border point is in different ways:
#       increase upper part or decrease de lower part
# getHops3MeansAndVarsArray called before call this func
# return the new linkSturB, that have greater slope but not the border point, 
#
def increaseSlope(linkStruA, initMidtuple,hops=3):
    initMidtupleValue=linkTupleValue(initMidtuple)
    initialslope=linkStruA.hops3Slope
    linksTuples=[]
    UpperPart=[]
    LowerPart=[]

    UpperPart,LowerPart=partitionlinks(linkStruA,initMidtuple,hops)

    #iniVar=varHops3LinkStuc(linkStruA,linksTuples)      

    #use var of the upper increase only, or lower side can decrease or combined decrease or not change.
    # the total solpe should inclrease.

    #from tail to head to check the value possible increase

        
    #firstly get the upper part increase the slope by a single step adding.

    UpperRevers=UpperPart.copy()
    UpperRevers.reverse()
    SetNewValue=0
    newUpperTuples=[]
    for ttuple in UpperRevers:
        if SetNewValue==0:
            # check if  0.011 exist
            newTuple=None
            for idx in range(len(ttuple)):
                if tuple[idx]==0.011:
                    newTuple=list(ttuple)
                    newTuple[idx]=0.015
                    SetNewValue=1
                    break

            if SetNewValue>0:
                newUpperTuples.append(tuple(newTuple))
                break
            

            # check if 0.015 exist
            for idx in range(len(ttuple)):
                if tuple[idx]==0.015:
                    newTuple=list(ttuple)
                    newTuple[idx]=0.02
                    SetNewValue=1
                    break
            if SetNewValue>0:
                newUpperTuples.append(tuple(newTuple))
                break
            newUpperTuples.append(ttuple)
        else:
            newUpperTuples.append(ttuple)
    
    #secondarily,get the lower part increase the slope by a single step deleting.
    # 
    #  check if the lower part can compansate the increased slope. and just make the total slop increase a little.
    #   if the second check fail to make the total slope increase, quit.  
    #  quit is safe because if the lower slop decreaded solution valid ,it can be 

    newLowerTuples=[]
    SetNewValue=0
    #decrease the lower part; the less the better
    for ttuple in LowerPart:
        if SetNewValue==0:
            newTuple=None
            # check if  0.015 exist
            for idx in range(len(ttuple)):
                if ttuple[idx]==0.015:
                    newTuple=list(ttuple)
                    newTuple[idx]=0.011
                    SetNewValue=1
                    break
            if SetNewValue>0:
                newLowerTuples.append(tuple(newTuple))
                continue
            # check if 0.02 exist
            for idx in range(len(ttuple)):
                if ttuple[idx]==0.02:
                    newTuple=list(ttuple)
                    newTuple[idx]=0.015
                    SetNewValue=1
                    break
            if SetNewValue>0:
                newLowerTuples.append(tuple(newTuple))
                continue
            newLowerTuples.append(ttuple)
        else:
            newLowerTuples.append(ttuple)

    ##resultcompare
    # added to the final solution by slop valid checking
    midcheckArrayAdd=[]#linkStruA.hops2MeanList.copy()
    midcheckArrayAdd.extend(LowerPart)
    midcheckArrayAdd.extend(newUpperTuples)
    upperAddedslope=linkTuplesSlope(midcheckArrayAdd,3)

    midcheckArrayDel=[]#linkStruA.hops2MeanList.copy()
    midcheckArrayDel.extend(newLowerTuples)
    midcheckArrayDel.extend(UpperPart)
    lowerAddedslope=linkTuplesSlope(midcheckArrayDel,3)

    print("upper:%f lower:%f initalslope:%f"%(upperAddedslope,lowerAddedslope,initialslope))

    BorderValueCompare=0

    if upperAddedslope>initialslope and lowerAddedslope>initialslope:
        if upperAddedslope>lowerAddedslope:
            #lower part added
            print("lower decreaded")
            returnList=linkStruA.hops2MeanList.copy()
            returnList.extend(midcheckArrayDel)       
            BorderValueCompare=-1
            
        if lowerAddedslope>upperAddedslope:
            #upper part added
            print("upper increaded")
            returnList=linkStruA.hops2MeanList.copy()
            returnList.extend(midcheckArrayAdd)
            BorderValueCompare=1
    elif upperAddedslope>initialslope:
        print("upper1 increaded")
        returnList=linkStruA.hops2MeanList.copy()
        returnList.extend(midcheckArrayAdd)
        BorderValueCompare=1

    elif lowerAddedslope>initialslope:
        print("lower1 decreaded")
        returnList=linkStruA.hops2MeanList.copy()
        returnList.extend(midcheckArrayDel)       
        BorderValueCompare=-1
    else:
        print("No increasing slope possible")
    
    Num=len(returnList)
    print("increase obj links num:%d"%(Num))
    linkDic={}
    for i in range(Num):
        key="F%d"%(i+1)
        linkDic[key]=list(returnList[i])
    linkStruB=linkArryStru(linkDic)
    #base on this value to make next search operations
    linkStruB.BorderValueCompare=BorderValueCompare

    return linkStruB
#bigge: 1 org is bigger than drived; -1 org is smaller than drived. 
#crossvalue: set the crossed value,  1 for all 1, 0 for all 0.
def getonestepTestDimention(linkStrOrg,linkStrDrived,Bigger,corssvalue,middletuple,hops=3):
    if hops==3:
        if corssvalue==1:
            testedDims={
                'F1':[1,2],# crossed? 0 unknow or 1 crossed or -1 failto crossed, tested(or drived or fixed or from )? 1 or 0 or 2  or  3/-3
                'F2':[1,2],#2
                'F3':[1,0],#3
                'F4':[1,0],#4
                'F5':[1,0],#5
                'F6':[1,0],#1
                'F7':[1,0],#4
                'F8':[1,0],#4
                'F9':[1,0],#4
                'F10':[1,0],#2
            }#if all crossed then it is the boundary point
        else:
            testedDims={
                'F1':[1,2],# crossed? 0 unknow or 1 crossed or -1 failto crossed, tested(or drived or fixed or from )? 1 or 0 or 2  or  3/-3
                'F2':[1,2],#2
                'F3':[0,0],#3
                'F4':[0,0],#4
                'F5':[0,0],#5
                'F6':[0,0],#1
                'F7':[0,0],#4
                'F8':[0,0],#4
                'F9':[0,0],#4
                'F10':[0,0],#2
            }#if all crossed then it is the boundary point
            midtupvalue=linkTupleValue(middletuple)
            if Bigger>0:
                #only lower parts need to test
                idx=0
                for tup in linkStrDrived.linkPlist:
                    idx+=1
                    value=linkTupleValue(tup)
                    if value>midtupvalue:
                        key='F%d'%(idx)
                        testedDims[key][0]=1
            else:
                #only upper parts need to test
                idx=0
                for tup in linkStrDrived.linkPlist:
                    idx+=1
                    value=linkTupleValue(tup)
                    if value<midtupvalue:
                        key='F%d'%(idx)
                        testedDims[key][0]=1


        idx=0
        for tup in linkStrDrived.linkPlist:
            idx+=1
            if tup in linkStrOrg.linkPlist:
                continue
            break #only one step change, so we can safely return.
        
        key='F%d'%(idx)
        if Bigger>0:
            testedDims[key][1]=3
        elif Bigger<0:
            testedDims[key][1]=-3
        return testedDims
#BiggerThanTc 1 org > tc, -1 org< tc
def genCandidates(linkStrOrg,BiggerThanTc,middletuple,hops=3):
    candidatelist=[]#(linkstru,testtim)
    hashkeylist=[] #no repeated in the list
    checkValues=[]
    midvalue=linkTupleValue(middletuple)
    if hops==3:
        if BiggerThanTc>0:
            #decrease to make a candidate
            for tup in linkStrOrg.hops3MeanList:
                value=linkTupleValue(tup)  
                if value in checkValues:
                    continue  
                checkValues.append(value)                     
                if value<=midvalue:
                    newtup=oneDOd.getPreOdLink(tup)
                    print("tup:%s pre tup:%s"%(str(tup),newtup))
                    if newtup and linkTupleValue(newtup)>=linkTupleValue((0.011,0.011,0.011)):
                        linkdic=eval(linkStrOrg.outPutToLinksDicStr())
                        for key in linkdic.keys():
                            tlist=linkdic[key]
                            thelink=tuple(tlist)
                            if thelink==tup:
                                linkdic[key]=list(newtup)
                                break
                        linkstrobj=linkArryStru(linkdic)
                        if linkstrobj.HashValue not in hashkeylist:
                            testDim=getonestepTestDimention(linkStrOrg,linkstrobj,1,0,middletuple)
                            #add to list
                            hashkeylist.append(linkstrobj.HashValue)
                            newtuple=(linkstrobj,testDim)
                            candidatelist.append(newtuple)
        else:
            #increase to make a candidate
            for tup in linkStrOrg.hops3MeanList:
                value=linkTupleValue(tup) 
                if value in checkValues:
                    continue  
                checkValues.append(value)                                
                if value>=midvalue:                    
                    newtup=oneDOd.getNextOdLink(tup)
                    print("tup:%s next tup:%s"%(str(tup),newtup))
                    if newtup and linkTupleValue(newtup)<=linkTupleValue((0.02,0.02,0.02)):
                        linkdic=eval(linkStrOrg.outPutToLinksDicStr())
                        for key in linkdic.keys():
                            tlist=linkdic[key]
                            thelink=tuple(tlist)
                            if thelink==tup:
                                linkdic[key]=list(newtup)
                                break
                        linkstrobj=linkArryStru(linkdic)
                        if linkstrobj.HashValue not in hashkeylist:
                            testDim=getonestepTestDimention(linkStrOrg,linkstrobj,-1,0,middletuple)
                            #add to list
                            hashkeylist.append(linkstrobj.HashValue)
                            newtuple=(linkstrobj,testDim)
                            candidatelist.append(newtuple)   
    return candidatelist

def getSourceIdxfromRwoList(sourceNodeobjs,RawCandidatesLKStrucs):
        indexedSourcobjs={}#idx:obj
        idx=0
        for tup in RawCandidatesLKStrucs:
            testdim=tup[1]
            linkdic=eval(tup[0].outPutToLinksDicStr())
            idx=0
            for key in testdim.keys():
                if testdim[key][1]==3:
                    thislink=tuple(linkdic[key])
                    orglink=oneDOd.getNextOdLink(thislink)
                    linkdic[key]=list(orglink)
                    orglinkstru=linkArryStru(linkdic)
                    for lkobj in sourceNodeobjs:
                        if lkobj.HashValue==orglinkstru.HashValue:
                            indexedSourcobjs[idx]=lkobj
                            break
                    break
                if testdim[key][1]==-3:
                    thislink=tuple(linkdic[key])
                    orglink=oneDOd.getPreOdLink(thislink)
                    linkdic[key]=list(orglink)
                    orglinkstru=linkArryStru(linkdic)
                    for lkobj in sourceNodeobjs:
                        if lkobj.HashValue==orglinkstru.HashValue:
                            indexedSourcobjs[idx]=lkobj
                            break
                    break

        return indexedSourcobjs

def genBorderTestset(linkStrOrg,testdim,middletuple,hops=3):
    bordertestlist=[]    
    hashkeylist=[]                          
    if hops==3:
        #increase to make a candidate
        for key in testdim.keys():
            tupl=testdim[key]
            linkdic=eval(linkStrOrg.outPutToLinksDicStr())  
            if tupl[0]==0 and tuple[1]!=3:
                linkorg=tuple(linkdic[key])
                newlktup=oneDOd.getNextOdLink(linkorg)
                if linkTupleValue(newlktup)<=linkTupleValue((0.02,0.02,0.02)):                    
                    linkdic[key]=list(newlktup)                    
                    linkstrobj=linkArryStru(linkdic)
                    if linkstrobj.HashValue not in hashkeylist:
                        testDim=getonestepTestDimention(linkStrOrg,linkstrobj,-1,0,middletuple)
                        #add to list
                        hashkeylist.append(linkstrobj.HashValue)
                        newtuple=(linkstrobj,testDim)
                        bordertestlist.append(newtuple) 
                    break 
    return bordertestlist



def genTestCase(linkStruB,idx):
    pass

def RunTestCase(testcasDir):
    pass

def GetResultTestCase(testcasDir):
    pass
 
#if the current T<T_c
#     in all links, try to inclrease a step, to see if new T cross the T_c.
#     if not, try new inclreased links.
#if the current T>T_c
#     in all links decrease a step, to see if new T cross the T_c
#     if not, try new decreased links. 
# linkSturB is T<T_c
# disabled in db based
def checkValidborderLinkStruc(linkSturB,hops=3):
    replacedic={}
    for lktuple in linkSturB.hops3MeanList:
        if lktuple not in replacedic.keys():
            prekeytuple=oneDOd.getPreOdLink(lktuple)
            replacedic[lktuple]=prekeytuple
    
    hop2array=linkSturB.hops2MeanList.copy()
    hop3array=linkSturB.hops3MeanList.copy()
    tryArryArray=[]

    for key in replacedic.keys():
        thisarray=hop2array.copy()
        replaceKey=None
        for hops3key in hop3array:
            if hops3key==key and replaceKey==None:
                #replace only once
                replaceKey=replacedic[key]
                thisarray.extend(replaceKey)
                continue
            thisarray.extend(hops3key)
            
        tryArryArray.append(thisarray)
    #check All tryArryArray
    tryidx=0
    for linkArray in tryArryArray:
        #simulation linkArray and wait for results.


        tryidx+=1
        pass
    #wait for resluts

    #got results, if crossed T_c, valid border. Otherwise, raise the  waterlevel, proceed to get the border..
    

    





#the A and B have same other hops. but hops 3
#compare them
# 1 >, 0 =, -1 <
def compareHops3LinkStuc(linkStruA,linkStruB):
    if linkStruA.hops3means>linkStruB.hops3means:
        return 1
    elif linkStruA.hops3means<linkStruB.hops3means:
        return -1
    else:
        return 0



def extract_floats(string):  
  pattern = r"[-+]?\d*\.\d+"  # Regular expression to match float numbers
  matches = re.findall(pattern, string)
  return [float(match) for match in matches]

#compare two linkArryStru, if we can compare now return boolean value
# if we can not compare, return None, 
#   and we need to add more data samples or more data structures for compare.
# this function is the key part to data engineer
# we need may data to test this function and to generate data; 
# 1. Coarse-grained search: mid+d1 compare with known data (link boundary)
# 2. fine tune search.
# 3. unknown compare add rule or add data.
class TestedLinkValue:
    def __init__(self,ID,linkdic,value,rl,lowBound,ru,upperbound,nextCk):
        self.id=ID#all tested value have a ID we can use it to address the link.
        self.linkArrayStruObj=linkArryStru(linkdic)
        self.Nlinks=self.linkArrayStruObj.linkNum
        self.Tvalue=value
        self.lowBDtup=(rl,lowBound)
        self.upBDtup=(ru,upperbound)
        self.middtup=tuple(self.linkArrayStruObj.midArray)
        self.midwidth=len(self.linkArrayStruObj.midArray)#we can categare links firstly base one midwidth
        self.nextCheckObjs=nextCk#key:(cond,par1,par2,par3) the middle is different from this middle; value: ID.
        pass
    #check more, or got result by this
    #return value: (nexcheckTestedLinkValueobj, result)
    #      if nexcheckTestedLinkValueobj!=None  pass to this obj to check
    #      if result is none, can not judge by this obj, if not none, the result is given
    #      if both are none, undefined, need more TestedLinkValue to be created.
    #      if both are valid value, we need to do more test for confirem, the result value is a guess value with more than 50%  probility
    #           we can use this feature to accerlate the lookup process
    def isTValid(self,linkAryStruObj):
        nextCheckobj=None
        result=None

        return (nextCheckobj,result)

#read list form xml file
class KnownLinksValues:
    def __init__(self,filetoread):
        self.KLVlist=[]
        self.IDidxMap={}#key ID: value idx of KLVlist
        tree = ET.parse(filetoread)
        root=tree.getroot()
        allLinkValues=root.findall('LinkValue')
        idx=0
        for linkValue in allLinkValues:
            lkID=int(linkValue.find('ID').text)
            lkValue=float(linkValue.find('Value').text)
            linkNum=int(linkValue.find('LinkNum').text)
            linkPisobjs=linkValue.findall('pLink')
            linkDic={}
            fidx=0
            for pilnk in linkPisobjs:
                fidx+=1
                arrytext=pilnk.findall('pLink').text
                lnkdata=extract_floats(arrytext)
                key='F%d'%fidx
                linkDic[key]=lnkdata

            upperLinkobj=linkValue.find('upperLink')
            ru=int(upperLinkobj['r'])
            arraytext=upperLinkobj.text
            lnkdata=extract_floats(arrytext)
            upperkey=tuple(lnkdata)

            lowerLinkobj=linkValue.find('lowerLink')
            rl=int(lowerLinkobj['r'])
            arraytext=lowerLinkobj.text
            lnkdata=extract_floats(arrytext)
            lowerkey=tuple(lnkdata)
            nextckobjs=linkValue.findall('nextcheck')
            nexckDic={}
            for ncobj in nextckobjs:
                con=int(ncobj['con'])
                par1=int(ncobj['par1'])
                par2=int(ncobj['par2'])
                par3=int(ncobj['par3'])
                key=(con,par1,par2,par3)
                nexID=int(ncobj.text)
                nexckDic[key]=nexID


            
            TLVobj=TestedLinkValue(lkID,linkDic,lkValue,rl,lowerkey,ru,upperkey,nexckDic)
            self.KLVlist.append(TLVobj)  
            self.IDidxMap[lkID]=idx
            idx+=1          



        pass

def greaterlinkArray(laAstruc,laBstruc):
    if laAstruc.midArray[0]==laBstruc.midArray[0]:
        pass
    elif len(laAstruc.midArray[0])==len(laBstruc.midArray[0]):
        pass

    return None#can not compare now


def simpleMVtest():
    linkData1={
    'F1':[0.011,0.011],#1
    'F2':[0.011,0.011],#2
    'F3':[0.015,0.015,0.015 ],#3
    'F4':[0.011,0.011,0.02 ],#4
    'F5':[0.011,0.011,0.02 ],#5
    'F6':[0.011,0.011,0.02 ],#1
    'F7':[0.011,0.011,0.02 ],#4
    'F8':[0.011,0.011,0.02 ],#4
    'F9':[0.011,0.011,0.02 ],#4
    'F10':[0.011,0.011,0.02 ],#2
    }
    linkData2={
    'F1':[0.011,0.011],#1
    'F2':[0.011,0.011],#2
    'F3':[0.015,0.015,0.015 ],#3
    'F4':[0.015,0.015,0.015 ],#4
    'F5':[0.015,0.015,0.015 ],#5
    'F6':[0.015,0.015,0.015 ],#4
    'F7':[0.015,0.015,0.015],#4
    'F8':[0.011,0.015,0.015],#4
    'F9':[0.011,0.015,0.015 ],#4
    'F10':[0.011,0.011,0.015 ],#2
    }
    LksturA=linkArryStru(linkData1)
    LksturB=linkArryStru(linkData2)
    LksturA.getHops3MeansAndVarsArray()
    LksturB.getHops3MeansAndVarsArray()


    var=varHops3LinkStuc(LksturA,LksturB.hops2MeanList)
    res=compareHops3LinkStuc(LksturA,LksturB)

    if res>0:
        print("var:%f Mean:%f SDT:%f  linkData1 > linkData2 Mean:%f SDT:%f"%(var,LksturA.hops3means,LksturA.hops3msdt,LksturB.hops3means,LksturB.hops3msdt))
    elif res<0:
        print("var:%f Mean:%f SDT:%f  linkData1 < linkData2 Mean:%f SDT:%f"%(var,LksturA.hops3means,LksturA.hops3msdt,LksturB.hops3means,LksturB.hops3msdt))
    else:
        print("var:%f Mean:%f SDT:%f  linkData1 == linkData2 Mean:%f SDT:%f"%(var,LksturA.hops3means,LksturA.hops3msdt,LksturB.hops3means,LksturB.hops3msdt))

def tupleValuetest():
    tuple0=(0.015,0.015,0.015)
    value0=linkTupleValue(tuple0)
    tuple1=(0.015,0.02,0.011)
    value1=linkTupleValue(tuple1)
    tuple2=(0.011,0.02,0.015)
    value2=linkTupleValue(tuple2)
    tuple3=(0.015,0.011,0.020)
    value3=linkTupleValue(tuple3)
    tuple4=(0.02,0.011,0.015)
    value4=linkTupleValue(tuple4)
    tuple5=(0.011,0.015,0.020)
    value5=linkTupleValue(tuple5)    
    tuple6=(0.02,0.015,0.011)
    value6=linkTupleValue(tuple6)
    tuple7=(0.015,0.02,0.015)
    value7=linkTupleValue(tuple7)
    print(f"v0:{value0},v1:{value1},v2:{value2},v3:{value3},v4:{value4},v5:{value5},v6:{value6},v7:{value7}")
def moduletest():
    #oneDOd.initialOrderList()
    #simpleMVtest()
    tupleValuetest()

if __name__=='__main__':moduletest()       

                                        
    
