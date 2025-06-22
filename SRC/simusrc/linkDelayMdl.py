#!/usr/bin/python3

import random
import matplotlib.pyplot as plt
import numpy as np
import os
import re 
import SGBDESIntevals as simMain

random.seed(555)
np.random.seed(555)

LinkMini=0.012
MiniDelay=0.03
# LinkMini=0.010#0.012
# LinkMiniNodeDelay=0.012
# MiniDelay=0.0255

class channelDelay:
    def __init__(self,maxDelayLst):
        self.hops=len(maxDelayLst)
        self.meanDelay=MiniDelay+LinkMini*(self.hops-1)
        self.HopsRange=[]#uniform random
        for i in range(self.hops):
            if maxDelayLst[i]>LinkMini:
                drnge=maxDelayLst[i]-LinkMini
                self.meanDelay+=(drnge/2)
            else:
                drnge=0
                #self.meanDelay+=LinkMini
            self.HopsRange.append(drnge)

    # def delaytime(self):
    #     time=0
    #     var=0
    #     for i in range(self.hops):
    #         #var+=self.HopsRange[i]*random.random()
    #         var+=self.HopsRange[i]*np.random.triangular(0,0.5,1)
    #         if i>0:                
    #             #var+=np.random.triangular(0,LinkMiniNodeDelay*0.3,LinkMiniNodeDelay)
    #             var+=np.random.gamma(0.5,LinkMiniNodeDelay)
    #     time=MiniDelay+var+LinkMiniNodeDelay*(self.hops-1)*0.45
    #     return time
    def delaytime(self):#compare, old func
        time=0
        var=0
        for i in range(self.hops):
            var+=self.HopsRange[i]
        time=MiniDelay+var*random.random()+LinkMini*(self.hops-1)
        return time

#hops type(inc):  1, 2, 3, 4,
#counts of type:  1, 2, 2, 5,  
linksData={
    'F1':[0.015,0.015],#1
    'F2':[0.011,0.015,0.015],#2
    'F3':[0.015,0.02],#3
    'F4':[0.02,0.02],#4
    'F5':[0.011,0.011,0.015],#5
    'F6':[0.011,0.015,0.015],#1
    'F7':[0.015,0.015,0.015],#4
    'F8':[0.015,0.015,0.02],#4
    'F9':[0.015,0.02,0.02],#4
    'F10':[0.02,0.02,0.02],#2
}

linkDelay={}   

workingDir=os.getcwd()
logfileName="linkDelayDistA-B.log"
def linkDistHisgramSave(histlist):
    strline=str(histlist)
    filename=os.path.join(workingDir,logfileName)
    with open(filename,'w') as f:
        f.writelines(strline)
        f.close()
def linkDistHisgramGot():
    filename=os.path.join(workingDir,logfileName)
    with open(filename,'r') as f:
        strline=f.readline()
        hislist=eval(strline)
        f.close()
    return hislist

def gotLinkDelayDistrLog():
    genLinkDelay()
    plotlist=[]
    for itmkey in linkDelay.keys():
        channel=linkDelay[itmkey]    
        for i in range(30000):
            delaytime=channel.delaytime()
            plotlist.append(delaytime)
        break#check only first link
    linkDistHisgramSave(plotlist)

def drawTheDistHisgram():
    plotlist=linkDistHisgramGot()
    plt.hist(plotlist, # 绘图数据
        bins=500, # 指定直方图的组距
        density = True, # 设置为频率直方图
        #color = 'steelblue', # 指定填充色
        #edgecolor = 'k',# 指定直方图的边界色
        edgecolor='tab:gray'
        ) 
    #plt.title('hisgram of delay time, mean:%f'%(channel.meanDelay))
    #plt.title('hisgram of delay time')
    plt.grid()
    plt.xlabel('delay time')
    plt.ylabel('rate')
    plt.show()
def moduletest():
    gotLinkDelayDistrLog()
    drawTheDistHisgram()

    
    
#convert linksData to linkDelay
def genLinkDelay():
    global linkDelay
    linkDelay={}
    for itmkey in linksData.keys():
        delaylist=linksData[itmkey]
        channel=channelDelay(delaylist)
        linkDelay[itmkey]=channel
        print("mean of %s :%f"%(itmkey,channel.meanDelay))

