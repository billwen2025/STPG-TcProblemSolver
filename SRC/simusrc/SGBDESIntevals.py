#!/usr/bin/python3
import random,math
import numpy as np
import pandas as pd 
import csv,os,shutil

import linkDelayMdl as lnkMdl

Alpha=0.05#packet fail rate check at leader with type ACK. (L:msg-> F:msg; F:ack->L:ack; do not check at follower side),
Lambda=2
Di=0.1
ReTransTimeOut=0.0# if ReTransTimeOut>=2*Di (0.3) ,enable fixtime resend, otherwise use optimum resent (0.0)
N=10
R=5#in paper (R-1)==6
#MAXROUND=200
#MAXROUND=300000#300000 for B2 statics
MAXROUND=100000#300000 for faster
#MAXROUND=90000#300000 for faster

LogBlockSize=5000

bCommited=0

MSG_TYPE=0#
ACK_TPYE=1

DEBUG_EXPTIME=0
MinCmitTime=0.2#0.4 is the first ack time; 0.8 is the first commit time
HisTarget='AckALL'#AckALL AckS6  1-11;AckB1,AckB2,AckSB3;AckB2R2,...AckB2R6;
FilterR=-1#-1 for all
FilterB=-1# -1 for all
GetTimeDistr=-1 # -1 for inteval, others for time distribution
FilterFisrtAckArrive=0.04 # for linkDelay
DeTimeOffset=0.4
ModeDiff=1
#in ModeDiff
FirstTimeSlice=0
TimeSlice=0.2#defined by system, the time slice is the duration which the p.d.f of AckInteval not changed

SLICENUM=0 #根据线性时间划分 walltime，目前的时间需要更新。归零的地方。

#The indicator of the commitment process; SucessAckCount>=R commited
#histogram of the commitCount is base on this value
MAXSLICE=13
RSucCount0His=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]#slice 1,2,3,4,5,6,7,8,9,10,11,12,13 +2[initial,end]
RSucCount1His=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
RSucCount2His=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
RSucCount3His=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
RSucCount4His=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
RSucCount5His=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
RSucCount6orMoreHis=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

#wallTimeStamp=0.0#increase only
#def getwallTimeStamp():
#    return wallTimeStamp

random.seed(555)
np.random.seed(555)


#Get time from IdeaSwitch
gTimeStamp=0.0#round time
def getCurTimeStamp():
    return gTimeStamp

FirstAckIntervalDisable=1

if FirstAckIntervalDisable:
    preAckTimestamp=0
else:
    preAckTimestamp=MinCmitTime

preAckRaftRNum=0



AckPDObj=None
AckB1=None
AckB2=None
AckB3=None
AckB2R0=None
AckB2R1=None
AckB2R2=None
AckB2R3=None
AckB2R4=None
AckB2R5=None
AckB2R6=None



AckS1=None
AckS2=None
AckS3=None
AckS4=None
AckS5=None
AckS6=None
AckS7=None
AckS8=None
AckS9=None
AckS10=None

AckFR3=None
AckFR4=None

CommitPDObj=None

CommitB1=None
CommitB2=None
CommitB3=None

CommitB2R0=None
CommitB2R1=None
CommitB2R2=None
CommitB2R3=None
CommitB2R4=None
CommitB2R5=None
CommitB2R6=None

CommitS1=None
CommitS2=None
CommitS3=None
CommitS4=None
CommitS5=None
CommitS6=None
CommitS7=None
CommitS8=None
CommitS9=None
CommitS10=None
CommitS11=None
CommitS12=None

DebugExpObj=None

CURRENTDIR=os.getcwd()
LOGDATADIR=os.path.join(CURRENTDIR,"datahdd")

ACKINTFilePath=os.path.join(LOGDATADIR,'ackintevals.csv')

ACKB1Path=os.path.join(LOGDATADIR,'ackB1.csv')
ACKB2Path=os.path.join(LOGDATADIR,'ackB2.csv')
ACKB3Path=os.path.join(LOGDATADIR,'ackB3.csv')

ACKB2R0Path=os.path.join(LOGDATADIR,'ackB2R0.csv')
ACKB2R1Path=os.path.join(LOGDATADIR,'ackB2R1.csv')
ACKB2R2Path=os.path.join(LOGDATADIR,'ackB2R2.csv')
ACKB2R3Path=os.path.join(LOGDATADIR,'ackB2R3.csv')
ACKB2R4Path=os.path.join(LOGDATADIR,'ackB2R4.csv')
ACKB2R5Path=os.path.join(LOGDATADIR,'ackB2R5.csv')
ACKB2R6Path=os.path.join(LOGDATADIR,'ackB2R6.csv')

ACKS1Path=os.path.join(LOGDATADIR,'ackS1.csv')
ACKS2Path=os.path.join(LOGDATADIR,'ackS2.csv')
ACKS3Path=os.path.join(LOGDATADIR,'ackS3.csv')
ACKS4Path=os.path.join(LOGDATADIR,'ackS4.csv')
ACKS5Path=os.path.join(LOGDATADIR,'ackS5.csv')
ACKS6Path=os.path.join(LOGDATADIR,'ackS6.csv')
ACKS7Path=os.path.join(LOGDATADIR,'ackS7.csv')
ACKS8Path=os.path.join(LOGDATADIR,'ackS8.csv')
ACKS9Path=os.path.join(LOGDATADIR,'ackS9.csv')
ACKS10Path=os.path.join(LOGDATADIR,'ackS10.csv')

ACKFR3Path=os.path.join(LOGDATADIR,'ackSFR3.csv')
ACKFR4Path=os.path.join(LOGDATADIR,'ackSFR4.csv')



CommitIntvalFilePath=os.path.join(LOGDATADIR,'CommitInteval.csv')

CommitB1Path=os.path.join(LOGDATADIR,'CommitB1.csv')
CommitB2Path=os.path.join(LOGDATADIR,'CommitB2.csv')
CommitB3Path=os.path.join(LOGDATADIR,'CommitB3.csv')

CommitB2R0Path=os.path.join(LOGDATADIR,'CommitB2R0.csv')
CommitB2R1Path=os.path.join(LOGDATADIR,'CommitB2R1.csv')
CommitB2R2Path=os.path.join(LOGDATADIR,'CommitB2R2.csv')
CommitB2R3Path=os.path.join(LOGDATADIR,'CommitB2R3.csv')
CommitB2R4Path=os.path.join(LOGDATADIR,'CommitB2R4.csv')
CommitB2R5Path=os.path.join(LOGDATADIR,'CommitB2R5.csv')
CommitB2R6Path=os.path.join(LOGDATADIR,'CommitB2R6.csv')

CommitS1Path=os.path.join(LOGDATADIR,'CommitS1.csv')
CommitS2Path=os.path.join(LOGDATADIR,'CommitS2.csv')
CommitS3Path=os.path.join(LOGDATADIR,'CommitS3.csv')
CommitS4Path=os.path.join(LOGDATADIR,'CommitS4.csv')
CommitS5Path=os.path.join(LOGDATADIR,'CommitS5.csv')
CommitS6Path=os.path.join(LOGDATADIR,'CommitS6.csv')
CommitS7Path=os.path.join(LOGDATADIR,'CommitS7.csv')
CommitS8Path=os.path.join(LOGDATADIR,'CommitS8.csv')
CommitS9Path=os.path.join(LOGDATADIR,'CommitS9.csv')
CommitS10Path=os.path.join(LOGDATADIR,'CommitS10.csv')
CommitS11Path=os.path.join(LOGDATADIR,'CommitS11.csv')
CommitS12Path=os.path.join(LOGDATADIR,'CommitS12.csv')



DebugExpTimeVerifyFilePath=os.path.join(LOGDATADIR,'DebugPropTime.csv')

RSussSliceHisPath=os.path.join(LOGDATADIR,'RSussSlicesHis.csv')


def getRandomInteveralExponetial(tlambda):
    #divisionnum=50
    #dataunitfor01=1/divisionnum
    r=np.random.exponential(1/tlambda) 
    #n=math.ceil(r/dataunitfor01)
    #n=(r/dataunitfor01)
    #if n>10*divisionnum:
    #    n=10*divisionnum
    #return 0.1*n/divisionnum
    return r*0.1

