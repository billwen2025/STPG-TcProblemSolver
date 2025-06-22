#!/usr/bin/env python3
import os, sys, time
from collections import defaultdict
import STPGcommon as common


# Renamed from find_edge_to_remove_from_invalid_smt
def find_edge_to_remove_from_invalid_smt_alg0(smt_nodes, smt_edges_with_cost, terminals, current_edges_dict):
    """Identifies the edge to remove from the worst path of an invalid SMT using the original algorithm (alg0), prioritizing connectivity."""

    # 1. Find the middle worst paths (middle M PKs)
    worst_paths_info, worst_pks = common.find_middle_worst_path_and_pk(smt_nodes, smt_edges_with_cost, terminals)

    if not worst_paths_info:
        print("Error: Could not determine the worst paths to identify edges for removal.")
        return None

    print(f"Worst paths (PKs={worst_pks}) nodes: {[info['nodes'] for info in worst_paths_info]}")
    print(f"Worst paths edges (keys): {[info['edges_keys'] for info in worst_paths_info]}")

    # 2. Find usage count of all edges in the SMT across all root-terminal paths
    edge_usage_count = defaultdict(int)
    adj = defaultdict(list)
    edge_set_for_lookup = set()
    for u, v, _ in smt_edges_with_cost:
        adj[u].append(v)
        adj[v].append(u)
        edge_set_for_lookup.add(tuple(sorted((u, v))))

    rootidx = common.ROOT_TERMINAL_IDX
    root = terminals[rootidx]
    other_terminals = terminals[:rootidx] + terminals[rootidx+1:]

    for target_terminal in other_terminals:
        path_nodes = common._find_path(adj, root, target_terminal)
        if path_nodes:
            for i in range(len(path_nodes) - 1):
                u, v = path_nodes[i], path_nodes[i+1]
                edge_key = tuple(sorted((u, v)))
                if edge_key in edge_set_for_lookup:
                    edge_usage_count[edge_key] += 1

    # 3. Filter edges in the worst paths that are used only once (unique to these paths in the SMT)
    unique_worst_paths_edges_info = []
    for path_info in worst_paths_info:
        for edge_key in path_info['edges_keys']:
            if edge_usage_count[edge_key] == 1:
                if edge_key in current_edges_dict:  # Get cost from the *current* problem dict
                    cost = current_edges_dict[edge_key]
                    q_value = common.g_QureyEdgeQValues_map.get(edge_key, float('inf'))  # Get Q value
                    unique_worst_paths_edges_info.append({'key': edge_key, 'cost': cost, 'q': q_value})
                else:
                    # This means the edge was in the SMT but somehow not in the dict used to generate the SMT? Error.
                    print(f"CRITICAL Error: Edge {edge_key} from worst path not in current_edges_dict!")
                    return None

    candidate_edges_for_removal = []
    selection_method = ""  # Initialize selection_method

    if not unique_worst_paths_edges_info:
        print("Warning: No edges on the worst paths are unique to them within the SMT. Cannot use uniqueness criteria.")
        # Fallback Strategy: Remove the lowest cost edge from the worst paths directly?
        # Or remove the edge with lowest cost / highest Q? Let's try lowest cost first.
        selection_method = "Fallback (Worst Paths Min Cost)"  # Assign selection_method
        worst_paths_edges_info = []
        for path_info in worst_paths_info:
            for edge_key in path_info['edges_keys']:
                if edge_key in current_edges_dict:
                    cost = current_edges_dict[edge_key]
                    q_value = common.g_QureyEdgeQValues_map.get(edge_key, float('inf'))
                    worst_paths_edges_info.append({'key': edge_key, 'cost': cost, 'q': q_value})
                else:
                    print(f"CRITICAL Error: Edge {edge_key} from worst path not in current_edges_dict!")
                    return None
        if not worst_paths_edges_info:
            print("Error: Could not get info for any edge on the worst paths.")
            return None

        print("Fallback: Selecting lowest cost edge from the entire worst paths.")
        min_cost = float('inf')
        for edge_info in worst_paths_edges_info:
            min_cost = min(min_cost, edge_info['cost'])
        candidate_edges_for_removal = [e for e in worst_paths_edges_info if e['cost'] == min_cost]
        # Apply Q-value tie-breaker if needed
        if len(candidate_edges_for_removal) > 1:
            min_q = float('inf')
            selected_edge_info = None
            for edge_info in candidate_edges_for_removal:
                if edge_info['q'] < min_q:
                    min_q = edge_info['q']
                    selected_edge_info = edge_info
            if selected_edge_info is None:
                selected_edge_info = candidate_edges_for_removal[0]  # Default tie-break
            candidate_edges_for_removal = [selected_edge_info]
        # End Fallback

    else:
        # --- Original Logic: Use unique edges ---
        print(f"Unique edges on worst paths: {unique_worst_paths_edges_info}")
        selection_method = "Unique Worst Paths Min Cost"  # Assign selection_method

        # 4. Find the edge with the minimum cost among the unique edges
        min_cost = float('inf')
        for edge_info in unique_worst_paths_edges_info:
            min_cost = min(min_cost, edge_info['cost'])

        candidate_edges_for_removal = [e for e in unique_worst_paths_edges_info if e['cost'] == min_cost]

        print(f"Candidate edges for removal (min cost={min_cost}): {candidate_edges_for_removal}")

        # 5. If tie in cost, find the one with the minimum Q-value
        if len(candidate_edges_for_removal) > 1:
            min_q = float('inf')
            selected_edge_info = None
            for edge_info in candidate_edges_for_removal:
                if edge_info['q'] < min_q:
                    min_q = edge_info['q']
                    selected_edge_info = edge_info
            if selected_edge_info is None and candidate_edges_for_removal:
                selected_edge_info = candidate_edges_for_removal[0]  # Default tie-break
            candidate_edges_for_removal = [selected_edge_info] if selected_edge_info else []
        # --- End Original Logic ---

    if not candidate_edges_for_removal:
        print(f"Error: ({selection_method}) Could not select candidate edge to remove after cost/Q comparison.")
        return None

    # --- Prioritize Connectivity ---
    print(f"Checking connectivity for {len(candidate_edges_for_removal)} candidate edge(s) selected by {selection_method}...")
    non_bridge_primary_candidates = []
    bridge_primary_candidates = []

    # Check each primary candidate edge
    for edge_info in candidate_edges_for_removal:
        edge_key = edge_info['key']
        temp_edges_dict = {k: v for k, v in current_edges_dict.items() if k != edge_key}
        # Use initial_nodes for a robust connectivity check across the original graph structure
        # We need access to initial_nodes here. Let's assume it's available or passed.
        # For now, using smt_nodes as a proxy, but this might be less accurate if SMT is disconnected subset
        # TODO: Consider passing initial_nodes if available for better accuracy
        if common.is_graph_still_connected(smt_nodes, temp_edges_dict, terminals):
            non_bridge_primary_candidates.append(edge_info)
        else:
            bridge_primary_candidates.append(edge_info)

    selected_edge_info = None
    if non_bridge_primary_candidates:
        print(f"Found {len(non_bridge_primary_candidates)} non-bridge primary candidate(s). Selecting the best one.")
        # The list candidate_edges_for_removal already contains the best based on cost/QoS tie-break
        selected_edge_info = non_bridge_primary_candidates[0]
        selection_info_str = f"Alg0 - {selection_method} (Non-Bridge)"
    elif bridge_primary_candidates:
        print(f"Warning: All {len(bridge_primary_candidates)} primary candidate(s) are bridges. Looking for other non-bridge edges.")
        # Fallback: Look for any other edge in the SMT that is not a bridge
        other_non_bridges = []
        primary_bridge_keys = {info['key'] for info in bridge_primary_candidates}
        smt_edge_keys_in_current = {tuple(sorted((u, v))) for u, v, _ in smt_edges_with_cost if tuple(sorted((u, v))) in current_edges_dict}

        for edge_key in smt_edge_keys_in_current:
            if edge_key not in primary_bridge_keys:
                temp_edges_dict = {k: v for k, v in current_edges_dict.items() if k != edge_key}
                if common.is_graph_still_connected(smt_nodes, temp_edges_dict, terminals):
                    cost = current_edges_dict[edge_key]
                    q_value = common.g_QureyEdgeQValues_map.get(edge_key, float('inf'))
                    other_non_bridges.append({'key': edge_key, 'cost': cost, 'q': q_value})

        if other_non_bridges:
            print(f"Found {len(other_non_bridges)} other non-bridge edge(s) in the SMT. Selecting the one with the lowest cost.")
            other_non_bridges.sort(key=lambda x: (x['cost'], x['q']))  # Sort by cost ascending, then Q ascending
            selected_edge_info = other_non_bridges[0]
            selection_info_str = "Alg0 - Fallback (Lowest Cost Non-Bridge)"
        else:
            print("Warning: No other non-bridge edges found in the SMT. Reluctantly selecting the best bridge from primary candidates.")
            selected_edge_info = bridge_primary_candidates[0]  # Select the best bridge based on original criteria
            selection_info_str = f"Alg0 - {selection_method} (Bridge - No Alternative)"
    else:
        # This case should not happen if candidate_edges_for_removal was not empty
        print("Error: No candidates found after connectivity check.")
        return None

    edge_to_remove_key = selected_edge_info['key']
    final_cost = selected_edge_info['cost']
    print(f"Final selected edge for removal ({selection_info_str}): {edge_to_remove_key} (Cost: {final_cost}, Q: {selected_edge_info['q']})")

    # Return the edge details (u, v, cost)
    return (edge_to_remove_key[0], edge_to_remove_key[1], final_cost)


