#!/usr/bin/python3
import sqlite3,math,os
import sortlinklist as sorLL
import pathsSeqGen as pthG

DataDir=os.path.join(pthG.RUNNINGDRR,"ResultDataHis")
TheDataBaseFile=os.path.join(DataDir,'BorderPointsDBSqlite.db')
DBconn=None
DBcusr=None

def OpenDatabase():
    global DBconn,DBcusr
    DBconn = sqlite3.connect(TheDataBaseFile)
    DBcusr=DBconn.cursor()

def CloseDatabase():
    global DBconn,DBcusr
    DBconn.commit()
    DBconn.close()
    DBcusr=None
    DBconn=None

def commitChanges():
    DBconn.commit()

ALLPREFIX='AllPrefixMAP'
BORDERPOINTS='BorderPoints'
LINKDESTABLE='LinksDes'
PREFIXTAILS='PrefixTails'
ALLTAILTABLE='AllTailTable'
TAILSTABLE='TailsTable'
WORKSCHEDUL='RangeTable'



GOTTYPE_SIMULATION=0
GOTTYPE_DERIVED=1

TODOACT_NONE=0
TODOACT_SIMUCK=1
TODOACT_DEL=2

PREFIX_STATE_NONE=0
PREFIX_STATE_DEDUC_TAILS=1
PREFIX_STATE_SIMU_TAILS=2



IDX_HASH=0
IDX_ID1=1
IDX_ID2=2
IDX_ID3=3
IDX_ID4=4
IDX_ID5=5
IDX_ID6=6
IDX_ID7=7
IDX_ID8=8
IDX_ID9=9
IDX_ID10=10

IDX_PREFIXVALUE=0

#ALLFPRFIX
IDX_ORDERNUM=6
IDX_CKTYPE=7

#BORDERPOINTS
IDX_TVALUE=11
IDX_GOTTYPE=12
IDX_TODOACT=13
IDX_PREFIXDB=14


#PREFIXTAILS
IDX_PREFIX_TAILSV=6
IDX_PREFIX_TAILSNUM=7


IDX_ADDIDX=1
IDX_DISPREFIX=2
IDX_NEWADDED=3
IDX_LKDISP=4

IDX_TTAILVALUE=0
IDX_TID6=1
IDX_TID7=2
IDX_TID8=3
IDX_TID9=4
IDX_TID10=5

IDX_TAILSV=0
IDX_TAILSNUM=1
IDX_TAILSLSTSTR=2

def createDBs():
    OpenDatabase()    
    #checkType: 0 uncheck
    #           1 simu set
    #           2 deduct set
    #           3 outliner

    sql_text_0 = '''CREATE TABLE %s
           (PrefixValue INTEGER PRIMARY KEY NOT NULL,            
            ID1 INTEGER,
            ID2 INTEGER,
            ID3 INTEGER,
            ID4 INTEGER,
            ID5 INTEGER,
            OrderNum INTEGER,
            CheckType INTEGER);'''%(ALLPREFIX)
    
    # 建表的sql语句
    # HashKey is the not change able key for the links
    # IDs can change with the mapping functions
    # Tvalue is not important, since all points are broder points
    # GOTTYPE: 0:simulation; 1: derived.
    # TODOACT: 0:nothing; 1: checkbySimulation; 2: after check, not valid, to be deleted
    # for GOTTYPE derived, TODOACT firstly set 1, then check ,if ok set 0 , if fail set 2; at same time new border will be tested by user programs.
    # for GOTTYPE simulation, TODOACT always set 0.

    sql_text_1 = '''CREATE TABLE %s
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
            TValue REAL,
            GOTTYPE INTEGER,
            TODOACT INTEGER,
            PrefixDB INTEGER);'''%(BORDERPOINTS)
    
    sql_text_2 = '''CREATE TABLE %s
           (HashKey TEXT PRIMARY KEY NOT NULL,
            AddIdx INTEGER,
            PrefixValue INGETER,
            NewAdded INGEGER,
            LinksDicStr TEXT);'''%(LINKDESTABLE)
    
    sql_text_3 = '''CREATE TABLE %s
           (PrefixValue INTEGER PRIMARY KEY NOT NULL,            
            ID1 INTEGER,
            ID2 INTEGER,
            ID3 INTEGER,
            ID4 INTEGER,
            ID5 INTEGER,
            TailsValue TEXT,
            TailsNum INTEGER);'''%(PREFIXTAILS)
    
    #not used now
    sql_text_4 = '''CREATE TABLE %s
           (TailValue INTEGER PRIMARY KEY NOT NULL,            
            ID6 INTEGER,
            ID7 INTEGER,
            ID8 INTEGER,
            ID9 INTEGER,
            ID10 INTEGER);'''%(ALLTAILTABLE)
    # TailsValuesLstStr list of TailValue
    sql_text_5 = '''CREATE TABLE %s
           (TailSValue TEXT PRIMARY KEY NOT NULL,            
            TailsNum INTEGER,
            TailsValuesLstStr TEXT);'''%(TAILSTABLE)
    
    
    
    # check scheduler for automatic checking prefix pattners,
    #   to use: 1. we just set the plan by scripts (some functions) to record the  items in this tables
    #           2. run the routines to check the items with  VerifiedResult==0, and change VerifiedResult with results.
    #           3. if some VerifiedResult!=0 and VerifiedResult!=1, we need do more checking on the prefix of BreakPrefixValue. 
    #               the checking maybe by hand, or by simulations to get all tails of this prefix.
    #               and the result will lead to new schedul items inserted in the table.
    #           4. if all item are finished and VerifiedResult==1, those items can be set to BorderDB
    #           5. check if all prefix beed set already? if not with new unset prefixes and make new scheduls, then goto 1 to process
    #           6. otherwise, done, and build the searctree base one BorderDB 
    #               6.1 generate prefix-tails table
    #               6.2 for each tails, generate a seachtree 
    # check prefix in StartPrefixValue--EndPrefixValue with PrefixPattner
    # CKType: tails all same, mid check, 3point check; loop pattern with TailsList1 and TailsList2, 
    # CKParam : check tail pattner with some parameter, depth
    # VerifiedResult: Check result, 0: not checked yet, 1: check ok, 2: check fails some point, 
    # if check fail ,BreakPrefixValue record the failed prefix, next round we should check this prefix by hand
    # if VerifiedResult==1, BreakPrefixValue=0 mean just checked, but not fill the BorderDB, 
    #                      if BreakPrefixValue>0, the related prefix have bedd filled in BorderDB.

    sql_text_6 = '''CREATE TABLE %s
           (StartPrefixValue TEXT PRIMARY KEY NOT NULL,            
            EndPrefixValue INTEGER,
            PrefixPattner TEXT,
            TailsList1 TEXT,
            TailsList2 TEXT,
            CKType INTEGER,
            CKParam0 INTEGER,
            CKParam1 INTEGER,
            VerifiedResult INTEGER,
            BreakPrefixValue INTEGER
            );'''%(WORKSCHEDUL)    
    # 执行sql语句
    DBcusr.execute(sql_text_0)
    DBcusr.execute(sql_text_1)
    DBcusr.execute(sql_text_2)
    DBcusr.execute(sql_text_3)
    DBcusr.execute(sql_text_4)
    DBcusr.execute(sql_text_5)
    DBcusr.execute(sql_text_6)

    commitChanges()
    CloseDatabase()

