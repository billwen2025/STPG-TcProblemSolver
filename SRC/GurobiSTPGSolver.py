import gurobipy as gp
from gurobipy import GRB
import re # 用于解析文件
import time,os,shutil, subprocess,sys, logging # 添加 subprocess 和 logging

import pathsSeqGen as pthGen
import BPDATA # Added for new check_solution_with_database logic
from collections import defaultdict, deque # Added for path finding
import networkx as nx # Added for connectivity check
import STPGcommon as common # Added for shared variables and functions
import sciprelatedRemoveAlg as rmAlg # Added for SCIP-related edge removal algorithm
import BPDBCreate as BPDBCrt

g_SimpleCheck=0 # 0: for lookup table check, by checkValidLinks, 1: for simple check, by checkValidLinkSimplified
g_SolverChoose=1 # 0: for Gurobi, 1: for SCIP-jack
remove_Edge_alg_select=2 # 0: for original algorithm (worst path), 1: for max cost unique edge with connectivity check,  bridge value based。2：PK values higher than the middle worst paths 3： a mixture of 0,1
SCIPJACKMAXITERATION=40
GUROBI_MAXCOMPUTE_TIME=5
TEMPERATURE=-20 # Default temperature for Q value adjustment


# --- New QoS Functionality ---

class QueryEdgeQValue:
    """
    Generates/reads .stq file for base QoS (T=0),
    and provides lookup for edge Q values adjusted for temperature on demand.
    """
    def __init__(self, stp_file_path):
        """
        Initializes the QoS query object by generating/reading the base .stq file.

        Args:
            stp_file_path (str): Path to the .stp file.
        """
        if not os.path.exists(stp_file_path):
            raise FileNotFoundError(f"STP file not found: {stp_file_path}")

        self.stp_file_path = stp_file_path
        # Ensure stq file path is derived correctly even if stp has no extension
        base_path = os.path.splitext(stp_file_path)[0]
        self.stq_file_path = base_path + ".stq"
        self.base_edge_q_values = {} # Stores Q values for Temperature=0

        self._initialize_base_q_values()

    def _initialize_base_q_values(self):
        """Handles the process of generating/reading the base Q values (T=0)."""
        # 1. Generate .stq file if needed or always regenerate.
        # Let's stick with always regenerating for simplicity, ensuring it's fresh.
        try:
             common.generate_stq_file(self.stp_file_path, self.stq_file_path)
        except Exception as e:
             print(f"Failed to generate STQ file: {e}")
             # If generation fails, we cannot proceed.
             raise RuntimeError(f"Could not generate STQ file from {self.stp_file_path}") from e

        # 2. Read the generated .stq file to get base Q values
        try:
            self.base_edge_q_values = common.read_stq_file(self.stq_file_path)
            if not self.base_edge_q_values:
                 # Handle case where STQ is empty or unreadable properly
                 raise ValueError(f"STQ file {self.stq_file_path} was read but resulted in an empty Q map.")
            print(f"Base QoS values (T=0) initialized from {self.stq_file_path}.")
        except Exception as e:
            print(f"Failed to read STQ file: {e}")
            # If reading fails after generation, something is wrong.
            raise RuntimeError(f"Could not read STQ file {self.stq_file_path}") from e

    def get_q_value(self, u, v, temperature=0):
        """
        Gets the Q value for a given edge, adjusted for the specified temperature.

        Args:
            u (int): First node of the edge.
            v (int): Second node of the edge.
            temperature (int/float): Temperature for Q value adjustment. Defaults to 0.

        Returns:
            float: The Q value for the edge at the given temperature,
                   or None if the edge is not found in the base map.
        """
        # Get the appropriate Q map (base or adjusted)
        q_map = self.get_all_q_values(temperature=temperature)

        # Ensure consistent key format (u < v)
        if u > v:
            u, v = v, u
        edge_key = (u, v)

        q_val = q_map.get(edge_key)
        # Keep the warning if lookup fails even in the correct map
        if q_val is None:
             # Check if it existed in the base map at all
             if edge_key not in self.base_edge_q_values:
                  print(f"Warning: Edge ({u}, {v}) was not found in the base STQ file.")
             else:
                  # This case shouldn't happen if adjustment logic is correct
                  print(f"Warning: Q value for edge ({u}, {v}) not found after adjustment (T={temperature}).")
        return q_val

    def get_all_q_values(self, temperature=0):
        """
        Returns the dictionary containing all edge Q values, adjusted for temperature.

        Args:
            temperature (int/float): Temperature for Q value adjustment. Defaults to 0.

        Returns:
            dict: A dictionary mapping edge tuples (u, v) to their Q values
                  at the specified temperature. Returns the base map if T=0.
        """
        if temperature == 0:
            # Return the stored base values directly
            return self.base_edge_q_values
        else:
            # Dynamically adjust the base values for the requested temperature
            try:
                # Pass a copy to avoid modifying the base map if adjustment fails midway
                adjusted_map = common.adjust_q_values_by_temperature(self.base_edge_q_values.copy(), temperature)
                return adjusted_map
            except Exception as e:
                print(f"Error adjusting Q values for temperature {temperature}: {e}")
                print("Warning: Returning base Q values (T=0) due to adjustment error.")
                return self.base_edge_q_values
    
    def getQvalueGraph(self, adjusted_map):
        """
        根据 edge Q value map 创建 networkx 无向图。

        Args:
            adjusted_map (dict): 边 Q value map，例如 get_all_q_values() 的返回值。

        Returns:
            nx.Graph: NetworkX 无向图，边 cost 为 Q 值。
        """
        q_graph = nx.Graph()
        for edge, q_value in adjusted_map.items():
            u, v = edge
            q_graph.add_edge(u, v, cost=q_value)  # 使用 'cost' 属性存储 Q 值
        return q_graph

# --- End of New QoS Functionality ---


# check solution with database, edges is the SMT edges
#return valid
def check_solution_with_database(nodes, edges, terminals):
    """
    使用基于路径Q值和BPDATA数据库的方法验证解。
    仅适用于包含11个终端的情况。

    Args:
        nodes (list): SMT 中的节点列表 (当前未使用，但保留签名一致性).
        edges (list): SMT 中的边列表 [(u, v, cost), ...].
        terminals (list): 终端节点列表.

    Returns:
        bool: 如果解满足数据库约束 (valid)，返回 True，否则返回 False.
               如果终端数量不是11，或者路径查找/Q值获取失败，也返回 False。
    """
    #global g_QureyEdgeQValues_map# readonly, no change # Ensure access to global and imported module

    # 1. 检查终端数量是否为 11 (1 root + 10 others)
    if len(terminals) != 11:
        print(f"Warning: check_solution_with_database only supports 11 terminals. Found {len(terminals)}. Skipping check.")
        # 或者根据需求返回 True 或 False，这里假设不满足条件则无效
        return False # Or True if non-11 terminal cases should pass by default
        
    if common.g_QureyEdgeQValues_map is None:
        print("Error: g_QureyEdgeQValues_map is not initialized. Cannot check solution.")
        return False
    
    sm_tree,newkeystrings=common.build_smt_pk_array(edges,terminals,0)

    if len(sm_tree)!=10:
        print("Error: Build smt pk array fail.")
        return False

    # 5. 根据 g_SimpleCheck 调用相应的验证函数
    try:
        if g_SimpleCheck == 1:
            # 使用简化的检查逻辑
            check_result = BPDATA.checkValidLinkSimplified(sm_tree)
            if common.g_LoggerAdapter:
                common.g_LoggerAdapter.info(f"BPDATA.checkValidLinkSimplified result for SMTree {sm_tree}: {check_result}")
            else:
                print(f"BPDATA.checkValidLinkSimplified result for SMTree {sm_tree}: {check_result}")
            # checkValidLinkSimplified returns 1 for invalid, -1 for valid
            is_valid = (check_result == -1)
        else:
            # 使用原始的基于数据库的检查逻辑
            check_result = BPDATA.checkValidLink(sm_tree)
            if common.g_LoggerAdapter:
                common.g_LoggerAdapter.info(f"BPDATA.checkValidLink result for SMTree {sm_tree}: {check_result}")
            else:
                print(f"BPDATA.checkValidLink result for SMTree {sm_tree}: {check_result}")
            # checkValidLink returns <= 0 for valid, > 0 for invalid
            is_valid = (check_result <= 0)

        return is_valid
    except AttributeError as e:
        # 更具体的错误信息
        if 'checkValidLinkSimplified' in str(e) and g_SimpleCheck == 1:
             print("Error: 'BPDATA' module or 'checkValidLinkSimplified' function not available.")
        elif 'checkValidLink' in str(e) and g_SimpleCheck != 1:
             print("Error: 'BPDATA' module or 'checkValidLink' function not available.")
        else:
             print(f"Error: Missing function in BPDATA module: {e}")
        return False
    except Exception as e:
        print(f"Error calling BPDATA check function: {e}") # Generic error message
        return False

# --- SCIP-Jack Integration ---

# current Scip-jack setup path (Make sure these paths are correct for your system)
curBinDir='/home/bill/Documents/VScode/newplan/researchplan/'
theSCIJackCfgpath=curBinDir+'SteinerTreeWithConstrains/STP/settings/writelogo.set'
theSCIJackpath=curBinDir+'SteinerTreeWithConstrains/STP/bin/stp'

