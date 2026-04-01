from __future__ import annotations

import networkx as nx



def detect_patterns(graph: nx.DiGraph) -> list[dict]:
    patterns: list[dict] = []
    nodes = list(graph.nodes(data=True))

    # Consecutive transport
    for node_id, data in nodes:
        if data.get("process_class") == "transport":
            for succ in graph.successors(node_id):
                if graph.nodes[succ].get("process_class") == "transport":
                    patterns.append({
                        "pattern": "repeated_transport",
                        "steps": [node_id, succ],
                        "message": "Consecutive transport steps detected. Check layout, handoffs, and backtracking.",
                    })

    # Storage followed by immediate use
    for node_id, data in nodes:
        if data.get("process_class") == "storage":
            for succ in graph.successors(node_id):
                if graph.nodes[succ].get("process_class") in {"retrieve", "handling", "transport", "operation"}:
                    patterns.append({
                        "pattern": "storage_then_use",
                        "steps": [node_id, succ],
                        "message": "Temporary storage followed by immediate use. Consider direct flow.",
                    })

    # Repeated inspection
    for node_id, data in nodes:
        if data.get("process_class") == "inspection":
            for succ in graph.successors(node_id):
                if graph.nodes[succ].get("process_class") == "inspection":
                    patterns.append({
                        "pattern": "repeated_inspection",
                        "steps": [node_id, succ],
                        "message": "Back-to-back inspection steps detected. Check for redundancy.",
                    })

    # Delay before operation
    for node_id, data in nodes:
        if data.get("process_class") == "delay":
            for succ in graph.successors(node_id):
                if graph.nodes[succ].get("process_class") == "operation":
                    patterns.append({
                        "pattern": "delay_before_operation",
                        "steps": [node_id, succ],
                        "message": "Waiting before operation suggests a synchronization, capacity, or planning issue.",
                    })

    # Retrieve inside critical path
    for node_id, data in nodes:
        if data.get("process_class") == "retrieve" and graph.out_degree(node_id) > 0 and graph.in_degree(node_id) > 0:
            patterns.append({
                "pattern": "retrieve_inside_flow",
                "steps": [node_id],
                "message": "Retrieval exists inside the main sequence. Check if it can be externalized or pre-kitted.",
            })

    return patterns