#check before add
def addLinksToBDDB(linkStruObj,TValue,gotType=GOTTYPE_SIMULATION,todoType=TODOACT_NONE):
    
    table=BORDERPOINTS
    sqlcheck0=f'''SELECT * FROM {table} WHERE HashKey='{linkStruObj.HashValue}' '''
    result=DBcusr.execute(sqlcheck0)
    exisItm=result.fetchone()
    if exisItm!=None:
        #exsit already
        return
    
    ###insert new
    sqltext=f'''INSERT INTO {table} (HashKey,ID1,ID2,ID3,ID4,ID5,ID6,ID7,ID8,ID9,ID10,TValue,GOTTYPE,TODOACT,PrefixDB) VALUES ('{linkStruObj.HashValue}',{linkStruObj.IDs[0]},{linkStruObj.IDs[1]},{linkStruObj.IDs[2]},{linkStruObj.IDs[3]},{linkStruObj.IDs[4]},{linkStruObj.IDs[5]},{linkStruObj.IDs[6]},{linkStruObj.IDs[7]},{linkStruObj.IDs[8]},{linkStruObj.IDs[9]},{TValue},{gotType},{todoType},0)'''
    print(sqltext)
    result=DBcusr.execute(sqltext)


    destable=LINKDESTABLE
    sqlcheck=f'''SELECT * FROM {destable}'''
    results=DBcusr.execute(sqlcheck)
    alltuples=results.fetchall()
    num=0
    for trupl in alltuples:
        if trupl[IDX_ADDIDX]>num:
            num=trupl[IDX_ADDIDX]    
    num+=1
    prefix=[linkStruObj.IDs[0],linkStruObj.IDs[1],linkStruObj.IDs[2],linkStruObj.IDs[3],linkStruObj.IDs[4]]
    prefixValue=prefixMetric(prefix)
    sqltext1=f'''INSERT INTO {destable} (HashKey,AddIdx,PrefixValue,NewAdded,LinksDicStr) VALUES ('{linkStruObj.HashValue}',{num},{prefixValue},0,"{linkStruObj.outPutToLinksDicStr()}")'''
    print(sqltext1)
    result=DBcusr.execute(sqltext1)




#prefix is the id1-id5 of a links
#return -1: A<B, 0: A=B, 1:A>B
def prefixCompare(Aid1,Aid2,Aid3,Aid4,Aid5,Bid1,Bid2,Bid3,Bid4,Bid5):
    Avlu=Aid1+2*Aid2+4*Aid3+8*Aid4+16*Aid5
    Bvlu=Bid1+2*Bid2+4*Bid3+8*Bid4+16*Bid5
    res=Avlu-Bvlu
    if res>1:
        return 1
    elif res<0:
        return -1
    else: 
        return 0