##
# dirpath + inputfile is the input stp file path but without extension '.stp'
# the output file have same name as inputfile but with extension '.stplog'
def callSCIPJack(dirpath, inputfile_no_ext):
    """Calls the SCIP-Jack solver using the command line."""
    problemfilename = inputfile_no_ext + ".stp"
    outputfilename = inputfile_no_ext + ".stplog" # SCIP-Jack output
    # SCIP-Jack reads from the input file specified in the config,
    # but we need the output path for the command line argument.
    # Let's assume the config points to the correct input file or SCIP-Jack takes it implicitly.
    # The command structure provided seems to only specify the output file path.
    # We might need to adjust how SCIP-Jack is called if it requires the input path explicitly.
    # For now, following the provided structure:
    outputstppath = os.path.join(dirpath, outputfilename)
    inputstppath = os.path.join(dirpath, problemfilename)
    # Ensure the output directory exists
    os.makedirs(dirpath, exist_ok=True)

    # Construct the command string
    # IMPORTANT: Ensure theSCIJackpath and theSCIJackCfgpath are correct and executable.
    # The provided command uses -f for the *output* file, which seems unusual.
    # Typically, -f might be for the input file. Double-check SCIP-Jack documentation.
    # Assuming the provided command is correct for now:
    # It seems SCIP-Jack reads the problem from the file specified in the .set file's 'problem filename' parameter.
    # We need to ensure the .set file points to the correct iteration's .stp file.
    # This is complex to manage dynamically by modifying the .set file.
    # A common pattern for command-line tools is to accept the input file directly
    # Without knowing SCIP-Jack's exact CLI, we'll stick to the user's provided command format,
    # but add a HUGE CAVEAT that the .set file MUST point to the correct input file for this to work.
    # A better approach would be to confirm SCIP-Jack's CLI or use a wrapper that handles the config.
    print(f"WARNING: Assuming SCIP-Jack config '{theSCIJackCfgpath}' correctly points to the input file '{os.path.join(dirpath, problemfilename)}'.")
    # 构建命令列表，避免 shell=True
    command_list = [
        theSCIJackpath,
        '-q',
        '-s', theSCIJackCfgpath,
        '-f', inputstppath,
        #'-l', outputstppath #the output file will be automatically created by scip-jack,so no need this option
    ]

    print(f"Executing SCIP-Jack: {' '.join(command_list)}") # 打印命令以便查看
    start_time = time.time()
    try:
        # 使用 subprocess.run
        result = subprocess.run(
            command_list,
            capture_output=True, # 捕获 stdout 和 stderr
            text=True,           # 将输出解码为文本
            check=False          # 不要在返回码非零时自动抛出异常，手动处理
        )
        end_time = time.time()
        solve_time = end_time - start_time
        return_code = result.returncode

        print(f"SCIP-Jack finished with return code: {return_code} in {solve_time:.4f} seconds.")
        # 打印 stdout 和 stderr 以便调试 (可以根据需要移除或设为条件打印)
        # print("SCIP-Jack stdout:\n", result.stdout)
        # print("SCIP-Jack stderr:\n", result.stderr)

        # 检查返回码和输出文件
        if return_code != 0:
            print(f"Warning: SCIP-Jack failed with return code {return_code}.")
            print("SCIP-Jack stderr:")
            print(result.stderr) # 打印错误信息
            # 即使失败，也检查文件是否存在，因为有时即使出错也可能创建部分文件
            if not os.path.exists(outputstppath):
                 print(f"Warning: SCIP-Jack output file not found: {outputstppath}")
            return None, solve_time # 指示失败

        # 如果返回码为 0，仍然检查文件是否存在（以防万一）
        if not os.path.exists(outputstppath):
             print(f"Warning: SCIP-Jack finished successfully (Code: 0) but output file not found: {outputstppath}")
             # 打印 stdout/stderr 帮助诊断
             print("SCIP-Jack stdout:\n", result.stdout)
             print("SCIP-Jack stderr:\n", result.stderr)
             return None, solve_time # 指示失败

        # 可选：如果需要，添加小的延迟
        time.sleep(0.1)

        return outputstppath, solve_time # 返回输出文件路径和时间

    except FileNotFoundError:
        end_time = time.time()
        solve_time = end_time - start_time
        print(f"Error: SCIP-Jack executable not found at '{theSCIJackpath}'. Please check the path.")
        return None, solve_time
    except Exception as e:
        end_time = time.time()
        solve_time = end_time - start_time
        print(f"An unexpected error occurred while running SCIP-Jack: {e}")
        return None, solve_time



# got stp solution by gurobi, and check database for valid solution
def solve_stp_flow_balance(nodes, edges, terminals, time_limit=None,logger=None):
    """
    使用 Gurobi 和 Flow Balance Directed Cut Formulation 解决 STP.

    Args:
        nodes (list): 图中所有节点的列表.
        edges (dict): 边字典 {(u, v): cost} (其中 u < v).
        terminals (list): 终端节点列表.
        time_limit (float, optional): Gurobi 求解时间限制 (秒). Defaults to None.

    Returns:
        tuple: (status, selected_edges, objective_value, model, solve_time)
               status: Gurobi 优化状态 (e.g., GRB.OPTIMAL)
               selected_edges: 构成 SMT 的边列表 [(u, v, cost), ...]
               objective_value: SMT 的总成本
               model: Gurobi model object
               solve_time: Time taken by Gurobi optimize() call
    """
    # Define a variable to store SMT PK values from the callback
    global gurobi_smt_pk_values
    gurobi_smt_pk_values = None # Initialize before optimization

    if not terminals:
        logger.info("Error: No terminals provided.")
        return GRB.INFEASIBLE, [], float('inf'), None, 0.0
    if len(terminals) == 1:
        logger.info("Warning: Only one terminal. The Steiner tree is just the terminal itself.")
        # Need to create a dummy model object to return for consistency
        model = gp.Model()
        return GRB.OPTIMAL, [], 0.0, model, 0.0

    # 选择根节点
    root = terminals[0]
    non_root_terminals = [t for t in terminals if t != root]
    num_sinks = len(non_root_terminals)

    # Handle case where root is the only terminal after filtering
    if num_sinks == 0 and len(terminals) == 1 :
         model = gp.Model()
         return GRB.OPTIMAL, [], 0.0, model, 0.0

    logger.info(f"Root selected: {root}")
    logger.info(f"Non-root terminals (sinks): {non_root_terminals}")
    logger.info(f"Number of sinks: {num_sinks}")

    # 创建 Gurobi 模型
    model = gp.Model("SteinerTree_FlowBalance")
    model.setParam('LogToConsole', 0)
    model.setParam('LogFile', 'gurobi_log.log')

    # --- 变量定义 ---
    # 1. 边选择变量 (二元)
    x = {}
    for u, v in edges:
        x[u, v] = model.addVar(vtype=GRB.BINARY, name=f"x_{u}_{v}")

    # 2. 流变量 (非负连续)
    f = {}
    # 需要为每个无向边 {u, v} 创建两个有向流变量 f[u,v] 和 f[v,u]
    for u_orig, v_orig in edges:
        # 确保索引一致性，即使原始边是 (u,v) 且 u<v
        # 我们需要 f(u,v) 和 f(v,u)
        f[u_orig, v_orig] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"f_{u_orig}_{v_orig}")
        f[v_orig, u_orig] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"f_{v_orig}_{u_orig}")

    # --- 目标函数 ---
    model.setObjective(gp.quicksum(cost * x[u, v] for (u, v), cost in edges.items()), GRB.MINIMIZE)

    # --- 约束条件 ---
    # 1. 流守恒约束
    for k in nodes:
        # 计算流入 k 的总流量: sum(f[j, k] for j where edge {j,k} exists)
        in_flow = gp.LinExpr()
        # 计算流出 k 的总流量: sum(f[k, j] for j where edge {k,j} exists)
        out_flow = gp.LinExpr()

        # 遍历所有与 k 相连的边 {i, k}
        for i_node in nodes:
            if i_node == k: continue # 避免自环 (虽然通常STP输入不包含)

            # 检查边是否存在 (需要考虑两种顺序)
            edge_key = (min(i_node, k), max(i_node, k))
            if edge_key in edges:
                # f[i, k] 是流入 k 的
                if (i_node, k) in f:
                    in_flow += f[i_node, k]
                # No need for elif, f should contain both directions if edge exists

                # f[k, i] 是流出 k 的
                if (k, i_node) in f:
                    out_flow += f[k, i_node]


        # 设置约束
        if k == root:
            # 源节点: 流出 - 流入 = num_sinks
            model.addConstr(out_flow - in_flow == num_sinks, name=f"flow_balance_{k}_root")
        elif k in non_root_terminals:
            # 汇节点: 流出 - 流入 = -1
            model.addConstr(out_flow - in_flow == -1, name=f"flow_balance_{k}_sink")
        else:
            # 非终端节点: 流出 - 流入 = 0
            model.addConstr(out_flow - in_flow == 0, name=f"flow_balance_{k}_steiner")

    # 2. 流容量约束 (关联流与边选择)
    for u, v in edges: # 这里的 key 已经是 u < v
        # f[u, v] <= num_sinks * x[u, v]
        if (u,v) in f:
            model.addConstr(f[u, v] <= num_sinks * x[u, v], name=f"capacity_{u}_{v}")
        # f[v, u] <= num_sinks * x[u, v] (注意这里还是 x[u,v])
        if (v,u) in f:
            model.addConstr(f[v, u] <= num_sinks * x[u, v], name=f"capacity_{v}_{u}")


    # 设置时间限制 (如果提供)
    if time_limit:
        model.setParam(GRB.Param.TimeLimit, time_limit)

    # --- 创建回调函数 (定义在内部以访问 terminals) ---
    def check_solution_callback(model, where):
        if where == GRB.Callback.MIPSOL:
            # 提取当前解的边
            selected_edges_result = []
            # Need to access 'x' variables defined in the outer scope
            # current_x = model.cbGetSolution(x) # Get all solution variables - might be slow
            for u_cb, v_cb in edges: # Iterate through original edge keys
                try:
                    # Access the specific variable for the edge
                    if model.cbGetSolution(x[u_cb, v_cb]) > 0.5:
                         selected_edges_result.append((u_cb, v_cb, edges[(u_cb, v_cb)]))
                except gp.GurobiError as e_cb:
                     # Handle cases where variable might not be available in callback solution
                     # print(f"Callback Warning: Could not get solution value for x_{u_cb}_{v_cb}: {e_cb}")
                     pass # Ignore if variable not found in this solution


            # 检查解是否满足数据库约束 (使用新的函数和传递 terminals)
            # Need access to 'nodes' and 'terminals' from the outer scope
            # Also need the full nodes list for check_solution_with_database
            if selected_edges_result: # Only check if we found some edges
                is_valid = check_solution_with_database(nodes, selected_edges_result, terminals)
                if not is_valid:
                    logger.info("Solution does not satisfy database constraints (via Q-value check). Adding lazy constraint.")                                       
                    # 添加 lazy constraint 排除当前解
                    # Ensure 'x' is accessible here as well
                    lazy_constraint_lhs = gp.LinExpr()
                    edges_in_solution_keys = set()
                    for u_lazy, v_lazy, cost_lazy in selected_edges_result:
                         edge_key_lazy = tuple(sorted((u_lazy, v_lazy))) # Use the key format used in 'x'
                         if edge_key_lazy in x: # Check if the variable exists
                             lazy_constraint_lhs += x[edge_key_lazy]
                             edges_in_solution_keys.add(edge_key_lazy)

                    # The constraint ensures at least one edge from the invalid solution is removed
                    if edges_in_solution_keys: # Only add if there are edges to constrain
                         model.cbLazy(lazy_constraint_lhs <= len(edges_in_solution_keys) - 1)
                    else:
                         # This case means selected_edges_result had edges, but none matched keys in x? Error.
                         logger.info("Warning: No valid edge variables found in the current infeasible solution to build a lazy constraint.")
            # else: No edges selected in this callback solution, nothing to check/constrain


    # 3. 设置回调函数
    model.Params.lazyConstraints = 1


    # --- 求解模型 ---
    solve_time = 0.0
    try:
        start_time = time.time()
        model.optimize(check_solution_callback) # Use the nested callback
        end_time = time.time()
        solve_time = end_time - start_time
        logger.info(f"Gurobi optimization finished in {solve_time:.4f} seconds.")
    except gp.GurobiError as e:
        logger.info(f"Gurobi error during optimization: {e}")
        # 即使出错，也返回当前状态和模型
        return model.Status, [], float('inf'), model, solve_time


    # --- 提取结果 ---
    selected_edges_result = []
    objective_value_result = float('inf')
    status = model.Status

    if status == GRB.OPTIMAL or (status == GRB.TIME_LIMIT and model.SolCount > 0):
        if status == GRB.TIME_LIMIT:
            logger.info("Warning: Time limit reached, solution may not be optimal.")
        logger.info(f"Solution found (Status: {status}).")
        # 确保目标值是可用的
        if model.SolCount > 0:
            objective_value_result = model.ObjVal
            logger.info(f"Objective (Total Cost): {objective_value_result}")
            for u, v in edges:
                # 使用 try-except 避免在无解时访问 X 属性出错
                try:
                    if x[u, v].X > 0.5:
                        selected_edges_result.append((u, v, edges[(u, v)]))
                except gp.GurobiError: # 如果变量 X 不可用
                    pass # 保持 selected_edges_result 为空
                except AttributeError: # If model has no solution (e.g., time limit before first sol)
                    pass
        else: # 例如时间限制在找到任何解之前到达
            logger.info("Warning: Solver status indicates a solution might exist, but SolCount is 0.")

        return status, selected_edges_result, objective_value_result, model, solve_time

    elif status == GRB.INFEASIBLE:
        logger.info("Model is infeasible. Check constraints or input graph.")
        # 可能需要导出 .lp 文件进行调试
        # model.write("debug_infeasible_stp.lp")
        return status, [], float('inf'), model, solve_time
    elif status == GRB.UNBOUNDED:
        logger.info("Model is unbounded. This shouldn't happen for STP.")
        return status, [], float('inf'), model, solve_time
    else:
        logger.info(f"Optimization ended with status code: {status}")
        # Try to get objective value even if status is not optimal (e.g., interrupted)
        obj_val = float('inf')
        if model.SolCount > 0:
            try: obj_val = model.ObjVal
            except: pass
        return status, [], obj_val, model, solve_time


