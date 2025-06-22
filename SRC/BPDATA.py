#!/usr/bin/python3
import BPDBCreate as BPCT
import BorderPointDB as BPDB
import pathsSeqGen as PTGen
import re,ast,os
import findTailsFHSTtoSHFL as FTsH
DataDir=os.path.join(PTGen.RUNNINGDRR,"ResultDataHis")

def extract_BPdata(text):
    # 分割文本为独立的数据块
    blocks = [b.strip() for b in text.split('\n\n') if b.strip()]
    
    results = []
    for block in blocks:
        print("blocktext:\n%s\n--------------\n"%(block))
        # 3. 提取块开头的 Prefix 数组
        #    使用 re.match 确保从字符串开头匹配
        prefix_match = re.match(r'Prefix## (\[.*?\])', block, re.DOTALL) # DOTALL 让 . 匹配换行符 (虽然这里可能不需要)
        if not prefix_match:
            continue # 如果块不是以数组开头，则跳过

        prefix_array_str = prefix_match.group(1)

        # 4. 提取块内所有的 tail 数组
        #    使用 re.findall 查找所有匹配 "tail-N:[...]" 模式的数组部分
        tails_matches = re.findall(r'tail-\d+:(\[.*?\])', block)

        # 5. 将提取到的字符串数组转换为实际的 Python 列表
        try:
            # 使用 ast.literal_eval 安全地评估字符串表达式
            prefix_array = ast.literal_eval(prefix_array_str)
            tails_arrays = [ast.literal_eval(t) for t in tails_matches]

            # 6. 组合成元组并添加到结果列表 (确保确实找到了 tails)
            #if tails_arrays:
            results.append((prefix_array, tails_arrays))

        except (ValueError, SyntaxError) as e:
            print(f"warrming (array formart): {e}")
            print(f"error Prefix: {prefix_array_str}")
            # 可以选择跳过此块或进行其他错误处理
    return results

#read prefix tails blocks in refineFile, and store them to the DB
def sortbyprio(itm):
    return itm[2]

def refinefile_processing(refineFilePath):
        with open(refineFilePath, 'r') as f:
            content = f.read()
        
        results = extract_BPdata(content)
        #Insert BP points to prefix-tails DB and set prefix db state
        BPDB.OpenDatabase()#
        for bdpoint in results:
            prefix=bdpoint[0]
            tails=bdpoint[1]
            BPDB.addTailsToDB(tails)#if not in DB added 
            BPDB.setfixRLOfPrefixWithTails(prefix,tails)# set the borderpoint relations
            BPDB.updatePrefixState(prefix)#firstly all the prefix and tails have been simulated

        results= extract_patterns(content)
        results.sort(key=sortbyprio)
        for pattertup in results:
            pattern=pattertup[0]
            tailsValue=pattertup[1]
            preVBegin=pattertup[3]
            preVEnd=pattertup[4]
            print("VB:%d VE:%d pattner:%s tailsV:%d"%(preVBegin,preVEnd,pattern,tailsValue))
            BPDB.setPrefixWithTailsByRange(preVBegin,preVEnd,pattern,tailsValue)

        

        BPDB.CloseDatabase()#
            
def getNullPrefixDump():
    ####
    BPDB.OpenDatabase()#
    arrayNullPrefix=BPDB.getNullPrefixArray()
    print("Current Null Prefix count:%d"%(len(arrayNullPrefix)))
    for prefix in arrayNullPrefix:
        print("%s prefixValue:%d"%(prefix,BPDB.prefixMetric(prefix)))
    BPDB.CloseDatabase()#

