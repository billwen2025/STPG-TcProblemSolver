#!/usr/bin/env python3
from collections import defaultdict, deque
import networkx as nx
import pathsSeqGen as pthGen
import random,os # Added for QoS generation

def seedinit():
    random.seed(555) # Set seed for reproducibility

# 全局变量
g_QureyEdgeQValues_map = None
g_QGraph=None
g_LoggerAdapter=None

ROOT_TERMINAL_IDX = 0
MIDDLE_MPATHS=3


Q_VALUES = [0.011, 0.015, 0.02]

# Helper function to convert edge key to string for printing
def key_str(edge_key):
    return f"({edge_key[0]}-{edge_key[1]})"

# 辅助函数

def parse_stp_file(filename):
    """解析标准的 .stp 文件"""
    nodes = set()
    edges = {} # 使用 (u, v) with u < v 作为 key
    terminals = []
    num_nodes = 0
    num_edges = 0

    with open(filename, 'r') as f:
        section = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line == 'EOF':
                continue

            if line.startswith('SECTION'):
                section = line.split()[1].upper()
                continue

            parts = line.split()
            if not parts:
                continue

            keyword = parts[0].upper()

            if section == 'GRAPH':
                if keyword == 'NODES':
                    num_nodes = int(parts[1])
                elif keyword == 'EDGES':
                    num_edges = int(parts[1])
                elif keyword == 'E':
                    u, v, cost = int(parts[1]), int(parts[2]), float(parts[3])
                    # 确保 u < v 以避免重复存储无向边
                    if u > v:
                        u, v = v, u
                    edges[(u, v)] = cost
                    nodes.add(u)
                    nodes.add(v)
            elif section == 'TERMINALS':
                if keyword == 'TERMINALS':
                    # 有些格式可能省略这个，直接列出 T
                    pass
                elif keyword == 'T':
                    terminals.append(int(parts[1]))
                    nodes.add(int(parts[1])) # 确保终端节点在节点集合中

    # 验证节点数量和边数量（可选）
    # print(f"Parsed {len(nodes)} nodes (declared: {num_nodes})")
    # print(f"Parsed {len(edges)} edges (declared: {num_edges})")
    # print(f"Parsed {len(terminals)} terminals")

    if not terminals:
        raise ValueError("No terminals found in the file.")
    if not edges:
         raise ValueError("No edges found in the file.")

    # 确保所有节点都在 nodes 集合中 (1 到 num_nodes)
    # 如果文件没有显式列出所有节点，我们只使用边和终端中提到的节点
    # all_nodes = set(range(1, num_nodes + 1)) # 或者基于edges和terminals推断
    all_nodes = set()
    for u,v in edges:
        all_nodes.add(u)
        all_nodes.add(v)
    for t in terminals:
        all_nodes.add(t)


    return list(all_nodes), edges, terminals


def _parse_stp_edges(filename):
    """Helper to parse only edges from an STP file."""
    edges = {}
    with open(filename, 'r') as f:
        section = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line == 'EOF':
                continue
            if line.startswith('SECTION'):
                section = line.split()[1].upper()
                continue
            if section == 'GRAPH':
                parts = line.split()
                if not parts: continue
                keyword = parts[0].upper()
                if keyword == 'E':
                    u, v = int(parts[1]), int(parts[2])
                    if u > v: u, v = v, u
                    # Store edge without cost for QoS generation
                    edges[(u, v)] = None # Value doesn't matter here
    if not edges:
        raise ValueError(f"No edges found in the GRAPH section of {filename}")
    return list(edges.keys())

def generate_stq_file(stp_file_path, stq_file_path):
    """Generates a .stq file with random QoS values for edges from .stp file."""
    print(f"Generating STQ file: {stq_file_path} from {stp_file_path}")
    try:
        edges_list = _parse_stp_edges(stp_file_path)
        num_edges = len(edges_list)

        with open(stq_file_path, 'w') as f:
            f.write("SECTION GraphQoS\n")
            f.write(f"Edges {num_edges}\n")
            for u, v in edges_list:
                # Initial random assignment with equal probability
                q_value = random.choice(Q_VALUES)
                f.write(f"Q {u} {v} {q_value}\n")
            f.write("END\n")
        print(f"Successfully generated {stq_file_path} with {num_edges} edges.")
    except FileNotFoundError:
        print(f"Error: Input STP file not found at {stp_file_path}")
        raise
    except ValueError as e:
        print(f"Error parsing STP file {stp_file_path}: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during STQ generation: {e}")
        raise