def solve_stp_scipjack_iterative(initial_nodes, initial_edges_dict, initial_terminals, base_filename_no_ext, output_dir):
    """
    Solves STP using SCIP-Jack iteratively, removing edges from invalid solutions.
    Includes logic to save the log of the iteration *before* disconnection occurs.

    Args:
        initial_nodes (list): Initial list of all nodes in the graph.
        initial_edges_dict (dict): Initial dictionary of edges {(u, v): cost}.
        initial_terminals (list): List of terminal nodes.
        base_filename_no_ext (str): Base name for input/output files (without extension).
        output_dir (str): Directory to store intermediate and final files.

    Returns:
        tuple: (status, final_smt_edges_with_cost, final_objective, total_solve_time)
               status: 'OPTIMAL', 'INFEASIBLE', 'ERROR', 'ITERATION_LIMIT'
               final_smt_edges_with_cost: List [(u, v, cost), ...] or None
               final_objective: Cost of the solution or float('inf')
               total_solve_time: Accumulated time across SCIP-Jack calls.
    """
    print("\n--- Starting SCIP-Jack Iterative Solver ---")
    current_nodes = list(initial_nodes) # Copy initial state
    current_edges_dict = initial_edges_dict.copy()
    current_terminals = list(initial_terminals)
    current_filename_no_ext = base_filename_no_ext
    iteration = 0
    max_iterations = SCIPJACKMAXITERATION # Safety limit to prevent infinite loops
    total_solve_time = 0.0
    removed_edges_history = set() # Keep track of edges removed across iterations

    # --- State for saving the best log before failure ---
    last_successful_stplogo_path = None # Track the log file of the last successful iteration
    copied_best_log = False # Flag to ensure we only copy once
    target_best_log_path = os.path.join(output_dir, base_filename_no_ext + "_final_used.stplog")
    # --- End state ---

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    while iteration < max_iterations:
        print(f"\nIteration {iteration + 1}/{max_iterations}")
        iteration_input_stp_path = os.path.join(output_dir, current_filename_no_ext + ".stp")

        # 1. Write the current problem state to a .stp file
        print(f"Writing current problem to: {iteration_input_stp_path}")
        try:
            # Reconstruct nodes list based on current edges and terminals for accuracy
            nodes_for_current_stp = set(current_terminals)
            for u, v in current_edges_dict:
                nodes_for_current_stp.add(u)
                nodes_for_current_stp.add(v)
            # Convert edges dict to list format for write_stp_file_generic
            edges_list_for_current_stp = [(u, v, cost) for (u, v), cost in current_edges_dict.items()]
            common.write_stp_file_generic(iteration_input_stp_path, list(nodes_for_current_stp), edges_list_for_current_stp, current_terminals, comment=f"Iteration {iteration + 1}")

        except Exception as e:
            print(f"Error writing STP file for iteration {iteration + 1}: {e}")
            # --- Copy log from last success if error occurs during write ---
            if not copied_best_log and last_successful_stplogo_path:
                 common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
                 copied_best_log = True
            # --- End copy log ---
            return 'ERROR', None, float('inf'), total_solve_time

        # 2. Call SCIP-Jack to solve the current .stp file
        print(f"INFO: Ensure SCIP-Jack config '{theSCIJackCfgpath}' reads from '{iteration_input_stp_path}' before proceeding.")
        stplogo_output_path, solve_time = callSCIPJack(output_dir, current_filename_no_ext)
        total_solve_time += solve_time

        if stplogo_output_path is None:
            print("SCIP-Jack failed to produce an output file or execution failed. Assuming infeasible or error.")
            # --- Copy log from last success ---
            if not copied_best_log and last_successful_stplogo_path:
                common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
                copied_best_log = True
            # --- End copy log ---
            # Check if the graph was potentially disconnected *before* calling SCIP-Jack
            if not common.is_graph_still_connected(initial_nodes, current_edges_dict, current_terminals): # Use initial_nodes for full check
                 print("Input graph for this iteration was already disconnected.")
                 return 'INFEASIBLE', None, float('inf'), total_solve_time
            else:
                 # SCIP-Jack itself might have determined infeasibility
                 print("Assuming SCIP-Jack determined infeasibility.")
                 return 'INFEASIBLE', None, float('inf'), total_solve_time

        # 3. Parse the SCIP-Jack output (.stplog)
        # --- Update last successful log path *before* parsing ---
        # This ensures we have the path even if parsing fails or solution is invalid
        last_successful_stplogo_path = stplogo_output_path
        # --- End update ---
        smt_edges_no_cost, objective_value_from_log, smt_nodes = common.parse_stplogo_file(stplogo_output_path)

        if smt_edges_no_cost is None:
            print("Failed to parse SCIP-Jack solution or no solution found in log. Assuming infeasible.")
            # --- Copy log from last success (which is the one we just failed to parse) ---
            if not copied_best_log and last_successful_stplogo_path:
                 common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
                 copied_best_log = True
            # --- End copy log ---
            # It's possible SCIP-Jack ran but found no solution
            return 'INFEASIBLE', None, float('inf'), total_solve_time

        # Reconstruct SMT edges with costs from the *current* problem definition
        smt_edges_with_cost = []
        calculated_smt_cost = 0.0
        valid_solution_edges = True
        for u, v in smt_edges_no_cost:
            edge_key = tuple(sorted((u, v)))
            if edge_key in current_edges_dict:
                cost = current_edges_dict[edge_key]
                smt_edges_with_cost.append((edge_key[0], edge_key[1], cost))
                calculated_smt_cost += cost
            else:
                # This case should ideally not happen if SCIP-Jack respects the input file
                print(f"Error: Edge {edge_key} from SCIP-Jack solution not found in current problem definition ({iteration_input_stp_path})!")
                valid_solution_edges = False
                break

        if not valid_solution_edges:
             # --- Copy log from last success (which produced the invalid edge) ---
             if not copied_best_log and last_successful_stplogo_path:
                  common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
                  copied_best_log = True
             # --- End copy log ---
             return 'ERROR', None, float('inf'), total_solve_time

        # Use the objective value from the log file if available, otherwise use recalculated cost
        final_objective_value = objective_value_from_log if objective_value_from_log != float('inf') else calculated_smt_cost
        print(f"SCIP-Jack found solution. Edges: {len(smt_edges_with_cost)}. Cost (from log/recalculated): {final_objective_value:.2f}.")

        # 3.5 Check connectivity of the *solution* graph itself
        if not common.is_graph_still_connected(list(smt_nodes), {tuple(sorted((u,v))): cost for u,v,cost in smt_edges_with_cost}, current_terminals):
            print(f"SCIP-Jack solution in iteration {iteration + 1} is DISCONNECTED. Stopping.")
            # --- Copy log from this iteration (as it produced the disconnected result) ---
            if not copied_best_log and last_successful_stplogo_path: # last_successful_stplogo_path holds the path for this iteration now
                common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
                copied_best_log = True
            # --- End copy log ---
            return 'INFEASIBLE', None, float('inf'), total_solve_time # Treat disconnected solution as infeasible


        # 4. Check the validity of the SMT solution using the database/QoS logic
        if common.g_QureyEdgeQValues_map is None:
             print("Error: g_QureyEdgeQValues_map is not initialized. Cannot validate solution.")
             # --- Copy log from last success ---
             if not copied_best_log and last_successful_stplogo_path:
                  common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
                  copied_best_log = True
             # --- End copy log ---
             return 'ERROR', None, float('inf'), total_solve_time
        if len(current_terminals) != 11:
             print("Warning: Skipping solution validation as terminal count is not 11.")
             is_valid_solution = False # Assume invalid if not 11 terminals
        else:
             is_valid_solution = check_solution_with_database(list(smt_nodes), smt_edges_with_cost, current_terminals)

        if is_valid_solution:
            print(f"Solution found in iteration {iteration + 1} is VALID.")
            # Copy the final valid STP and STPLOGO files for clarity
            final_stp_path = os.path.join(output_dir, base_filename_no_ext + "_scipjack_final.stp")
            final_stplogo_path = os.path.join(output_dir, base_filename_no_ext + "_scipjack_final.stplog")
            try:
                # Source files for copy might have iteration number, use the latest ones
                latest_iter_stp = iteration_input_stp_path
                latest_iter_stplogo = stplogo_output_path # This is the log of the valid solution
                shutil.copy(latest_iter_stp, final_stp_path)
                shutil.copy(latest_iter_stplogo, final_stplogo_path)
                print(f"Final valid STP saved to: {final_stp_path}")
                print(f"Final valid STPLOGO saved to: {final_stplogo_path}")
            except Exception as e:
                print(f"Warning: Could not copy final output files: {e}")

            return 'OPTIMAL', smt_edges_with_cost, final_objective_value, total_solve_time
        else:
            # --- Solution is Invalid ---
            print(f"Solution found in iteration {iteration + 1} is INVALID (QoS check failed). Identifying edge to remove.")

            # 5. Identify the edge to remove from the invalid SMT based on selected algorithm
            if remove_Edge_alg_select == 0:
                print("Using original algorithm (worst path, connectivity prioritized) for edge removal.")
                edge_to_remove_details = rmAlg.find_edge_to_remove_from_invalid_smt_alg0(list(smt_nodes), smt_edges_with_cost, current_terminals, current_edges_dict)
            elif remove_Edge_alg_select == 1:
                print("Using alternative algorithm (max cost unique edge, connectivity prioritized) for edge removal.") # Already prioritized connectivity
                edge_to_remove_details = rmAlg.find_edge_to_remove_from_invalid_smt_alg1(list(smt_nodes), smt_edges_with_cost, current_terminals, current_edges_dict)
            elif remove_Edge_alg_select == 2:
                print("Using alternative algorithm (PK values higher than the middle worst paths) for edge removal.") # Already prioritized connectivity
                edge_to_remove_details = rmAlg.find_edge_to_remove_from_invalid_smt_alg2(list(smt_nodes), smt_edges_with_cost, current_terminals, current_edges_dict)
            elif remove_Edge_alg_select == 3:
                print("Using alternative algorithm (comprehensive scoring system) for edge removal.")
                edge_to_remove_details = rmAlg.find_edge_to_remove_from_invalid_smt_alg3(list(smt_nodes), smt_edges_with_cost, current_terminals, current_edges_dict)

            if edge_to_remove_details is None:
                print("Could not identify a unique edge to remove based on selected algorithm criteria. Stopping.")
                # --- Copy log from last success (which produced the invalid solution) ---
                if not copied_best_log and last_successful_stplogo_path:
                     common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
                     copied_best_log = True
                # --- End copy log ---
                return 'ERROR', None, float('inf'), total_solve_time

            edge_key_to_remove = tuple(sorted((edge_to_remove_details[0], edge_to_remove_details[1])))
            print(f"Identified edge to remove: {edge_key_to_remove} with cost {edge_to_remove_details[2]}")

            # Check if this edge was already removed (should not happen with current logic, but good check)
            if edge_key_to_remove in removed_edges_history:
                 print(f"Warning: Edge {edge_key_to_remove} was already removed. Cycle detected or logic issue. Stopping.")
                 # --- Copy log from last success ---
                 if not copied_best_log and last_successful_stplogo_path:
                      common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
                      copied_best_log = True
                 # --- End copy log ---
                 return 'ERROR', None, float('inf'), total_solve_time

            # 6. Create the new problem definition by removing the edge
            new_edges_dict = current_edges_dict.copy()
            if edge_key_to_remove in new_edges_dict:
                del new_edges_dict[edge_key_to_remove]
                removed_edges_history.add(edge_key_to_remove)
                print(f"Removed edge {edge_key_to_remove}. New edge count: {len(new_edges_dict)}")
            else:
                # This indicates a logic error somewhere
                print(f"Error: Edge {edge_key_to_remove} identified for removal not found in current edge dict. Stopping.")
                # --- Copy log from last success ---
                if not copied_best_log and last_successful_stplogo_path:
                     common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
                     copied_best_log = True
                # --- End copy log ---
                return 'ERROR', None, float('inf'), total_solve_time

            # 7. Check connectivity of the graph *after* removing the edge
            # Use the original full node list for connectivity check, as some nodes might become isolated
            if not common.is_graph_still_connected(initial_nodes, new_edges_dict, current_terminals):
                print(f"Removing edge {edge_key_to_remove} disconnects terminals. Problem declared infeasible.")
                # --- Copy log from last success (before removal caused disconnect) ---
                if not copied_best_log and last_successful_stplogo_path:
                    common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
                    copied_best_log = True
                # --- End copy log ---
                return 'INFEASIBLE', None, float('inf'), total_solve_time

            # 8. Prepare for the next iteration
            current_edges_dict = new_edges_dict
            current_filename_no_ext = f"{base_filename_no_ext}_iter{iteration + 1}"
            # Nodes list for the *next* STP file generation should reflect reachable nodes
            # Terminals remain the same

        iteration += 1
        # Clean up intermediate files? Optional.
        # if os.path.exists(iteration_input_stp_path): os.remove(iteration_input_stp_path)
        # if os.path.exists(stplogo_output_path): os.remove(stplogo_output_path)


    print(f"Reached maximum iterations ({max_iterations}) without finding a valid solution.")
    # --- Copy log from last success ---
    if not copied_best_log and last_successful_stplogo_path:
         common.copy_log_section(last_successful_stplogo_path, target_best_log_path)
         copied_best_log = True
    # --- End copy log ---
    return 'ITERATION_LIMIT', None, float('inf'), total_solve_time