#the input prefix not exist in DB 
# Then find the upper and lower prefix that closest to this prefix  
# The max and min of ID already been set in DB, and this function is call by searching algorithm, 
#   the input ids is in between min and max  
# id4,id5 should be already exploerd, all possible combination is in DB
def findUpperAndLowerPrefixInDB(id1,id2,id3,id4,id5):
    InDBID3Array=[]
    InDBID2Array=[]
    InDBID1Array=[]
    upperarray=[]
    lowerarray=[]
    sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID3={id3} AND ID4={id4} AND ID5={id5}'''
    result=DBcusr.execute(sqltext)
    if result:
        Thetuples=result.fetchall()
        for eachtupl in Thetuples:
            if eachtupl[IDX_ID3] not in InDBID3Array:
                InDBID3Array.append(eachtupl[IDX_ID3]) 
            if eachtupl[IDX_ID2] not in InDBID2Array:
                InDBID2Array.append(eachtupl[IDX_ID2])
            if eachtupl[IDX_ID1] not in InDBID1Array:
                InDBID1Array.append(eachtupl[IDX_ID1])

        if id2 in InDBID2Array:
            #id1 is impossible in InDBID1Array
            lowerID1=InDBID1Array[0]#min
            upperID1=InDBID1Array[-1]#max
            for newid1 in InDBID1Array:
                if newid1<id1:
                    if newid1>lowerID1:
                        lowerID1=newid1
                else:
                    if newid1<upperID1:
                        upperID1=newid1
            upperarray=[upperID1,id2,id3,id4,id5]
            lowerarray=[lowerID1,id2,id3,id4,id5]
        else:
            lowerID2=InDBID2Array[0]#min
            upperID2=InDBID2Array[-1]#max
            for newid2 in InDBID2Array:
                if newid2<id2:
                    if newid2>lowerID2:
                        lowerID2=newid2
                else:
                    if newid2<upperID2:
                        upperID2=newid2
            sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID2={upperID2} AND ID3={id3} AND ID4={id4} AND ID5={id5}'''
            result=DBcusr.execute(sqltext)
            if result:
                Thetuples=result.fetchall()
                for eachtupl in Thetuples:
                    if eachtupl[IDX_ID3] not in InDBID3Array:
                        InDBID3Array.append(eachtupl[IDX_ID3]) 
                    if eachtupl[IDX_ID2] not in InDBID2Array:
                        InDBID2Array.append(eachtupl[IDX_ID2])
                    if eachtupl[IDX_ID1] not in InDBID1Array:
                        InDBID1Array.append(eachtupl[IDX_ID1])
            upperID1=InDBID1Array[0]#min
            sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID2={lowerID2} AND ID3={id3} AND ID4={id4} AND ID5={id5}'''
            result=DBcusr.execute(sqltext)
            if result:
                Thetuples=result.fetchall()
                for eachtupl in Thetuples:
                    if eachtupl[IDX_ID3] not in InDBID3Array:
                        InDBID3Array.append(eachtupl[IDX_ID3]) 
                    if eachtupl[IDX_ID2] not in InDBID2Array:
                        InDBID2Array.append(eachtupl[IDX_ID2])
                    if eachtupl[IDX_ID1] not in InDBID1Array:
                        InDBID1Array.append(eachtupl[IDX_ID1])
            lowerID1=InDBID1Array[-1]#max
            upperarray=[upperID1,upperID2,id3,id4,id5]
            lowerarray=[lowerID1,lowerID2,id3,id4,id5]
    else:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID4={id4} AND ID5={id5}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID3] not in InDBID3Array:
                    InDBID3Array.append(eachtupl[IDX_ID3]) 
                if eachtupl[IDX_ID2] not in InDBID2Array:
                    InDBID2Array.append(eachtupl[IDX_ID2])
                if eachtupl[IDX_ID1] not in InDBID1Array:
                    InDBID1Array.append(eachtupl[IDX_ID1])
        lowerID3=InDBID3Array[0]#min
        upperID3=InDBID3Array[-1]#max
        for newid3 in InDBID3Array:
            if newid3<id3:
                if newid3>lowerID3:
                    lowerID3=newid3
            else:
                if newid3<upperID3:
                    upperID3=newid3
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID3={upperID3} AND ID4={id4} AND ID5={id5}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID3] not in InDBID3Array:
                    InDBID3Array.append(eachtupl[IDX_ID3]) 
                if eachtupl[IDX_ID2] not in InDBID2Array:
                    InDBID2Array.append(eachtupl[IDX_ID2])
                if eachtupl[IDX_ID1] not in InDBID1Array:
                    InDBID1Array.append(eachtupl[IDX_ID1])
        upperID2=InDBID2Array[0]#min
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID2={upperID2} AND ID3={upperID3} AND ID4={id4} AND ID5={id5}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID3] not in InDBID3Array:
                    InDBID3Array.append(eachtupl[IDX_ID3]) 
                if eachtupl[IDX_ID2] not in InDBID2Array:
                    InDBID2Array.append(eachtupl[IDX_ID2])
                if eachtupl[IDX_ID1] not in InDBID1Array:
                    InDBID1Array.append(eachtupl[IDX_ID1])
        upperID1=InDBID1Array[0]#min
        upperarray=[upperID1,upperID2,upperID3,id4,id5]

        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID3={lowerID3} AND ID4={id4} AND ID5={id5}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID3] not in InDBID3Array:
                    InDBID3Array.append(eachtupl[IDX_ID3]) 
                if eachtupl[IDX_ID2] not in InDBID2Array:
                    InDBID2Array.append(eachtupl[IDX_ID2])
                if eachtupl[IDX_ID1] not in InDBID1Array:
                    InDBID1Array.append(eachtupl[IDX_ID1])
        lowerID2=InDBID2Array[-1]#max
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID2={lowerID2} AND ID3={lowerID3} AND ID4={id4} AND ID5={id5}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID3] not in InDBID3Array:
                    InDBID3Array.append(eachtupl[IDX_ID3]) 
                if eachtupl[IDX_ID2] not in InDBID2Array:
                    InDBID2Array.append(eachtupl[IDX_ID2])
                if eachtupl[IDX_ID1] not in InDBID1Array:
                    InDBID1Array.append(eachtupl[IDX_ID1])
        lowerID1=InDBID1Array[-1]#max
        lowerarray=[lowerID1,lowerID2,lowerID3,id4,id5]

    return upperarray,lowerarray

#the prefix array is ID1-ID5
#the return tails are lists of ID6-ID10
def getTailsofPrefix(prefixarray):
    sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID1={prefixarray[0]} AND ID2={prefixarray[1]} AND ID3={prefixarray[2]} AND ID4={prefixarray[3]} AND ID5={prefixarray[4]}'''
    result=DBcusr.execute(sqltext)
    rettails=[]
    if result:
        Thetuples=result.fetchall()
        for eachtupl in Thetuples:
            tail=[eachtupl[IDX_ID6],eachtupl[IDX_ID7],eachtupl[IDX_ID8],eachtupl[IDX_ID9],eachtupl[IDX_ID10]]
            rettails.append(tail)
    return rettails