def extract_patterns(text):
    # 匹配包含模式信息的代码块
    blocks = re.findall(r'##\$\$#(.*?)##\$\$#', text, re.DOTALL)

    #print("blocks:%s"%(blocks))

    results = []
    for block in blocks:

        # 处理换行和多余空格（保留关键格式）
        cleaned_block = ' '.join(line.strip() for line in block.split('\n'))

        match_combined = re.search(r'(\[.*?\])\s*tailsValue:(\d+)\s*@@@\s*PRIO:(\d+)\s*prefixVB:(\d+)\s*prefixVE:(\d+)', cleaned_block)
        if match_combined:
            array_str_combined = match_combined.group(1)
            tails_value_combined = match_combined.group(2)
            prio_value_combined = match_combined.group(3)
            prefixVBeginStr = match_combined.group(4)
            prefixVEndStr = match_combined.group(5)
            #print(f"组合提取 - 数组: {array_str_combined}")
            #print(f"组合提取 - tailsValue: {tails_value_combined}")
            #print(f"组合提取 - PRIO: {prio_value_combined}")
            pattern=[int(num) for num in re.findall(r'\d+', array_str_combined)]
            tails_value=int(tails_value_combined)
            prio=int(prio_value_combined)
            preVB=int(prefixVBeginStr)
            preVE=int(prefixVEndStr)
            results.append((pattern, tails_value, prio,preVB, preVE))
        else:
            print("pattern not found")

    return results



def createBPDB():
    ###
    BPDB.createDBs()
    ##########
    PTGen.loadValuToLinkMapDic()  
    ##prefix table created at begining
    ###
    BPDB.OpenDatabase()
    BPDB.InitPrefixTables()
    BPDB.commitChanges()

def addBPtoDBData():    
    BPDB.OpenDatabase()
    #BPCT.buildDBwithSimulationResults(data)
    BPDB.commitChanges()

def makeStatisticcOnDB():
    BPDB.OpenDatabase()
    BPCT.drawIDScatterPointsInDB()


def fillDBData():    
    createBPDB()
    PTGen.loadValuToLinkMapDic() 
    file1path=os.path.join(DataDir,'logV2Refined.txt')
    file2path=os.path.join(DataDir,'logV2Refine2.txt')
    file3path=os.path.join(DataDir,'logV2Refine3.txt')
    refinefile_processing(file1path)
    refinefile_processing(file2path)
    refinefile_processing(file3path)
    getNullPrefixDump()

    #PTGen.loadValuToLinkMapDic()  
    #addBPtoDBData()
    #makeStatisticcOnDB()

def checkprefix():
    PTGen.loadValuToLinkMapDic()
    BPDB.OpenDatabase()#
    arrayNullTailPrefix=BPDB.checkprefixNullTails()
    print("Current Null Prefix count:%d"%(len(arrayNullTailPrefix)))
    for prefix in arrayNullTailPrefix:
        print("%s prefixValue:%d"%(prefix,BPDB.prefixMetric(prefix)))
    BPDB.CloseDatabase()#

def checkRedundantPrefix():
    PTGen.loadValuToLinkMapDic()
    BPDB.OpenDatabase()#
    arrayRedundantPrefix=BPDB.checkRedundantPrefix()
    print("Redundant Prefix count:%d"%(len(arrayRedundantPrefix)))
    for prefix in arrayRedundantPrefix:
        print("%s prefixValue:%d"%(prefix,BPDB.prefixMetric(prefix)))
    BPDB.CloseDatabase()#


searchTreeObjDic=None
def checkTailsDBTreeBuild():
    global searchTreeObjDic
    PTGen.loadValuToLinkMapDic()
    BPDB.OpenDatabase()# 
    searchTreeObjDic=BPCT.buildTreeWithTailsInDB()
    BPDB.CloseDatabase()# 