# --- NEW VCF Iterative Solver (Corrected) ---
def solve_stp_scipjack_VCF_iterative(initial_nodes, initial_edges_dict, initial_terminals, base_filename_no_ext, output_dir):
    """
    Solves the STP using SCIP-Jack iteratively with Validation Check Firstly (VCF) approach.
    1. Uses Q values as costs to generate and solve a new STPG problem with SCIP-Jack.
    2. Validates the resulting SMT using check_solution_with_database.
    3. If valid, stores the solution with its *original* cost.
    4. Removes the edge with the *smallest Q value* from the current SMT solution graph.
    5. Repeats steps 1-4 with the reduced graph until no solution is found or max iterations are reached.
    6. Returns the stored valid solution with the minimum *original* cost.

    Args:
        initial_nodes (list): Initial list of all nodes in the graph.
        initial_edges_dict (dict): Initial dictionary of edges {(u, v): original_cost}.
        initial_terminals (list): List of terminal nodes.
        base_filename_no_ext (str): Base name for input/output files (without extension).
        output_dir (str): Directory to store intermediate and final files.

    Returns:
        tuple: (status, final_smt_edges_with_original_cost, final_original_objective, total_solve_time)
               status: 'OPTIMAL', 'INFEASIBLE', 'ERROR', 'ITERATION_LIMIT'
               final_smt_edges_with_original_cost: List [(u, v, original_cost), ...] or None
               final_original_objective: Minimum original cost of the valid solutions or float('inf')
               total_solve_time: Accumulated time across SCIP-Jack calls.
    """
    print("\n--- Starting SCIP-Jack VCF Iterative Solver ---")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Ensure Q values are initialized
    if common.g_QureyEdgeQValues_map is None:
        print("Error: Q values map (common.g_QureyEdgeQValues_map) is not initialized. Cannot proceed with VCF iterative solver.")
        return 'ERROR', None, float('inf'), 0.0

    # Check terminal count for validation compatibility
    # Allow proceeding even if not 11, but validation will be skipped/fail.
    if len(initial_terminals) != 11:
        print(f"Warning: VCF solver validation (check_solution_with_database) requires 11 terminals. Found {len(initial_terminals)}. Validation will likely fail or be skipped.")

    current_edges_dict = initial_edges_dict.copy() # Stores edges with ORIGINAL costs, but gets reduced
    current_nodes_list = list(initial_nodes) # Keep track of nodes potentially involved
    terminals = list(initial_terminals)
    feasible_solutions = []  # Stores valid solutions: {'iteration': i, 'original_cost': c, 'edges': [(u,v,cost),...], 'nodes': set(...)}
    iteration = 0
    max_iterations = SCIPJACKMAXITERATION  # Use existing global limit
    total_solve_time = 0.0
    removed_edges_history = set() # Keep track of edges removed (using original edge keys)

    # Log file setup
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    iterative_log_filename = os.path.join(output_dir, f"{base_filename_no_ext}_VCF_iterative_{timestamp}.log")
    summary_log_filename = os.path.join(output_dir, f"{base_filename_no_ext}_VCF_summary_{timestamp}.log")

    try:
        with open(iterative_log_filename, 'w') as iterative_log_file, open(summary_log_filename, 'w') as summary_log_file:
            iterative_log_file.write(f"Iterative SCIP-Jack VCF Solver Log for {base_filename_no_ext}\nStarted at {timestamp}\n\n")
            summary_log_file.write(f"Summary Log for Iterative SCIP-Jack VCF Solver on {base_filename_no_ext}\nStarted at {timestamp}\nMax Iterations: {max_iterations}\n\n")
            summary_log_file.write("Iter | Q-Cost (SCIP) | Valid? | Orig. Cost | Edge Removed (Q-Val) | Status\n")
            summary_log_file.write("-" * 90 + "\n")

            while iteration < max_iterations:
                iteration += 1
                if common.g_LoggerAdapter:
                    common.g_LoggerAdapter.info(f"Starting VCF Iteration {iteration}")
                print(f"\n--- VCF Iteration {iteration}/{max_iterations} ---")
                iterative_log_file.write(f"\n--- VCF Iteration {iteration} ---\n")
                iterative_log_file.write(f"Current edge count: {len(current_edges_dict)}\n")

                # 1. Create Q-based edge list for this iteration's STP problem
                q_based_edges_list_for_stp = []
                current_stp_nodes = set(terminals)
                q_value_lookup_this_iter = {} # Store Q values for edges in this iteration's graph
                for edge_key, original_cost in current_edges_dict.items():
                    u, v = edge_key
                    q_value = common.g_QureyEdgeQValues_map.get(edge_key)
                    
                    if q_value is None:
                        print(f"Warning: Q value not found for edge {edge_key} in global map. Skipping edge for this iteration.")
                        iterative_log_file.write(f"Warning: Q value not found for edge {edge_key}. Skipping.\n")
                        continue
                    #else:
                    #    iterative_log_file.write(f"Q value for edge {edge_key}:{q_value}.\n")
                    
                    # Use Q value as cost for the STP solver
                    q_based_edges_list_for_stp.append((u, v, q_value))
                    q_value_lookup_this_iter[edge_key] = q_value # Keep track for validation step
                    current_stp_nodes.add(u)
                    current_stp_nodes.add(v)

                if not q_based_edges_list_for_stp:
                     print("Error: No edges with Q values available for this iteration. Stopping.")
                     iterative_log_file.write("Error: No edges with Q values available. Stopping.\n")
                     break # Exit while loop

                # 2. Write the Q-based STP file
                iter_filename_no_ext = f"{base_filename_no_ext}_VCF_iter{iteration}"
                iter_stp_filepath = os.path.join(output_dir, iter_filename_no_ext + ".stp")
                print(f"Writing Q-based STP file: {iter_stp_filepath}")
                iterative_log_file.write(f"Writing Q-based STP: {iter_stp_filepath}\n")
                try:
                    common.write_stp_file_generic(iter_stp_filepath, list(current_stp_nodes), q_based_edges_list_for_stp, terminals, comment=f"VCF Iteration {iteration} (Q-based costs)")
                except Exception as e:
                    print(f"Error writing STP file for VCF iteration {iteration}: {e}")
                    iterative_log_file.write(f"Error writing STP file: {e}\n")
                    return 'ERROR', None, float('inf'), total_solve_time # Fatal error

                # 3. Call SCIP-Jack
                print(f"Calling SCIP-Jack for VCF iteration {iteration}...")
                iterative_log_file.write(f"Calling SCIP-Jack...\n")
                # Corrected: Call SCIPJack and get the log path
                stplogo_output_path, solve_time = callSCIPJack(output_dir, iter_filename_no_ext)
                total_solve_time += solve_time
                iterative_log_file.write(f"SCIP-Jack solve time: {solve_time:.4f}s\n")

                # Check if SCIP-Jack succeeded and returned a path
                if stplogo_output_path is None:
                    print("SCIP-Jack failed or produced no output file. Stopping VCF iterations.")
                    iterative_log_file.write("SCIP-Jack failed or no output file. Stopping.\n")
                    summary_log_file.write(f"{iteration:<4d} | {'N/A':<15} | {'N/A':<6} | {'N/A':<10} | {'N/A':<20} | SCIP FAIL\n")
                    break # Exit while loop

                # 4. Parse SCIP-Jack result from the log file
                print(f"Parsing SCIP-Jack output: {stplogo_output_path}")
                iterative_log_file.write(f"Parsing SCIP-Jack output: {stplogo_output_path}\n")
                # Corrected: Parse the file path returned by callSCIPJack
                smt_edges_no_cost_tuples, objective_value_from_log, smt_nodes_set = common.parse_stplogo_file(stplogo_output_path)

                if smt_edges_no_cost_tuples is None:
                    print("Failed to parse SCIP-Jack solution or no solution found in log. Stopping VCF iterations.")
                    iterative_log_file.write("Parsing failed or no solution in log. Stopping.\n")
                    summary_log_file.write(f"{iteration:<4d} | {'N/A':<15} | {'N/A':<6} | {'N/A':<10} | {'N/A':<20} | PARSE FAIL\n")
                    break # Exit while loop

                # Reconstruct SMT edges with Q-values for validation
                smt_edges_with_q_cost_for_validation = []
                current_q_cost_recalculated = 0.0
                valid_parse = True
                for u_smt, v_smt in smt_edges_no_cost_tuples:
                    edge_key_smt = tuple(sorted((u_smt, v_smt)))
                    q_value = q_value_lookup_this_iter.get(edge_key_smt) # Get Q value used in *this* iteration's solve
                    if q_value is None:
                        # This might happen if SCIP returns an edge not in the input? Unlikely but handle.
                        print(f"Error: Edge {edge_key_smt} from SCIP solution not found in this iteration's Q-map. Critical error.")
                        iterative_log_file.write(f"Error: Edge {edge_key_smt} from SCIP solution not in iter Q-map.\n")
                        valid_parse = False
                        break
                    smt_edges_with_q_cost_for_validation.append((u_smt, v_smt, q_value))
                    current_q_cost_recalculated += q_value

                if not valid_parse:
                     summary_log_file.write(f"{iteration:<4d} | {objective_value_from_log:<15.4f} | {'N/A':<6} | {'N/A':<10} | {'N/A':<20} | Q-MAP ERROR\n")
                     break # Exit while loop

                q_cost_to_log = objective_value_from_log if objective_value_from_log != float('inf') else current_q_cost_recalculated
                print(f"SCIP-Jack found solution. Edges: {len(smt_edges_no_cost_tuples)}. Q-Cost (log/recalc): {q_cost_to_log:.4f}")
                iterative_log_file.write(f"SCIP-Jack solution: {len(smt_edges_no_cost_tuples)} edges. Q-Cost: {q_cost_to_log:.4f}\n")
                iterative_log_file.write(f"SMT Edges (no cost): {smt_edges_no_cost_tuples}\n")
                iterative_log_file.write(f"SMT Nodes: {smt_nodes_set}\n")

                # 5. Validate the solution using database check (requires edges with Q-cost)
                print("Validating solution with database...")
                iterative_log_file.write("Validating solution...\n")
                # Pass the SMT edges with their Q-values as costs for validation
                # Ensure nodes are passed as a list
                is_valid_solution= check_solution_with_database(list(smt_nodes_set), smt_edges_with_q_cost_for_validation, terminals)
                valid_str = "VALID" if is_valid_solution else "INVALID"
                print(f"Validation result: {valid_str}")
                iterative_log_file.write(f"Validation result: {valid_str}\n")

                original_cost_this_solution = float('inf')
                if is_valid_solution:
                    # Calculate original cost and store
                    original_smt_edges = []
                    current_original_cost = 0.0
                    valid_original_cost = True
                    for u_orig, v_orig in smt_edges_no_cost_tuples:
                        edge_key_orig = tuple(sorted((u_orig, v_orig)))
                        cost = initial_edges_dict.get(edge_key_orig) # Get cost from the *initial* full dict
                        if cost is None:
                             print(f"Error: Edge {edge_key_orig} from valid SMT not found in initial_edges_dict. Critical error.")
                             iterative_log_file.write(f"Error: Edge {edge_key_orig} from valid SMT not in initial dict.\n")
                             valid_original_cost = False
                             break
                        original_smt_edges.append((u_orig, v_orig, cost))
                        current_original_cost += cost

                    if valid_original_cost:
                        original_cost_this_solution = current_original_cost
                        print(f"Original cost for this valid solution: {original_cost_this_solution}")
                        iterative_log_file.write(f"Original cost: {original_cost_this_solution}\n")
                        feasible_solutions.append({
                            'iteration': iteration,
                            'original_cost': original_cost_this_solution,
                            'edges': original_smt_edges, # Store edges with original cost
                            'nodes': smt_nodes_set,
                            'q_cost': q_cost_to_log # Store the Q-cost for reference
                        })
                    else:
                         # Handle error case where original cost couldn't be calculated
                         valid_str = "ORIG_COST_ERR"
                         original_cost_this_solution = float('inf')


                # 6. Identify edge with minimum Q value in the *current SMT solution* to remove for next iteration, ensuring it's not a bridge.
                edge_to_remove_key = None
                edge_to_remove_q_val = float('inf')

                if not smt_edges_no_cost_tuples:
                     print("Warning: SMT solution has no edges, cannot remove an edge.")
                     iterative_log_file.write("Warning: SMT has no edges.\n")
                     summary_log_file.write(f"{iteration:<4d} | {q_cost_to_log:<15.4f} | {valid_str:<6} | {original_cost_this_solution:<10.2f} | {'NO EDGES':<20} | OK\n")
                     break

                # Create a list of edges in the current SMT with their Q values, sorted by Q value
                smt_edges_with_q = []
                for u_rem, v_rem in smt_edges_no_cost_tuples:
                    rem_key = tuple(sorted((u_rem, v_rem)))
                    q_val = common.g_QureyEdgeQValues_map.get(rem_key)
                    # Ensure edge exists in the current graph being considered for the *next* iteration
                    if q_val is not None and rem_key in current_edges_dict:
                        smt_edges_with_q.append({'key': rem_key, 'q': q_val})
                    else:
                        if q_val is None:
                            print(f"Debug: Q value not found for SMT edge {rem_key}.")
                            iterative_log_file.write(f"Debug: Q value not found for SMT edge {rem_key}.\n")
                        if rem_key not in current_edges_dict:
                            # This means SCIP returned an edge that was already removed in a previous VCF iteration.
                            # This shouldn't happen if SCIP respects the input STP file. Log it.
                            print(f"Warning: SMT edge {rem_key} (Q={q_val}) from SCIP solution is not in current_edges_dict. Ignoring for removal consideration.")
                            iterative_log_file.write(f"Warning: SMT edge {rem_key} (Q={q_val}) not in current_edges_dict. Ignoring for removal.\n")

                if not smt_edges_with_q:
                    print("Error: No valid edges found in SMT (present in current_edges_dict) to consider for removal. Stopping.")
                    iterative_log_file.write("Error: No valid edges in SMT for removal. Stopping.\n")
                    summary_log_file.write(f"{iteration:<4d} | {q_cost_to_log:<15.4f} | {valid_str:<6} | {original_cost_this_solution:<10.2f} | {'NO VALID EDGES':<20} | STOP\n")
                    break

                smt_edges_with_q.sort(key=lambda x: x['q']) # Sort edges by Q value ascending

                # Iterate through sorted edges to find the first non-bridge edge
                edge_to_remove_key = None
                edge_to_remove_q_val = float('inf')

                # Build the graph *before* removing the candidate edge for connectivity check.
                # This graph represents the state *before* this iteration's removal.
                graph_for_check = nx.Graph()
                # Add edges from the current dictionary (edges available for *this* iteration's solve)
                for edge_key_check, _ in current_edges_dict.items():
                    graph_for_check.add_edge(*edge_key_check)

                # Ensure all terminals are nodes in the graph, even if isolated
                for t in terminals:
                    if not graph_for_check.has_node(t):
                        graph_for_check.add_node(t)

                for edge_info in smt_edges_with_q:
                    candidate_key = edge_info['key']
                    candidate_q = edge_info['q']

                    # Check if the candidate edge exists in the graph built for check
                    # This check should always pass now due to the filtering when building smt_edges_with_q
                    if not graph_for_check.has_edge(*candidate_key):
                         print(f"Internal Warning: Candidate edge {candidate_key} for removal not found in the graph built for connectivity check, though it should be. Skipping.")
                         iterative_log_file.write(f"Internal Warning: Candidate edge {candidate_key} not in connectivity check graph. Skipping.\n")
                         continue

                    # Temporarily remove the edge to check for bridges affecting terminal connectivity
                    graph_for_check.remove_edge(*candidate_key)

                    is_still_connected = True
                    if len(terminals) > 1:
                        try:
                            # Check if all terminals are still in the same connected component
                            first_terminal = terminals[0]
                            # Ensure first_terminal is actually in the graph after potential removals
                            if graph_for_check.has_node(first_terminal):
                                reachable_nodes = nx.node_connected_component(graph_for_check, first_terminal)
                                for t in terminals[1:]:
                                    # Ensure the terminal exists in the graph before checking reachability
                                    if not graph_for_check.has_node(t) or t not in reachable_nodes:
                                        is_still_connected = False
                                        break
                            else:
                                # If the first terminal itself is not in the graph (e.g., isolated and removed edge connected it)
                                # then terminals are disconnected.
                                print(f"Warning: First terminal {first_terminal} no longer in graph after removing {candidate_key}. Terminals disconnected.")
                                iterative_log_file.write(f"Warning: First terminal {first_terminal} not in graph after removing {candidate_key}.\n")
                                is_still_connected = False

                        except nx.NetworkXError as e:
                             # Handle cases where a terminal might not be in the graph after edge removal
                             print(f"NetworkX error during connectivity check after removing {candidate_key}: {e}. Assuming disconnected.")
                             iterative_log_file.write(f"NetworkX error checking connectivity for {candidate_key}: {e}. Assuming disconnected.\n")
                             is_still_connected = False
                        except KeyError as e:
                             # Handle cases where a terminal node might not exist in the graph component
                             print(f"KeyError during connectivity check for terminal {e} after removing {candidate_key}. Assuming disconnected.")
                             iterative_log_file.write(f"KeyError checking connectivity for terminal {e} after removing {candidate_key}. Assuming disconnected.\n")
                             is_still_connected = False


                    # Add the edge back for the next candidate check
                    graph_for_check.add_edge(*candidate_key)

                    if is_still_connected:
                        # Found the lowest Q-value edge that is not a bridge for terminals
                        edge_to_remove_key = candidate_key
                        edge_to_remove_q_val = candidate_q
                        print(f"Selected non-bridge edge {edge_to_remove_key} with Q={edge_to_remove_q_val:.4f} for removal.")
                        iterative_log_file.write(f"Selected non-bridge edge {edge_to_remove_key} (Q={edge_to_remove_q_val:.4f}) for removal.\n")
                        break # Exit the loop once the best non-bridge edge is found
                    else:
                        # This edge is a bridge for terminals, log it and continue
                        print(f"Edge {candidate_key} (Q={candidate_q:.4f}) is a bridge for terminals. Checking next edge.")
                        iterative_log_file.write(f"Edge {candidate_key} (Q={candidate_q:.4f}) is a bridge for terminals. Checking next.\n")

                # If loop finishes without finding a non-bridge edge
                if edge_to_remove_key is None and smt_edges_with_q:
                     print("Warning: All edges in the current SMT are bridges for terminals. Cannot remove any edge without disconnecting terminals. Stopping.")
                     iterative_log_file.write("Warning: All SMT edges are bridges for terminals. Stopping.\n")
                     last_checked_edge_info = f"{smt_edges_with_q[-1]['key']} (Q={smt_edges_with_q[-1]['q']:.4f})" if smt_edges_with_q else "N/A"
                     summary_log_file.write(f"{iteration:<4d} | {q_cost_to_log:<15.4f} | {valid_str:<6} | {original_cost_this_solution:<10.2f} | {last_checked_edge_info:<20} | ALL_BRIDGES\n")
                     break # Stop iteration

                # --- Original code continues below, using the determined edge_to_remove_key ---
                edge_removed_info = "N/A"
                if edge_to_remove_key:
                    # This part remains largely the same, using the selected non-bridge edge
                    edge_removed_info = f"{edge_to_remove_key} (Q={edge_to_remove_q_val:.4f})"
                    # Safety check: Ensure the edge still exists before attempting removal (should always be true here)
                    if edge_to_remove_key not in current_edges_dict:
                        print(f"CRITICAL ERROR: Edge {edge_to_remove_key} selected for removal was not found in current_edges_dict at removal time. Stopping.")
                        iterative_log_file.write(f"CRITICAL ERROR: Edge {edge_to_remove_key} not in current_edges_dict at removal time.\n")
                        summary_log_file.write(f"{iteration:<4d} | {q_cost_to_log:<15.4f} | {valid_str:<6} | {original_cost_this_solution:<10.2f} | {edge_removed_info:<20} | REMOVAL_SYNC_ERR\n")
                        break

                    # Check if already removed (another safety check)
                    if edge_to_remove_key in removed_edges_history:
                         print(f"Warning: Edge {edge_to_remove_key} was already removed (history check). Stopping.")
                         iterative_log_file.write(f"Warning: Edge {edge_to_remove_key} already removed (history check). Stopping.\n")
                         summary_log_file.write(f"{iteration:<4d} | {q_cost_to_log:<15.4f} | {valid_str:<6} | {original_cost_this_solution:<10.2f} | {edge_removed_info:<20} | REMOVAL_HIST_ERR\n")
                         break

                    # Remove the edge from the dictionary used for the *next* iteration's input graph
                    del current_edges_dict[edge_to_remove_key]
                    removed_edges_history.add(edge_to_remove_key)
                    iterative_log_file.write(f"Removed edge {edge_to_remove_key} from next iteration's graph.\n")

                    # Final connectivity check after removal (using common function as safeguard)
                    # This uses the *initial_nodes* list which might include nodes not currently connected.
                    # The bridge check above is more specific to terminal connectivity.
                    if not common.is_graph_still_connected(initial_nodes, current_edges_dict, terminals):
                        print(f"POST-REMOVAL WARNING: common.is_graph_still_connected indicates disconnect after removing non-bridge edge {edge_to_remove_key}. Stopping.")
                        iterative_log_file.write(f"POST-REMOVAL WARNING: common.is_graph_still_connected indicates disconnect for {edge_to_remove_key}. Stopping.\n")
                        summary_log_file.write(f"{iteration:<4d} | {q_cost_to_log:<15.4f} | {valid_str:<6} | {original_cost_this_solution:<10.2f} | {edge_removed_info:<20} | DISCONNECT_POST_ERR\n")
                        break # Stop if graph becomes disconnected unexpectedly

                else:
                    # This case is handled by the "All bridges" or "No valid edges" checks above.
                    # The 'break' statement would have already exited the while loop.
                    print("Could not identify a suitable edge to remove (already logged reason). Stopping.")
                    iterative_log_file.write("Could not identify suitable edge to remove (already logged reason). Stopping.\n")
                    # Summary log was written when the specific condition (all bridges/no valid edges) was met.
                    break # Stop if no edge could be removed

                # Log summary for this iteration if removal was successful
                summary_log_file.write(f"{iteration:<4d} | {q_cost_to_log:<15.4f} | {valid_str:<6} | {original_cost_this_solution:<10.2f} | {edge_removed_info:<20} | OK\n")

                # Clean up intermediate STP/STPLOG files for this iteration (optional)
                # try:
                #     if os.path.exists(iter_stp_filepath): os.remove(iter_stp_filepath)
                #     if os.path.exists(stplogo_output_path): os.remove(stplogo_output_path)
                # except OSError as e:
                #     print(f"Warning: Could not remove intermediate file: {e}")

            # --- End of while loop ---

            iterative_log_file.write("\n--- VCF Iterative Process Complete ---\n")
            summary_log_file.write("-" * 90 + "\n")

            # 7. Select the best solution from feasible_solutions based on minimum original_cost
            best_solution_cost = float('inf')
            best_solution_edges = None
            best_solution_nodes = None
            best_solution_iter = -1
            status_final = 'INFEASIBLE' # Default if no valid solutions found

            if feasible_solutions:
                # Sort by original_cost to find the minimum
                feasible_solutions.sort(key=lambda x: x['original_cost'])
                best_solution = feasible_solutions[0] # The one with the lowest original cost

                best_solution_cost = best_solution['original_cost']
                best_solution_edges = best_solution['edges'] # Already has original costs
                best_solution_nodes = best_solution['nodes']
                best_solution_iter = best_solution['iteration']
                status_final = 'OPTIMAL' # Found at least one valid solution

                print(f"\nBest feasible solution found at VCF iteration {best_solution_iter} with original cost {best_solution_cost}")
                iterative_log_file.write(f"Best feasible solution found at VCF iteration {best_solution_iter} with original cost {best_solution_cost}\n")
                iterative_log_file.write(f"Best Edges: {best_solution_edges}\n")
                summary_log_file.write(f"Best Feasible Solution Found:\n")
                summary_log_file.write(f"  Iteration: {best_solution_iter}\n")
                summary_log_file.write(f"  Original Cost: {best_solution_cost}\n")
                summary_log_file.write(f"  Q-Cost (at that iter): {best_solution['q_cost']}\n")

                # Write the best solution to dedicated files
                best_stp_filename = os.path.join(output_dir, f"{base_filename_no_ext}_VCF_best.stp")
                best_stplog_filename = os.path.join(output_dir, f"{base_filename_no_ext}_VCF_best.stplog")
                print(f"Writing best feasible solution to {best_stp_filename} and {best_stplog_filename}")
                iterative_log_file.write(f"Writing best solution to {best_stp_filename} and {best_stplog_filename}\n")
                try:
                    # Use write_stp_file for the final STP output with original costs
                    common.write_stp_file(best_stp_filename, list(best_solution_nodes), best_solution_edges, terminals, comment=f"Best feasible solution from VCF iteration {best_solution_iter}")
                    # Write a corresponding log file for the best solution
                    common.write_stplog_file(
                        log_filename=best_stplog_filename,
                        input_filename=f"{base_filename_no_ext}.stp", # Original input base
                        nodes_in_smt=list(best_solution_nodes),
                        edges_in_smt=best_solution_edges, # Edges with original cost
                        terminals_original=terminals,
                        objective_value=best_solution_cost, # Original cost is the final objective
                        solve_time=total_solve_time, # Total time for the iterative process
                        solver_name="SCIP-Jack (VCF Iterative)",
                        solver_version="N/A", # Add version if known
                        threads_used="N/A"# Add threads if known
                    )
                    summary_log_file.write(f"  Best Solution STP File: {best_stp_filename}\n")
                    summary_log_file.write(f"  Best Solution LOG File: {best_stplog_filename}\n")
                except Exception as e:
                    print(f"Error writing best VCF solution files: {e}")
                    iterative_log_file.write(f"Error writing best solution files: {e}\n")
                    status_final = 'ERROR' # Mark as error if final write fails

            else:
                print("\nNo feasible solution found across all VCF iterations.")
                iterative_log_file.write("No feasible solution found.\n")
                summary_log_file.write("No Feasible Solution Found.\n")
                if iteration >= max_iterations and not feasible_solutions: # Check if max iterations was reached *without* finding solutions
                     status_final = 'ITERATION_LIMIT'
                # If loop broke earlier or max iterations reached *after* finding some invalid ones, it's effectively INFEASIBLE
                # The status_final remains 'INFEASIBLE' unless changed above

            return status_final, best_solution_edges, best_solution_cost, total_solve_time

    except IOError as e:
        print(f"Error opening or writing VCF log files: {e}")
        return 'ERROR', None, float('inf'), total_solve_time
    except Exception as e:
        print(f"An unexpected error occurred during VCF iterative process: {e}")
        import traceback
        traceback.print_exc()
        return 'ERROR', None, float('inf'), total_solve_time


