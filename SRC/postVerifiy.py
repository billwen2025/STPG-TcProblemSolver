# SRC/postVerifiy.py

import shutil
import sys
import time
import logging
import glob # For finding generated files
import STPGcommon as common 
import BPDATA
import BPDBCreate as BPDBCrt
# 假设 GurobiSTPGSolver.py 在同一目录 (SRC) 下
try:
    from GurobiSTPGSolver import run_single_test_case
except ImportError as e:
    print(f"错误：无法从 GurobiSTPGSolver 导入：{e}")
    print("请确保 GurobiSTPGSolver.py 在 SRC 目录下且已正确重构。")
    sys.exit(1)

import ast # 导入 ast 模块
import BorderPointDB as BPDB
import os
import sortlinklist as sorLL
import findTailsFHSTtoSHFL as fndTails

def parse_KeyPoints_data_file(datafilepath):
    """
    从指定路径的文件中提取数据块，并将每个块转换为字典。
    使用 ast.literal_eval 解析列表字符串。

    文件格式假定：
    - 数据以块的形式出现。
    - 每个块由11行有意义的数据组成（忽略注释和空行）。
    - 块的第一行是整数列表（将被忽略）。
    - 块的第2到11行格式为 '数字:[浮点数列表]'。
    - 以 '#' 开头的行是注释，将被忽略。
    - 空行将被忽略。

    Args:
        datafilepath (str): 包含数据的文件的路径。

    Returns:
        list: 一个包含字典的列表。每个字典代表文件中的一个数据块，
              键为 'F1' 到 'F10'，值为对应的浮点数列表。
              如果文件无法读取或格式不正确，则可能返回空列表或引发错误。
    """
    results = []
    current_block_data = {}
    data_line_count = 0 # 用于追踪当前块中已处理的数据行数 (预期为 10 行)

    try:
        with open(datafilepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1): # 添加行号便于调试
                stripped_line = line.strip()

                # 跳过空行和注释行
                if not stripped_line or stripped_line.startswith('#'):
                    continue

                # 检查是否是块的第一行（整数列表）
                # 使用更严格的检查，确保它看起来像一个列表并且之前块已完成或刚开始
                if stripped_line.startswith('[') and stripped_line.endswith(']'):
                    # 在遇到新的块开始标记时，处理上一个完整收集的块
                    if data_line_count == 10:
                        if len(current_block_data) == 10:
                             results.append(current_block_data)
                        else:
                             # 通常不应该发生，因为 data_line_count == 10 保证了
                             print(f"警告：在文件 {datafilepath} 行 {line_num} 检测到内部逻辑错误。块标记完成但数据不足。")
                        # 为新块重置
                        current_block_data = {}
                        data_line_count = 0
                    elif data_line_count != 0:
                        # 如果遇到新的块开始，但前一个块不完整
                        print(f"警告：在文件 {datafilepath} 行 {line_num} 检测到新的数据块开始 '[...]'，但前一个块不完整（只有 {data_line_count} 行数据）。之前的块数据将被丢弃。")
                        # 为新块重置
                        current_block_data = {}
                        data_line_count = 0
                    # else: data_line_count is 0, starting fresh, do nothing extra

                    # 忽略这一行的内容，继续读取下一行
                    continue

                # 处理数据行（格式：数字:[列表]）
                # 只有在 data_line_count < 10 时才处理，表示当前块未满
                if data_line_count < 10:
                    try:
                        parts = stripped_line.split(':', 1)
                        if len(parts) == 2:
                            key_part = parts[0].strip() # 可以保留，但在此逻辑中未使用
                            list_str = parts[1].strip()

                            # 使用 ast.literal_eval 安全地将字符串转换为 Python 列表
                            try:
                                data_list = ast.literal_eval(list_str)
                                # 确保解析结果是列表类型
                                if isinstance(data_list, list):
                                    data_line_count += 1
                                    key = f'F{data_line_count}'
                                    current_block_data[key] = data_list
                                else:
                                     print(f"警告：在文件 {datafilepath} 行 {line_num} 解析得到非列表类型，内容：'{stripped_line}'。已跳过此行。")

                            # ast.literal_eval 可能引发 ValueError, TypeError, SyntaxError, MemoryError, RecursionError
                            # 这里捕获常见的解析错误
                            except (ValueError, SyntaxError, TypeError) as e:
                                print(f"警告：在文件 {datafilepath} 行 {line_num} 使用 ast.literal_eval 解析列表字符串时出错，内容：'{stripped_line}'。错误：{e}。已跳过此行。")

                        else:
                            print(f"警告：在文件 {datafilepath} 行 {line_num} 发现格式不正确的数据行（缺少':'），内容：'{stripped_line}'。已跳过此行。")

                    except Exception as e:
                         print(f"处理文件 {datafilepath} 行 {line_num} '{stripped_line}' 时发生意外错误: {e}")
                else:
                    # 如果 data_line_count >= 10 但行不是块开始标记、注释或空行，说明格式可能有问题
                    print(f"警告：在文件 {datafilepath} 行 {line_num} 发现预期之外的数据行（可能块过长或格式错误），内容：'{stripped_line}'。已忽略此行。")


        # 文件读取循环结束后，检查最后一个块是否完整并需要添加
        if data_line_count == 10:
             if len(current_block_data) == 10:
                 results.append(current_block_data)
             else:
                 # 这同样是一个内部逻辑问题的指示
                 print(f"警告：在文件 {datafilepath} 结束时，最后一个块标记完成但数据不足。")
        elif data_line_count > 0: # 文件结束，但最后一个块不完整
             print(f"警告：文件 {datafilepath} 结束时，最后一个数据块不完整（只有 {data_line_count} 行数据）。此不完整块已被丢弃。")


    except FileNotFoundError:
        print(f"错误：文件 {datafilepath} 未找到。")
    except Exception as e:
        print(f"读取或处理文件 {datafilepath} 时发生严重错误：{e}")

    return results