IntervalNum=0

def genPropagationTime(followerID):
    
    """ #old implements
    #the expontential distribution
    time=0.0
    time=Di+getRandomInteveralExponetial(Lambda)
    #time=getRandomInteveralExponetial(Lambda)
    if DEBUG_EXPTIME:
        global IntervalNum,DebugExpObj
        IntervalNum+=1
        ptdata = pd.DataFrame({'SimuRoundN':[IntervalNum],'PropTime':[time]}) 
        DebugExpObj=pd.concat([DebugExpObj,ptdata])
        if DebugExpObj.shape[0]>LogBlockSize:
            DebugExpObj.to_csv(DebugExpTimeVerifyFilePath,index=False,mode='a+', header=False)
            DebugExpObj=pd.DataFrame()

    return time
    """

    time = lnkMdl.linkDelay[followerID].delaytime()
    return time




def sortPacketbySentOutTime(packet):
    time=packet.createTime+packet.propagationTime
    return time

class Packet:
    def __init__(self,typeMsg,prob,propaTime,curTimeStamp,fromID,toID):
        self.type=typeMsg# MSG:0 ACK：1
        self.FailProb=prob# fail prob, uniformly random[0-1]. if prob<alpha :resent, else count.
        self.propagationTime=propaTime# time to propaatione to the next node,if time's up the packet transfer form the source to the garget node 
        self.createTime=curTimeStamp#
        self.fromNode=fromID
        self.toNode=toID
        #Round order to  Leader
        self.RoundOrderToLeader=0
        self.AckInteval=0
        self.ReboundTimes=0#record the rebound Times, this is the reason for distribution change, but can be seperated.
                           #keep increasing, if resend this packet!!! leader increase, follower copy
        pass