def read_stq_file(stq_file_path):
    """Reads edge QoS values from a .stq file."""
    edge_q_map = {}
    print(f"Reading STQ file: {stq_file_path}")
    try:
        with open(stq_file_path, 'r') as f:
            section = None
            num_edges_declared = 0
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line == 'EOF':
                    continue
                if line.startswith('SECTION'):
                    section = line.split()[1].upper()
                    continue

                if section == 'GRAPHQOS':
                    parts = line.split()
                    if not parts: continue
                    keyword = parts[0].upper()
                    if keyword == 'EDGES':
                        num_edges_declared = int(parts[1])
                    elif keyword == 'Q':
                        if len(parts) != 4:
                            print(f"Warning: Malformed Q line in {stq_file_path}: {line}. Skipping.")
                            continue
                        u, v, q_value = int(parts[1]), int(parts[2]), float(parts[3])
                        if q_value not in Q_VALUES:
                             print(f"Warning: Invalid Q value {q_value} for edge ({u},{v}) in {stq_file_path}. Skipping.")
                             continue
                        if u > v: u, v = v, u
                        edge_q_map[(u, v)] = q_value

        if len(edge_q_map) != num_edges_declared:
             print(f"Warning: Declared edges ({num_edges_declared}) != Found edges ({len(edge_q_map)}) in {stq_file_path}")
        print(f"Successfully read {len(edge_q_map)} edges from {stq_file_path}.")
        return edge_q_map
    except FileNotFoundError:
        print(f"Error: STQ file not found at {stq_file_path}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during STQ reading: {e}")
        raise


def adjust_q_values_by_temperature(initial_edge_q_map, temperature):
    """Adjusts Q values based on temperature with proportional scaling.
    At -50, all edges are set to 0.011 (lowest Q value).
    At +50, all edges are set to 0.02 (highest Q value).
    At 0, initial random values are retained.
    For intermediate temperatures, Q values are adjusted proportionally."""
    if not isinstance(temperature, (int, float)):
        raise TypeError("Temperature must be a number.")
    if not -50 <= temperature <= 50:
        print(f"Warning: Temperature {temperature} is outside the expected range [-50, 50]. Clamping.")
        temperature = max(-50, min(50, temperature))

    if temperature == 0:
        print("Temperature is 0, returning initial Q values.")
        return initial_edge_q_map

    print(f"Adjusting Q values for temperature: {temperature}")
    adjusted_edge_q_map = {}
    
    if temperature == -50:
        # Set all edges to the lowest Q value
        for edge in initial_edge_q_map:
            adjusted_edge_q_map[edge] = Q_VALUES[0]  # 0.011
    elif temperature == 50:
        # Set all edges to the highest Q value
        for edge in initial_edge_q_map:
            adjusted_edge_q_map[edge] = Q_VALUES[2]  # 0.02
    else:
        # Calculate the proportion of edges to adjust based on temperature
        scale = abs(temperature) / 50.0  # Between 0 and 1
        num_edges = len(initial_edge_q_map)
        if temperature < 0:
            # Adjust towards lower Q value (0.011)
            num_to_adjust = int(num_edges * scale)
            edges_to_adjust = random.sample(list(initial_edge_q_map.keys()), num_to_adjust)
            for edge in initial_edge_q_map:
                if edge in edges_to_adjust:
                    adjusted_edge_q_map[edge] = Q_VALUES[0]  # 0.011
                else:
                    adjusted_edge_q_map[edge] = initial_edge_q_map[edge]
        else:
            # Adjust towards higher Q value (0.02)
            num_to_adjust = int(num_edges * scale)
            edges_to_adjust = random.sample(list(initial_edge_q_map.keys()), num_to_adjust)
            for edge in initial_edge_q_map:
                if edge in edges_to_adjust:
                    adjusted_edge_q_map[edge] = Q_VALUES[2]  # 0.02
                else:
                    adjusted_edge_q_map[edge] = initial_edge_q_map[edge]

    print(f"Finished adjusting Q values based on temperature {temperature}.")
    return adjusted_edge_q_map