def find_edge_to_remove_from_invalid_smt_alg1(smt_nodes, smt_edges_with_cost, terminals, current_edges_dict):
    """Identifies the edge to remove from an invalid SMT by selecting the highest cost unique edge across all paths, prioritizing connectivity."""

    # 1. Find the middle worst paths to identify edges contributing to invalidity
    worst_paths_info, worst_pks = common.find_middle_worst_path_and_pk(smt_nodes, smt_edges_with_cost, terminals)

    if not worst_paths_info:
        print("Error: Could not determine the worst paths to identify edges for removal.")
        return None

    print(f"Worst paths (PKs={worst_pks}) nodes: {[info['nodes'] for info in worst_paths_info]}")
    print(f"Worst paths edges (keys): {[info['edges_keys'] for info in worst_paths_info]}")

    # 2. Build adjacency list and edge set for connectivity and path analysis
    adj = defaultdict(list)
    edge_set_for_lookup = set()
    for u, v, _ in smt_edges_with_cost:
        adj[u].append(v)
        adj[v].append(u)
        edge_set_for_lookup.add(tuple(sorted((u, v))))

    # 3. Compute bridge value for edges using a simplified approach
    # Bridge value approximation: edges that are part of fewer alternative paths have higher bridge value
    # We will prioritize edges with low bridge value (less critical to overall connectivity)
    edge_bridge_value = defaultdict(float)
    rootidx = common.ROOT_TERMINAL_IDX
    root = terminals[rootidx]
    other_terminals = terminals[:rootidx] + terminals[rootidx+1:]

    # Count how many root-to-terminal paths each edge appears in (approximates bridge importance)
    edge_usage_count = defaultdict(int)
    for target_terminal in other_terminals:
        path_nodes = common._find_path(adj, root, target_terminal)
        if path_nodes:
            for i in range(len(path_nodes) - 1):
                u, v = path_nodes[i], path_nodes[i+1]
                edge_key = tuple(sorted((u, v)))
                if edge_key in edge_set_for_lookup:
                    edge_usage_count[edge_key] += 1

    # Assign bridge value: lower usage count means higher bridge value (more critical)
    # But for removal, we want edges with high usage count (low bridge value) to be less critical
    # Inverse relation: bridge_value = 1 / usage_count (or some function)
    for edge_key in edge_set_for_lookup:
        usage = edge_usage_count.get(edge_key, 0)
        if usage == 0:
            edge_bridge_value[edge_key] = float('inf')  # Not used in any path, critical if it's a bridge
        else:
            edge_bridge_value[edge_key] = 1.0 / usage  # Higher usage means lower bridge value (less critical)

    # 4. Collect edge information with cost, Q value, bridge value, and whether it's on the worst path
    edges_info = []
    all_worst_path_edges_keys = set()
    for path_info in worst_paths_info:
        all_worst_path_edges_keys.update(path_info['edges_keys'])

    for edge_key in edge_set_for_lookup:
        if edge_key in current_edges_dict:
            cost = current_edges_dict[edge_key]
            q_value = common.g_QureyEdgeQValues_map.get(edge_key, float('inf'))
            on_worst_path = edge_key in all_worst_path_edges_keys
            bridge_val = edge_bridge_value[edge_key]
            edges_info.append({
                'key': edge_key,
                'cost': cost,
                'q': q_value,
                'bridge_value': bridge_val,
                'on_worst_path': on_worst_path
            })
        else:
            print(f"CRITICAL Error: Edge {edge_key} from SMT not in current_edges_dict!")
            return None

    print(f"Edges with bridge values: {edges_info}")

    # 5. Sort edges by a combined score to prioritize removal
    # Priority: edges on worst path, low bridge value (high usage count), high cost, high Q value
    edges_info.sort(key=lambda x: (-x['on_worst_path'], x['bridge_value'], -x['cost'], -x['q']))
    # This sorts:
    # 1. First by whether on worst path (descending, True first)
    # 2. Then by bridge value (ascending, lower bridge value first, meaning less critical)
    # 3. Then by cost (descending, higher cost first)
    # 4. Then by Q value (descending, higher Q first)

    # 6. Check connectivity for each edge removal starting from the prioritized list
    for edge_info in edges_info:
        edge_key = edge_info['key']
        # Create a temporary edge dictionary without this edge
        temp_edges_dict = {k: v for k, v in current_edges_dict.items() if k != edge_key}
        # Check if removing this edge maintains connectivity
        if common.is_graph_still_connected(smt_nodes, temp_edges_dict, terminals):
            print(f"Selected edge for removal (cost={edge_info['cost']}, bridge_value={edge_info['bridge_value']}, on_worst_path={edge_info['on_worst_path']}, maintains connectivity): {edge_key}")
            return (edge_key[0], edge_key[1], edge_info['cost'])
        else:
            print(f"Edge {edge_key} with cost {edge_info['cost']} would disconnect graph, skipping.")

    print("Error: No edge can be removed without disconnecting the graph.")
    return None