class Node:
    def __init__(self,ID,Type):
        self.nID=ID
        self.type=Type#0:leader others:followers
        self.Rcount=0
        self.AckCount=0
        self.B2StartR=-1#when first ack in B2 arrived, the Rcount number of leader
    def InQueue(self,packet):
        #no queue actually,
        #process directly.
        if packet.toNode==self.nID:
            if self.type==0:
                self.processPacketLeader(packet)
            else:
                self.processPacketFollower(packet)

    def processPacketLeader(self,packet):
        global SimuRound,SLICENUM
        global AckPDOBJ,AckB1,AckB2,AckB3,AckS1,AckS2,AckS3,AckS4,AckS5,AckS6,AckS7,AckS8,AckS9,AckS10
        global CommitPDObj,CommitB1,CommitB2,CommitB3,CommitS1,CommitS2,CommitS3,CommitS4,CommitS5,CommitS6,CommitS7,CommitS8,CommitS9,CommitS10,CommitS11,CommitS12
        global AckB2R0,AckB2R1,AckB2R2,AckB2R3,AckB2R4,AckB2R5,AckB2R6,CommitB2R0,CommitB2R1,CommitB2R2,CommitB2R3,CommitB2R4,CommitB2R5,CommitB2R6,AckFR3,AckFR4
        if self.type!=0:
            print("?")
            return
        if packet.type==ACK_TPYE:
            if self.Rcount>=R:#TimeSlice decided here
                #print("+")
                return
            #log data here for intevals
            timstmp=getCurTimeStamp()
            self.AckCount+=1

            sliceInteval=0.0
            dataslice=None
            #all time statics
            
            packet.RoundOrderToLeader+=1
            packet.ReboundTimes+=1#leader increase ReboundTimes 

            ##special cases for ack interval process
            #name those packets as S1R2
            FirstAckPacket=0
            if packet.AckInteval>=TimeSlice and packet.AckInteval==timstmp:
                if FirstAckIntervalDisable:
                    FirstAckPacket=1
                # print("inteval:%f tm:%f B++:%d"%(packet.AckInteval,timstmp,packet.ReboundTimes))
                # packet.AckInteval=packet.AckInteval-TimeSlice
                # packet.ReboundTimes+=1#leader increase ReboundTimes 
            if packet.ReboundTimes==2 and self.B2StartR==-1:
                self.B2StartR=self.Rcount#set B2StartR only once
                #print("B2Start R=%d time:%f"%(self.B2StartR,timstmp))
                FirstAckPacket=1

            #all ack    
            

            if FirstAckPacket==0:

                data=pd.DataFrame({'SimuRoundN':[SimuRound],'SeqN':[self.AckCount],'Timeorg':[timstmp],'Inteval':[packet.AckInteval],'R':[self.Rcount],'B':[packet.ReboundTimes]}) 

                AckPDOBJ=pd.concat([AckPDOBJ,data])
                if AckPDOBJ.shape[0]>LogBlockSize:
                    AckPDOBJ.to_csv(ACKINTFilePath,index=False, mode='a+', header=False)
                    AckPDOBJ=pd.DataFrame() 
                #time slice statics 
                #windows slice distribution
                #   it is the results, not the input
                # if SLICENUM>0 and timstmp >=((SLICENUM-1)*TimeSlice+MinCmitTime):
                #     sliceInteval=(timstmp-((SLICENUM-1)*TimeSlice+MinCmitTime))
                #     dataslice=pd.DataFrame({'SimuRoundN':[SimuRound],'SeqN':[self.AckCount],'Timeorg':[timstmp],'Inteval':[sliceInteval],'R':[self.Rcount]})
                #full distribution of slice
                dataslice=data
                #Round Ack log   
                if SLICENUM==1:                
                    AckS1=pd.concat([AckS1,dataslice])
                    if AckS1.shape[0]>LogBlockSize:
                        AckS1.to_csv(ACKS1Path,index=False, mode='a+', header=False)
                        AckS1=pd.DataFrame()  
                if SLICENUM==2:
                    AckS2=pd.concat([AckS2,dataslice])
                    if AckS2.shape[0]>LogBlockSize:
                        AckS2.to_csv(ACKS2Path,index=False, mode='a+', header=False)
                        AckS2=pd.DataFrame()  
                if SLICENUM==3:
                    AckS3=pd.concat([AckS3,dataslice])
                    if AckS3.shape[0]>LogBlockSize:
                        AckS3.to_csv(ACKS3Path,index=False, mode='a+', header=False)
                        AckS3=pd.DataFrame()  
                if SLICENUM==4:
                    AckS4=pd.concat([AckS4,dataslice])
                    if AckS4.shape[0]>LogBlockSize:
                        AckS4.to_csv(ACKS4Path,index=False, mode='a+', header=False)
                        AckS4=pd.DataFrame()  
                if SLICENUM==5:
                    AckS5=pd.concat([AckS5,dataslice])
                    if AckS5.shape[0]>LogBlockSize:
                        AckS5.to_csv(ACKS5Path,index=False, mode='a+', header=False)
                        AckS5=pd.DataFrame()  
                if SLICENUM==6:
                    AckS6=pd.concat([AckS6,dataslice])
                    if AckS6.shape[0]>LogBlockSize:
                        AckS6.to_csv(ACKS6Path,index=False, mode='a+', header=False)
                        AckS6=pd.DataFrame()  
                if SLICENUM==7:
                    AckS7=pd.concat([AckS7,dataslice])
                    if AckS7.shape[0]>LogBlockSize:
                        AckS7.to_csv(ACKS7Path,index=False, mode='a+', header=False)
                        AckS7=pd.DataFrame()  
                if SLICENUM==8:
                    AckS8=pd.concat([AckS8,dataslice])
                    if AckS8.shape[0]>LogBlockSize:
                        AckS8.to_csv(ACKS8Path,index=False, mode='a+', header=False)
                        AckS8=pd.DataFrame()  
                if SLICENUM==9:
                    AckS9=pd.concat([AckS9,dataslice])
                    if AckS9.shape[0]>LogBlockSize:
                        AckS9.to_csv(ACKS9Path,index=False, mode='a+', header=False)
                        AckS9=pd.DataFrame()  
                if SLICENUM==10:
                    AckS10=pd.concat([AckS10,dataslice])
                    if AckS10.shape[0]>LogBlockSize:
                        AckS10.to_csv(ACKS10Path,index=False, mode='a+', header=False)
                        AckS10=pd.DataFrame()  
                

                #rebound times statics
                if packet.ReboundTimes==1:                
                    AckB1=pd.concat([AckB1,dataslice])
                    if AckB1.shape[0]>LogBlockSize:
                        AckB1.to_csv(ACKB1Path,index=False, mode='a+', header=False)
                        AckB1=pd.DataFrame()  
                if packet.ReboundTimes==2:
                    AckB2=pd.concat([AckB2,dataslice])
                    if AckB2.shape[0]>LogBlockSize:
                        AckB2.to_csv(ACKB2Path,index=False, mode='a+', header=False)
                        AckB2=pd.DataFrame() 

                    if self.B2StartR<5:
                        AckB2R0=pd.concat([AckB2R0,dataslice])
                        if AckB2R0.shape[0]>LogBlockSize:
                            AckB2R0.to_csv(ACKB2R0Path,index=False, mode='a+', header=False)
                            AckB2R0=pd.DataFrame() 

                    if self.B2StartR==1:
                        AckB2R1=pd.concat([AckB2R1,dataslice])
                        if AckB2R1.shape[0]>LogBlockSize:
                            AckB2R1.to_csv(ACKB2R1Path,index=False, mode='a+', header=False)
                            AckB2R1=pd.DataFrame() 

                    if self.B2StartR==2:
                        AckB2R2=pd.concat([AckB2R2,dataslice])
                        if AckB2R2.shape[0]>LogBlockSize:
                            AckB2R2.to_csv(ACKB2R2Path,index=False, mode='a+', header=False)
                            AckB2R2=pd.DataFrame() 

                    if self.B2StartR==3:
                        AckB2R3=pd.concat([AckB2R3,dataslice])
                        if AckB2R3.shape[0]>LogBlockSize:
                            AckB2R3.to_csv(ACKB2R3Path,index=False, mode='a+', header=False)
                            AckB2R3=pd.DataFrame() 

                    if self.B2StartR==4:
                        AckB2R4=pd.concat([AckB2R4,dataslice])
                        if AckB2R4.shape[0]>LogBlockSize:
                            AckB2R4.to_csv(ACKB2R4Path,index=False, mode='a+', header=False)
                            AckB2R4=pd.DataFrame() 

                    if self.B2StartR==5:
                        AckB2R5=pd.concat([AckB2R5,dataslice])
                        if AckB2R5.shape[0]>LogBlockSize:
                            AckB2R5.to_csv(ACKB2R5Path,index=False, mode='a+', header=False)
                            AckB2R5=pd.DataFrame() 


                if packet.ReboundTimes==3:
                    AckB3=pd.concat([AckB3,dataslice])
                    if AckB3.shape[0]>LogBlockSize:
                        AckB3.to_csv(ACKB3Path,index=False, mode='a+', header=False)
                        AckB3=pd.DataFrame()  
            else:
                if FirstAckPacket==1:#direct commit
                    if packet.ReboundTimes==2:#only ReboundTimes>1 possible
                        #sliceInteval=timstmp
                        dataslice=pd.DataFrame({'SimuRoundN':[SimuRound],'SeqN':[self.AckCount],'Timeorg':[timstmp],'Inteval':[packet.AckInteval],'R':[self.Rcount],'B':[packet.ReboundTimes]}) 
                        AckB2=pd.concat([AckB2,dataslice])
                        if AckB2.shape[0]>LogBlockSize:
                            AckB2.to_csv(ACKB2Path,index=False, mode='a+', header=False)
                            AckB2=pd.DataFrame()

                        if self.B2StartR==5:# only self.B2StartR==5 is possible                            
                            AckB2R5=pd.concat([AckB2R5,dataslice])
                            if AckB2R5.shape[0]>LogBlockSize:
                                AckB2R5.to_csv(ACKB2R5Path,index=False, mode='a+', header=False)
                                AckB2R5=pd.DataFrame() 
                            # AckB2R6=pd.concat([AckB2R6,dataslice])
                            # if AckB2R6.shape[0]>LogBlockSize:
                            #     AckB2R6.to_csv(ACKB2R6Path,index=False, mode='a+', header=False)
                            #     AckB2R6=pd.DataFrame()
                            # 
                        if self.B2StartR==3:# first Packet distritution
                            AckFR3=pd.concat([AckFR3,dataslice])
                            if AckFR3.shape[0]>LogBlockSize:
                                AckFR3.to_csv(ACKFR3Path,index=False, mode='a+', header=False)
                                AckFR3=pd.DataFrame() 
                        if self.B2StartR==4:# first Packet distritution
                            AckFR4=pd.concat([AckFR4,dataslice])
                            if AckFR4.shape[0]>LogBlockSize:
                                AckFR4.to_csv(ACKFR4Path,index=False, mode='a+', header=False)
                                AckFR4=pd.DataFrame() 
            

            #prob assigen here
            packet.FailProb=random.random()
            if packet.FailProb<Alpha:
                #fail, resend the packet
                propagatetime=genPropagationTime(packet.fromNode)
                failprob=1#random.random(); this do not matter;assign when check              
                newPacket=Packet(MSG_TYPE,failprob,propagatetime,timstmp,self.nID,packet.fromNode)
                newPacket.RoundOrderToLeader=packet.RoundOrderToLeader
                newPacket.ReboundTimes=packet.ReboundTimes#leader retransmit copy ReboundTimes                 
                ISwitch.PacketInQueue(newPacket)
                #record resent time
                dataslice=pd.DataFrame({'SimuRoundN':[SimuRound],'SeqN':[self.AckCount],'Timeorg':[timstmp],'Inteval':[packet.AckInteval],'R':[self.Rcount],'B':[packet.ReboundTimes]}) 
                AckB2R6=pd.concat([AckB2R6,dataslice])
                if AckB2R6.shape[0]>LogBlockSize:
                    AckB2R6.to_csv(ACKB2R6Path,index=False, mode='a+', header=False)
                    AckB2R6=pd.DataFrame() 
            else:
                #sucess, drop the packet
                self.Rcount+=1
                
                if self.Rcount==R:
                    global bCommited
                    bCommited=1                    

                    if FirstAckPacket==0:#0-5: R==6     
                        #all commit
                        cmdata = pd.DataFrame({'SimuRoundN':[SimuRound],'CmitTime':[timstmp]}) 
                        CommitPDObj=pd.concat([CommitPDObj,cmdata])
                        if CommitPDObj.shape[0]>LogBlockSize:
                            CommitPDObj.to_csv(CommitIntvalFilePath,index=False, mode='a+', header=False)
                            CommitPDObj=pd.DataFrame()    
                        if SimuRound%LogBlockSize==0:
                            print("Commit! round:%d slice:%d time:%f"%(SimuRound,SLICENUM,timstmp))
                    
                        if packet.ReboundTimes==1:#mostly S1 and S2
                            CommitB1=pd.concat([CommitB1,cmdata])
                            if CommitB1.shape[0]>LogBlockSize:
                                CommitB1.to_csv(CommitB1Path,index=False, mode='a+', header=False)
                                CommitB1=pd.DataFrame()

                        if packet.ReboundTimes==2:#mostaly S2
                            CommitB2=pd.concat([CommitB2,cmdata])
                            if CommitB2.shape[0]>LogBlockSize:
                                CommitB2.to_csv(CommitB2Path,index=False, mode='a+', header=False)
                                CommitB2=pd.DataFrame()

                            if self.B2StartR<5:
                                CommitB2R0=pd.concat([CommitB2R0,cmdata])
                                if CommitB2R0.shape[0]>LogBlockSize:
                                    CommitB2R0.to_csv(CommitB2R0Path,index=False, mode='a+', header=False)
                                    CommitB2R0=pd.DataFrame()

                            if self.B2StartR==1:
                                CommitB2R1=pd.concat([CommitB2R1,cmdata])
                                if CommitB2R1.shape[0]>LogBlockSize:
                                    CommitB2R1.to_csv(CommitB2R1Path,index=False, mode='a+', header=False)
                                    CommitB2R1=pd.DataFrame()

                            if self.B2StartR==2:
                                CommitB2R2=pd.concat([CommitB2R2,cmdata])
                                if CommitB2R2.shape[0]>LogBlockSize:
                                    CommitB2R2.to_csv(CommitB2R2Path,index=False, mode='a+', header=False)
                                    CommitB2R2=pd.DataFrame()

                            if self.B2StartR==3:
                                CommitB2R3=pd.concat([CommitB2R3,cmdata])
                                if CommitB2R3.shape[0]>LogBlockSize:
                                    CommitB2R3.to_csv(CommitB2R3Path,index=False, mode='a+', header=False)
                                    CommitB2R3=pd.DataFrame()
                            
                            if self.B2StartR==4:
                                CommitB2R4=pd.concat([CommitB2R4,cmdata])
                                if CommitB2R4.shape[0]>LogBlockSize:
                                    CommitB2R4.to_csv(CommitB2R4Path,index=False, mode='a+', header=False)
                                    CommitB2R4=pd.DataFrame()
                            
                            if self.B2StartR==5:
                                CommitB2R5=pd.concat([CommitB2R5,cmdata])
                                if CommitB2R5.shape[0]>LogBlockSize:
                                    CommitB2R5.to_csv(CommitB2R5Path,index=False, mode='a+', header=False)
                                    CommitB2R5=pd.DataFrame()

                        if packet.ReboundTimes==3:#windowed B1 S2 commit
                            CommitB3=pd.concat([CommitB3,cmdata])
                            if CommitB3.shape[0]>LogBlockSize:
                                CommitB3.to_csv(CommitB3Path,index=False, mode='a+', header=False)
                                CommitB3=pd.DataFrame()

                        #Round Commit log 
                        if SLICENUM==1:
                            CommitS1=pd.concat([CommitS1,cmdata])
                            if CommitS1.shape[0]>LogBlockSize:
                                CommitS1.to_csv(CommitS1Path,index=False, mode='a+', header=False)
                                CommitS1=pd.DataFrame()
                            
                        if SLICENUM==2:
                            CommitS2=pd.concat([CommitS2,cmdata])
                            if CommitS2.shape[0]>LogBlockSize:
                                CommitS2.to_csv(CommitS2Path,index=False, mode='a+', header=False)
                                CommitS2=pd.DataFrame()  
                                
                        if SLICENUM==3:
                            CommitS3=pd.concat([CommitS3,cmdata])
                            if CommitS3.shape[0]>LogBlockSize:
                                CommitS3.to_csv(CommitS3Path,index=False, mode='a+', header=False)
                                CommitS3=pd.DataFrame()
                                
                        if SLICENUM==4:
                            CommitS4=pd.concat([CommitS4,cmdata])
                            if CommitS4.shape[0]>LogBlockSize:
                                CommitS4.to_csv(CommitS4Path,index=False, mode='a+', header=False)
                                CommitS4=pd.DataFrame()  
                                
                        if SLICENUM==5:
                            CommitS5=pd.concat([CommitS5,cmdata])
                            if CommitS5.shape[0]>LogBlockSize:
                                CommitS5.to_csv(CommitS5Path,index=False, mode='a+', header=False)
                                CommitS5=pd.DataFrame()
                                
                        if SLICENUM==6:
                            CommitS6=pd.concat([CommitS6,cmdata])
                            if CommitS6.shape[0]>LogBlockSize:
                                CommitS6.to_csv(CommitS6Path,index=False, mode='a+', header=False)
                                CommitS6=pd.DataFrame()  
                                
                        if SLICENUM==7:
                            CommitS7=pd.concat([CommitS7,cmdata])
                            if CommitS7.shape[0]>LogBlockSize:
                                CommitS7.to_csv(CommitS7Path,index=False, mode='a+', header=False)
                                CommitS7=pd.DataFrame()  
                                
                        if SLICENUM==8:
                            CommitS8=pd.concat([CommitS8,cmdata])
                            if CommitS8.shape[0]>LogBlockSize:
                                CommitS8.to_csv(CommitS8Path,index=False, mode='a+', header=False)
                                CommitS8=pd.DataFrame()  
                        
                        if SLICENUM==9:
                            CommitS9=pd.concat([CommitS9,cmdata])
                            if CommitS9.shape[0]>LogBlockSize:
                                CommitS9.to_csv(CommitS9Path,index=False, mode='a+', header=False)
                                CommitS9=pd.DataFrame() 
                        
                        if SLICENUM==10:
                            CommitS10=pd.concat([CommitS10,cmdata])
                            if CommitS10.shape[0]>LogBlockSize:
                                CommitS10.to_csv(CommitS10Path,index=False, mode='a+', header=False)
                                CommitS10=pd.DataFrame() 
                        
                        
                    else:
                        #all include first Ack
                        cmdata = pd.DataFrame({'SimuRoundN':[SimuRound],'CmitTime':[timstmp]}) 
                        CommitPDObj=pd.concat([CommitPDObj,cmdata])
                        if CommitPDObj.shape[0]>LogBlockSize:
                            CommitPDObj.to_csv(CommitIntvalFilePath,index=False, mode='a+', header=False)
                            CommitPDObj=pd.DataFrame()    

                        if packet.ReboundTimes==2:#only ReboundTimes>1 possible to commit
                            CommitB2=pd.concat([CommitB2,cmdata])
                            if CommitB2.shape[0]>LogBlockSize:
                                CommitB2.to_csv(CommitB2Path,index=False, mode='a+', header=False)
                                CommitB2=pd.DataFrame()

                            if self.B2StartR==5:#no self.B2StartR==6, we use R6 to reprent FirstAckPacket==1
                                cmdata = pd.DataFrame({'SimuRoundN':[SimuRound],'CmitTime':[timstmp]})
                                CommitB2R5=pd.concat([CommitB2R5,cmdata])
                                if CommitB2R5.shape[0]>LogBlockSize:
                                    CommitB2R5.to_csv(CommitB2R5Path,index=False, mode='a+', header=False)
                                    CommitB2R5=pd.DataFrame()
                                # CommitB2R6=pd.concat([CommitB2R6,cmdata])#R5 merge
                                # if CommitB2R6.shape[0]>LogBlockSize:
                                #     CommitB2R6.to_csv(CommitB2R6Path,index=False, mode='a+', header=False)
                                #     CommitB2R6=pd.DataFrame()

                    #log the data here for commit
                # else: #the packe received and Round increased
                #     # if self.Rcount>R:
                #     #      global bCommited
                #     #      bCommited=1
                    
                        

                

    def processPacketFollower(self,packet):
        if self.type==0:
            return
        #just convert, not need to consider the resend
        #because the one round is only valid for a FailProb of one packet
        if packet.type==MSG_TYPE:
            propagatetime=genPropagationTime(self.nID)
            failprob=0#random.random()
            timstmp=getCurTimeStamp()
            ###resend logical 
            #use the send NOK packet to implement 
            if packet.FailProb==1 and (ReTransTimeOut>2*Di):#failed packet from leader
                resendTime=packet.createTime+ReTransTimeOut
                if resendTime>timstmp:
                    propagatetime=resendTime
                #else: neglect

            newPacket=Packet(ACK_TPYE,failprob,propagatetime,timstmp,self.nID,packet.fromNode)
            newPacket.RoundOrderToLeader=packet.RoundOrderToLeader
            newPacket.ReboundTimes=packet.ReboundTimes#follower keep ReboundTimes 
            ISwitch.PacketInQueue(newPacket)
        return
    