def parse_stplogo_file(stplogo_filepath):
    """Parses the .stplog file generated by SCIP-Jack to extract the solution."""
    solution_edges = []
    objective_value = float('inf')
    nodes_in_smt = set()
    found_solution_cost = False
    in_final_solution_section = False

    print(f"Parsing SCIP-Jack output file: {stplogo_filepath}")
    try:
        with open(stplogo_filepath, 'r') as f:
            section = None
            for line in f:
                line = line.strip()
                if not line: continue

                if line.startswith("SECTION"):
                    section = line.split()[1].upper()
                    in_final_solution_section = (section == "FINALSOLUTION")
                    continue
                if line == "End":
                    section = None
                    in_final_solution_section = False
                    continue

                if section == "SOLUTIONS":
                    # Example: Solution 12.3            150.000000000
                    if line.startswith("Solution"):
                        parts = line.split()
                        if len(parts) >= 3:
                             try:
                                 # Get the cost from the last part
                                 cost = float(parts[-1])
                                 # Use the *first* valid solution's cost found
                                 if not found_solution_cost:
                                     objective_value = cost
                                     found_solution_cost = True # Mark that we have a cost
                             except ValueError:
                                 print(f"Warning: Could not parse cost from Solution line: {line}")
                elif in_final_solution_section: # Check flag instead of section name
                     if line.startswith("V"):
                         try:
                             node = int(line.split()[1])
                             nodes_in_smt.add(node)
                         except (IndexError, ValueError):
                             print(f"Warning: Could not parse node from V line: {line}")
                     elif line.startswith("E"):
                         try:
                             u, v = int(line.split()[1]), int(line.split()[2])
                             # Store edges without cost initially, as .stplog doesn't have it
                             solution_edges.append(tuple(sorted((u, v))))
                         except (IndexError, ValueError):
                             print(f"Warning: Could not parse edge from E line: {line}")

        # Check if we actually found edges in the final solution section
        if not solution_edges:
             # If we found a cost but no edges, it might be an issue or just a single node solution
             if found_solution_cost and objective_value == 0 and len(nodes_in_smt) == 1:
                 print("Parsed a single-node solution (cost 0).")
             else:
                 print(f"Warning: No edges found in Finalsolution section of {stplogo_filepath}. File might indicate infeasibility or error.")
                 return None, objective_value if found_solution_cost else float('inf'), nodes_in_smt # Return nodes found, even if no edges

        print(f"Parsed {len(nodes_in_smt)} nodes, {len(solution_edges)} edges. Objective from Solutions section: {objective_value if found_solution_cost else 'Not Found'}")
        # Return objective_value which comes from SOLUTIONS section, might differ from recalc cost
        return solution_edges, objective_value if found_solution_cost else float('inf'), nodes_in_smt

    except FileNotFoundError:
        print(f"Error: SCIP-Jack output file not found: {stplogo_filepath}")
        return None, float('inf'), set()
    except Exception as e:
        print(f"An error occurred parsing {stplogo_filepath}: {e}")
        return None, float('inf'), set()

# --- Helper functions for SCIP-Jack iterative approach ---

def write_stp_file_generic(filename, nodes_list, edges_list_with_cost, terminals_list, comment=""):
    """Writes a graph to a .stp file (more generic version)."""
    # Determine the actual nodes present based on edges and terminals
    present_nodes = set(terminals_list)
    for u, v, _ in edges_list_with_cost:
        present_nodes.add(u)
        present_nodes.add(v)
    # Also include nodes from the original list that might be isolated but are terminals
    # The header needs the count of *all* nodes potentially involved.
    # Using the initial full list might be safer for the header count if SCIP needs it.
    # Let's use the count of nodes actually present in edges + terminals for header.
    num_nodes_header = len(present_nodes)
    num_edges = len(edges_list_with_cost)
    num_terminals = len(terminals_list)

    with open(filename, 'w') as f:
        f.write("33D32945 STP File, STP Format Version 1.0\n")
        f.write("SECTION Comment\n")
        f.write(f"Generated by Python script\n")
        if comment:
            f.write(f"{comment}\n")
        f.write("END\n\n")

        f.write("SECTION Graph\n")
        f.write(f"Nodes {num_nodes_header}\n") # Use count of nodes in edges/terminals
        f.write(f"Edges {num_edges}\n")
        # Write edges using original node IDs
        for u, v, cost in edges_list_with_cost:
            cost_str = float(cost) if cost == float(cost) else f"{cost:.011f}" # Format cost
            f.write(f"E {u} {v} {cost_str}\n")
        f.write("END\n\n")

        f.write("SECTION Terminals\n")
        f.write(f"Terminals {num_terminals}\n")
        for t in terminals_list:
            f.write(f"T {t}\n")
        f.write("END\n\n")

        f.write("EOF\n")






# --- End of SCIP-Jack Helpers ---

# Helper function to copy log section
def copy_log_section(source_log_path, target_log_path):
    """Copies the content from 'SECTION Run' onwards from source to target."""
    if not source_log_path:
        print("Warning: No source log path provided for copying section.")
        return
    if not os.path.exists(source_log_path):
        print(f"Error: Source log file not found for copying section: {source_log_path}")
        return

    try:
        with open(source_log_path, 'r') as infile:
            lines = infile.readlines()

        start_index = -1
        for i, line in enumerate(lines):
            # Match "SECTION Run" case-insensitively and ignore leading/trailing whitespace
            if line.strip().upper() == "SECTION RUN":
                start_index = i
                break

        if start_index != -1:
            content_to_copy = "".join(lines[start_index:])
            # Ensure target directory exists
            target_dir = os.path.dirname(target_log_path)
            if target_dir: # Only create if path includes a directory part
                 os.makedirs(target_dir, exist_ok=True)
            with open(target_log_path, 'w') as outfile:
                outfile.write(content_to_copy)
            print(f"Copied 'SECTION Run' onwards from {source_log_path} to {target_log_path}")
        else:
            print(f"Warning: 'SECTION Run' not found in {source_log_path}. Cannot copy section.")

    except IOError as e:
        print(f"Error copying log section from {source_log_path} to {target_log_path}: {e}")
    except Exception as e:
        print(f"Unexpected error during log section copy: {e}")