def checkValidLink(linkArrayIn):
    linkArray=linkArrayIn.copy()
    linkArray.sort()
    prefix=[linkArray[0],linkArray[1],linkArray[2],linkArray[3],linkArray[4]]

    if linkArray[5]>FTsH.INFINITYLKVALUE:
        linkArray[5]=FTsH.INFINITYLKVALUE
    if linkArray[6]>FTsH.INFINITYLKVALUE:   
        linkArray[6]=FTsH.INFINITYLKVALUE
    if linkArray[7]>FTsH.INFINITYLKVALUE:       
        linkArray[7]=FTsH.INFINITYLKVALUE
    if linkArray[8]>FTsH.INFINITYLKVALUE:
        linkArray[8]=FTsH.INFINITYLKVALUE
    if linkArray[9]>FTsH.INFINITYLKVALUE:
        linkArray[9]=FTsH.INFINITYLKVALUE

    tail=[linkArray[5],linkArray[6],linkArray[7],linkArray[8],linkArray[9]] 
    #PTGen.loadValuToLinkMapDic()
    BPDB.OpenDatabase()# 
    result=BPCT.checkLinksValid(prefix,tail,searchTreeObjDic)
    BPDB.CloseDatabase()#  
    return result

# Simplified check based on the median path key
def checkValidLinkSimplified(linkArrayIn):
    """
    Simplified validity check based on the median path key.
    Sorts the link keys and compares the median value (index 5) against a threshold (364).

    Args:
        linkArrayIn (list): A list of 10 path key values.

    Returns:
        int: 1 if invalid (median > 364), -1 if valid (median <= 364).
    """
    linkArray = linkArrayIn.copy()
    linkArray.sort()
    # Check the median path key (index 5 for a list of 10)
    if len(linkArray) == 10:
        if linkArray[5] > 364:
            return 1 # Invalid
        else:
            return -1 # Valid
    else:
        # Handle cases where the input array doesn't have 10 elements if necessary
        print(f"Warning: checkValidLinkSimplified expects 10 elements, got {len(linkArray)}. Returning invalid.")
        return 1 # Default to invalid if input size is wrong


def checklinks():
    #linkArray=[104,224,344,344,360,364,364,420,420,466]
    #linkArray=[104, 208, 208, 208, 312, 312, 466, 466, 864, 1108]
    #linkArray=[140, 245, 280, 280, 364, 364, 384, 554, 574, 1044]
    #linkArray=[140, 208, 280, 280, 328, 348, 420, 518, 1044, 1080]
    #linkArray=[104, 140, 140, 224, 328, 348, 538, 1213, 1527, 1916]# should valid
    linkArray=[140, 208, 245, 280, 312, 348, 466, 656, 880, 1474]# should invalid
    #linkArray=[104, 208, 208, 245, 328, 348, 538, 896, 932, 1125]
    #linkArray=[140, 208, 280, 280, 328, 348, 420, 518, 1044, 1080]
    #linkArray=[208, 240, 245, 245, 260, 348, 502, 502, 725, 948]
    #linkArray=[104, 208, 245, 280, 312, 348, 482, 498, 653, 912]
    # linkArraySimpInvalid = [104, 104, 104, 208, 208, 365, 365, 365, 400, 400] # Example for simplified check invalid
    # linkArraySimpValid =   [104, 104, 104, 208, 208, 364, 364, 364, 400, 400] # Example for simplified check valid

    linkArray.sort()
    checkTailsDBTreeBuild()
    
    # Test original check
    valid_orig = checkValidLink(linkArray)
    print(f"Original check for {linkArray}: {'valid' if valid_orig <= 0 else 'invalid'} (Result: {valid_orig})")

    # Test simplified check
    # valid_simp_inv = checkValidLinkSimplified(linkArraySimpInvalid)
    # print(f"Simplified check for {linkArraySimpInvalid}: {'valid' if valid_simp_inv <= 0 else 'invalid'} (Result: {valid_simp_inv})")
    # valid_simp_val = checkValidLinkSimplified(linkArraySimpValid)
    # print(f"Simplified check for {linkArraySimpValid}: {'valid' if valid_simp_val <= 0 else 'invalid'} (Result: {valid_simp_val})")

import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['pdf.fonttype'] = 42
scalfontsize=20
plt.rcParams.update({'font.size': scalfontsize})