# --- 主程序 ---

def solver_main(inputfilename,logadapter):
    global g_SolverChoose # Ensure global access

    input_stp_file = os.path.join(pthGen.ABSSIMULDIR, inputfilename)
    filenamewithoutext = os.path.splitext(inputfilename)[0]

    # Define output paths consistently
    os.chdir(pthGen.ABSSIMULDIR)
    output_dir = pthGen.ABSSIMULDIR # Output in the same directory as input for simplicity
    # Base name for Gurobi output (mimicking SCIP-Jack)
    gurobi_output_stplogo_path = os.path.join(output_dir, filenamewithoutext + "_gurobi_output.stplog") # Distinguish output
    # Base name for SCIP-Jack output (will be handled by iterative solver)
    scipjack_base_name = filenamewithoutext # Iterative solver will add suffixes
    scipjack_final_stplogo_path = os.path.join(output_dir, filenamewithoutext + "_final_used.stplog") # Expected failed final name

    # --- QoS Initialization ---
    try:
        qos_query = QueryEdgeQValue(input_stp_file)
        # Adjust temperature as needed
        temperature = TEMPERATURE # Example temperature
        if common.g_QureyEdgeQValues_map==None:
            common.g_QureyEdgeQValues_map = qos_query.get_all_q_values(temperature=temperature)
        if common.g_QGraph==None:
            common.g_QGraph=qos_query.getQvalueGraph(common.g_QureyEdgeQValues_map)
            
        logadapter.info(f"Initialized QoS map for Temperature={temperature}")
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        logadapter.info(f"Error initializing QoS: {e}. Cannot proceed.")
        return # Exit if QoS setup fails
    except Exception as e:
        logadapter.info(f"Unexpected error during QoS initialization: {e}")
        return

    # --- Copy original STP for reference (useful for drawing/comparison) ---
    if g_SolverChoose == 0:
        outputorgfilewithext = filenamewithoutext + "_gurobi_output.stp" # More descriptive name
    else:
        outputorgfilewithext = filenamewithoutext + "_final_used.stp" # for tail to find valid solution

    outputorgfile = os.path.join(output_dir, outputorgfilewithext)

    try:
        shutil.copy(input_stp_file, outputorgfile)
        logadapter.info(f"Copied original STP to {outputorgfile}")
    except Exception as e:
        logadapter.info(f"Warning: Could not copy original STP file: {e}")


    # --- Parse Initial Problem ---
    try:
        logadapter.info(f"Parsing initial STP file: {input_stp_file}")
        nodes_list, edges_dict, terminals_list = common.parse_stp_file(input_stp_file)
        logadapter.info(f"Parsing complete. Nodes: {len(nodes_list)}, Edges: {len(edges_dict)}, Terminals: {len(terminals_list)}")
        if len(terminals_list) != 11:
            logadapter.info(f"Warning: The number of terminals is {len(terminals_list)}. QoS validation requires 11.")
    except (FileNotFoundError, ValueError) as e:
        logadapter.info(f"Error parsing initial STP file: {e}. Cannot proceed.")
        return
    except Exception as e:
        logadapter.info(f"Unexpected error during initial parsing: {e}")
        return


    #global g_SolverChoose # Ensure global access

    input_stp_file = os.path.join(pthGen.ABSSIMULDIR, inputfilename)
    filenamewithoutext = os.path.splitext(inputfilename)[0]

    # Define output paths consistently
    os.chdir(pthGen.ABSSIMULDIR)
    output_dir = pthGen.ABSSIMULDIR # Output in the same directory as input for simplicity
    # Base name for Gurobi output (mimicking SCIP-Jack)
    gurobi_output_stplogo_path = os.path.join(output_dir, filenamewithoutext + "_gurobi_output.stplog") # Distinguish output
    # Base name for SCIP-Jack output (will be handled by iterative solver)
    scipjack_base_name = filenamewithoutext # Iterative solver will add suffixes
    scipjack_final_stplogo_path = os.path.join(output_dir, filenamewithoutext + "_final_used.stplog") # Expected failed final name

    # --- QoS Initialization ---
    try:
        qos_query = QueryEdgeQValue(input_stp_file)
        # Adjust temperature as needed
        temperature = TEMPERATURE # Example temperature
        if common.g_QureyEdgeQValues_map==None:
            common.g_QureyEdgeQValues_map = qos_query.get_all_q_values(temperature=temperature)
        if common.g_QGraph==None:
            common.g_QGraph=qos_query.getQvalueGraph(common.g_QureyEdgeQValues_map)

        logadapter.info(f"Initialized QoS map for Temperature={temperature}")
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        logadapter.info(f"Error initializing QoS: {e}. Cannot proceed.")
        return # Exit if QoS setup fails
    except Exception as e:
        logadapter.info(f"Unexpected error during QoS initialization: {e}")
        return

    # --- Copy original STP for reference (useful for drawing/comparison) ---
    if g_SolverChoose == 0:
        outputorgfilewithext = filenamewithoutext + "_gurobi_output.stp" # More descriptive name
    elif g_SolverChoose == 1: # Keep original logic for solver 1
        outputorgfilewithext = filenamewithoutext + "_final_used.stp"
    elif g_SolverChoose == 2: # Use a specific name for VCF original copy
        outputorgfilewithext = filenamewithoutext + "_VCF_original.stp"
    else:
        outputorgfilewithext = filenamewithoutext + "_unknown_solver.stp"


    outputorgfile = os.path.join(output_dir, outputorgfilewithext)

    try:
        shutil.copy(input_stp_file, outputorgfile)
        logadapter.info(f"Copied original STP to {outputorgfile}")
    except Exception as e:
        logadapter.info(f"Warning: Could not copy original STP file: {e}")


    # --- Parse Initial Problem ---
    try:
        logadapter.info(f"Parsing initial STP file: {input_stp_file}")
        nodes_list, edges_dict, terminals_list = common.parse_stp_file(input_stp_file)
        logadapter.info(f"Parsing complete. Nodes: {len(nodes_list)}, Edges: {len(edges_dict)}, Terminals: {len(terminals_list)}")
        # Warning moved inside VCF function as it's specific to its validation logic
        # if len(terminals_list) != 11:
        #     print(f"Warning: The number of terminals is {len(terminals_list)}. QoS validation requires 11.")
    except (FileNotFoundError, ValueError) as e:
        logadapter.info(f"Error parsing initial STP file: {e}. Cannot proceed.")
        return
    except Exception as e:
        logadapter.info(f"Unexpected error during initial parsing: {e}")
        return


    # --- Choose Solver ---
    status_str = 'ERROR' # Default status
    smt_edges = None
    smt_cost = float('inf')
    actual_solve_time = 0.0
    model_object = None # Only relevant for Gurobi
    start_time = time.perf_counter()
    

    if g_SolverChoose == 0:
        # --- Use Gurobi Solver ---
        logadapter.info("\n--- Solver Chosen: Gurobi (Flow Balance with Lazy Constraints) ---")
        gurobi_time_limit = GUROBI_MAXCOMPUTE_TIME # Example time limit
        try:
            status, smt_edges, smt_cost, model_object, actual_solve_time = solve_stp_flow_balance(
                nodes_list,
                edges_dict,
                terminals_list,
                time_limit=gurobi_time_limit,
                logger=logadapter
            )
            # Convert Gurobi status code to string if needed for logging
            status_str = f"Gurobi Status {status}" # Or map codes to names
            if status == GRB.OPTIMAL: status_str = 'OPTIMAL'
            elif status == GRB.INFEASIBLE: status_str = 'INFEASIBLE'
            elif status == GRB.TIME_LIMIT: status_str = 'TIME_LIMIT'
            # ... other statuses

        except gp.GurobiError as e:
            logadapter.info(f"Gurobi error occurred during solve: {e.errno} - {e}")
            status_str = 'GUROBI_ERROR'
        except Exception as e:
            logadapter.info(f"An unexpected error occurred during Gurobi solve: {e}")
            import traceback
            traceback.print_exc()
            status_str = 'UNEXPECTED_ERROR'

        # --- Log Gurobi Results (mimicking stplog) ---
        gurobi_version = "N/A"
        threads = "N/A"
        if model_object:
             try:
                 gurobi_version_tuple = gp.gurobi.version()
                 gurobi_version = f"{gurobi_version_tuple[0]}.{gurobi_version_tuple[1]}.{gurobi_version_tuple[2]}"
                 threads = model_object.Params.Threads if model_object.Status != GRB.LOADED else "N/A"
                 if threads == 0: threads = "Auto"
             except: pass # Ignore errors getting info

        # Check if a solution (even suboptimal) was found
        if status in [GRB.OPTIMAL, GRB.SUBOPTIMAL] or (status == GRB.TIME_LIMIT and model_object and model_object.SolCount > 0):
            logadapter.info(f"\nGurobi found a solution (Status: {status}) with cost: {smt_cost}")
            smt_nodes = set(terminals_list) # Start with terminals
            if smt_edges: # Ensure smt_edges is not None
                for u, v, _ in smt_edges:
                     smt_nodes.add(u)
                     smt_nodes.add(v)
            logadapter.info(f"Writing Gurobi solution log to: {gurobi_output_stplogo_path}")
            common.write_stplog_file(
                 log_filename=gurobi_output_stplogo_path,
                 input_filename=input_stp_file,
                 nodes_in_smt=list(smt_nodes),
                 edges_in_smt=smt_edges if smt_edges else [],
                 terminals_original=terminals_list,
                 objective_value=smt_cost,
                 solve_time=actual_solve_time,
                 solver_name="Gurobi",
                 solver_version=gurobi_version,
                 threads_used=threads
            )
        else:
            logadapter.info(f"\nGurobi did not find an optimal solution (Status: {status}). Writing run log.")
            common.write_stplog_file(
                 log_filename=gurobi_output_stplogo_path,
                 input_filename=input_stp_file,
                 nodes_in_smt=list(set(terminals_list)), # Only terminals if no solution
                 edges_in_smt=[],
                 terminals_original=terminals_list,
                 objective_value=float('inf') if status == GRB.INFEASIBLE else smt_cost, # Use cost if available (e.g. time limit)
                 solve_time=actual_solve_time,
                 solver_name="Gurobi",
                 solver_version=gurobi_version,
                 threads_used=threads
            )
        logadapter.info("Gurobi logging complete.")


    elif g_SolverChoose == 1:
        # --- Use SCIP-Jack Iterative Solver ---
        logadapter.info("\n--- Solver Chosen: SCIP-Jack (Iterative Edge Removal) ---")
        try:
            status_str, smt_edges, smt_cost, actual_solve_time = solve_stp_scipjack_iterative(
                nodes_list,
                edges_dict,
                terminals_list,
                scipjack_base_name, # Pass base name, function handles iteration suffixes
                output_dir
            )
            # The iterative function already prints progress and saves final files.
            # It generates the final .stplog file itself.

            end_time = time.perf_counter()
            elapsed_time = end_time - start_time

            logadapter.info(f"\nSCIP-Jack iterative process finished with status: {status_str}")
            if status_str == 'OPTIMAL':
                 logadapter.info(f"Final valid solution cost: {smt_cost}")
                 logadapter.info(f"Total SCIP-Jack solve time (accumulated): {actual_solve_time:.4f} seconds elasped {elapsed_time:.4f} sec.")
                 # The final log file should be at scipjack_final_stplogo_path if successful
                 if os.path.exists(scipjack_final_stplogo_path):
                      logadapter.info(f"Final SCIP-Jack log saved to: {scipjack_final_stplogo_path}")
                 else:
                      logadapter.info(f"Warning: Expected final SCIP-Jack log file not found at {scipjack_final_stplogo_path}")

            elif status_str == 'INFEASIBLE':
                 logadapter.info("SCIP-Jack iterative process determined the problem is infeasible with constraints.")
                 # Optionally write a log indicating infeasibility
                 # Check if the _final_used file was created, if not, write an infeasible log
                 gotbest_log_path = os.path.join(output_dir, scipjack_base_name + "_final_used.stplog")
                 if not os.path.exists(gotbest_log_path):
                     common.write_stplog_file(
                         log_filename=scipjack_final_stplogo_path.replace(".stplog", "_infeasible.stplog"),
                         input_filename=input_stp_file,
                         nodes_in_smt=list(set(terminals_list)),
                         edges_in_smt=[],
                         terminals_original=terminals_list,
                         objective_value=float('inf'),
                         solve_time=actual_solve_time,
                         solver_name="SCIP-Jack (Iterative)",
                         solver_version="N/A", # Get SCIP-Jack version if possible
                         threads_used="N/A"
                     )

            elif status_str == 'ITERATION_LIMIT':
                 
                 logadapter.info(f"SCIP-Jack iterative process reached iteration limit without finding a valid solution. elasped {elapsed_time:.4f} sec.")
                 # Optionally write a log indicating limit reached
                 # Check if the _final_used file was created, if not, write an iterlimit log
                 gotbest_log_path = os.path.join(output_dir, scipjack_base_name + "_final_used.stplog")
                 if not os.path.exists(gotbest_log_path):
                     common.write_stplog_file(
                         log_filename=scipjack_final_stplogo_path.replace(".stplog", "_iterlimit.stplog"),
                         input_filename=input_stp_file,
                         nodes_in_smt=list(set(terminals_list)),
                         edges_in_smt=[],
                         terminals_original=terminals_list,
                         objective_value=float('inf'), # No valid solution found
                         solve_time=actual_solve_time,
                         solver_name="SCIP-Jack (Iterative)",
                         solver_version="N/A",
                         threads_used="N/A"
                     )
            else:
                logadapter.info(f"SCIP-Jack stopped without finding a valid solution. elasped {elapsed_time:.4f} sec.")


        except Exception as e:
            logadapter.info(f"An unexpected error occurred during SCIP-Jack iterative solve: {e}")
            import traceback
            traceback.print_exc()
            status_str = 'UNEXPECTED_ERROR'

    elif g_SolverChoose == 2:
        # --- Use SCIP-Jack VCF Iterative Solver ---
        logadapter.info("\n--- Solver Chosen: SCIP-Jack (VCF Iterative) ---")
        # Define output paths specific to VCF if needed, or use the general ones
        vcf_base_name = filenamewithoutext # Base name for VCF files
        vcf_final_best_stplog_path = os.path.join(output_dir, f"{vcf_base_name}_VCF_best.stplog") # Expected final log name

        try:
            status_str, smt_edges, smt_cost, actual_solve_time = solve_stp_scipjack_VCF_iterative(
                nodes_list,
                edges_dict,       # Pass original edges dict
                terminals_list,
                vcf_base_name,    # Pass base name for VCF files
                output_dir
            )
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            # The VCF function handles its own detailed logging and file saving.
            logadapter.info(f"\nSCIP-Jack VCF iterative process finished with status: {status_str}")
            if status_str == 'OPTIMAL':
                 logadapter.info(f"Final best valid solution original cost: {smt_cost}")
                 logadapter.info(f"Total SCIP-Jack VCF solve time (accumulated): {actual_solve_time:.4f} seconds. elapsed {elapsed_time:.4f} sec.")
                 if os.path.exists(vcf_final_best_stplog_path):
                      logadapter.info(f"Final best VCF solution log saved to: {vcf_final_best_stplog_path}")
                 else:
                      # The VCF function should have created this, maybe an error during write?
                      logadapter.info(f"Warning: Expected final best VCF log file not found at {vcf_final_best_stplog_path}")
            elif status_str == 'INFEASIBLE' or status_str == 'ITERATION_LIMIT' or status_str == 'ERROR':
                 logadapter.info(f"SCIP-Jack VCF iterative process did not find a valid solution or encountered an error (Status: {status_str}). elasped {elapsed_time:.4f} sec.")
                 # VCF function logs details, maybe write a simple overall status log here if needed
            # Handle 'UNEXPECTED_ERROR' from the try-except block below if needed

        except Exception as e:
            logadapter.info(f"An unexpected error occurred during SCIP-Jack VCF iterative solve: {e}")
            import traceback
            traceback.print_exc()
            status_str = 'UNEXPECTED_ERROR'

    else:
        logadapter.info(f"Error: Invalid g_SolverChoose value: {g_SolverChoose}. Must be 0, 1, or 2.") # Updated error message
        return


    # --- Final Q Value Saving (Common to both solvers) ---
    if common.g_QureyEdgeQValues_map is not None:
        # Use a consistent name for the Q values used in the run
        outputQfilewithext = filenamewithoutext + "_final_used.stq"
        output_stq_filepath = os.path.join(output_dir, outputQfilewithext)
        logadapter.info(f"\nSaving final Q values used (T={temperature}) to: {output_stq_filepath}")
        try:
            with open(output_stq_filepath, 'w') as f_out_q:
                f_out_q.write("SECTION GraphQoS\n")
                f_out_q.write(f"Edges {len(common.g_QureyEdgeQValues_map)}\n")
                sorted_edges_q = sorted(common.g_QureyEdgeQValues_map.keys())
                for u, v in sorted_edges_q:
                    q_value = common.g_QureyEdgeQValues_map[(u, v)]
                    f_out_q.write(f"Q {u} {v} {q_value}\n")
                f_out_q.write("END\n")
            logadapter.info(f"Successfully saved {len(common.g_QureyEdgeQValues_map)} Q values.")
        except IOError as e:
            logadapter.info(f"Error writing final Q values to {output_stq_filepath}: {e}")
        except Exception as e:
             logadapter.info(f"An unexpected error occurred while saving final Q values: {e}")
    else:
        logadapter.info("\nWarning: g_QureyEdgeQValues_map is None, cannot save final Q values.")

    logadapter.info("\n--- Solver Main Finished ---")


