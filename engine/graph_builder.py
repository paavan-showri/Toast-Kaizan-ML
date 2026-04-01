from __future__ import annotations

import networkx as nx

from models.schema import ProcessStep


def build_process_graph(steps: list[ProcessStep]) -> nx.DiGraph:
    graph = nx.DiGraph()
    step_map = {s.step_id: s for s in steps}

    for step in steps:
        graph.add_node(
            step.step_id,
            description=step.description,
            process_class=step.process_class,
            duration_sec=step.duration_sec,
            resources=step.resources,
            obj=step.obj,
            source=step.source,
            destination=step.destination,
            location=step.location,
        )

    for step in steps:
        for pred in step.predecessors:
            pred = str(pred).strip()
            if pred in step_map:
                graph.add_edge(pred, step.step_id)

    return graph