gComputeNodeList={}#id:nodeobj all nodes should be in this list, idealswith is neglected in this case, sending is implemented by idealswitch

def getNodeByID(id):
    return gComputeNodeList[id]

#global time is managed here        
class IdealSwitch:
    def __init__(self):
        self.stackOutTimeOrdered=[]#packetstack,
        #each update should be sync with gTimeStamp

    def PacketInQueue(self,packet):
        #check the src/dest
        #get send out time
        #sort by send out time
        self.stackOutTimeOrdered.append(packet)
        #print("pre sort:%s",self.stackOutTimeOrdered)
        self.stackOutTimeOrdered.sort(key=sortPacketbySentOutTime)

        ##debug code
        # orderstr=''
        # for cpacket in self.stackOutTimeOrdered:
        #     outtime=cpacket.createTime+cpacket.propagationTime
        #     addstr="%f, "%(outtime)
        #     orderstr+=addstr
        # print("post sort:%s"%orderstr)

    def PacketDeQueue(self):
        global gTimeStamp,bCommited,SLICENUM
        global preAckTimestamp
        global RSucCount0His,RSucCount1His,RSucCount2His,RSucCount3His,RSucCount4His,RSucCount5His,RSucCount6orMoreHis
        #the queue already sorted by send out time
        if len(self.stackOutTimeOrdered)>0:
            packettosend=self.stackOutTimeOrdered.pop(0)
            #updage gTimeStamp wallTimeStamp
            #preTimestamp=gTimeStamp
            gTimeStamp=packettosend.createTime+packettosend.propagationTime
            #wallTimeStamp inclrease only
            #wallTimeStamp=wallTimeStamp+(gTimeStamp-preTimestamp)
            #print("Time update! %f"%(gTimeStamp))
            toID=packettosend.toNode
            theNode=getNodeByID(toID)
            #to leader packet inteval cacluate 
            #update SLICENUM
            if preAckTimestamp>gTimeStamp:
                if FirstAckIntervalDisable:
                    preAckTimestamp=0
                else:
                    preAckTimestamp=MinCmitTime
            delta=gTimeStamp-preAckTimestamp            
            preR=0
            #pre process
            if toID=="L":
                #print("Leader InQueue time:%f slice:%d"%(gTimeStamp,SLICENUM)) 
                #if delta>TimeSlice and SLICENUM==1:
                #    print("delta:%f tm:%f crt:%f prop:%f"%(delta,gTimeStamp,packettosend.createTime,packettosend.propagationTime))              
                preAckTimestamp=gTimeStamp
                packettosend.AckInteval=delta
                preR=theNode.Rcount
                   
                #disable slice count, faster
                while gTimeStamp>=(SLICENUM*TimeSlice+MinCmitTime):
                    SLICENUM+=1  

            else:           
                packettosend.AckInteval=0
            
            #packet process
            theNode.InQueue(packettosend)#this may lead to new packet in queue
            
            #post statics
            if toID=="L":
                if SLICENUM>=0:#slice 0,1,2...                   
                    if SLICENUM<=MAXSLICE:                        
                        if theNode.Rcount>preR: 
                            #one packet increase at most one count
                            #decrease from preR of SLICENUM-1 and add to the theNode.Rcount of SLICENUM
                            if theNode.Rcount==0:
                                RSucCount0His[SLICENUM]+=1
                            if theNode.Rcount==1:
                                RSucCount1His[SLICENUM]+=1
                            if theNode.Rcount==2:
                                RSucCount2His[SLICENUM]+=1
                            if theNode.Rcount==3:
                                RSucCount3His[SLICENUM]+=1
                            if theNode.Rcount==4:
                                RSucCount4His[SLICENUM]+=1
                            if theNode.Rcount==5:
                                RSucCount5His[SLICENUM]+=1
                            if theNode.Rcount>=6:
                                RSucCount6orMoreHis[SLICENUM]+=1

                            if preR==0:
                                RSucCount0His[SLICENUM]-=1
                            if preR==1:
                                RSucCount1His[SLICENUM]-=1
                            if preR==2:
                                RSucCount2His[SLICENUM]-=1
                            if preR==3:
                                RSucCount3His[SLICENUM]-=1
                            if preR==4:
                                RSucCount4His[SLICENUM]-=1
                            if preR==5:
                                RSucCount5His[SLICENUM]-=1
                            if preR>=6:
                                RSucCount6orMoreHis[SLICENUM]-=1
        else:
            print("Queue Empty!!")