def write_stp_file(filename, nodes_in_smt, edges_in_smt, terminals_original, comment=""):
    """将 SMT 结果写入 .stp 文件"""
    num_nodes_smt = len(nodes_in_smt)
    num_edges_smt = len(edges_in_smt)
    num_terminals = len(terminals_original)

    with open(filename, 'w') as f:
        f.write("33D32945 STP File, STP Format Version 1.0\n") # 标准头
        f.write("SECTION Comment\n")
        f.write(f"Steiner Minimal Tree generated by Gurobi (Flow Balance Formulation)\n")
        if comment:
            f.write(f"{comment}\n")
        f.write("END\n\n")

        f.write("SECTION Graph\n")
        f.write(f"Nodes {num_nodes_smt}\n")
        f.write(f"Edges {num_edges_smt}\n")
        for u, v, cost in edges_in_smt:
            # Gurobi/Python 可能返回浮点数，确保成本是整数或适当格式
            cost_str = int(cost) if cost == int(cost) else f"{cost:.1f}" # Format cost
            f.write(f"E {u} {v} {cost_str}\n")
        f.write("END\n\n")

        f.write("SECTION Terminals\n")
        f.write(f"Terminals {num_terminals}\n")
        for t in terminals_original:
            # 确保输出的终端节点确实存在于SMT的节点中（理论上应该都在）
            nodes_set = set(nodes_in_smt) # Convert list to set for efficient lookup
            if t in nodes_set:
                f.write(f"T {t}\n")
            else:
                 print(f"Warning: Original terminal {t} is not in the final SMT node set? This might indicate an issue.")
                 # 即使不在，也可能需要列出，根据 .stp 严格定义
                 f.write(f"T {t}\n")
        f.write("END\n\n")

        f.write("EOF\n")

def write_stplog_file(log_filename, input_filename,
                      nodes_in_smt, edges_in_smt,terminals_original,
                      objective_value, solve_time,
                      solver_name="Gurobi", solver_version="N/A", threads_used="N/A"):
    """
    将 SMT 结果和运行信息写入 .stplog 文件, 模拟 SCIP-Jack 格式.
    Made more generic to handle Gurobi or SCIP-Jack info.

    Args:
        log_filename (str): 输出的 .stplog 文件名.
        input_filename (str): 原始输入的 .stp 文件名.
        nodes_in_smt (list/set): SMT 中的节点列表.
        edges_in_smt (list): SMT 中的边列表 [(u, v, cost), ...]. Cost is optional for SCIP-Jack.
        objective_value (float): SMT 的最终成本 (Primal bound).
        solve_time (float): Solver's total execution time.
        solver_name (str): Name of the solver used (e.g., "Gurobi", "SCIP-Jack").
        solver_version (str): Version string of the solver.
        threads_used (str/int): Threads used by the solver.
    """
    # Ensure objective value is not infinite for formatting
    objective_str = f"{objective_value:.9f}" if objective_value != float('inf') else "Infeasible/Error"
    nodes_in_smt_list = sorted(list(set(nodes_in_smt))) # Ensure unique and sorted nodes

    smt_pk_values=[]
    
    smt_pk_values,newKeyStrings=build_smt_pk_array(edges_in_smt,terminals_original,0,1)

    with open(log_filename, 'w') as f:
        # SECTION Comment
        f.write("SECTION Comment\n")
        f.write(f"Name {os.path.abspath(input_filename)}\n")
        f.write("Problem SPG\n")
        f.write(f"Program {solver_name}\n") # Use provided solver name
        f.write(f"Version {solver_version}\n") # Use provided version
        if smt_pk_values is not None:
            f.write(f"SMT_PK_Values {smt_pk_values}\n") # Add SMT PK values
        if len(newKeyStrings)>1:
            f.writelines(newKeyStrings)
        f.write("End\n\n")

        # SECTION Solutions
        f.write("SECTION Solutions\n")
        # Use total solve time as the time the final solution was found
        f.write(f"Solution {solve_time:.1f}            {objective_str}\n")
        f.write("End\n\n")

        # SECTION Run
        f.write("SECTION Run\n")
        f.write(f"Threads {threads_used}\n") # Use provided threads info
        f.write(f"Time {solve_time:.1f}\n")
        f.write(f"Primal    {objective_str}\n")
        f.write("End\n\n")

        # SECTION Finalsolution
        f.write("SECTION Finalsolution\n")
        if objective_value != float('inf') and nodes_in_smt_list: # Check if a valid solution exists
            num_vertices = len(nodes_in_smt_list)
            num_edges_smt = len(edges_in_smt)

            f.write(f"Vertices {num_vertices}\n")
            for v_node in nodes_in_smt_list:
                f.write(f"V {v_node}\n")

            f.write(f"Edges {num_edges_smt}\n")
            # Sort edges for consistent output (u < v)
            # SCIP-Jack log only needs connectivity, not cost here
            sorted_edges_tuples = sorted([(min(u,v), max(u,v)) for u, v, *_ in edges_in_smt]) # Handle edges with or without cost
            for u, v in sorted_edges_tuples:
                f.write(f"E {u} {v}\n")
        else:
             # No valid solution found
             f.write("Vertices 0\n")
             f.write("Edges 0\n")

        f.write("End\n") # File end