def find_edge_to_remove_from_invalid_smt_alg2(smt_nodes, smt_edges_with_cost, terminals, current_edges_dict):
    """Identifies the edge to remove from an invalid SMT by calculating bridge_value
    based on indirect connection strength with Q-value based paths from candidate_paths_info.
    Ensures the selected edge is from smt_edges_with_cost to impact the solution.
    """

    # 1. 获取 SMT 中间最差路径信息和 PK 阈值
    worst_paths_info, worst_pks = common.find_middle_worst_path_and_pk(smt_nodes, smt_edges_with_cost, terminals)

    if not worst_paths_info:
        print("Error: Could not determine the worst paths to identify edges for removal.")
        return None

    pk_threshold = worst_paths_info[0]['pk']  # 取最高PK值作为阈值
    print(f"SMT Middle Worst Paths PKs: {worst_pks}, PK Threshold: {pk_threshold}")

    # 计算搜索深度限制
    max_smt_hops = 0
    for path_info in worst_paths_info:
        max_smt_hops = max(max_smt_hops, len(path_info['edges_keys']))
    search_depth_limit = max_smt_hops + 3  # 增加 3 跳作为缓冲区

    # 2. 查找基于 Q 值的路径，不限制范围到 SMT
    candidate_paths_info = []
    rootidx = common.ROOT_TERMINAL_IDX
    root = terminals[rootidx]
    other_terminals = terminals[:rootidx] + terminals[rootidx+1:]

    for target_terminal in other_terminals:
        paths_info = common.find_paths_qgraph_weighted_iterative(current_edges_dict, root, target_terminal, search_depth_limit)
        if not paths_info:
            print(f"Warning: No path found from {root} to {target_terminal} within depth limit.")
            continue

        for path_info in paths_info:
            if path_info['pk'] >= pk_threshold:  # 筛选PK值高于阈值的路径
                candidate_paths_info.append(path_info)

    if not candidate_paths_info:
        print("Warning: No candidate paths found with PK value higher than threshold. Falling back to SMT edges scoring.")
    else:
        print(f"Candidate paths for edge removal (count: {len(candidate_paths_info)}), ordered by PK desc:")
        for path_info in candidate_paths_info[:3]:  # 打印前 3 条路径信息
            print(f"  PK={path_info['pk']:.2f}, Nodes={[node for node in path_info['nodes']]}, Edges={[common.key_str(key) for key in path_info['edges_keys']]}")

    # 3. 计算 SMT 中每条边的 bridge_value，基于与候选路径的间接联系强度
    edge_bridge_value = {}
    base_value = 100.0  # 默认高值
    shared_node_factor = 5.0  # 共享节点路径数量的权重
    q_value_similarity_factor = 10.0  # Q 值相似性的权重
    max_q_difference = max(common.Q_VALUES) - min(common.Q_VALUES) if common.Q_VALUES else 1.0  # Q 值最大差异，用于归一化

    # 获取所有候选路径中的节点和边的 Q 值统计
    path_nodes = set()
    path_q_values = []
    for path_info in candidate_paths_info:
        path_nodes.update(path_info['nodes'])
        for edge_key in path_info['edges_keys']:
            q_value = common.g_QureyEdgeQValues_map.get(edge_key)
            if q_value is not None:
                path_q_values.append(q_value)

    avg_path_q = sum(path_q_values) / len(path_q_values) if path_q_values else 0.0

    for u, v, cost in smt_edges_with_cost:
        edge_key = tuple(sorted((u, v)))
        # 计算共享节点数量
        shared_nodes = sum(1 for node in (u, v) if node in path_nodes)
        num_shared_paths = sum(1 for path_info in candidate_paths_info if u in path_info['nodes'] or v in path_info['nodes'])
        # 计算 Q 值相似性
        edge_q = common.g_QureyEdgeQValues_map.get(edge_key, 0.0)
        q_similarity = 1.0 - abs(edge_q - avg_path_q) / max_q_difference if max_q_difference > 0 else 0.0
        # 计算 bridge_value
        bridge_value = base_value - (shared_node_factor * num_shared_paths) - (q_value_similarity_factor * q_similarity)
        edge_bridge_value[edge_key] = max(bridge_value, 0.0)  # 确保 bridge_value 不为负值

    # 4. 为 SMT 中的每条边计算综合评分
    edges_info = []
    all_worst_path_edges_keys = set()
    for path_info in worst_paths_info:
        all_worst_path_edges_keys.update(path_info['edges_keys'])

    for u, v, cost in smt_edges_with_cost:
        edge_key = tuple(sorted((u, v)))
        q_value = common.g_QureyEdgeQValues_map.get(edge_key, 0.0)
        on_worst_path = edge_key in all_worst_path_edges_keys
        bridge_val = edge_bridge_value.get(edge_key, base_value)
        # 综合评分：结合是否在最差路径上、bridge_value、成本和 Q 值
        score = (20.0 if on_worst_path else 0.0) - (5.0 * bridge_val / base_value) + (0.5 * cost) - (10.0 * q_value)
        edges_info.append({
            'key': edge_key,
            'cost': cost,
            'q': q_value,
            'bridge_value': bridge_val,
            'on_worst_path': on_worst_path,
            'score': score
        })

    #print(f"SMT edges with scores: {edges_info}")

    # 5. 按综合评分从低到高排序边
    edges_info.sort(key=lambda x: x['score'])

    # 6. 检查每条边的移除是否保持连通性
    for edge_info in edges_info:
        edge_key = edge_info['key']
        temp_edges_dict = {k: v for k, v in current_edges_dict.items() if k != edge_key}
        if common.is_graph_still_connected(smt_nodes, temp_edges_dict, terminals):
            print(f"Selected edge for removal (Alg2, score={edge_info['score']:.2f}, cost={edge_info['cost']}, bridge_value={edge_info['bridge_value']:.2f}, on_worst_path={edge_info['on_worst_path']}, maintains connectivity): {common.key_str(edge_key)}")
            return (edge_key[0], edge_key[1], edge_info['cost'])
        else:
            print(f"Edge {common.key_str(edge_key)} with score {edge_info['score']:.2f} would disconnect graph, skipping.")

    print("Error: No edge can be removed without disconnecting the graph in Alg2.")
    return None