ISwitch=IdealSwitch()



SimuRound=0

def InitialLogFileOpen():
    global AckPDOBJ,AckB1,AckB2,AckB3,AckS1,AckS2,AckS3,AckS4,AckS5,AckS6,AckS7,AckS8,AckS9,AckS10
    global CommitPDObj,CommitB1,CommitB2,CommitB3,CommitS1,CommitS2,CommitS3,CommitS4,CommitS5,CommitS6,CommitS7,CommitS8,CommitS9,CommitS10,CommitS11,CommitS12
    global AckB2R0,AckB2R1,AckB2R2,AckB2R3,AckB2R4,AckB2R5,AckB2R6,CommitB2R0,CommitB2R1,CommitB2R2,CommitB2R3,CommitB2R4,CommitB2R5,CommitB2R6,AckFR3,AckFR4
    global DebugExpObj   
    
    #write AckPT file
    AckPDOBJ = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckPDOBJ.to_csv(ACKINTFilePath, index=False)
    AckPDOBJ = pd.DataFrame()

    #ReBoundTimes
    AckB1 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckB1.to_csv(ACKB1Path, index=False)
    AckB1 = pd.DataFrame()

    AckB2 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckB2.to_csv(ACKB2Path, index=False)
    AckB2 = pd.DataFrame()

    AckB3 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckB3.to_csv(ACKB3Path, index=False)
    AckB3 = pd.DataFrame()

    AckB2R0 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckB2R0.to_csv(ACKB2R0Path, index=False)
    AckB2R0 = pd.DataFrame()
    
    AckB2R1 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckB2R1.to_csv(ACKB2R1Path, index=False)
    AckB2R1 = pd.DataFrame()

    AckB2R2 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckB2R2.to_csv(ACKB2R2Path, index=False)
    AckB2R2 = pd.DataFrame()

    AckB2R3 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckB2R3.to_csv(ACKB2R3Path, index=False)
    AckB2R3 = pd.DataFrame()

    AckB2R4 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckB2R4.to_csv(ACKB2R4Path, index=False)
    AckB2R4 = pd.DataFrame()

    AckB2R5 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckB2R5.to_csv(ACKB2R5Path, index=False)
    AckB2R5 = pd.DataFrame()

    AckB2R6 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckB2R6.to_csv(ACKB2R6Path, index=False)
    AckB2R6 = pd.DataFrame()

    #slice

    AckS1 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckS1.to_csv(ACKS1Path, index=False)
    AckS1 = pd.DataFrame()

    AckS2 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckS2.to_csv(ACKS2Path, index=False)
    AckS2 = pd.DataFrame()

    AckS3 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckS3.to_csv(ACKS3Path, index=False)
    AckS3 = pd.DataFrame()

    AckS4 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckS4.to_csv(ACKS4Path, index=False)
    AckS4 = pd.DataFrame()

    AckS5 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckS5.to_csv(ACKS5Path, index=False)
    AckS5 = pd.DataFrame()

    AckS6 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckS6.to_csv(ACKS6Path, index=False)
    AckS6 = pd.DataFrame()

    AckS7 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckS7.to_csv(ACKS7Path, index=False)
    AckS7 = pd.DataFrame()

    AckS8 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckS8.to_csv(ACKS8Path, index=False)
    AckS8 = pd.DataFrame()

    AckS9 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckS9.to_csv(ACKS9Path, index=False)
    AckS9 = pd.DataFrame()

    AckS10 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckS10.to_csv(ACKS10Path, index=False)
    AckS10 = pd.DataFrame()

    AckFR3 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckFR3.to_csv(ACKFR3Path, index=False)
    AckFR3 = pd.DataFrame()

    AckFR4 = pd.DataFrame({'SimuRoundN':[-1],'SeqN':[-1],'Timeorg':[0],'Inteval':[0],'R':[0],'B':[0]}) 
    AckFR4.to_csv(ACKFR4Path, index=False)
    AckFR4 = pd.DataFrame()

    

    #write CommitPT file
    CommitPDObj = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitPDObj.to_csv(CommitIntvalFilePath, index=False)
    CommitPDObj = pd.DataFrame()

    #ReBound Times

    CommitB1 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitB1.to_csv(CommitB1Path, index=False)
    CommitB1 = pd.DataFrame()

    CommitB2 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitB2.to_csv(CommitB2Path, index=False)
    CommitB2 = pd.DataFrame()

    CommitB3 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitB3.to_csv(CommitB3Path, index=False)
    CommitB3 = pd.DataFrame()

    CommitB2R0 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitB2R0.to_csv(CommitB2R0Path, index=False)
    CommitB2R0 = pd.DataFrame()
    
    CommitB2R1 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitB2R1.to_csv(CommitB2R1Path, index=False)
    CommitB2R1 = pd.DataFrame()

    CommitB2R2 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitB2R2.to_csv(CommitB2R2Path, index=False)
    CommitB2R2 = pd.DataFrame()

    CommitB2R3 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitB2R3.to_csv(CommitB2R3Path, index=False)
    CommitB2R3 = pd.DataFrame()

    CommitB2R4 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitB2R4.to_csv(CommitB2R4Path, index=False)
    CommitB2R4 = pd.DataFrame()

    CommitB2R5 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitB2R5.to_csv(CommitB2R5Path, index=False)
    CommitB2R5 = pd.DataFrame()

    CommitB2R6 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitB2R6.to_csv(CommitB2R6Path, index=False)
    CommitB2R6 = pd.DataFrame()

    #Slice

    CommitS1 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS1.to_csv(CommitS1Path, index=False)
    CommitS1 = pd.DataFrame()

    CommitS2 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS2.to_csv(CommitS2Path, index=False)
    CommitS2 = pd.DataFrame()

    CommitS3 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS3.to_csv(CommitS3Path, index=False)
    CommitS3 = pd.DataFrame()

    CommitS4 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS4.to_csv(CommitS4Path, index=False)
    CommitS4 = pd.DataFrame()

    CommitS5 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS5.to_csv(CommitS5Path, index=False)
    CommitS5 = pd.DataFrame()

    CommitS6 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS6.to_csv(CommitS6Path, index=False)
    CommitS6 = pd.DataFrame()

    CommitS7 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS7.to_csv(CommitS7Path, index=False)
    CommitS7 = pd.DataFrame()

    CommitS8 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS8.to_csv(CommitS8Path, index=False)
    CommitS8 = pd.DataFrame()

    CommitS9 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS9.to_csv(CommitS9Path, index=False)
    CommitS9 = pd.DataFrame()

    CommitS10 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS10.to_csv(CommitS10Path, index=False)
    CommitS10 = pd.DataFrame()

    CommitS11 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS11.to_csv(CommitS11Path, index=False)
    CommitS11 = pd.DataFrame()

    CommitS12 = pd.DataFrame({'SimuRoundN':[-1],'CmitTime':[0]}) 
    CommitS12.to_csv(CommitS12Path, index=False)
    CommitS12 = pd.DataFrame()


    #write ExpTimeDebug file
    if DEBUG_EXPTIME:
        DebugExpObj = pd.DataFrame({'SimuRoundN':[-1],'PropTime':[0]})
        DebugExpObj.to_csv(DebugExpTimeVerifyFilePath, index=False)
        DebugExpObj = pd.DataFrame()