def run_single_test_case(input_filename_in_working_dir: str,
                         temperature: float,
                         solver_choice: int,
                         simple_check: int,logadapter):
    """
    配置并运行一次 STP 测试。
    此函数设置全局变量（温度、求解器选择、检查方法），
    然后调用 solver_main 处理指定的输入文件。
    假定输入文件已存在于工作目录 (TestWorkingGDir)。
    返回 True 表示调用成功完成（不代表求解器找到解），
    返回 False 表示在调用 solver_main 期间发生异常。
    """
    global TEMPERATURE, g_SolverChoose, g_SimpleCheck, common # 声明需要修改的全局变量

    common.seedinit()

    

    logadapter.info(f"--- 配置并运行 Case: 文件={input_filename_in_working_dir}, 温度={temperature} ---")

    # 1. 设置全局变量 (模拟 if __name__ == "__main__" 的配置部分)
    try:
        TEMPERATURE = temperature
        g_SolverChoose = solver_choice
        g_SimpleCheck = simple_check

        # 打印配置信息 (类似 if __name__ == "__main__")
        solver_choice_str = "Gurobi"
        if g_SolverChoose == 1:
            solver_choice_str = "SCIP-Jack (Iterative)"
        elif g_SolverChoose == 2:
            solver_choice_str = "SCIP-Jack (VCF Iterative)"
        logadapter.info(f"设置 Solver Choice: {solver_choice_str} ({g_SolverChoose})")
        logadapter.info(f"设置 Validity Check: {'Database Lookup' if g_SimpleCheck == 0 else 'Simplified Median'} ({g_SimpleCheck})")
        logadapter.info(f"设置 Temperature: {TEMPERATURE}")
        logadapter.info(f"目标输入文件 (应在工作目录中): {input_filename_in_working_dir}")

        # 2. 重置 QoS 全局变量 (关键步骤)
        # 强制 solver_main 内部的 QoS 初始化逻辑使用新的 TEMPERATURE
        logadapter.info("重置全局 QoS Map 和 Graph 以强制使用新温度重新初始化。")
        common.g_QureyEdgeQValues_map = None
        common.g_QGraph = None

        # 3. 调用现有的 solver_main
        logadapter.info(f"调用 solver_main('{input_filename_in_working_dir}')...")
        solver_main(input_filename_in_working_dir,logadapter) # 调用核心逻辑
        logadapter.info(f"solver_main 调用完成。")
        return True # 表示调用流程成功

    except Exception as e:
        # 捕获 solver_main 执行期间的任何异常
        logadapter.error(f"运行 solver_main 时发生错误: {e}", exc_info=True) # 记录完整错误信息
        return False # 表示调用流程失败


