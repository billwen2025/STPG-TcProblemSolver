#!/usr/bin/python3
import sqlite3
import sortlinklist as sorLL

TheDataBaseFile="/home/bill/Documents/VScode/newplan/researchplan/STPGPlusTraffic/src/ResultDataHis/resultDataBaseSqlite.db"
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

LINKDESTABLE='LinksDes'
HOPS2PRE3MAIN='testResluts2Hops3'
WORKSCHEDUL='WORKLOADPLAN'




def createDBTestResults():
    # 建表的sql语句
    sql_text_1 = '''CREATE TABLE %s
           (HashKey TEXT PRIMARY KEY NOT NULL,
            KeyCmpHops INTEGER,
            PathNum INTEGER,
            Hop2Num INTEGER,
            Hop3Num INTEGER,
            TValue REAL,
            Mean REAL,
            Slope REAL,
            IsBorder INTEGER,
            UpperFineTune INTEGER);'''%(HOPS2PRE3MAIN)
    
    sql_text_2 = '''CREATE TABLE %s
           (HashKey TEXT PRIMARY KEY NOT NULL,
            LinksDicStr TEXT,
            TestedDims TEXT);'''%(LINKDESTABLE)
    # 执行sql语句
    DBcusr.execute(sql_text_1)
    DBcusr.execute(sql_text_2)

#return tuple for item in table
#if not exist, return None
def CheckValuesByLinkStruc(linkStruc,table=HOPS2PRE3MAIN):
    sqltext=f"SELECT * FROM {table} WHERE HashKey='{linkStruc.HashValue}'"
    result=DBcusr.execute(sqltext)
    TheTuple=result.fetchone()
    return TheTuple

def getDicByLinkStruc(linkStruc,destable=LINKDESTABLE):
    sqltext=f"SELECT * FROM {destable} WHERE HashKey='{linkStruc.HashValue}'"
    result=DBcusr.execute(sqltext)
    TheTuple=result.fetchone()
    if TheTuple:
        return eval(TheTuple[1])
    else:
        return None
def getTestDimsByLinkStruc(linkStruc,destable=LINKDESTABLE):
    sqltext=f"SELECT * FROM {destable} WHERE HashKey='{linkStruc.HashValue}'"
    result=DBcusr.execute(sqltext)
    TheTuple=result.fetchone()
    if TheTuple:
        return eval(TheTuple[2])
    else:
        return None
    
def aleadyInDB(linkStru,destable=LINKDESTABLE):
    sqltext=f"SELECT * FROM {destable} WHERE HashKey='{linkStru.HashValue}'"
    result=DBcusr.execute(sqltext)
    TheTuple=result.fetchone()
    if TheTuple:
        return 1
    else:
        return 0


#new value insert, IsBorder, UpperFinTune set 0
def InsertResult(linkStru,TValue,testdims,table=HOPS2PRE3MAIN,destable=LINKDESTABLE):
    sqltext=f'''INSERT INTO {table} (HashKey,KeyCmpHops,PathNum,Hop2Num,Hop3Num,TValue,Mean,Slope,IsBorder,UpperFineTune) VALUES ('{linkStru.HashValue}',3,{len(linkStru.linkPlist)},{len(linkStru.hops2MeanList)},{len(linkStru.hops3MeanList)},{TValue},{linkStru.hops3means},{linkStru.hops3Slope},0,0)'''
    print(sqltext)
    result=DBcusr.execute(sqltext)

    sqltext1=f'''INSERT INTO {destable} (HashKey,LinksDicStr,TestedDims) VALUES ('{linkStru.HashValue}',"{linkStru.outPutToLinksDicStr()}","{str(testdims)}")'''
    print(sqltext1)
    result=DBcusr.execute(sqltext1)




#update isborder
def UpdateIsBorderByHKey(HashValue,isborder=1,table=HOPS2PRE3MAIN):
    sqltext=f'''UPDATE {table} SET IsBorder={isborder} WHERE HashKey='{HashValue}' '''
    result=DBcusr.execute(sqltext)    
    pass
def UpdateIsBorder(linkStru,isborder=1,table=HOPS2PRE3MAIN):
    sqltext=f'''UPDATE {table} SET IsBorder={isborder} WHERE HashKey='{linkStru.HashValue}' '''
    result=DBcusr.execute(sqltext)    
    pass

