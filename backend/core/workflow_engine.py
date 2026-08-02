"""
backend/core/workflow_engine.py

Enterprise DAG Workflow Engine with Topological Cycle Detection,
Parallel Execution Worker Pools, and Idempotent Execution Guarantees.
"""

import hashlib
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Callable, Set, Optional, Union

from backend.core.exceptions import ClinicalSystemError

logger = logging.getLogger(__name__)


class DAGCycleError(ClinicalSystemError):
    """Raised when a cyclic dependency is detected in the Workflow DAG."""
    error_code = "DAG-400"
    status_code = 400


class WorkflowNode:
    """
    Represents a discrete step or agent task in a Clinical Workflow DAG.
    """
    def __init__(
        self,
        node_id: str,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
        depends_on: Optional[List[str]] = None,
        is_idempotent: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.node_id = node_id
        self.handler = handler
        self.depends_on = depends_on or []
        self.is_idempotent = is_idempotent
        self.metadata = metadata or {}

    def compute_execution_hash(self, inputs: Dict[str, Any]) -> str:
        """Computes a SHA-256 execution hash based on node_id and input payload."""
        try:
            serialized_inputs = json.dumps(inputs, sort_keys=True, default=str)
        except Exception:
            serialized_inputs = str(inputs)
        raw_key = f"{self.node_id}:{serialized_inputs}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class WorkflowEngine:
    """
    Enterprise DAG Workflow Orchestrator.
    Validates DAG topological constraints, executes independent nodes in parallel,
    and maintains an idempotent execution cache for exactly-once guarantees.
    """

    def __init__(self, workflow_name: str = "EnterpriseClinicalWorkflow"):
        self.workflow_name = workflow_name
        self.dag_name = workflow_name
        self.nodes: Dict[str, WorkflowNode] = {}
        self.execution_cache: Dict[str, Dict[str, Any]] = {}
        self.completed_checkpoints: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.Lock()
        self._lock = threading.Lock()

    def add_node(
        self,
        node_or_id: Union[WorkflowNode, str],
        func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        depends_on: Optional[List[str]] = None,
        is_idempotent: bool = True
    ) -> "WorkflowEngine":
        """Registers a WorkflowNode or raw function in the workflow DAG."""
        if isinstance(node_or_id, WorkflowNode):
            node = node_or_id
        else:
            if func is None:
                raise ValueError("Function handler must be provided if node_or_id is a string ID")
            node = WorkflowNode(
                node_id=node_or_id,
                handler=func,
                depends_on=depends_on,
                is_idempotent=is_idempotent
            )

        self.nodes[node.node_id] = node
        return self

    def detect_cycles(self) -> List[str]:
        """
        Performs Kahn's Algorithm / Topological Sort to detect cycles in the DAG.
        Returns topological ordering if valid; raises DAGCycleError if a cycle exists.
        """
        in_degree: Dict[str, int] = {node_id: 0 for node_id in self.nodes}
        adj_list: Dict[str, List[str]] = {node_id: [] for node_id in self.nodes}

        for node_id, node in self.nodes.items():
            for dep in node.depends_on:
                if dep not in self.nodes:
                    raise ValueError(f"Node '{node_id}' depends on non-existent node '{dep}'")
                adj_list[dep].append(node_id)
                in_degree[node_id] += 1

        queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
        topo_order = []

        while queue:
            curr = queue.pop(0)
            topo_order.append(curr)

            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topo_order) != len(self.nodes):
            unvisited = set(self.nodes.keys()) - set(topo_order)
            raise DAGCycleError(
                f"DAG cycle detected in workflow '{self.workflow_name}'. Nodes involved in cycle: {list(unvisited)}"
            )

        return topo_order

    def validate_dag(self) -> bool:
        """Backwards compatible validator calling detect_cycles()."""
        self.detect_cycles()
        return True

    def execute(
        self,
        initial_inputs: Optional[Dict[str, Any]] = None,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Executes the Workflow DAG concurrently using thread pools.
        Respects topological dependency barriers and uses idempotent hashing.
        """
        topo_order = self.detect_cycles()
        initial_inputs = initial_inputs or {}

        completed_nodes: Set[str] = set()
        node_results: Dict[str, Dict[str, Any]] = {}
        execution_summary: Dict[str, Any] = {
            "workflow_name": self.workflow_name,
            "executed_nodes": [],
            "cached_nodes": [],
            "results": {}
        }

        lock = threading.Lock()

        # Group dependencies
        in_degree: Dict[str, int] = {node_id: len(self.nodes[node_id].depends_on) for node_id in self.nodes}
        dependents: Dict[str, List[str]] = {node_id: [] for node_id in self.nodes}
        for node_id, node in self.nodes.items():
            for dep in node.depends_on:
                dependents[dep].append(node_id)

        ready_queue = [node_id for node_id, deg in in_degree.items() if deg == 0]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while len(completed_nodes) < len(self.nodes):
                if not ready_queue:
                    if len(completed_nodes) < len(self.nodes):
                        remaining = set(self.nodes.keys()) - completed_nodes
                        raise DAGCycleError(f"Workflow execution stalled. Unresolved nodes: {list(remaining)}")
                    break

                current_batch = list(ready_queue)
                ready_queue.clear()

                futures = {}
                for node_id in current_batch:
                    node = self.nodes[node_id]

                    combined_input = dict(initial_inputs)
                    for dep in node.depends_on:
                        if dep in node_results:
                            combined_input[dep] = node_results[dep]

                    # Idempotency Hash Check
                    exec_hash = node.compute_execution_hash(combined_input)
                    with self._cache_lock:
                        if node.is_idempotent and exec_hash in self.execution_cache:
                            logger.info(f"Idempotent hit for node '{node_id}' with hash {exec_hash[:8]}")
                            node_results[node_id] = self.execution_cache[exec_hash]
                            completed_nodes.add(node_id)
                            execution_summary["cached_nodes"].append(node_id)

                            for dep_id in dependents[node_id]:
                                in_degree[dep_id] -= 1
                                if in_degree[dep_id] == 0:
                                    ready_queue.append(dep_id)
                            continue

                    futures[executor.submit(self._run_node_safe, node, combined_input, exec_hash)] = (node_id, exec_hash)

                for future in as_completed(futures):
                    node_id, exec_hash = futures[future]
                    result = future.result()

                    with lock:
                        node_results[node_id] = result
                        completed_nodes.add(node_id)
                        execution_summary["executed_nodes"].append(node_id)

                        if self.nodes[node_id].is_idempotent:
                            with self._cache_lock:
                                self.execution_cache[exec_hash] = result

                        for dep_id in dependents[node_id]:
                            in_degree[dep_id] -= 1
                            if in_degree[dep_id] == 0:
                                ready_queue.append(dep_id)

        execution_summary["results"] = node_results
        return execution_summary

    def execute_dag(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Backwards compatible execution method."""
        res = self.execute(initial_inputs=initial_context)
        out = dict(initial_context)
        for _, n_res in res.get("results", {}).items():
            if isinstance(n_res, dict):
                out.update(n_res)
        return out

    def _run_node_safe(
        self,
        node: WorkflowNode,
        inputs: Dict[str, Any],
        exec_hash: str
    ) -> Dict[str, Any]:
        """Safely executes node handler and captures outputs or errors."""
        logger.info(f"Executing workflow node '{node.node_id}' [hash={exec_hash[:8]}]")
        try:
            res = node.handler(inputs)
            return res if isinstance(res, dict) else {"output": res}
        except Exception as e:
            logger.error(f"Error in node '{node.node_id}': {e}", exc_info=True)
            raise