# --- 使用示例 ---

# 1. 确保你有一个名为 data.txt 的文件，内容与之前示例相同。
'''
[140, 280, 280, 280, 280, 280, 420, 801, 1360, 1360]
140:[0.02]
280:[0.02, 0.02]
280:[0.02, 0.02]
280:[0.02, 0.02]
280:[0.02, 0.02]
280:[0.02, 0.02]
420:[0.02, 0.02, 0.02]
801:[0.02, 0.02, 0.02, 0.02, 0.02]
1360:[0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02]
1360:[0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02]

#comments
# another comment

[140, 245, 280, 280, 280, 280, 420, 801, 1285, 1305]
140:[0.02]
245:[0.011, 0.02]
280:[0.02, 0.02]
280:[0.02, 0.02]
280:[0.02, 0.02]
280:[0.02, 0.02]
420:[0.02, 0.02, 0.02]
801:[0.02, 0.02, 0.02, 0.02, 0.02]
1285:[0.011, 0.015, 0.015, 0.02, 0.02, 0.02, 0.02]
1305:[0.011, 0.015, 0.02, 0.02, 0.02, 0.02, 0.02]

'''

# 2. 调用函数并打印结果
theKeypoints_file_path =os.path.join(BPDB.DataDir,'finalVerifyDatalist.txt') # 确保路径正确

def paserfile_testfunc(file_path):
    parsed_data = parse_KeyPoints_data_file(file_path)
    return parsed_data


def simulationCheck(dicsArray):
    simuAry=[]
    for dic in dicsArray:
        linkobj=sorLL.linkArryStru(dic)
        simuAry.append(linkobj)
    
        
    resutls=fndTails.getSimuResultsForLinkStrArray(simuAry)
    print("got sim results:%s"%(resutls))