#update isborder
def UpdateUpperFineTuneByHKey(HashValue,fineTune=1,table=HOPS2PRE3MAIN):
    sqltext=f'''UPDATE {table} SET UpperFineTune={fineTune} WHERE HashKey='{HashValue}' '''
    result=DBcusr.execute(sqltext)    
    pass
def UpdateUpperFineTune(linkStru,fineTune=1,table=HOPS2PRE3MAIN):
    sqltext=f'''UPDATE {table} SET UpperFineTune={fineTune} WHERE HashKey='{linkStru.HashValue}' '''
    result=DBcusr.execute(sqltext)    
    pass
    
def InitialDB():
    OpenDatabase()
    createDBTestResults()
    CloseDatabase()

def InitialWorkLoad():
    OpenDatabase()
    createWorkLoadPlanTable()
    CloseDatabase()

def createWorkLoadPlanTable():
    #WorkingTable the tablename that need to work on,its the main key of this db.
    #NewBDCount is the current assiged jobs, if  STATE==1 its the workplan. if STATE==2 its the left works to do. if STAte==3 its should be 0.
    #STATE 1:plan 2:working 3:finish others invalid    
    #Improveable is the working table improvable ,set by working jobs. when they finish their work.
    #   if Improveable==0, no need to do more work in this table. if  Improveable==1 we still need to work on this table.
    # ckCandidates are temporary checking candidates records.  checking in working state.
    #   records are tuples of checking linkStrucs, all of them are recored in DB. so the checking result can be queryed by each of then in HOPS2PRE3MAIN 
    #   it is a tuple (BPkey, incSlopeobjKey, testing1key ,testing2key,....) all testing linkStrucs are in  this tuple. if some testing object got result, then  a new tuple need to be updated and the finshed object's key should reocrded in the ckCandidatesResult field.
    # ckCandidatesResult are checking results of the process. records the finished object's key, in tuple form. (finishedkey1,finishedkey2,finishedkey3,finishedkey4,...)
    # ckBorders are candidates that need to verified be border or not.  checking in working state. 
    # ckBordersResult are checking results of the process. records the finished object's key, in tuple form. (finishedkey1,finishedkey2,finishedkey3,finishedkey4,...)
    #   result can be get by query WORKSCHEDUL for dimtest. 
    # by CheckValuesByLinkStruc to check the Tvalue we can know if this linkstru is been simulation or have been tested or derived. the 0 value means just created record and have not been updated by simulation or derived.
    #  
    sql_text_2 = '''CREATE TABLE %s
           (WorkingTable TEXT PRIMARY KEY NOT NULL,            
            NewBDCount INTEGER,
            STAGE INTEGER,
            Improveable INTEGER,
            ckCandidates TEXT,
            ckCandidatesResult TEXT,
            ckBorders TEXT,
            ckBordersResult TEXT
            );'''%(WORKSCHEDUL)
    DBcusr.execute(sql_text_2)

#new work load insert
def InsertWorkLoad(loadNum=5, toworktable=HOPS2PRE3MAIN, theworktable=WORKSCHEDUL):
    sqltext=f'''INSERT INTO {theworktable} (WorkingTable,NewBDCount,STAGE,Improveable) VALUES ('{toworktable}',{loadNum},0,1)'''
    #print(sqltext)
    result=DBcusr.execute(sqltext)

def getWorkCountLeft(toworktable=HOPS2PRE3MAIN, theworktable=WORKSCHEDUL):
        
    sqltext=f'''SELECT * FROM {theworktable} WHERE WorkingTable='{toworktable}' '''
    result=DBcusr.execute(sqltext)
    Thetuple=result.fetchone()    

    return Thetuple[1]



def UpdateLeftWorkCount(leftNum,toworktable=HOPS2PRE3MAIN, theworktable=WORKSCHEDUL):
    if leftNum==0:
        improvable=0
        state=2
    else:
        improvable=1
        state=3
    
    sqltext=f'''UPDATE {theworktable} SET NewBDCount={leftNum}, STAGE={state}, Improveable={improvable}, ckCandidates=Null, ckCandidatesResult=Null, ckBorders=Null, ckBordersResult=Null WHERE WorkingTable='{toworktable}' '''
    result=DBcusr.execute(sqltext)    
    pass