def drawstatics1():
    PTGen.loadValuToLinkMapDic()
    BPDB.OpenDatabase()# 
    freq_data=BPDB.getTailSValueFrequencyInAllTailTable()
    BPDB.CloseDatabase()# 

    colorset='tab:gray'

    # 提取排序后的键值索引、count 和 tails_num
    indices = list(range(len(freq_data)))
    print("total suffix groups:%d"%(len(indices)))
    counts = [freq_data[key]['count'] for key in freq_data]
    tails_nums = [freq_data[key]['tails_num'] for key in freq_data]
    
    # 绘制第一个直方图 (count)
    plt.figure(1)#(figsize=(10, 6))
    plt.bar(indices, counts,color=colorset)
    plt.xlabel('Suffix Group Index')
    plt.ylabel('Frequency')
    plt.title(r'Frequency Distribution of Suffixes in $\mathcal{P}_{eff}$')
    plt.grid(True)
    plt.show()
    
    # 绘制第二个直方图 (tails_num)
    plt.figure(2)#(figsize=(10, 6))
    plt.bar(indices, tails_nums,color=colorset)
    plt.xlabel('Suffix Group Index')
    plt.ylabel('Suffix Group Size')
    plt.title(r'Suffix Group Size in $\mathcal{P}_{eff}$')
    plt.grid(True)
    plt.show()



def plotBoundaryPointBitmap(bitmap_dic):
    """
    绘制边界点位图，将 prefixValue 和 TailValue 转化到范围内作为 x 和 y 坐标。
    使用 matplotlib 库绘制散点图表示位图。
    """
    if not bitmap_dic:
        print("empty bitmap_dic")
        return
    
    # 提取 prefixValue 和 TailValue 的范围
    prefix_values = sorted(set(key[0] for key in bitmap_dic.keys()))
    tail_values = sorted(set(key[1] for key in bitmap_dic.keys()))
    
    # 创建映射，将原始值映射到连续的索引范围内
    prefix_map = {val: idx for idx, val in enumerate(prefix_values)}
    tail_map = {val: idx for idx, val in enumerate(tail_values)}
    
    # 转换坐标
    x_coords = [prefix_map[key[0]] for key in bitmap_dic.keys()]
    y_coords = [tail_map[key[1]] for key in bitmap_dic.keys()]
    
    # 绘制散点图
    plt.figure(figsize=(12, 8))
    plt.scatter(x_coords, y_coords, c='tab:blue', marker='s', s=10, alpha=0.5)
    plt.xlabel('PrefixValue Index')
    plt.ylabel('SuffixValue Index')
    plt.title('Boundary Point Bitmap')
    plt.grid(True)
    plt.show()


def BoundaryPointsPlot_boxplot(id_distributions):
    # 设置x轴标签
    x_labels = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']
    
    # 绘制箱线图
    plt.figure(figsize=(10, 6))
    plt.boxplot(id_distributions, labels=x_labels,medianprops={'linestyle': '-', 'linewidth': 5, 'color': 'darkblue'},showmeans=True, meanprops={'marker': 'D', 'markersize': 12, 'markerfacecolor': 'white'}, capprops={'linestyle': '-', 'linewidth': 5, 'color': 'darkblue'}) 
    plt.xlabel('Sorted Path Index')
    plt.ylabel('Path Score Index')
    plt.title('Distribution of path scores for $T_c(\%95)$ in 0.12 ± 0.00005 sec.')
    plt.grid(True)
    
    # 显示图表
    plt.show()




def drawBoundaryPointBitmap():
    PTGen.loadValuToLinkMapDic()
    BPDB.OpenDatabase()# 
    bitmap=BPDB.generateBoundaryPointBitmap()
    BPDB.CloseDatabase()# 
# 使用示例

    plotBoundaryPointBitmap(bitmap)


def drawBPIDstatics():
    idstaic=PTGen.extract_BPdata_from_db()
    BoundaryPointsPlot_boxplot(idstaic)

def moduletest():
    #fillDBData()
    #checkprefix()
    #checkRedundantPrefix()
    #checklinks()
    #drawstatics1()
    #drawBoundaryPointBitmap()
    drawBPIDstatics()

if __name__=='__main__':moduletest()