def postverifytest():
    # 3. 打印结果
    import pprint
    parsed_data=paserfile_testfunc(theKeypoints_file_path)   
    
    #pprint.pprint(parsed_data)

    print("total dic counts:%d"%(len(parsed_data)))
    
    simulationCheck(parsed_data)



# --- 配置 ---

# 获取此脚本所在的目录 (SRC)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录 (上级目录)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# 定义相对于项目根目录的路径
TESTCASES_DIR = os.path.join(PROJECT_ROOT, 'ResultDataHis', 'testcases')
WORKING_DIR_BASE = os.path.join(PROJECT_ROOT, 'TestWorkingGDir')
# LOG_FILE = os.path.join(PROJECT_ROOT, 'TestWorkingGDir', 'automation_run.log') # 不再使用全局日志文件

TEMPERATURES = [0]#[50, 20, 0, -20, -50]
TEMP_INPUT_FILENAME = 'solver_input.stp' # 固定输入文件名
TEMP_LOG_FILENAME = 'case_temp.log' # 每个 case 临时的日志文件名

# --- 用户可配置设置 ---
# 这些设置最好通过命令行参数或配置文件来配置
SOLVER_CHOICE = 0  # 0: Gurobi, 1: SCIP-Iterative, 2: SCIP-VCF
SIMPLE_CHECK = 0   # 0: DB check, 1: Simplified median check
# --- 用户可配置设置结束 ---
#command in parent dir of SRC,
#run: python3 SRC/postVerifiy.py 

# --- 日志设置 (修改为 case 级别) ---
# 全局日志配置移除，将在每个 case 内部处理
# 创建一个基础 logger 和 adapter，但 handler 将动态添加/移除
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # 设置基础 logger 的级别
# 添加控制台输出 handler (这个可以保持全局)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - Case %(case_idx)s - %(message)s'))
logger.addHandler(console_handler)
# 创建 adapter
adapter = logging.LoggerAdapter(logger, {'case_idx': 'N/A'})
common.g_LoggerAdapter=adapter

# --- 文件查找与清理函数 ---

def find_generated_files(working_dir, base_filename_no_ext, files_before):
    """查找在 working_dir 中新生成的 *文件* (忽略目录)"""
    files_after = set(glob.glob(os.path.join(working_dir, '*')))
    new_items = files_after - files_before
    # 只保留文件，过滤掉目录
    new_files = {item for item in new_items if os.path.isfile(item)}
    # 过滤掉临时输入文件自身
    temp_input_path = os.path.join(working_dir, TEMP_INPUT_FILENAME)
    if temp_input_path in new_files:
        new_files.remove(temp_input_path)
    return list(new_files)

def cleanup_working_dir(working_dir, files_to_remove):
    """清理工作目录中的指定文件 (现在只清理文件，不清理目录)"""
    for f_path in files_to_remove:
        try:
            if os.path.isfile(f_path): # 确保只删除文件
                os.remove(f_path)
                adapter.info(f"已清理文件: {os.path.basename(f_path)}")
            elif os.path.exists(f_path): # 如果路径存在但不是文件 (可能是目录或链接等)，记录警告
                 adapter.warning(f"尝试清理路径 {os.path.basename(f_path)}，但它不是一个文件，已跳过。")
        except OSError as e:
            adapter.error(f"清理文件 {os.path.basename(f_path)} 时出错: {e}")


# --- 主要自动化逻辑 ---

# 全局变量，用于跟踪当前的 case 文件 handler
current_case_log_handler = None