def find_edge_to_remove_from_invalid_smt_alg3(smt_nodes, smt_edges_with_cost, terminals, current_edges_dict):
    """Identifies the edge to remove from an invalid SMT using a comprehensive scoring system
    that balances PK value, cost, Q value, and bridge value, while prioritizing connectivity."""
    
    # 1. 获取 SMT 中间最差路径信息和 PK 值
    worst_paths_info, worst_pks = common.find_middle_worst_path_and_pk(smt_nodes, smt_edges_with_cost, terminals)
    
    if not worst_paths_info:
        print("Error: Could not determine the worst paths to identify edges for removal.")
        return None
    
    print(f"Worst paths (PKs={worst_pks}) nodes: {[info['nodes'] for info in worst_paths_info]}")
    print(f"Worst paths edges (keys): {[info['edges_keys'] for info in worst_paths_info]}")
    
    # 2. 构建邻接表和边集，用于连通性和路径分析
    adj = defaultdict(list)
    edge_set_for_lookup = set()
    for u, v, _ in smt_edges_with_cost:
        adj[u].append(v)
        adj[v].append(u)
        edge_set_for_lookup.add(tuple(sorted((u, v))))
    
    # 3. 计算边的桥值（bridge value），使用简化的方法
    # 桥值近似：边的替代路径越少，桥值越高
    # 我们将优先选择桥值较低的边（对整体连通性不那么关键）
    edge_bridge_value = defaultdict(float)
    rootidx = common.ROOT_TERMINAL_IDX
    root = terminals[rootidx]
    other_terminals = terminals[:rootidx] + terminals[rootidx+1:]
    
    # 统计每条边出现在多少根到终端的路径中（近似桥的重要性）
    edge_usage_count = defaultdict(int)
    for target_terminal in other_terminals:
        path_nodes = common._find_path(adj, root, target_terminal)
        if path_nodes:
            for i in range(len(path_nodes) - 1):
                u, v = path_nodes[i], path_nodes[i+1]
                edge_key = tuple(sorted((u, v)))
                if edge_key in edge_set_for_lookup:
                    edge_usage_count[edge_key] += 1
    
    # 分配桥值：使用次数越少，桥值越高（更关键）
    # 但对于移除，我们希望使用次数多的边（桥值低）不那么关键
    # 反向关系：bridge_value = 1 / usage_count（或某种函数）
    for edge_key in edge_set_for_lookup:
        usage = edge_usage_count.get(edge_key, 0)
        if usage == 0:
            edge_bridge_value[edge_key] = float('inf')  # 不在任何路径中，如果是桥则很关键
        else:
            edge_bridge_value[edge_key] = 1.0 / usage  # 使用次数越多，桥值越低（不那么关键）
    
    # 4. 收集边信息，包括成本、Q 值、桥值以及是否在最差路径上
    edges_info = []
    all_worst_path_edges_keys = set()
    for path_info in worst_paths_info:
        all_worst_path_edges_keys.update(path_info['edges_keys'])
    
    # 获取 SMT 中的 PK 阈值
    pk_threshold = worst_paths_info[0]['pk'] if worst_paths_info else float('inf')
    
    # 计算搜索深度限制
    max_smt_hops = max((len(path_info['edges_keys']) for path_info in worst_paths_info), default=0)
    search_depth_limit = max_smt_hops + 3  # 增加缓冲区
    
    # 5. 分析原图中的路径，找出 PK 值高于阈值的路径上的边
    high_pk_edges = set()
    for target_terminal in other_terminals:
        candidate_paths_info = common.find_paths_qgraph_weighted_iterative(current_edges_dict, root, target_terminal, search_depth_limit)
        if not candidate_paths_info:
            print(f"Warning: No path found from {root} to {target_terminal} within depth limit.")
            continue
        
        for path_info in candidate_paths_info:
            if path_info['pk'] >= pk_threshold:
                high_pk_edges.update(path_info['edges_keys'])
    
    # 6. 为每条边计算综合评分
    for edge_key in edge_set_for_lookup:
        if edge_key in current_edges_dict:
            cost = current_edges_dict[edge_key]
            q_value = common.g_QureyEdgeQValues_map.get(edge_key, float('inf'))
            on_worst_path = edge_key in all_worst_path_edges_keys
            on_high_pk_path = edge_key in high_pk_edges
            bridge_val = edge_bridge_value[edge_key]
            
            # 计算综合评分
            # 权重可以根据需要调整
            cost_weight = -0.2
            q_weight = 0.4
            bridge_weight = 0.2
            worst_path_weight = -0.1
            high_pk_weight = -0.1
            
            # 归一化处理（可选）
            # 这里假设成本和 Q 值已经有合理的范围
            score = (cost * cost_weight +
                     q_value * q_weight -
                     bridge_val * bridge_weight +  # 桥值越低越好，所以用减法
                     (10 if on_worst_path else 0) * worst_path_weight +
                     (5 if on_high_pk_path else 0) * high_pk_weight)
            
            edges_info.append({
                'key': edge_key,
                'cost': cost,
                'q': q_value,
                'bridge_value': bridge_val,
                'on_worst_path': on_worst_path,
                'on_high_pk_path': on_high_pk_path,
                'score': score
            })
        else:
            print(f"CRITICAL Error: Edge {edge_key} from SMT not in current_edges_dict!")
            return None
    
    print(f"Edges with comprehensive scores: {edges_info}")
    
    # 7. 按综合评分排序边，优先移除评分最高的边
    edges_info.sort(key=lambda x: -x['score'])
    
    # 8. 检查每条边的移除是否保持连通性，从排序列表开始
    for edge_info in edges_info:
        edge_key = edge_info['key']
        # 创建一个不包含此边的临时边字典
        temp_edges_dict = {k: v for k, v in current_edges_dict.items() if k != edge_key}
        # 检查移除此边是否保持连通性
        if common.is_graph_still_connected(smt_nodes, temp_edges_dict, terminals):
            print(f"Selected edge for removal (Alg3, score={edge_info['score']:.2f}, cost={edge_info['cost']}, bridge_value={edge_info['bridge_value']}, on_worst_path={edge_info['on_worst_path']}, on_high_pk_path={edge_info['on_high_pk_path']}, maintains connectivity): {edge_key}")
            return (edge_key[0], edge_key[1], edge_info['cost'])
        else:
            print(f"Edge {edge_key} with score {edge_info['score']:.2f} would disconnect graph, skipping.")
    
    print("Error: No edge can be removed without disconnecting the graph in Alg3.")
    return None