CONFIGFILE="SimParam.cfg"
#CURRENTDIR=os.getcwd()
"""
  Extracts all float numbers from the given string.

  Args:
    string: The input string.

  Returns:
    A list of float numbers extracted from the string.
  """
def extract_floats(string):  
  pattern = r"[-+]?\d*\.\d+"  # Regular expression to match float numbers
  matches = re.findall(pattern, string)
  return [float(match) for match in matches]

def genLinkDelayFromCfg():
    global linkDelay
    linkDelay={}
    delaylist=[]
    #cfg file read
    cfgfile=os.path.join(simMain.CURRENTDIR,CONFIGFILE)
    with open(cfgfile,'r') as f:
        for line in f:
            match =re.search(r'DimensionOrderTest:(\d+)', line)
            if match:
                type=int(match.group(1))
                if type!=1:#type may extend in future
                    return
            #line='PathMaxDelay:0.97, 0.98, 0.99, 0.0100, 0.0101, 0.0102, 0.0103, 0.0104, 0.015, 0.02'
            match =re.search(r'PathMaxDelay:(.*?)', line)
            if match:
                #print(match.groups())
                #timekeytitle=match.group(1)
                numberstr=line              
                delaylist= extract_floats(numberstr)


    # for itmkey in linksData.keys():        
    #     channel=channelDelay(delaylist)
    #     linkDelay[itmkey]=channel
    #     print("mean of %s :%f"%(itmkey,channel.meanDelay))
    idx=0
    for itmkey in linksData.keys():
         idx+=1
         if idx!=1:#only 1 itm replaced with testing cases
             delaylist=linksData[itmkey]
         channel=channelDelay(delaylist)
         linkDelay[itmkey]=channel
         print("mean of %s :%f"%(itmkey,channel.meanDelay))

def genLinkDelayFromCfgDim2():
    global linkDelay
    linkDelay={}
    delaylist=[]
    #cfg file read
    cfgfile=os.path.join(simMain.CURRENTDIR,CONFIGFILE)
    with open(cfgfile,'r') as f:
        for line in f:
            match =re.search(r'DimensionOrderTest:(\d+)', line)
            if match:
                type=int(match.group(1))
                if type!=2:#type may extend in future
                    return
            #line='PathMaxDelay:0.97, 0.98, 0.99, 0.0100, 0.0101, 0.0102, 0.0103, 0.0104, 0.015, 0.02'
            match =re.search(r'MiddleKey:(.*?)', line)
            if match:
                #print(match.groups())
                #timekeytitle=match.group(1)
                numberstr=line              
                middkey= extract_floats(numberstr)
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
    
    ##simulation scale setting
    N=6
    R=3

    #follower id 1-to-N
    for i in range(1,N+1): 
        itmkey='F%d'%i   
        if i==1:
            channel=channelDelay(delaylist0)
        elif i==2:
            channel=channelDelay(delaylist1)
        else:                
            channel=channelDelay(middkey)
        linkDelay[itmkey]=channel
        print("mean of %s :%f"%(itmkey,channel.meanDelay))
    return N,R

def genLinkDelayFromCfgD3():
    global linkDelay
    linkDelay={}
    #cfg file read
    linkDic={}
    cfgfile=os.path.join(simMain.CURRENTDIR,CONFIGFILE)
    with open(cfgfile,'r') as f:
        for line in f:
            match =re.search(r'DimensionOrderTest:(\d+)', line)
            if match:
                type=int(match.group(1))
                if type!=3:#type may extend in future
                    return
            
            #line='PathMaxDelay:0.97, 0.98, 0.99, 0.0100, 0.0101, 0.0102, 0.0103, 0.0104, 0.015, 0.02'
            match =re.search(r'UseTheLink:{(.*?)}', line)
            if match:
                #print(match.groups())
                objstr=match.group(1)
                linkDic=eval(f"{{{objstr}}}")               
    for key in linkDic.keys():
        linkDelay[key]=channelDelay(linkDic[key])
    return

    
    
        

if __name__=='__main__':moduletest()