#####################
# simuLoad required functions
#####################

def getMostSlopingBorderPointAndAllBorderKey(destable=HOPS2PRE3MAIN):
    sqltext=f"SELECT * FROM {destable} WHERE IsBorder=1 AND UpperFineTune=1"
    result=DBcusr.execute(sqltext)
    Tuplearry=result.fetchall()
    mostSloping=0
    theBestKey=None
    borderKeyArray=[]
    for tupl in Tuplearry:
        borderKeyArray.append(tupl[0])
        if tupl[7]>mostSloping:
            theBestKey=tupl[0]
            mostSloping=tupl[7]
    return theBestKey,borderKeyArray

def getLeastSlopeIncreaseUpdateKey(preslope,destable=HOPS2PRE3MAIN):
    sqltext=f"SELECT * FROM {destable} WHERE IsBorder=1 AND UpperFineTune=1"
    result=DBcusr.execute(sqltext)
    Tuplearry=result.fetchall()
    increasedslope=0
    leastIncreasedSlope=100
    theBestKey=None
    for tupl in Tuplearry:
        if tupl[7]>preslope:
            increasedslope=tupl[7]-preslope
            if increasedslope<leastIncreasedSlope:
                leastIncreasedSlope=increasedslope
                theBestKey=tupl[0]


    for tupl in Tuplearry:
        #update key
        if tupl[0]==theBestKey:
            sqltext1=f'''UPDATE {destable} SET UpperFineTune={1} WHERE HashKey='{tupl[0]}' ''' #for next max degree
            result=DBcusr.execute(sqltext1) 
        elif tupl[7]>preslope:
            sqltext1=f'''UPDATE {destable} SET UpperFineTune={-1} WHERE HashKey='{tupl[0]}' ''' #for not next max degree
            result=DBcusr.execute(sqltext1)       


    return theBestKey

def getLkStruObjByHkey(theHkey,table=LINKDESTABLE):
    sqltext=f"SELECT * FROM {table} WHERE HashKey='{theHkey}'"
    result=DBcusr.execute(sqltext)
    tup=result.fetchone()
    dicobj=eval(tup[1])
    obj=sorLL.linkArryStru(dicobj)
    return obj

def getTestDimObjByHkey(theHkey,table=LINKDESTABLE):
    sqltext=f"SELECT * FROM {table} WHERE HashKey='{theHkey}'"
    result=DBcusr.execute(sqltext)
    tup=result.fetchone()
    testDimobj=eval(tup[2])    
    return testDimobj

def updateTestDim(theHkey, testDimdic ,table=LINKDESTABLE):
    sqltext=f'''UPDATE {table} SET TestedDims="{str(testDimdic)}" WHERE HashKey='{theHkey}' '''
    result=DBcusr.execute(sqltext)   
    pass

def getTvalueByHKey(theHkey,table=HOPS2PRE3MAIN):
    sqltext=f"SELECT * FROM {table} WHERE HashKey='{theHkey}'"
    result=DBcusr.execute(sqltext)
    TheTuple=result.fetchone()
    if TheTuple:
        return TheTuple[5]
    return None

def getIsBorderFineTuneByHKey(theHkey,table=HOPS2PRE3MAIN):
    sqltext=f"SELECT * FROM {table} WHERE HashKey='{theHkey}'"
    result=DBcusr.execute(sqltext)
    TheTuple=result.fetchone()
    return TheTuple[8],TheTuple[9]

def UpdateTvalueByHKey(theHkey,Tvalue ,table=HOPS2PRE3MAIN):
    sqltext=f"UPDATE {table} SET TValue={Tvalue} WHERE HashKey='{theHkey}'"
    result=DBcusr.execute(sqltext)
    

def UpdateWorkState(stateNum,toworktable=HOPS2PRE3MAIN, theworktable=WORKSCHEDUL):        
    sqltext=f'''UPDATE {theworktable} SET  STAGE={stateNum} WHERE WorkingTable='{toworktable}' '''
    result=DBcusr.execute(sqltext)    
    pass