def find_edge_to_remove_from_invalid_smt_alg1(smt_nodes, smt_edges_with_cost, terminals, current_edges_dict):
    """Identifies the edge to remove from an invalid SMT by selecting the highest cost unique edge across all paths, prioritizing connectivity."""

    # 1. Find the middle worst paths to identify edges contributing to invalidity
    worst_paths_info, worst_pks = common.find_middle_worst_path_and_pk(smt_nodes, smt_edges_with_cost, terminals)

    if not worst_paths_info:
        print("Error: Could not determine the worst paths to identify edges for removal.")
        return None

    print(f"Worst paths (PKs={worst_pks}) nodes: {[info['nodes'] for info in worst_paths_info]}")
    print(f"Worst paths edges (keys): {[info['edges_keys'] for info in worst_paths_info]}")

    # 2. Build adjacency list and edge set for connectivity and path analysis
    adj = defaultdict(list)
    edge_set_for_lookup = set()
    for u, v, _ in smt_edges_with_cost:
        adj[u].append(v)
        adj[v].append(u)
        edge_set_for_lookup.add(tuple(sorted((u, v))))

    # 3. Compute bridge value for edges using a simplified approach
    # Bridge value approximation: edges that are part of fewer alternative paths have higher bridge value
    # We will prioritize edges with low bridge value (less critical to overall connectivity)
    edge_bridge_value = defaultdict(float)
    rootidx = common.ROOT_TERMINAL_IDX
    root = terminals[rootidx]
    other_terminals = terminals[:rootidx] + terminals[rootidx+1:]

    # Count how many root-to-terminal paths each edge appears in (approximates bridge importance)
    edge_usage_count = defaultdict(int)
    for target_terminal in other_terminals:
        path_nodes = common._find_path(adj, root, target_terminal)
        if path_nodes:
            for i in range(len(path_nodes) - 1):
                u, v = path_nodes[i], path_nodes[i+1]
                edge_key = tuple(sorted((u, v)))
                if edge_key in edge_set_for_lookup:
                    edge_usage_count[edge_key] += 1

    # Assign bridge value: lower usage count means higher bridge value (more critical)
    # But for removal, we want edges with high usage count (low bridge value) to be less critical
    # Inverse relation: bridge_value = 1 / usage_count (or some function)
    for edge_key in edge_set_for_lookup:
        usage = edge_usage_count.get(edge_key, 0)
        if usage == 0:
            edge_bridge_value[edge_key] = float('inf')  # Not used in any path, critical if it's a bridge
        else:
            edge_bridge_value[edge_key] = 1.0 / usage  # Higher usage means lower bridge value (less critical)

    # 4. Collect edge information with cost, Q value, bridge value, and whether it's on the worst path
    edges_info = []
    all_worst_path_edges_keys = set()
    for path_info in worst_paths_info:
        all_worst_path_edges_keys.update(path_info['edges_keys'])

    for edge_key in edge_set_for_lookup:
        if edge_key in current_edges_dict:
            cost = current_edges_dict[edge_key]
            q_value = common.g_QureyEdgeQValues_map.get(edge_key, float('inf'))
            on_worst_path = edge_key in all_worst_path_edges_keys
            bridge_val = edge_bridge_value[edge_key]
            edges_info.append({
                'key': edge_key,
                'cost': cost,
                'q': q_value,
                'bridge_value': bridge_val,
                'on_worst_path': on_worst_path
            })
        else:
            print(f"CRITICAL Error: Edge {edge_key} from SMT not in current_edges_dict!")
            return None

    print(f"Edges with bridge values: {edges_info}")

    # 5. Sort edges by a combined score to prioritize removal
    # Priority: edges on worst path, low bridge value (high usage count), high cost, high Q value
    edges_info.sort(key=lambda x: (-x['on_worst_path'], x['bridge_value'], -x['cost'], -x['q']))
    # This sorts:
    # 1. First by whether on worst path (descending, True first)
    # 2. Then by bridge value (ascending, lower bridge value first, meaning less critical)
    # 3. Then by cost (descending, higher cost first)
    # 4. Then by Q value (descending, higher Q first)

    # 6. Check connectivity for each edge removal starting from the prioritized list
    for edge_info in edges_info:
        edge_key = edge_info['key']
        # Create a temporary edge dictionary without this edge
        temp_edges_dict = {k: v for k, v in current_edges_dict.items() if k != edge_key}
        # Check if removing this edge maintains connectivity
        if common.is_graph_still_connected(smt_nodes, temp_edges_dict, terminals):
            print(f"Selected edge for removal (cost={edge_info['cost']}, bridge_value={edge_info['bridge_value']}, on_worst_path={edge_info['on_worst_path']}, maintains connectivity): {edge_key}")
            return (edge_key[0], edge_key[1], edge_info['cost'])
        else:
            print(f"Edge {edge_key} with cost {edge_info['cost']} would disconnect graph, skipping.")

    print("Error: No edge can be removed without disconnecting the graph.")
    return None