def FlashLogFile():
    global AckPDOBJ,AckB1,AckB2,AckB3,AckS1,AckS2,AckS3,AckS4,AckS5,AckS6,AckS7,AckS8,AckS8,AckS9,AckS10  
    global CommitPDObj,CommitB1,CommitB2,CommitB3,CommitS1,CommitS2,CommitS3,CommitS4,CommitS5,CommitS6,CommitS7,CommitS8,CommitS9,CommitS10,CommitS11,CommitS12
    global AckB2R0,AckB2R1,AckB2R2,AckB2R3,AckB2R4,AckB2R5,AckB2R6,CommitB2R0,CommitB2R1,CommitB2R2,CommitB2R3,CommitB2R4,CommitB2R5,CommitB2R6,AckFR3,AckFR4
    global DebugExpObj   
    global RSucCount0His,RSucCount1His,RSucCount2His,RSucCount3His,RSucCount4His,RSucCount5His,RSucCount6orMoreHis 
    
    #write AckPT file
    if AckPDOBJ.shape[0]>0:   
        AckPDOBJ.to_csv(ACKINTFilePath, index=False,mode='a+', header=False)
        AckPDOBJ = pd.DataFrame()

    if AckB1.shape[0]>0:   
        AckB1.to_csv(ACKB1Path, index=False,mode='a+', header=False)
        AckB1 = pd.DataFrame()
    
    if AckB2.shape[0]>0:   
        AckB2.to_csv(ACKB2Path, index=False,mode='a+', header=False)
        AckB2 = pd.DataFrame()

    if AckB3.shape[0]>0:   
        AckB3.to_csv(ACKB3Path, index=False,mode='a+', header=False)
        AckB3 = pd.DataFrame()


    if AckB2R0.shape[0]>0:   
        AckB2R0.to_csv(ACKB2R0Path, index=False,mode='a+', header=False)
        AckB2R0 = pd.DataFrame()
        
    if AckB2R1.shape[0]>0:   
        AckB2R1.to_csv(ACKB2R1Path, index=False,mode='a+', header=False)
        AckB2R1 = pd.DataFrame()

    if AckB2R2.shape[0]>0:   
        AckB2R2.to_csv(ACKB2R2Path, index=False,mode='a+', header=False)
        AckB2R2 = pd.DataFrame()
    
    if AckB2R3.shape[0]>0:   
        AckB2R3.to_csv(ACKB2R3Path, index=False,mode='a+', header=False)
        AckB2R3 = pd.DataFrame()
    
    if AckB2R4.shape[0]>0:   
        AckB2R4.to_csv(ACKB2R4Path, index=False,mode='a+', header=False)
        AckB2R4 = pd.DataFrame()
    
    if AckB2R5.shape[0]>0:   
        AckB2R5.to_csv(ACKB2R5Path, index=False,mode='a+', header=False)
        AckB2R5 = pd.DataFrame()
    
    if AckB2R6.shape[0]>0:   
        AckB2R6.to_csv(ACKB2R6Path, index=False,mode='a+', header=False)
        AckB2R6 = pd.DataFrame()


    if AckS1.shape[0]>0:   
        AckS1.to_csv(ACKS1Path, index=False,mode='a+', header=False)
        AckS1 = pd.DataFrame()
    
    if AckS2.shape[0]>0:   
        AckS2.to_csv(ACKS2Path, index=False,mode='a+', header=False)
        AckS2 = pd.DataFrame()

    if AckS3.shape[0]>0:   
        AckS3.to_csv(ACKS3Path, index=False,mode='a+', header=False)
        AckS3 = pd.DataFrame()

    if AckS4.shape[0]>0:   
        AckS4.to_csv(ACKS4Path, index=False,mode='a+', header=False)
        AckS4 = pd.DataFrame()

    if AckS5.shape[0]>0:   
        AckS5.to_csv(ACKS5Path, index=False,mode='a+', header=False)
        AckS5 = pd.DataFrame()

    if AckS6.shape[0]>0:   
        AckS6.to_csv(ACKS6Path, index=False,mode='a+', header=False)
        AckS6 = pd.DataFrame()

    if AckS7.shape[0]>0:   
        AckS7.to_csv(ACKS7Path, index=False,mode='a+', header=False)
        AckS7 = pd.DataFrame()

    if AckS8.shape[0]>0:   
        AckS8.to_csv(ACKS8Path, index=False,mode='a+', header=False)
        AckS8 = pd.DataFrame()

    if AckS9.shape[0]>0:   
        AckS9.to_csv(ACKS9Path, index=False,mode='a+', header=False)
        AckS9 = pd.DataFrame()
    
    if AckS10.shape[0]>0:   
        AckS10.to_csv(ACKS10Path, index=False,mode='a+', header=False)
        AckS10 = pd.DataFrame()

    if AckFR3.shape[0]>0:   
        AckFR3.to_csv(ACKFR3Path, index=False,mode='a+', header=False)
        AckFR3 = pd.DataFrame()
    
    if AckFR4.shape[0]>0:   
        AckFR4.to_csv(ACKFR4Path, index=False,mode='a+', header=False)
        AckFR4 = pd.DataFrame()



    #write CommitPT file
    if CommitPDObj.shape[0]>0: 
        CommitPDObj.to_csv(CommitIntvalFilePath, index=False,mode='a+', header=False)
        CommitPDObj = pd.DataFrame()

    if CommitB1.shape[0]>0: 
        CommitB1.to_csv(CommitB1Path, index=False,mode='a+', header=False)
        CommitB1 = pd.DataFrame()

    if CommitB2.shape[0]>0: 
        CommitB2.to_csv(CommitB2Path, index=False,mode='a+', header=False)
        CommitB2 = pd.DataFrame()
        
    if CommitB3.shape[0]>0: 
        CommitB3.to_csv(CommitB3Path, index=False,mode='a+', header=False)
        CommitB3 = pd.DataFrame()


    if CommitB2R0.shape[0]>0: 
        CommitB2R0.to_csv(CommitB2R0Path, index=False,mode='a+', header=False)
        CommitB2R0 = pd.DataFrame()
        
    if CommitB2R1.shape[0]>0: 
        CommitB2R1.to_csv(CommitB2R1Path, index=False,mode='a+', header=False)
        CommitB2R1 = pd.DataFrame()
    
    if CommitB2R2.shape[0]>0: 
        CommitB2R2.to_csv(CommitB2R2Path, index=False,mode='a+', header=False)
        CommitB2R2 = pd.DataFrame()
    
    if CommitB2R3.shape[0]>0: 
        CommitB2R3.to_csv(CommitB2R3Path, index=False,mode='a+', header=False)
        CommitB2R3 = pd.DataFrame()
    
    if CommitB2R4.shape[0]>0: 
        CommitB2R4.to_csv(CommitB2R4Path, index=False,mode='a+', header=False)
        CommitB2R4 = pd.DataFrame()
    
    if CommitB2R5.shape[0]>0: 
        CommitB2R5.to_csv(CommitB2R5Path, index=False,mode='a+', header=False)
        CommitB2R5 = pd.DataFrame()

    if CommitB2R6.shape[0]>0: 
        CommitB2R6.to_csv(CommitB2R6Path, index=False,mode='a+', header=False)
        CommitB2R6 = pd.DataFrame()
    
    
    if CommitS1.shape[0]>0: 
        CommitS1.to_csv(CommitS1Path, index=False,mode='a+', header=False)
        CommitS1 = pd.DataFrame()

    if CommitS2.shape[0]>0: 
        CommitS2.to_csv(CommitS2Path, index=False,mode='a+', header=False)
        CommitS2 = pd.DataFrame()
        
    if CommitS3.shape[0]>0: 
        CommitS3.to_csv(CommitS3Path, index=False,mode='a+', header=False)
        CommitS3 = pd.DataFrame()
        
    if CommitS4.shape[0]>0: 
        CommitS4.to_csv(CommitS4Path, index=False,mode='a+', header=False)
        CommitS4 = pd.DataFrame()
        
    if CommitS5.shape[0]>0: 
        CommitS5.to_csv(CommitS5Path, index=False,mode='a+', header=False)
        CommitS5 = pd.DataFrame()
        
    if CommitS6.shape[0]>0: 
        CommitS6.to_csv(CommitS6Path, index=False,mode='a+', header=False)
        CommitS6 = pd.DataFrame()
        
    if CommitS7.shape[0]>0: 
        CommitS7.to_csv(CommitS7Path, index=False,mode='a+', header=False)
        CommitS7 = pd.DataFrame()
        
    if CommitS8.shape[0]>0: 
        CommitS8.to_csv(CommitS8Path, index=False,mode='a+', header=False)
        CommitS8 = pd.DataFrame()

    if CommitS9.shape[0]>0: 
        CommitS9.to_csv(CommitS9Path, index=False,mode='a+', header=False)
        CommitS9 = pd.DataFrame()
    
    if CommitS10.shape[0]>0: 
        CommitS10.to_csv(CommitS10Path, index=False,mode='a+', header=False)
        CommitS10 = pd.DataFrame()

    if CommitS11.shape[0]>0: 
        CommitS11.to_csv(CommitS11Path, index=False,mode='a+', header=False)
        CommitS11 = pd.DataFrame()
    
    if CommitS12.shape[0]>0: 
        CommitS12.to_csv(CommitS12Path, index=False,mode='a+', header=False)
        CommitS12 = pd.DataFrame()
 


    if DEBUG_EXPTIME:
        if DebugExpObj.shape[0]>0: 
            DebugExpObj.to_csv(DebugExpTimeVerifyFilePath, index=False,mode='a+', header=False)
            DebugExpObj = pd.DataFrame()

    #R Slice Histogram
    RSSHisData =None   
    #delta value
    for i in range(0,MAXSLICE+2):
        
        S1his=pd.DataFrame({'SliceNum':[-i],'RSuss0Num':[RSucCount0His[i]],'RSuss1Num':[RSucCount1His[i]],'RSuss2Num':[RSucCount2His[i]],'RSuss3Num':[RSucCount3His[i]],'RSuss4Num':[RSucCount4His[i]],'RSuss5Num':[RSucCount5His[i]],'RSuss6andMoreNum':[RSucCount6orMoreHis[i]]}) 
        RSSHisData=pd.concat([RSSHisData,S1his])
    #resudial value
    for i in range(0,MAXSLICE+2):        
        if i==0:
            RSucCount0His[i]+=MAXROUND#initial count adjust
        S1his=pd.DataFrame({'SliceNum':[i],'RSuss0Num':[RSucCount0His[i]],'RSuss1Num':[RSucCount1His[i]],'RSuss2Num':[RSucCount2His[i]],'RSuss3Num':[RSucCount3His[i]],'RSuss4Num':[RSucCount4His[i]],'RSuss5Num':[RSucCount5His[i]],'RSuss6andMoreNum':[RSucCount6orMoreHis[i]]}) 
        RSSHisData=pd.concat([RSSHisData,S1his])
        #next slice count adjust base on current slice
        if (i+1)<(MAXSLICE+2):
            RSucCount0His[i+1]=RSucCount0His[i+1]+RSucCount0His[i]
            RSucCount1His[i+1]=RSucCount1His[i+1]+RSucCount1His[i]
            RSucCount2His[i+1]=RSucCount2His[i+1]+RSucCount2His[i]
            RSucCount3His[i+1]=RSucCount3His[i+1]+RSucCount3His[i]
            RSucCount4His[i+1]=RSucCount4His[i+1]+RSucCount4His[i]
            RSucCount5His[i+1]=RSucCount5His[i+1]+RSucCount5His[i]
            RSucCount6orMoreHis[i+1]=RSucCount6orMoreHis[i+1]+RSucCount6orMoreHis[i]

    RSSHisData.to_csv(RSussSliceHisPath, index=False)
    RSSHisData =None