#prefixIDsarray is the asending  IDs or ID1 to IDx, x depend on the array len, [] is possbile
#return the next hop x IDs set, return is as an array, that are all possible next hop(x) ID values
# this function can be used in a complete DB to generate the search tree.
def getBDPointsNextHopIDs(prefixIDsarray):
    x=len(prefixIDsarray)
    retArray=[]

    if x==0:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID1] not in retArray:
                    retArray.append(eachtupl[IDX_ID1])  
            retArray.sort()
    elif x==1:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID1={prefixIDsarray[0]}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID2] not in retArray:
                    retArray.append(eachtupl[IDX_ID2])  
            retArray.sort()
    elif x==2:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID1={prefixIDsarray[0]} AND ID2={prefixIDsarray[1]}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID3] not in retArray:
                    retArray.append(eachtupl[IDX_ID3])  
            retArray.sort()
    elif x==3:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID1={prefixIDsarray[0]} AND ID2={prefixIDsarray[1]} AND ID3={prefixIDsarray[2]}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID4] not in retArray:
                    retArray.append(eachtupl[IDX_ID4])  
            retArray.sort()
    elif x==4:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID1={prefixIDsarray[0]} AND ID2={prefixIDsarray[1]} AND ID3={prefixIDsarray[2]} AND ID4={prefixIDsarray[3]}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID5] not in retArray:
                    retArray.append(eachtupl[IDX_ID5])  
            retArray.sort()
    elif x==5:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID1={prefixIDsarray[0]} AND ID2={prefixIDsarray[1]} AND ID3={prefixIDsarray[2]} AND ID4={prefixIDsarray[3]} AND ID5={prefixIDsarray[4]}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID6] not in retArray:
                    retArray.append(eachtupl[IDX_ID6])  
            retArray.sort()
    elif x==6:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID1={prefixIDsarray[0]} AND ID2={prefixIDsarray[1]} AND ID3={prefixIDsarray[2]} AND ID4={prefixIDsarray[3]} AND ID5={prefixIDsarray[4]} AND ID6={prefixIDsarray[5]}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID7] not in retArray:
                    retArray.append(eachtupl[IDX_ID7])  
            retArray.sort()
    elif x==7:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID1={prefixIDsarray[0]} AND ID2={prefixIDsarray[1]} AND ID3={prefixIDsarray[2]} AND ID4={prefixIDsarray[3]} AND ID5={prefixIDsarray[4]} AND ID6={prefixIDsarray[5]}  AND ID7={prefixIDsarray[6]}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID8] not in retArray:
                    retArray.append(eachtupl[IDX_ID8])  
            retArray.sort()
    elif x==8:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID1={prefixIDsarray[0]} AND ID2={prefixIDsarray[1]} AND ID3={prefixIDsarray[2]} AND ID4={prefixIDsarray[3]} AND ID5={prefixIDsarray[4]} AND ID6={prefixIDsarray[5]}  AND ID7={prefixIDsarray[6]} AND ID8={prefixIDsarray[7]}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID9] not in retArray:
                    retArray.append(eachtupl[IDX_ID9])  
            retArray.sort()
    elif x==9:
        sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0 AND ID1={prefixIDsarray[0]} AND ID2={prefixIDsarray[1]} AND ID3={prefixIDsarray[2]} AND ID4={prefixIDsarray[3]} AND ID5={prefixIDsarray[4]} AND ID6={prefixIDsarray[5]}  AND ID7={prefixIDsarray[6]} AND ID8={prefixIDsarray[7]} AND ID9={prefixIDsarray[8]}'''
        result=DBcusr.execute(sqltext)
        if result:
            Thetuples=result.fetchall()
            for eachtupl in Thetuples:
                if eachtupl[IDX_ID10] not in retArray:
                    retArray.append(eachtupl[IDX_ID10])  
            retArray.sort()

    return retArray

#return dic:hoppos:linkid arrays
def getAllValidIDTuplesInDB():
    sqltext=f'''SELECT * FROM {BORDERPOINTS} WHERE TODOACT=0'''
    result=DBcusr.execute(sqltext)
    DicArray=[]
    if result:
        Thetuples=result.fetchall()        
        for eachtupl in Thetuples:
            theDic={}#hop:linkid
            theDic[1]=eachtupl[IDX_ID1]
            theDic[2]=eachtupl[IDX_ID2]
            theDic[3]=eachtupl[IDX_ID3]
            theDic[4]=eachtupl[IDX_ID4]
            theDic[5]=eachtupl[IDX_ID5]
            theDic[6]=eachtupl[IDX_ID6]
            theDic[7]=eachtupl[IDX_ID7]
            theDic[8]=eachtupl[IDX_ID8]
            theDic[9]=eachtupl[IDX_ID9]
            theDic[10]=eachtupl[IDX_ID10]
            DicArray.append(theDic)
    return DicArray



####################
#create new API for perfix based search
###################
PREFIXDIMNUM=16

def prefixMetric(prefixAray):

    idx1=pthG.ValuOrderList.index(prefixAray[0])
    idx2=pthG.ValuOrderList.index(prefixAray[1])
    idx3=pthG.ValuOrderList.index(prefixAray[2])
    idx4=pthG.ValuOrderList.index(prefixAray[3])
    idx5=pthG.ValuOrderList.index(prefixAray[4])

    prefixValue=idx1+idx2*PREFIXDIMNUM+idx3*PREFIXDIMNUM*PREFIXDIMNUM+idx4*PREFIXDIMNUM*PREFIXDIMNUM*PREFIXDIMNUM+idx5*PREFIXDIMNUM*PREFIXDIMNUM*PREFIXDIMNUM*PREFIXDIMNUM

    #print("prefixValue:%d for %s idx<%d,%d,%d,%d,%d>"%(prefixValue,prefixAray,idx1,idx2,idx3,idx4,idx5))

    return prefixValue

def tailMetric(tailArray):
    idx1=pthG.ValuOrderList.index(tailArray[4])
    idx2=pthG.ValuOrderList.index(tailArray[3])
    idx3=pthG.ValuOrderList.index(tailArray[2])
    idx4=pthG.ValuOrderList.index(tailArray[1])
    idx5=pthG.ValuOrderList.index(tailArray[0])

    tailValue=idx1+idx2*PREFIXDIMNUM+idx3*PREFIXDIMNUM*PREFIXDIMNUM+idx4*PREFIXDIMNUM*PREFIXDIMNUM*PREFIXDIMNUM+idx5*PREFIXDIMNUM*PREFIXDIMNUM*PREFIXDIMNUM*PREFIXDIMNUM

    return tailValue

#list of tails
def tailsMetric(arrayofTailValue):
    rtvalue=0
    multiplier=1
    for value in arrayofTailValue:
        rtvalue+=(value*multiplier)
        multiplier*=PREFIXDIMNUM
        #multiplier+=1
    return rtvalue


def tailsHashValue(tailsList):
    
    arrayValues=[]
    for tail in tailsList:
        tvalu=tailMetric(tail)
        arrayValues.append(tvalu)

    arrayValues.sort()

    rtvalue=tailsMetric(arrayValues)
   
    return rtvalue

#[0.011, 0.015, 0.02] is the lastlk in our current work
def genAllPrefix(lastLk):
    allprefix=[]
    biggestValue=pthG.linkIDValue(lastLk)
    lstidx=pthG.ValuOrderList.index(biggestValue)+1
    for idx1 in range(lstidx):
        for idx2 in range(lstidx):
            if idx2<idx1:
                continue
            for idx3 in range(lstidx):
                if idx3<idx2:
                    continue
                for idx4 in range(lstidx):
                    if idx4<idx3:
                        continue
                    for idx5 in range(lstidx):
                        if idx5<idx4:
                            continue
                        lk5Value=pthG.ValuOrderList[idx5]
                        lk4Value=pthG.ValuOrderList[idx4]
                        lk3Value=pthG.ValuOrderList[idx3]
                        lk2Value=pthG.ValuOrderList[idx2]
                        lk1Value=pthG.ValuOrderList[idx1]

                        prefix=[lk1Value,lk2Value,lk3Value,lk4Value,lk5Value]
                        allprefix.append(prefix)
    return allprefix


def addPrefixToDB(prefixArray,orderNum):
    prevValue=prefixMetric(prefixArray)
    sqltext1=f'''INSERT INTO {ALLPREFIX} (PrefixValue,ID1,ID2,ID3,ID4,ID5,OrderNum,CheckType) VALUES ({prevValue},{prefixArray[0]},{prefixArray[1]},{prefixArray[2]},{prefixArray[3]},{prefixArray[4]},{orderNum},0)'''
    result=DBcusr.execute(sqltext1)


def updatePrefixState(prefix,State=PREFIX_STATE_SIMU_TAILS):
    prevValue=prefixMetric(prefix)
    sqltext=f'''UPDATE {ALLPREFIX} SET CheckType={State} WHERE PrefixValue={prevValue} '''
    result=DBcusr.execute(sqltext)

def getPrefixCkStateByPrefixValue(prefixValue):
    sqltext2=f'''SELECT * FROM {ALLPREFIX} WHERE PrefixValue={prefixValue}'''
    result=DBcusr.execute(sqltext2)
    tuple2=result.fetchone()
    cktype=tuple2[IDX_CKTYPE]
    return cktype

def getPrefixCkStateByPrefix(prefix):
    prevValue=prefixMetric(prefix)    
    cktype=getPrefixCkStateByPrefixValue(prevValue)
    return cktype

def getNullPrefixArray():

    sqltext=f'''SELECT * FROM {ALLPREFIX} WHERE CheckType=0 AND (PrefixValue>=0 AND PrefixValue<=978670)'''

    result=DBcusr.execute(sqltext)
    alltuples=result.fetchall()
    prefixArray=[]
    for ttuple in alltuples:
        prefix=[ttuple[IDX_ID1],ttuple[IDX_ID2],ttuple[IDX_ID3],ttuple[IDX_ID4],ttuple[IDX_ID5]]
        prefixArray.append(prefix)
    
    return prefixArray

def checkprefixNullTails():
    NullTailList=[]
    sqltext=f'''SELECT * FROM {ALLPREFIX}'''
    result=DBcusr.execute(sqltext)
    alltuples=result.fetchall()
    for ttuple in alltuples:
        sqltext1=f'''SELECT * FROM {PREFIXTAILS} WHERE PrefixValue={ttuple[IDX_PREFIXVALUE]}'''
        result1=DBcusr.execute(sqltext1)
        tuple1=result1.fetchone()
        if tuple1==None:
            prefix=[ttuple[IDX_ID1],ttuple[IDX_ID2],ttuple[IDX_ID3],ttuple[IDX_ID4],ttuple[IDX_ID5]]
            NullTailList.append(prefix)
            print("add prefix:%s"%prefix)
    return NullTailList

def checkRedundantPrefix():
    RedundantList=[]
    sqltext=f'''SELECT * FROM {PREFIXTAILS}'''
    result=DBcusr.execute(sqltext)
    alltuples=result.fetchall()
    for ttuple in alltuples:
        sqltext1=f'''SELECT * FROM {ALLPREFIX} WHERE PrefixValue={ttuple[IDX_PREFIXVALUE]}'''
        result1=DBcusr.execute(sqltext1)
        tuple1=result1.fetchone()
        if tuple1==None:
            prefix=[ttuple[IDX_ID1],ttuple[IDX_ID2],ttuple[IDX_ID3],ttuple[IDX_ID4],ttuple[IDX_ID5]]
            RedundantList.append(prefix)
            print("Redundant prefix:%s"%prefix)
    return RedundantList

def getPrefixArrayByRange(FullPattner,BeginPrefixValue,EndPrefixValue):

    sqltext=f'''SELECT * FROM {ALLPREFIX} WHERE CheckType=0 AND (PrefixValue>={BeginPrefixValue} AND PrefixValue<={EndPrefixValue}) AND ({FullPattner[1]}=0 OR (ID1>={FullPattner[0]} AND ID1<={FullPattner[1]})) AND ({FullPattner[3]}=0 OR (ID2>={FullPattner[2]} AND ID2<={FullPattner[3]})) AND ({FullPattner[5]}=0 OR (ID3>={FullPattner[4]} AND ID3<={FullPattner[5]})) AND ({FullPattner[7]}=0 OR (ID4>={FullPattner[6]} AND ID4<={FullPattner[7]})) AND ({FullPattner[9]}=0 OR (ID5>={FullPattner[8]} AND ID5<={FullPattner[9]}))'''

    result=DBcusr.execute(sqltext)
    alltuples=result.fetchall()
    prefixArray=[]
    for ttuple in alltuples:
        prefix=[ttuple[IDX_ID1],ttuple[IDX_ID2],ttuple[IDX_ID3],ttuple[IDX_ID4],ttuple[IDX_ID5]]
        prefixArray.append(prefix)
    
    return prefixArray

def getMidPrefix(BeginPrefix,EndPrefix):

    #BeginPrefixValue=prefixMetric(BeginPrefix)
    #EndPrefixValue=prefixMetric(EndPrefix)

    #sqltext=f'''SELECT * FROM {ALLPREFIX} WHERE CheckType=0 AND (PrefixValue>{BeginPrefixValue} AND PrefixValue<{EndPrefixValue})'''

    sqltext=f'''SELECT * FROM {ALLPREFIX} WHERE CheckType=0 AND (ID1>={BeginPrefix[0]} AND ID1<={EndPrefix[0]}) AND (ID2>={BeginPrefix[1]} AND ID2<={EndPrefix[1]}) AND (ID3>={BeginPrefix[2]} AND ID3<={EndPrefix[2]}) AND (ID4>={BeginPrefix[3]} AND ID4<={EndPrefix[3]}) AND (ID5>={BeginPrefix[4]} AND ID5<={EndPrefix[4]})'''

    result=DBcusr.execute(sqltext)
    alltuples=result.fetchall()
    prefixArray=[]
    for ttuple in alltuples:
        prefix=[ttuple[IDX_ID1],ttuple[IDX_ID2],ttuple[IDX_ID3],ttuple[IDX_ID4],ttuple[IDX_ID5]]
        prefixArray.append(prefix)

    mididx=math.floor(len(prefixArray)/2)

    return prefixArray[mididx]


#if exist do notion
#if not exist, added
def addTailtoDB(tail):
    tvalu=tailMetric(tail)
    sqltext=f'''SELECT * FROM {ALLTAILTABLE} WHERE TailValue={tvalu}'''
    result=DBcusr.execute(sqltext)
    tuple0=result.fetchone()
    if tuple0==None:
        sqltext1=f'''INSERT INTO {ALLTAILTABLE} (TailValue,ID6,ID7,ID8,ID9,ID10) VALUES ({tvalu},{tail[0]},{tail[1]},{tail[2]},{tail[3]},{tail[4]})'''
        result=DBcusr.execute(sqltext1)
    pass

#if exist do nothing
def addTailsToDB(tailsList):
    arrayValues=[]
    for tail in tailsList:
        addTailtoDB(tail)
        tvalu=tailMetric(tail)
        arrayValues.append(tvalu)
    arrayValues.sort()

    TailsValue=str(tailsMetric(arrayValues))
    sqltext=f'''SELECT * FROM {TAILSTABLE} WHERE TailSValue='{TailsValue}' '''
    result=DBcusr.execute(sqltext)
    tuple0=result.fetchone()
    if tuple0==None:
        sqltext1=f'''INSERT INTO {TAILSTABLE} (TailSValue,TailsNum,TailsValuesLstStr) VALUES ('{TailsValue}',{len(arrayValues)},"{str(arrayValues)}")'''
        print(sqltext1)
        result=DBcusr.execute(sqltext1)

    return TailsValue
def getTailsVByPrefix(prefix):
    prefixValue=prefixMetric(prefix)
    sqltext=f'''SELECT * FROM {PREFIXTAILS} WHERE PrefixValue={prefixValue}'''
    result=DBcusr.execute(sqltext)
    tuple0=result.fetchone()
    if tuple0:
        tailsV=int(tuple0[IDX_PREFIX_TAILSV])
        return tailsV
    else:
        return -1
def getTailsDicInDB():
    sqltext=f'''SELECT * FROM {TAILSTABLE}'''
    result=DBcusr.execute(sqltext)
    alltuples=result.fetchall()
    tailsDic={}
    for ttuple in alltuples:
        tailsV=int(ttuple[IDX_TAILSV])
        if tailsV>0:
            tailsobj=eval(ttuple[IDX_TAILSLSTSTR])
            tails=[]
            for tailid in tailsobj:
                sqltext1=f'''SELECT * FROM {ALLTAILTABLE} WHERE TailValue={tailid}'''
                result1=DBcusr.execute(sqltext1)
                tuple1=result1.fetchone()                
                tailobj=[tuple1[IDX_TID6],tuple1[IDX_TID7],tuple1[IDX_TID8],tuple1[IDX_TID9],tuple1[IDX_TID10]]
                tails.append(tailobj)
            tailsDic[tailsV]=tails

        else:
            tailsDic[tailsV]=[]
    return tailsDic
# set prefix and tails relations in DB
# tails already been stored in DB, prefix already in DB
def setfixRLOfPrefixWithTails(prefix,tails):
    prefixValue=prefixMetric(prefix)
    NumTails=len(tails)
    arrayValues=[]
    for tail in tails:
        addTailtoDB(tail)
        tvalu=tailMetric(tail)
        arrayValues.append(tvalu)
    arrayValues.sort()

    TailsValue=str(tailsMetric(arrayValues))

    sqltext=f'''SELECT * FROM {PREFIXTAILS} WHERE PrefixValue={prefixValue}'''
    result=DBcusr.execute(sqltext)
    tuple0=result.fetchone()
    if tuple0==None:
        sqltext1=f'''INSERT INTO {PREFIXTAILS} (PrefixValue,ID1,ID2,ID3,ID4,ID5,TailsValue,TailsNum) VALUES ({prefixValue},{prefix[0]},{prefix[1]},{prefix[2]},{prefix[3]},{prefix[4]},'{TailsValue}',{NumTails})'''
        result=DBcusr.execute(sqltext1)


def setPrefixWithTailsByRange(prefixValueBegin,prefixValueEnd,prefixPattners,tailsValueint):
    prefixArray=getPrefixArrayByRange(prefixPattners,prefixValueBegin,prefixValueEnd)
    tailsValue=str(tailsValueint)
    for prefix in prefixArray:
        prefixValue=prefixMetric(prefix)
        sqltext=f'''SELECT * FROM {PREFIXTAILS} WHERE PrefixValue={prefixValue}'''
        result=DBcusr.execute(sqltext)
        tuple0=result.fetchone()
        if tuple0==None:
            sqltext0=f'''SELECT * FROM {TAILSTABLE} WHERE TailSValue='{tailsValue}' '''
            result=DBcusr.execute(sqltext0)
            tuple1=result.fetchone()
            if tuple1:
                NumTails=tuple1[IDX_TAILSNUM]
                sqltext1=f'''INSERT INTO {PREFIXTAILS} (PrefixValue,ID1,ID2,ID3,ID4,ID5,TailsValue,TailsNum) VALUES ({prefixValue},{prefix[0]},{prefix[1]},{prefix[2]},{prefix[3]},{prefix[4]},'{tailsValue}' ,{NumTails})'''
                #print(sqltext1)
                result=DBcusr.execute(sqltext1)
            else:
                print("@prefix %d Warring:tailsvalue %s not set!!!"%(prefixValue,tailsValue))
        cktype=getPrefixCkStateByPrefixValue(prefixValue)
        if cktype==0:
            print("@prefix %d set!!!"%(prefixValue))
            updatePrefixState(prefix,PREFIX_STATE_DEDUC_TAILS)
        else:
            print("@prefix %d already set!!"%(prefixValue))

#####workpals related #####
###the start point must be a prefix already been checked
# WORKSCHEDUL table
def addWorkPlanItem(startprefixValue,endPrefixFalue,prefixPattner,tails1,tails2,CkType,CKparam0,CKparam1):
    sqltext1=f'''INSERT INTO {WORKSCHEDUL} (StartPrefixValue,EndPrefixValue,PrefixPattner,TailsList1,TailsList2,CKType,CKParam0,CKParam1,VerifiedResult,BreakPrefixValue) VALUES ({startprefixValue},{endPrefixFalue},"{str(prefixPattner)}","{str(tails1)}","{str(tails2)}",{CkType},{CKparam0},{CKparam1},0,0)'''
    result=DBcusr.execute(sqltext1)
    pass

WORK_VERRES_NONE=0
WORK_VERRES_OK=1
WORK_VERRES_LOWER=2
WORK_VERRES_UPPER=3
WORK_VERRES_MIX=4

def UpdateWorkPlanItem(startprefixValue,result,BreakPrefixValue):
    sqltext=f'''UPDATE {WORKSCHEDUL} SET VerifiedResult={result},BreakPrefixValue={BreakPrefixValue}  WHERE StartPrefixValue={startprefixValue} '''
    result=DBcusr.execute(sqltext)

IDX_WORK_STARTPREV=0
IDX_WORK_ENDPREV=1
IDX_WORK_PREFIXPATTNER=2
IDX_WORK_TAILS1=3
IDX_WORK_TAILS2=4
IDX_WORK_CKTYPE=5
IDX_WORK_CKPARAM0=6
IDX_WORK_CKPARAM1=7

WORK_LOCKFLAG=10
#return the parameters object list 
# the frist and lock VerifiedResult=10 is lock for checking
def getFirstUntouchedWorkItems():
    sqltext=f'''SELECT * FROM {WORKSCHEDUL} WHERE VerifiedResult=0 AND BreakPrefixValue=0 '''
    result=DBcusr.execute(sqltext)
    item=result.fetchone()
    #worklist=[]
    if item:
        Svalue=item[IDX_WORK_STARTPREV]
        Evalue=item[IDX_WORK_ENDPREV]
        prefixPattern=eval(item[IDX_WORK_PREFIXPATTNER])
        tail1=eval(item[IDX_WORK_TAILS1])
        tail2=eval(item[IDX_WORK_TAILS2])
        CKtype=item[IDX_WORK_CKTYPE]
        CKParm0=item[IDX_WORK_CKPARAM0]
        CKParm1=item[IDX_WORK_CKPARAM1]
        thetuple=(Svalue,Evalue,prefixPattern,tail1,tail2,CKtype,CKParm0,CKParm1)
        #worklist.append(thetuple)
        UpdateWorkPlanItem(Svalue,WORK_LOCKFLAG,WORK_LOCKFLAG)
        return thetuple
    return None

################################
def getTailSValueFrequencyInAllTailTable():
    """
    统计每个 TailSValue 在 PrefixTails 表中的出现频率。
    返回一个字典，键是 TailSValue , 结果按 TailsNum 和 TailSValue 排序。
    """
    sqltext = f'''SELECT * FROM {PREFIXTAILS}  Ascending ORDER BY TailsNum, TailsValue'''
    result = DBcusr.execute(sqltext)
    alltuples = result.fetchall()
    frequency_dic = {}
    
    for ttuple in alltuples:
        tails_v = ttuple[IDX_PREFIX_TAILSV]
        tails_num = ttuple[IDX_PREFIX_TAILSNUM]
        #tails_values_str = ttuple[IDX_TAILSLSTSTR]
        #tails_values = eval(tails_values_str) if tails_values_str else []
        
        # 统计每个 TailValue 在 AllTailTable 中的出现次数
        if tails_v in frequency_dic:
            frequency_dic[tails_v]['count'] += 1
        else:
            frequency_dic[tails_v] = {'count': 0, 'tails_num': tails_num}
    
    # 按 TailsNum 和 TailSValue 排序
    sorted_freq = dict(sorted(frequency_dic.items(), key=lambda x: (x[1]['tails_num'], x[0])))
    return sorted_freq
################################

def generateBoundaryPointBitmap():
    """
    生成边界点的位图字典，键为 (prefixValue, TailValue)，值为 1。
    通过 PrefixTails 表找到每个 prefixValue 对应的 TailsValue，
    再通过 TailsTable 表的 TailsValuesLstStr 获取 TailValue 数组。
    """
    bitmap_dic = {}
    
    # 从 PrefixTails 表获取数据
    sqltext = f'''SELECT * FROM {PREFIXTAILS}'''
    result = DBcusr.execute(sqltext)
    all_prefix_tuples = result.fetchall()
    
    for prefix_tuple in all_prefix_tuples:
        prefix_value = prefix_tuple[IDX_PREFIXVALUE]
        tails_value = prefix_tuple[IDX_PREFIX_TAILSV]
        
        # 通过 TailsValue 查询 TailsTable 表获取 TailValue 数组
        sqltext1 = f'''SELECT * FROM {TAILSTABLE} WHERE TailSValue='{tails_value}' '''
        result1 = DBcusr.execute(sqltext1)
        tails_tuple = result1.fetchone()
        
        if tails_tuple:
            tails_values_str = tails_tuple[IDX_TAILSLSTSTR]
            tails_values = eval(tails_values_str) if tails_values_str else []
            
            # 将每个 TailValue 与 prefixValue 组合作为键
            for tail_value in tails_values:
                bitmap_dic[(prefix_value, tail_value)] = 1
    
    return bitmap_dic



####################################



##################

def InitPrefixTables():

    allprefix=genAllPrefix([0.011, 0.015, 0.02])
    
    pvlist=[]
    for prefix in allprefix:
        pv=prefixMetric(prefix)
        pvlist.append(pv)

    pvlist.sort()
    for prefix in allprefix:
        pv=prefixMetric(prefix)
        idx=pvlist.index(pv)
        addPrefixToDB(prefix,idx+1)
        

def CreateAndInitialBPDataBase():
    createDBs()
    pthG.loadValuToLinkMapDic()
    OpenDatabase()
    InitPrefixTables()
    commitChanges()
    CloseDatabase()

def printprefix():    
    prefixarray=[104, 120, 120, 208, 364]
    prefiValue=prefixMetric(prefixarray)
    print("prefix:%s prefixValue:%d"%(prefixarray,prefiValue))

def moduletest():
    pthG.loadValuToLinkMapDic()
    printprefix()
    pass

if __name__=='__main__':moduletest()