def getWorkState(toworktable=HOPS2PRE3MAIN, theworktable=WORKSCHEDUL):        
    sqltext=f'''SELECT * FROM  {theworktable} WHERE WorkingTable='{toworktable}' '''
    result=DBcusr.execute(sqltext)
    TheTuple=result.fetchone()    
    return TheTuple[2]

def UpdateCandidatesCkTempValue(UpdatedString,toworktable=HOPS2PRE3MAIN, theworktable=WORKSCHEDUL):        
    sqltext=f'''UPDATE {theworktable} SET  ckCandidates="{UpdatedString}" WHERE WorkingTable='{toworktable}' '''
    result=DBcusr.execute(sqltext)    
    pass
def UpdateCandidatesCkReslutValue(UpdatedString,toworktable=HOPS2PRE3MAIN, theworktable=WORKSCHEDUL):        
    sqltext=f'''UPDATE {theworktable} SET  ckCandidatesResult="{UpdatedString}" WHERE WorkingTable='{toworktable}' '''
    result=DBcusr.execute(sqltext)    
    pass
def UpdateBordersCkTempValue(UpdatedString,toworktable=HOPS2PRE3MAIN, theworktable=WORKSCHEDUL):        
    sqltext=f'''UPDATE {theworktable} SET  ckBorders="{UpdatedString}" WHERE WorkingTable='{toworktable}' '''
    result=DBcusr.execute(sqltext)    
    pass
def UpdateBordersCkReslutValue(UpdatedString,toworktable=HOPS2PRE3MAIN, theworktable=WORKSCHEDUL):        
    sqltext=f'''UPDATE {theworktable} SET  ckBordersResult="{UpdatedString}" WHERE WorkingTable='{toworktable}' '''
    result=DBcusr.execute(sqltext)    
    pass

def getUnmakedCandidatesLkstru(toworktable=HOPS2PRE3MAIN):
    sqltext=f"SELECT * FROM {toworktable} WHERE IsBorder=0 AND UpperFineTune=0"
    result=DBcusr.execute(sqltext)
    Tuplearry=result.fetchall()
    strulist=[]
    for tup in Tuplearry:
        obj=getLkStruObjByHkey(tup[0])
        strulist.append(obj)
    return strulist



########################
# test functions
########################

def testAddDataToDB():
    linksData={
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
    testedDims={
    'F1':[1,2],# crossed? 0 unknow or 1 crossed or -1 failto crossed, tested(or drived or fixed or from )? 1 or 0 or 2  or  3/-3
    'F2':[1,2],#2
    'F3':[1,1],#3
    'F4':[1,1],#4
    'F5':[1,1],#5
    'F6':[1,1],#1
    'F7':[1,1],#4
    'F8':[1,1],#4
    'F9':[1,1],#4
    'F10':[1,1],#2
    }#if all crossed then it is the boundary point
    TValue=0.074048
    linkstu=sorLL.linkArryStru(linksData)
    

    OpenDatabase()
    InsertResult(linkstu,TValue,testedDims)
    UpdateIsBorder(linkstu,1)
    UpdateUpperFineTune(linkstu,1)
    CloseDatabase()

def testquaryDB():
    linksData={
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
    
    linkstu=sorLL.linkArryStru(linksData)
    
    OpenDatabase()
    obj=getDicByLinkStruc(linkstu)
    if obj:
        print("got obj: %s"%(obj))
        print("got obj['F10'][2]: %f"%(obj['F10'][2]))
        values=CheckValuesByLinkStruc(linkstu)
        print("the values:%s"%(str(values)))
    else:
        print("not found with key:%s"%(linkstu.HashValue))
    CloseDatabase()

def testAddworkLoad():
    OpenDatabase()
    InsertWorkLoad()    
    CloseDatabase()

def testgetWorkLoadLeft():
    OpenDatabase()
    count=getWorkCountLeft()
    print("the workload left:%d"%(count))    
    CloseDatabase()

def moduletest():
    InitialDB()# run only once to create db
    testAddDataToDB()
    #testquaryDB()

    #workload table
    InitialWorkLoad()
    testAddworkLoad()
    #testgetWorkLoadLeft()



if __name__=='__main__':moduletest()   