def simuDES():
    global gComputeNodeList,SimuRound,gTimeStamp,preAckTimestamp,SLICENUM,N,R
    gComputeNodeList={}
    #Nodes create
    leader=None
    #initial links delay, system parameters also be changed by cfg
    #lnkMdl.genLinkDelay()
    #lnkMdl.genLinkDelayFromCfg()# link setting from cfg file for Dim1
    #N,R=lnkMdl.genLinkDelayFromCfgDim2() # for Dim2 test
    lnkMdl.genLinkDelayFromCfgD3() #for simu base on DB

    #get random id
    idlist=list(range(1,N+1))
    
    
    for i in range(N+1):
        if i==0:
            leader=Node('L',0)
            gComputeNodeList['L']=leader
        else:
            fid="F%d"%(i)
            fiobj=Node(fid,1)
            gComputeNodeList[fid]=fiobj

    #make log dir
    print(LOGDATADIR)
    if not os.path.exists(LOGDATADIR):
        os.makedirs(LOGDATADIR)
    
    InitialLogFileOpen()
    

    SimuRound=0
    while(SimuRound<MAXROUND):
        #initial packet sending from leader
        SimuRound+=1
        bCommited=0
        ##Raft initial, for each instance
        leader.Rcount=0
        leader.B2StartR=-1
        random.shuffle(idlist)
        #print("list:%s"%(idlist))
        for i in range(1,N+1):
            
            failprob=0#random.random()
            timstmp=getCurTimeStamp()
            #timstmp=getCurTimeStamp()+Di*i#sending secq from leader,send out one packet at a time so Di is meaningful
            #print("idx:%d"%(i))
            id=idlist[i-1]#random id

            toID="F%d"%(id)
            propagatetime=genPropagationTime(toID)
            newPacket=Packet(MSG_TYPE,failprob,propagatetime,timstmp,'L',toID)
            ISwitch.PacketInQueue(newPacket)
        ##DES main loop
        #while(bCommited==0):# the remainder packet in system should process also
        while(1):
            ISwitch.PacketDeQueue()
            if len(ISwitch.stackOutTimeOrdered)<=0:
                break
        
        ISwitch.stackOutTimeOrdered=[]#clear pending packets for new rounds
        gTimeStamp=0.0
        if FirstAckIntervalDisable:
            preAckTimestamp=0
        else:
            preAckTimestamp=MinCmitTime
        SLICENUM=0
        #print("*")
        

    print("Finish one round of DES!!")
    FlashLogFile()