# Example Usage (keep commented out or adjust as needed)
# def checkQureyEdgeQvalue():
#     #Example of using the new class (Optional: Keep commented out or remove)
#     test_stp_file = os.path.join(pthGen.ABSSIMULDIR, "b18.stp")
#     if os.path.exists(test_stp_file):
#         print("\n--- Testing QueryEdgeQValue ---")
#         try:
#             # Initialize (only reads/generates base T=0 values)
#             qos_query = QueryEdgeQValue(test_stp_file)
#             print("\nBase Q values (T=0):")
#             q_map_t0 = qos_query.get_all_q_values(temperature=0) # Explicitly get T=0 map
#             print(f"Got {len(q_map_t0)} Q values.")
#             count = 0
#             for edge, q in q_map_t0.items():
#                 print(f"Edge {edge}: Q={q}")
#                 count += 1
#                 if count >= 5: break
#
#             # Get Q values for T=40
#             print("\nAdjusted Q values (T=40):")
#             q_map_t40 = qos_query.get_all_q_values(temperature=40)
#             print(f"Got {len(q_map_t40)} Q values.")
#             count = 0
#             for edge, q in q_map_t40.items():
#                 print(f"Edge {edge}: Q={q}")
#                 count += 1
#                 if count >= 5: break
#             # Example lookup for T=40
#             if q_map_t40:
#                  first_edge = list(q_map_t40.keys())[0]
#                  print(f"Lookup for edge {first_edge} (T=40): Q={qos_query.get_q_value(first_edge[0], first_edge[1], temperature=40)}")
#                  # Compare with T=0 lookup for the same edge
#                  print(f"Lookup for edge {first_edge} (T=0): Q={qos_query.get_q_value(first_edge[0], first_edge[1], temperature=0)}")
#
#
#             # Get Q values for T=-30
#             print("\nAdjusted Q values (T=-30):")
#             q_map_tn30 = qos_query.get_all_q_values(temperature=-30)
#             print(f"Got {len(q_map_tn30)} Q values.")
#             count = 0
#             for edge, q in q_map_tn30.items():
#                 print(f"Edge {edge}: Q={q}")
#                 count += 1
#                 if count >= 5: break
#
#         except Exception as e:
#             print(f"Error during QueryEdgeQValue testing: {e}")
#             import traceback
#             traceback.print_exc() # Print full traceback for debugging
#     else:
#         print(f"\nSkipping QueryEdgeQValue test: {test_stp_file} not found.")