def _find_path(graph, start_node, end_node):
    """Finds a path between start_node and end_node in the graph using BFS."""
    if start_node == end_node:
        return [start_node]
    queue = deque([(start_node, [start_node])])  # (current_node, path_so_far)
    visited = {start_node}

    while queue:
        current_node, path = queue.popleft()

        for neighbor in graph.get(current_node, []):
            if neighbor == end_node:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None  # Path not found


def find_paths_qgraph_weighted_iterative(current_edges_dict,start_node, end_node, depth_limit):
    """
    基于 g_QGraph 迭代查找 Q 值总和最小的路径，
    并检查路径跳数是否超过 depth_limit。
    使用 current_edges_dict 过滤可用的边。

    Args:
        start_node: 起始节点
        end_node: 目标节点
        depth_limit (int): 路径跳数限制
        current_edges_dict (dict): 当前可用边的字典 {(u, v): cost}

    Returns:
        list: 路径信息列表，每个元素包含路径节点、边键和 PK 值
              [{'nodes': [...], 'edges_keys': [...], 'pk': ...}, ...]
              (与原 find_paths_limited_depth 输出结构一致)
    """
    paths_info = []

    if g_QGraph is None:
        print("Error: common.g_QGraph is not initialized.")
        return paths_info
    if g_QureyEdgeQValues_map is None:
         print("Error: common.g_QureyEdgeQValues_map is not initialized (needed for Q values).")
         return paths_info

    # Step 1: Create a copy of the QGraph, filtered by current_edges_dict
    tempQGraph = nx.Graph() # Create an empty graph first
    for edge_key in current_edges_dict:
        u, v = edge_key
        if g_QGraph.has_edge(u, v): # Check if the original QGraph has this edge
            edge_data = g_QGraph.get_edge_data(u, v)
            tempQGraph.add_edge(u, v, **edge_data) # Add edge with original attributes (like 'cost')
        else:
            print(f"Warning: Edge {edge_key} from current_edges_dict not found in g_QGraph. Skipping.")


    while True:
        try:
            # Step 2: Find the shortest path based on Q value sum (weight='cost')
            # Note: 'cost' attribute holds the Q value in g_QGraph
            path_nodes = nx.shortest_path(tempQGraph, source=start_node, target=end_node, weight='cost')

            # ... (后续步骤与之前的框架相同，从检查 depth_limit 开始)
            # ... (包括计算 PK 值，移除路径边等)
            path_length_hops = len(path_nodes) - 1

            # Step 3: Check hop count limit for the *newly found* path
            if path_length_hops > depth_limit:
                print(f"Found shortest path (Q-sum weighted) has {path_length_hops} hops, exceeding depth_limit {depth_limit}. Stopping.")
                break # Stop iteration

            # Extract edges and Q values for the found path
            path_edges_keys = []
            path_q_values = []
            valid_path = True
            for i in range(path_length_hops):
                u, v = path_nodes[i], path_nodes[i+1]
                edge_key = tuple(sorted((u, v)))
                path_edges_keys.append(edge_key)

                # Get Q value from the original map (more reliable than graph copy attribute)
                q_value = g_QureyEdgeQValues_map.get(edge_key)
                if q_value is None:
                    print(f"Warning: Q-value missing for edge {edge_key} in path. Skipping PK calculation for this path.")
                    valid_path = False
                    # We still need to remove the path edges later, so don't break the inner loop here
                    # Just mark the path as invalid for PK calculation
                else:
                     path_q_values.append(q_value)


            # Calculate PK value if the path had valid Q values
            if valid_path and path_q_values: # Ensure Q values were found
                try:
                    path_q_values.sort() # PK calculation requires sorted Q values
                    pk_i = pthGen.linkIDValue(path_q_values)
                    # Add to results, matching original function's structure
                    paths_info.append({
                        'nodes': list(path_nodes),
                        'edges_keys': list(path_edges_keys),
                        'pk': pk_i
                    })
                    print(f"Found valid path (hops={path_length_hops}, PK={pk_i}): {path_nodes}")
                except Exception as e:
                    print(f"Error calculating PK for path {path_nodes}: {e}")
                    # Decide if we should still remove the path edges even if PK fails? Yes.
            elif valid_path and not path_q_values and path_length_hops > 0:
                 print(f"Warning: Path {path_nodes} found, but no Q-values collected (likely missing in map). Skipping PK.")
            elif not valid_path:
                 print(f"Skipping PK calculation for path {path_nodes} due to missing Q values.")


            # Step 2 (cont.): Remove the edges of the found path P from tempQGraph
            # Remove edges regardless of PK calculation success/failure or missing Q values,
            # as the path itself was found by shortest_path.
            edges_to_remove = []
            for i in range(path_length_hops):
                 u, v = path_nodes[i], path_nodes[i+1]
                 # Check if edge exists before removing
                 if tempQGraph.has_edge(u, v):
                      edges_to_remove.append((u,v))

            if edges_to_remove:
                 tempQGraph.remove_edges_from(edges_to_remove)
                 print(f"Removed {len(edges_to_remove)} edges from tempQGraph corresponding to the found path.")
            elif path_length_hops > 0:
                 # This might indicate an issue if path had hops but no edges were removed
                 print(f"Warning: Path {path_nodes} found (hops={path_length_hops}), but no corresponding edges removed from tempQGraph.")


        except nx.NetworkXNoPath:
            print(f"No more paths found between {start_node} and {end_node} in tempQGraph based on Q-value sum.")
            break # No path exists, stop iteration
        except nx.NodeNotFound as e:
             print(f"Error: Node not found in tempQGraph: {e}. Stopping.")
             break
        except Exception as e:
            print(f"An unexpected error occurred during path finding/processing: {e}")
            import traceback
            traceback.print_exc()
            break # Stop on unexpected errors

    # Sort final results by PK value (optional, but might be useful)
    # paths_info.sort(key=lambda x: x.get('pk', float('inf')))

    return paths_info

