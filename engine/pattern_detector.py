
from __future__ import annotations

import networkx as nx


def _add(patterns: list[dict], pattern: str, steps: list[str], message: str) -> None:
    patterns.append({"pattern": pattern, "steps": steps, "message": message})


def detect_patterns(graph: nx.DiGraph) -> list[dict]:
    patterns: list[dict] = []
    node_ids = list(graph.nodes())

    for i, node_id in enumerate(node_ids):
        data = graph.nodes[node_id]
        curr = data.get('process_class')
        desc = str(data.get('description', '')).lower()
        succs = list(graph.successors(node_id))

        # Consecutive transport or handling motion
        for succ in succs:
            succ_class = graph.nodes[succ].get('process_class')
            succ_desc = str(graph.nodes[succ].get('description', '')).lower()
            if curr == 'transport' and succ_class == 'transport':
                _add(patterns, 'repeated_transport', [node_id, succ], 'Consecutive transport steps detected. Check layout, handoffs, and backtracking.')
            if curr == 'handling' and succ_class == 'handling':
                _add(patterns, 'repeated_handling', [node_id, succ], 'Consecutive handling steps detected. Check for excess motion or fragmented manual work.')
            if curr == 'delay' and succ_class in {'handling', 'transport', 'operation'}:
                _add(patterns, 'delay_before_work', [node_id, succ], 'A delay/search step is followed by work. Check point-of-use placement, synchronization, or planning.')
            if curr == 'storage' and succ_class in {'retrieve', 'handling', 'transport', 'operation'}:
                _add(patterns, 'storage_then_use', [node_id, succ], 'Temporary storage followed by immediate use. Consider direct flow.')
            if curr == 'inspection' and succ_class == 'inspection':
                _add(patterns, 'repeated_inspection', [node_id, succ], 'Back-to-back inspection steps detected. Check for redundancy.')

        # Search / retrieval pattern cues from text
        if any(word in desc for word in ['search', 'look for', 'find']):
            _add(patterns, 'search_waste', [node_id], 'Search activity detected. This often indicates poor workplace organization or point-of-use storage issues.')
        if any(word in desc for word in ['walk', 'carry', 'move', 'transport']) and curr in {'handling', 'transport'}:
            _add(patterns, 'motion_transport_waste', [node_id], 'Walking or movement step detected. Check whether distance or motion can be reduced.')
        if any(word in desc for word in ['open', 'close', 'grasp', 'pick', 'place', 'position', 'drop']) and curr == 'handling':
            _add(patterns, 'micro_handling', [node_id], 'Fine handling motion detected. Check if adjacent motions can be combined or simplified.')
        if curr == 'retrieve' and graph.out_degree(node_id) > 0 and graph.in_degree(node_id) > 0:
            _add(patterns, 'retrieve_inside_flow', [node_id], 'Retrieval exists inside the main sequence. Check if it can be externalized or pre-kitted.')

        # Three-step chains for repeated manual motion
        if i + 2 < len(node_ids):
            a, b, c = node_ids[i], node_ids[i + 1], node_ids[i + 2]
            ca = graph.nodes[a].get('process_class')
            cb = graph.nodes[b].get('process_class')
            cc = graph.nodes[c].get('process_class')
            if ca == cb == cc == 'handling':
                _add(patterns, 'handling_chain', [a, b, c], 'Three consecutive handling steps detected. Check for unnecessary micro-motions and combine/simplify opportunities.')
            if ca == 'delay' and cb == 'handling' and cc == 'handling':
                _add(patterns, 'search_then_handle_chain', [a, b, c], 'Search/delay followed by repeated handling suggests disorganized retrieval and placement flow.')

    # de-duplicate identical entries
    seen = set()
    deduped = []
    for p in patterns:
        key = (p['pattern'], tuple(p['steps']), p['message'])
        if key not in seen:
            seen.add(key)
            deduped.append(p)
    return deduped