if HisTarget=="AckALL":
    ACKInputPath=os.path.join(LOGDATADIR,'ackintevals.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackintevalsPostPro.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackintevalsPostPro.trace')

if HisTarget=="AckB1":
    ACKInputPath=os.path.join(LOGDATADIR,'ackB1.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB1Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB1Inteval.trace')

if HisTarget=="AckB2":
    if GetTimeDistr==-1:
        ACKInputPath=os.path.join(LOGDATADIR,'ackB2.csv')
        ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB2Inteval.csv')
        ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB2Inteval.trace')
    else:
        ACKInputPath=os.path.join(LOGDATADIR,'ackB2.csv')
        ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB2Dist.csv')
        ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB2Dist.trace')

if HisTarget=="AckB3":
    ACKInputPath=os.path.join(LOGDATADIR,'ackB3.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB3Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB3Inteval.trace')

if HisTarget=="AckB2R0":
    ACKInputPath=os.path.join(LOGDATADIR,'ackB2R0.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB2R0Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB2R0Inteval.trace')

if HisTarget=="AckB2R1":
    ACKInputPath=os.path.join(LOGDATADIR,'ackB2R1.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB2R1Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB2R1Inteval.trace')
if HisTarget=="AckB2R2":
    ACKInputPath=os.path.join(LOGDATADIR,'ackB2R2.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB2R2Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB2R2Inteval.trace')
if HisTarget=="AckB2R3":
    ACKInputPath=os.path.join(LOGDATADIR,'ackB2R3.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB2R3Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB2R3Inteval.trace')
if HisTarget=="AckB2R4":
    ACKInputPath=os.path.join(LOGDATADIR,'ackB2R4.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB2R4Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB2R4Inteval.trace')
if HisTarget=="AckB2R5":
    ACKInputPath=os.path.join(LOGDATADIR,'ackB2R5.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB2R5Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB2R5Inteval.trace')

if HisTarget=="AckB2R6":
    if GetTimeDistr==-1:
        ACKInputPath=os.path.join(LOGDATADIR,'ackB2R6.csv')
        ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB2R6Inteval.csv')
        ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB2R6Inteval.trace')
    else:
        ACKInputPath=os.path.join(LOGDATADIR,'ackB2R6.csv')
        ACKIntervalsPath=os.path.join(LOGDATADIR,'ackB1LeftDist.csv')
        ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackB1LeftDist.trace')

if HisTarget=="AckS1":
    ACKInputPath=os.path.join(LOGDATADIR,'ackS1.csv')
    if FilterB==-1:
        ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS1Inteval.csv')
        ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS1Inteval.trace')
    elif FilterB==1:
        ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS1B1Inteval.csv')
        ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS1B1Inteval.trace')
    elif FilterB==2:
        ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS1B2Inteval.csv')
        ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS1B2Inteval.trace')
    

if HisTarget=="AckS2":
    ACKInputPath=os.path.join(LOGDATADIR,'ackS2.csv')
    if FilterB==-1:
        ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS2Inteval.csv')
        ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS2Inteval.trace')
    elif FilterB==1:
        ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS2B1Inteval.csv')
        ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS2B1Inteval.trace')
    elif FilterB==2:
        ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS2B2Inteval.csv')
        ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS2B2Inteval.trace')

if HisTarget=="AckS3":
    ACKInputPath=os.path.join(LOGDATADIR,'ackS3.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS3Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS3Inteval.trace')

if HisTarget=="AckS4":
    ACKInputPath=os.path.join(LOGDATADIR,'ackS4.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS4Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackRSInteval.trace')

if HisTarget=="AckS5":
    ACKInputPath=os.path.join(LOGDATADIR,'ackS5.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS5Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS5Inteval.trace')

if HisTarget=="AckS6":
    ACKInputPath=os.path.join(LOGDATADIR,'ackS6.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS6Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS6Inteval.trace')

if HisTarget=="AckS7":
    ACKInputPath=os.path.join(LOGDATADIR,'ackS7.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS7Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS7Inteval.trace')

if HisTarget=="AckS8":
    ACKInputPath=os.path.join(LOGDATADIR,'ackS8.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS8Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS8Inteval.trace')

if HisTarget=="AckS9":
    ACKInputPath=os.path.join(LOGDATADIR,'ackS9.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS9Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS9Inteval.trace')

if HisTarget=="AckS10":
    ACKInputPath=os.path.join(LOGDATADIR,'ackS10.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackS10Inteval.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackS10Inteval.trace')

if HisTarget=="AckFR3":
    ACKInputPath=os.path.join(LOGDATADIR,'ackSFR3.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackSFR3Dist.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackSSFR3Dist.trace')

if HisTarget=="AckFR4":
    ACKInputPath=os.path.join(LOGDATADIR,'ackSFR4.csv')
    ACKIntervalsPath=os.path.join(LOGDATADIR,'ackSSFR4Dist.csv')
    ACKIntrvalTrack=os.path.join(LOGDATADIR,'ackSSFR4Dist.trace')


#def
def processAckIntevalGenFromRaw():
    AckItvlObj = pd.DataFrame({'SeqN':[-1],'Inteval':[0]}) 
    AckItvlObj.to_csv(ACKIntervalsPath, index=False)
    AckItvlObj = pd.DataFrame()
    Seqn=0
    stringlist=[]
    with open(ACKInputPath,'rt') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                idx=int(row['SeqN'])
                RtoFilter=int(row['R'])
                BtoFilter=int(row['B'])
                if idx>=1:
                    if GetTimeDistr==-1:
                        tdelta=(float(row['Inteval']))
                        if tdelta>FilterFisrtAckArrive:
                            tdelta=-0.1#skip
                    else:
                        tdelta=(float(row['Timeorg']))-DeTimeOffset
                    if tdelta>0 and (RtoFilter==FilterR or FilterR<0)and (BtoFilter==FilterB or FilterB<0):
                        Seqn+=1
                        if Seqn%LogBlockSize==0:
                            print("converted %d"%(Seqn))
                        tddata = pd.DataFrame({'SeqN':[Seqn],'Inteval':[tdelta]}) 
                        AckItvlObj=pd.concat([AckItvlObj,tddata])
                        if AckItvlObj.shape[0]>LogBlockSize:
                            AckItvlObj.to_csv(ACKIntervalsPath,index=False, mode='a+', header=False)
                            AckItvlObj=pd.DataFrame()   
                        #for trace gen
                        trackline="  %.7e\n"%(tdelta)
                        stringlist.append(trackline)
    if AckItvlObj.shape[0]>0:
        AckItvlObj.to_csv(ACKIntervalsPath, index=False, mode='a+', header=False)
        AckItvlObj = pd.DataFrame()
    #save trace file
    with open(ACKIntrvalTrack,'w') as f:
        f.writelines(stringlist)
        f.close()

def ConvertToHistorgram():
    pass

#main post pross  
# 
def postPorcess():
    processAckIntevalGenFromRaw()
      
#def GenHistogram():

#CommitInteval CommitIntvalFilePath
#return value of the 95 percent of asending order
ResultFile="result.log"
def Anilyze95pct():
    data=[]
    with open(CommitIntvalFilePath,'r') as csvfile:
        reader=csv.reader(csvfile)
        next(reader)#header
        next(reader)#invalid data       
        for row in reader:
            value=float(row[1])#index 1 is "CmitTime"
            data.append(value)
    length=len(data)
    index=math.floor(length*0.95)
    #idx=ceil(length(meanv)*0.05);    
    data.sort()
    
    strlist=[]
    resultstr="Percent95Value:%f\n"%(data[index])
    strlist.append(resultstr)
    resultfilepath=os.path.join(CURRENTDIR,ResultFile)
    with open(resultfilepath,'w') as f:
        f.writelines(strlist)
        f.close()



def SimuAndAnilyze():
    simuDES()
    Anilyze95pct()

if __name__=='__main__':SimuAndAnilyze()
#if __name__=='__main__':simuDES()
#if __name__=='__main__':postPorcess()