def find_paths_limited_depth(graph_edges_dict, start_node, end_node, depth_limit):
    """
    使用深度限制搜索 (DLS) 查找图中两节点之间指定深度限制内的所有路径，并计算每条路径的 PK 值。

    Args:
        graph_edges_dict (dict): 图的边字典 {(u, v): cost}
        start_node: 起始节点
        end_node: 目标节点
        depth_limit (int): 路径深度限制

    Returns:
        list: 路径信息列表，每个元素包含路径节点、边和 PK 值
    """
    paths_info = []
    adj = defaultdict(list)
    edge_set_for_lookup = set()
    for u, v in graph_edges_dict.keys():  # 只需要边键，不需要 cost
        adj[u].append(v)
        adj[v].append(u)
        edge_set_for_lookup.add(tuple(sorted((u, v))))

    def _dfs_paths(current_node, path_nodes, path_edges_keys):
        if current_node == end_node:
            # 计算路径 PK 值
            path_q_values = []
            for edge_key in path_edges_keys:
                q_value = g_QureyEdgeQValues_map.get(edge_key)
                if q_value is None:
                    print(f"Warning: Q-value missing for edge {edge_key} in path, skipping path PK calculation.")
                    return # 忽略此路径，不添加到结果中
                path_q_values.append(q_value)
            try:
                
                pk_i = pthGen.linkIDValue(path_q_values)
                paths_info.append({
                    'nodes': list(path_nodes),
                    'edges_keys': list(path_edges_keys),
                    'pk': pk_i
                })
            except Exception as e:
                print(f"Error calculating PK for path: {e}")
            return

        if len(path_nodes) > depth_limit:
            return  # 超过深度限制，停止搜索

        for neighbor in adj[current_node]:
            if neighbor not in path_nodes:  # 避免环路
                edge_key = tuple(sorted((current_node, neighbor)))
                if edge_key in edge_set_for_lookup:
                    _dfs_paths(neighbor, path_nodes + (neighbor,), path_edges_keys + (edge_key,))

    _dfs_paths(start_node, (start_node,), tuple())
    return paths_info