def run_all_tests():
    """
    执行所有 STP 文件和温度组合的自动化测试流程。
    """
    adapter.info("--- 开始自动化测试运行 ---")
    adapter.info(f"测试用例目录: {TESTCASES_DIR}")
    adapter.info(f"工作目录基础路径: {WORKING_DIR_BASE}")
    adapter.info(f"温度设置: {TEMPERATURES}")
    solver_map = {0: "Gurobi", 1: "SCIP-Iterative", 2: "SCIP-VCF"}
    check_map = {0: "Database Lookup", 1: "Simplified Median"}
    adapter.info(f"选择的求解器: {solver_map.get(SOLVER_CHOICE, '未知')} ({SOLVER_CHOICE})")
    adapter.info(f"有效性检查方法: {check_map.get(SIMPLE_CHECK, '未知')} ({SIMPLE_CHECK})")

    # 1. 初始化 BPDATA 数据库
    try:
        adapter.info("正在初始化 BPDATA 数据库...")
        BPDATA.checkTailsDBTreeBuild()
        adapter.info("BPDATA 初始化成功。")
    except AttributeError:
         adapter.warning("未找到 BPDATA 初始化函数 (checkTailsDBTreeBuild)。假设初始化在别处进行或不需要。")
    except Exception as e:
        adapter.error(f"初始化 BPDATA 时出错: {e}。有效性检查可能会失败。", exc_info=True)
        # 决定是否退出
        # sys.exit(1)

    # 2. 获取并排序测试用例文件
    try:
        all_files = [f for f in os.listdir(TESTCASES_DIR) if f.endswith('.stp')]
        sorted_stp_files = sorted(all_files)
        if not sorted_stp_files:
            adapter.error(f"在 {TESTCASES_DIR} 中未找到 .stp 文件。正在退出。")
            return
        adapter.info(f"找到 {len(sorted_stp_files)} 个 STP 文件待处理。")
    except FileNotFoundError:
        adapter.error(f"测试用例目录未找到: {TESTCASES_DIR}。正在退出。")
        return
    except Exception as e:
        adapter.error(f"列出测试用例文件时出错: {e}。正在退出。", exc_info=True)
        return

    # 3. 循环运行测试
    case_index = 0
    total_tests = len(sorted_stp_files) * len(TEMPERATURES)
    start_time_all = time.time()
    failed_cases = 0

    # 确保基础工作目录存在
    #os.makedirs(WORKING_DIR_BASE, exist_ok=True)#必然存在

    for stp_filename in sorted_stp_files:
        source_stp_path = os.path.join(TESTCASES_DIR, stp_filename)
        TEMP_INPUT_FILENAME=stp_filename
        
        for temp in TEMPERATURES:
            case_index += 1
            adapter.extra['case_idx'] = case_index # 更新日志适配器的 case_index

            # --- 配置当前 Case 的日志文件 Handler ---
            global current_case_log_handler
            # 如果之前有 handler，先移除
            if current_case_log_handler:
                logger.removeHandler(current_case_log_handler)
                current_case_log_handler.close()

            temp_log_filepath = os.path.join(WORKING_DIR_BASE, TEMP_LOG_FILENAME)
            # 创建新的文件 handler，模式设为 'w' 以覆盖上次 case 的临时日志
            current_case_log_handler = logging.FileHandler(temp_log_filepath, mode='w')
            current_case_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - Case %(case_idx)s - %(message)s'))
            logger.addHandler(current_case_log_handler)
            # --- 日志配置结束 ---

            adapter.info(f"--- 开始处理: 文件={stp_filename}, 温度={temp} ---")
            start_time_case = time.time()

            # 定义临时输入文件路径
            target_stp_in_working_dir = os.path.join(WORKING_DIR_BASE, TEMP_INPUT_FILENAME)

            # 准备工作目录：拷贝输入文件
            try:
                shutil.copy(source_stp_path, target_stp_in_working_dir)
                adapter.info(f"已拷贝 {stp_filename} 到 {TEMP_INPUT_FILENAME}")
            except Exception as e:
                adapter.error(f"拷贝文件 {stp_filename} 时出错: {e}。跳过此 case。", exc_info=True)
                failed_cases += 1
                continue # 跳到下一个 case

            # 记录调用前的状态 (只记录文件，因为目录会被忽略)
            files_before_run = set(glob.glob(os.path.join(WORKING_DIR_BASE, '*')))
            # 确保临时日志文件存在于 files_before_run 中，即使它是新创建的
            # 这样 find_generated_files 就不会把它当作 solver 生成的文件
            # 注意：如果 FileHandler 创建失败，这里可能会出错，但可能性较低
            if os.path.exists(temp_log_filepath):
                files_before_run.add(temp_log_filepath) #日志文件需要最后移动，属于特殊处理
            # 确保输入文件不存在于 files_before_run 中，即使它是新创建的
            if os.path.exists(target_stp_in_working_dir) and target_stp_in_working_dir in files_before_run:
                files_before_run.remove(target_stp_in_working_dir)


            # 调用 GurobiSTPGSolver 中的函数
            call_successful = False
            try:
                # 切换到工作目录执行，因为 solver_main 可能仍有相对路径依赖
                original_cwd = os.getcwd()
                os.chdir(WORKING_DIR_BASE)
                adapter.info(f"切换工作目录到: {WORKING_DIR_BASE}")

                BPDBCrt.checkhistOneInst.clear()

                call_successful = run_single_test_case(
                    input_filename_in_working_dir=TEMP_INPUT_FILENAME,
                    temperature=temp,
                    solver_choice=SOLVER_CHOICE,
                    simple_check=SIMPLE_CHECK, 
                    logadapter=adapter
                )
                OneinstFilePaht, AllInstFilePaht = BPDBCrt.savechkHisToDir(WORKING_DIR_BASE)
                #adapter.info(f"save checkhistOneInst to  {OneinstFilePaht} checkhisAll to {AllInstFilePaht}")
                adapter.info(f"运行单测试用例完成， checkhistOneInst: {len(BPDBCrt.checkhistOneInst)} checkhisAll:{len(BPDBCrt.checkhisAll)}")

                

            except Exception as e:
                 # 捕获 run_single_test_case 外部的错误 (例如 chdir 失败)
                 adapter.error(f"调用 run_single_test_case 之前/期间发生意外错误: {e}", exc_info=True)
                 call_successful = False # 确保标记为失败
            finally:
                # 无论如何都要切换回原始目录
                os.chdir(original_cwd)
                adapter.info(f"切换回工作目录: {original_cwd}")


            # --- 结果收集、日志处理和清理 ---
            generated_files = [] # Solver 生成的文件
            files_moved_successfully = set() # 记录成功移动的文件
            results_dir = os.path.join(WORKING_DIR_BASE, f'case{case_index}') # 结果目录路径

            try:
                # 无论成功与否，都尝试查找生成的文件
                generated_files = find_generated_files(WORKING_DIR_BASE, os.path.splitext(TEMP_INPUT_FILENAME)[0], files_before_run)
                if generated_files:
                     adapter.info(f"检测到 Solver 生成的文件: {[os.path.basename(f) for f in generated_files]}")
                else:
                     adapter.info("未检测到 Solver 生成的新文件。")


                if call_successful:
                    adapter.info("run_single_test_case 调用成功完成。")
                    # 创建结果目录
                    os.makedirs(results_dir, exist_ok=True)
                    adapter.info(f"创建/确认结果目录: {results_dir}")

                    # 移动 Solver 生成的文件
                    for gen_file in generated_files:
                        try:
                            dest_file = os.path.join(results_dir, os.path.basename(gen_file))
                            shutil.move(gen_file, dest_file)
                            adapter.info(f"已移动 Solver 文件 {os.path.basename(gen_file)} 到 {results_dir}")
                            files_moved_successfully.add(gen_file) # 记录成功移动
                        except Exception as e:
                            adapter.error(f"移动 Solver 文件 {os.path.basename(gen_file)} 时出错: {e}", exc_info=True)
                            # 文件保留在工作目录中，将在下面清理

                else:
                    adapter.error("run_single_test_case 调用失败或在执行期间引发错误。")
                    failed_cases += 1
                    # 如果调用失败，我们仍然找到了生成的文件，记录警告
                    if generated_files:
                        adapter.warning(f"调用失败，但找到以下 Solver 文件，将尝试清理: {[os.path.basename(f) for f in generated_files]}")

            except OSError as e:
                 adapter.error(f"创建结果目录 {results_dir} 时出错: {e}。结果可能未保存。", exc_info=True)
                 if call_successful: # 只有在调用成功但目录创建失败时才算 case 失败
                     failed_cases += 1
            except Exception as e:
                 adapter.error(f"结果收集或文件查找过程中发生意外错误: {e}", exc_info=True)
                 failed_cases += 1 # 标记为失败

            # --- 日志文件处理 ---
            # 关闭当前 case 的文件 handler
            if current_case_log_handler:
                logger.removeHandler(current_case_log_handler)
                current_case_log_handler.close()
                current_case_log_handler = None # 重置全局变量

            # 移动临时日志文件到结果目录 (如果结果目录存在)
            if os.path.exists(results_dir) and os.path.exists(temp_log_filepath):
                final_log_path = os.path.join(results_dir, f'case{case_index}.log')
                try:
                    shutil.move(temp_log_filepath, final_log_path)
                    adapter.info(f"已移动日志文件到 {final_log_path}")
                    files_moved_successfully.add(temp_log_filepath) # 标记日志文件移动成功
                except Exception as e:
                    adapter.error(f"移动日志文件 {TEMP_LOG_FILENAME} 到 {results_dir} 时出错: {e}", exc_info=True)
                    # 日志文件保留在工作目录中，将在下面清理
            elif not os.path.exists(temp_log_filepath):
                 adapter.warning(f"未找到预期的临时日志文件 {temp_log_filepath} 进行移动。")
            # else: results_dir 不存在，无法移动日志，将在下面清理

            # --- 清理工作目录 ---
            # 需要清理的文件：
            # 1. 原始的临时输入文件
            # 2. 所有找到的 Solver 生成的文件中，*未* 成功移动到 results_dir 的文件
            # 3. 临时日志文件，如果它*未* 成功移动到 results_dir
            files_to_clean = {target_stp_in_working_dir} # 使用集合避免重复

            # 添加未成功移动的 Solver 文件
            solver_files_to_clean = set(generated_files) - files_moved_successfully
            if solver_files_to_clean:
                 adapter.info(f"将清理以下未移动的 Solver 文件: {[os.path.basename(f) for f in solver_files_to_clean]}")
                 files_to_clean.update(solver_files_to_clean)

            # 添加未成功移动的临时日志文件
            if temp_log_filepath not in files_moved_successfully and os.path.exists(temp_log_filepath):
                 adapter.info(f"将清理未移动的临时日志文件: {TEMP_LOG_FILENAME}")
                 files_to_clean.add(temp_log_filepath)

            # 执行清理
            cleanup_working_dir(WORKING_DIR_BASE, list(files_to_clean))


            end_time_case = time.time()
            adapter.info(f"--- Case {case_index} 处理完成。耗时: {end_time_case - start_time_case:.2f}s ---")


    end_time_all = time.time()
    adapter.extra['case_idx'] = 'SUMMARY' # 设置日志的 case_idx
    adapter.info(f"--- 自动化测试运行结束 ---")
    adapter.info(f"总共处理的 cases: {case_index}")
    adapter.info(f"成功完成的 cases (调用流程): {case_index - failed_cases}")
    adapter.info(f"失败的 cases (调用流程或结果保存): {failed_cases}")
    adapter.info(f"总耗时: {end_time_all - start_time_all:.2f}s")
    adapter.info(f"详细日志见各个 caseN 目录下的 caseN.log 文件。")

if __name__ == "__main__":
    # 确保在程序退出时关闭可能残留的日志 handler
    if 1:#run tests
        try:
            run_all_tests()
        finally:
            if current_case_log_handler:
                logger.removeHandler(current_case_log_handler)
                current_case_log_handler.close()
    else:#verify results
        postverifytest()