if __name__ == "__main__":

    common.seedinit()
    #global g_SolverChoose, g_SimpleCheck
    # --- Configuration ---
    g_SolverChoose = 2# 0 for Gurobi, 1 for SCIP-Jack (Original Iterative), 2 for SCIP-Jack (VCF Iterative)
    g_SimpleCheck = 0 # 0 for DB check, 1 for simplified median check
    test_input_file = 'b10modi.stp'#'b10modi.stp' # Input file name
    # --- End Configuration ---

    print(f"--- Running STP Solver ---")
    solver_choice_str = "Gurobi"
    if g_SolverChoose == 1:
        solver_choice_str = "SCIP-Jack (Iterative)"
    elif g_SolverChoose == 2:
        solver_choice_str = "SCIP-Jack (VCF Iterative)" # Updated print statement
    print(f"Solver Choice: {solver_choice_str}")
    print(f"Validity Check: {'Database Lookup' if g_SimpleCheck == 0 else 'Simplified Median'}")
    print(f"Input File: {test_input_file}")

    # Initialize BPDATA (needed for validity checks)
    try:
        print("Initializing BPDATA database connection...")
        BPDATA.checkTailsDBTreeBuild() # This loads the DB tree needed by checkValidLink
        print("BPDATA initialized.")
    except Exception as e:
        print(f"Error initializing BPDATA: {e}. Validity checks might fail.")
        # Decide if you want to exit or continue with potentially failing checks
        # exit() # Or just print warning

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO) # 设置基础 logger 的级别
    # 添加控制台输出 handler (这个可以保持全局)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - Case %(case_idx)s - %(message)s'))
    logger.addHandler(console_handler)
    # 创建 adapter
    adapter = logging.LoggerAdapter(logger, {'case_idx': 'N/A'})
    common.g_LoggerAdapter=adapter
    # Run the main solver logic
    solver_main(test_input_file,common.g_LoggerAdapter)