def find_middle_worst_path_and_pk(smt_nodes, smt_edges_with_cost, terminals, M=MIDDLE_MPATHS):
    """Finds the paths with the highest M PK values in the SMT."""
    if len(terminals) != 11: return None, []  # Return path_edges as well
    if g_QureyEdgeQValues_map is None: return None, []

    rootidx = ROOT_TERMINAL_IDX
    root = terminals[rootidx]
    other_terminals = terminals[:rootidx] + terminals[rootidx+1:]

    adj = defaultdict(list)
    edge_set_for_lookup = set()
    for u, v, cost in smt_edges_with_cost:
        adj[u].append(v)
        adj[v].append(u)
        edge_set_for_lookup.add(tuple(sorted((u, v))))

    pk_values = []
    paths_info = []

    for target_terminal in other_terminals:
        path_nodes = _find_path(adj, root, target_terminal)
        if path_nodes is None:
            print(f"Warning: No path found from {root} to {target_terminal} in SMT for PK calculation.")
            continue

        path_q_values = []
        current_path_edges_keys = []
        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i+1]
            edge_key = tuple(sorted((u, v)))
            if edge_key not in edge_set_for_lookup:
                 print(f"Warning: Edge {edge_key} from path not in SMT edge set.")
                 continue  # Should not happen

            q_value = g_QureyEdgeQValues_map.get(edge_key)
            if q_value is None:
                print(f"Warning: Q-value missing for edge {edge_key} in path {root}->{target_terminal}.")
                # Decide how to handle missing Q: skip path, error out, or assign default?
                # Let's skip the path for PK calculation if Q is missing.
                current_path_edges_keys = []  # Invalidate this path's edges
                break

            path_q_values.append(q_value)
            current_path_edges_keys.append(edge_key)

        if not current_path_edges_keys:  # Path was skipped or had no edges
             continue

        path_q_values.sort()
        try:
            import pathsSeqGen as pthGen
            pk_i = pthGen.linkIDValue(path_q_values)
            pk_values.append(pk_i)
            paths_info.append({
                'nodes': path_nodes,
                'edges_keys': current_path_edges_keys,
                'pk': pk_i
            })
        except AttributeError:
             print("Error: pathsSeqGen.linkIDValue function not available during PK calculation.")
             return None, []  # Error state
        except Exception as e:
            print(f"Error calculating PK for path {root}->{target_terminal}: {e}")
            continue  # Ignore errors for this specific path

    if not pk_values:
        print("Warning: Could not determine any path with a valid PK value.")
        return None, []

    # Sort paths by PK value descending
    paths_info.sort(key=lambda x: -x['pk'])

    # Select the middle M paths
    start_index =max(0,(len(paths_info)-M+1) // 2)
    end_index= start_index + M

    selected_paths_info = paths_info[start_index:end_index]
    selected_pk_values = [info['pk'] for info in selected_paths_info]

    return selected_paths_info, selected_pk_values

def is_graph_still_connected(nodes_list, edges_dict, terminals_list):
    """验证所有终端节点是否在同一个连通分量中

    Args:
        nodes_list (list): 图中所有节点的列表（包含孤立节点）
        edges_dict (dict): 边字典 {(u, v): cost}
        terminals_list (list): 需要检查连通性的终端节点列表

    Returns:
        bool: 当且仅当所有终端节点在同一个连通分量时返回True
    """
    # 空图或无效输入处理
    if not terminals_list:
        return True  # 无终端需要连接
    if len(terminals_list) == 1:
        return True  # 单个终端总是连通
    if not edges_dict and len(terminals_list) > 1:
        return False  # 无边的多终端图必然不连通

    # 创建无向图
    G = nx.Graph()

    # 添加所有节点（确保孤立节点被包含）
    G.add_nodes_from(nodes_list)

    # 添加边（networkx会自动处理节点）
    G.add_edges_from(edges_dict.keys())

    # 检查终端存在性
    missing_terminals = [t for t in terminals_list if t not in G]
    if missing_terminals:
        print(f"连通性检查失败：终端 {missing_terminals} 不在图中")
        return False

    # 核心逻辑：检查所有终端的连通性
    connected_components = list(nx.connected_components(G))

    # Check if all terminals are in the *same* connected component
    if not connected_components:  # Should not happen if terminals exist in G
        return False

    first_terminal = terminals_list[0]
    component_of_first = None
    for component in connected_components:
        if first_terminal in component:
            component_of_first = component
            break

    if component_of_first is None:
        # This means the first terminal wasn't found in any component, which is an error state
        print(f"Error: First terminal {first_terminal} not found in any connected component.")
        return False

    # Check if all other terminals are in this same component
    all_terminals_connected = all(t in component_of_first for t in terminals_list)

    if not all_terminals_connected:
        print(f"连通性检查失败：并非所有终端都在同一个连通分量中。")
        # Optional: Print which terminals are in which component for debugging
        # terminal_components = {t: None for t in terminals_list}
        # for i, comp in enumerate(connected_components):
        #     for t in terminals_list:
        #         if t in comp:
        #             terminal_components[t] = i
        # print(f"Terminal component mapping: {terminal_components}")

    return all_terminals_connected

def build_smt_pk_array(edges, terminals, rootidx=0,printKey=0):
    """
    构建 SMT 的 PK 值数组。
    输入为 SMT 的边列表和终端节点列表，rootidx 默认为 0。
    
    Args:
        edges (list): SMT 中的边列表 [(u, v, cost), ...]。
        terminals (list): 终端节点列表。
        rootidx (int): 根节点在 terminals 列表中的索引，默认为 0。
    
    Returns:
        list: 排序后的 PK 值数组（即 sm_tree）。
        如果终端数量不是 11 或路径查找失败，返回空列表。
    """
    # 1. 检查终端数量是否为 11
    if len(terminals) != 11:
        print(f"Warning: build_smt_pk_array expects 11 terminals. Found {len(terminals)}. Returning empty list.")
        return [],[]
        
    if g_QureyEdgeQValues_map is None:
        print("Error: g_QureyEdgeQValues_map is not initialized. Cannot build smt_pk_array.")
        return [],[]
    
    root = terminals[rootidx]
    other_terminals = terminals[:rootidx] + terminals[rootidx+1:]  # 排除根节点

    # 构建邻接表表示 SMT 图
    adj = defaultdict(list)
    edge_set_for_lookup = set()  # 存储边用于快速查找
    for u, v, _ in edges:
        adj[u].append(v)
        adj[v].append(u)
        edge_set_for_lookup.add(tuple(sorted((u, v))))

    all_paths_q_values = []  # 存储每个路径 Pi 的排序后的 Q 值列表
    mapPathtoPK = {}  # 存储路径索引以供后续使用

    # 2. 查找从 root 到其他每个 terminal 的路径并获取 Q 值
    for target_terminal in other_terminals:
        path_nodes = _find_path(adj, root, target_terminal)

        if path_nodes is None:
            print(f"Error: Could not find path from root {root} to terminal {target_terminal} in the SMT solution.")
            return [],[]  # 路径必须存在于有效的 SMT 中

        path_q_values = []
        # 遍历路径中的边
        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i+1]
            edge_key = tuple(sorted((u, v)))

            # 确保路径中的边存在于原始 SMT 边列表中
            if edge_key not in edge_set_for_lookup:
                print(f"Error: Edge {edge_key} from found path not in original SMT edges.")
                return [],[]

            q_value = g_QureyEdgeQValues_map.get(edge_key)
            if q_value is None:
                print(f"Error: Q-value not found for edge {edge_key} in g_QureyEdgeQValues_map.")
                return [],[]
            path_q_values.append(q_value)

        path_q_values.sort()  # 对该路径的 Q 值进行排序
        all_paths_q_values.append(path_q_values)
        mapPathtoPK[len(all_paths_q_values)-1] = (root, target_terminal)  # 存储路径索引

    # 检查是否得到正好 10 个路径的 Q 值列表
    if len(all_paths_q_values) != 10:
        print(f"Error: Expected 10 paths from root, but collected Q-values for {len(all_paths_q_values)} paths.")
        return [],[]

    # 3. 计算每个路径的 PK 值
    pk_values = []
    insertStrings=[]
    try:
        newlink = 0
        pathidx = -1
        for pi_q_values in all_paths_q_values:
            pathidx += 1
            if not pi_q_values:
                print(f"Warning: Encountered empty Q-value list when calculating PK value.")
                pk_values.append(0)  # 或其他默认 PK 值
                continue
            
            currentEdge = mapPathtoPK[pathidx]
            pk_i = pthGen.linkIDValue(pi_q_values)
            
            if pk_i not in pthGen.ValuToLinkMapDic.keys():
                # 动态插入链接到字典中
                pthGen.ValuToLinkMapDic[pk_i] = pi_q_values
                #insertSTr=f'''NewKey {pk_i}:{pi_q_values} \n'''
                #insertStrings.append(insertSTr)
                newlink = 1

            pk_values.append(pk_i)
            
        if newlink:
            pthGen.updateValuToLinkMapDic()
    except AttributeError:
        print("Error: 'pathsSeqGen' module (pthGen) or 'linkIDValue' function not available.")
        return [],[]
    except Exception as e:
        print(f"Error calculating PK value using pthGen.linkIDValue: {e}")
        return [],[]

    if len(pk_values) != 10:
        print(f"Error: Expected 10 PK values, but calculated {len(pk_values)}.")
        return [],[]

    # 4. 构建 PK 数组并排序
    smt_pk_array = pk_values
    smt_pk_array.sort()
    if printKey:
        for key in smt_pk_array:
            strPK=f"{key}:{pthGen.ValuToLinkMapDic[key]}\n"
            insertStrings.append(strPK)

    return smt_pk_array,insertStrings
