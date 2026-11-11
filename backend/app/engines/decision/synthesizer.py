import time
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.decision import ConstraintResult, ConstraintEvaluation
from backend.app.models.leave import DecisionState
from backend.app.engines.constraint_graph.node import ConstraintNode

class DecisionSynthesizer:
    """
    EFCG Decision Synthesizer.
    Executes constraint graph nodes according to dependency topology,
    evaluates three-state evidence (PASS, FAIL, REVIEW),
    synthesizes overall decision (ELIGIBLE, NEEDS_REVIEW, BLOCKED),
    and generates an explainable natural language rationale.
    """

    @classmethod
    def execute_graph(
        cls,
        nodes: List[ConstraintNode],
        db: Session,
        request_id: str,
        request_type: str,  # "LEAVE" or "EXPENSE"
        persist_evaluations: bool = True
    ) -> Dict[str, Any]:
        node_map = {n.id: n for n in nodes}
        executed_order: List[str] = []
        visited = set()
        edges: List[Dict[str, str]] = []

        # Build edges
        for node in nodes:
            for dep_id in node.dependencies:
                edges.append({"source": dep_id, "target": node.id})

        # Topological sort traversal
        def execute_node(node: ConstraintNode):
            if node.id in visited:
                return
            
            # Execute dependencies first
            for dep_id in node.dependencies:
                if dep_id in node_map and dep_id not in visited:
                    execute_node(node_map[dep_id])

            visited.add(node.id)
            executed_order.append(node.id)

            # Check if any blocking dependency failed
            blocking_dep_failed = any(
                node_map[dep_id].status == ConstraintResult.FAIL and node_map[dep_id].is_blocking
                for dep_id in node.dependencies
                if dep_id in node_map
            )

            if blocking_dep_failed:
                node.status = ConstraintResult.FAIL
                node.executed = True
                node.execution_time_ms = 0.0
                node.evidence = None
                return

            if node.evaluator:
                start_t = time.perf_counter()
                evidence_rec = node.evaluator()
                end_t = time.perf_counter()

                node.evidence = evidence_rec
                node.status = evidence_rec.result
                node.executed = True
                node.execution_time_ms = round((end_t - start_t) * 1000, 2)

                if persist_evaluations and request_id:
                    eval_record = ConstraintEvaluation(
                        request_id=request_id,
                        request_type=request_type,
                        constraint_name=node.name,
                        result=node.status,
                        actual_value=evidence_rec.actual_condition,
                        expected_value=evidence_rec.expected_condition,
                        evidence_source=evidence_rec.evidence_source,
                        evidence_summary=evidence_rec.reason
                    )
                    db.add(eval_record)

        for n in nodes:
            execute_node(n)

        if persist_evaluations and request_id:
            db.flush()

        # Synthesis
        blocking_fails = [n for n in nodes if n.status == ConstraintResult.FAIL and n.is_blocking]
        non_blocking_fails = [n for n in nodes if n.status == ConstraintResult.FAIL and not n.is_blocking]
        reviews = [n for n in nodes if n.status == ConstraintResult.REVIEW]
        passes = [n for n in nodes if n.status == ConstraintResult.PASS]

        if blocking_fails:
            decision_state = DecisionState.BLOCKED
        elif reviews or non_blocking_fails:
            decision_state = DecisionState.NEEDS_REVIEW
        else:
            decision_state = DecisionState.ELIGIBLE

        # Generate Natural Language Explanation
        explanation = cls._generate_explanation(
            decision_state=decision_state,
            blocking_fails=blocking_fails,
            reviews=reviews,
            passes=passes,
            request_type=request_type
        )

        return {
            "decision_state": decision_state.value,
            "explanation": explanation,
            "summary": {
                "total_constraints": len(nodes),
                "passed": len(passes),
                "failed_blocking": len(blocking_fails),
                "failed_non_blocking": len(non_blocking_fails),
                "review_required": len(reviews),
            },
            "nodes": [n.to_dict() for n in nodes],
            "edges": edges,
            "execution_order": executed_order
        }

    @staticmethod
    def _generate_explanation(
        decision_state: DecisionState,
        blocking_fails: List[ConstraintNode],
        reviews: List[ConstraintNode],
        passes: List[ConstraintNode],
        request_type: str
    ) -> str:
        if decision_state == DecisionState.BLOCKED:
            fail_reasons = "; ".join(
                f"{n.name} [{n.evidence.reason if n.evidence else 'Policy violation'}]"
                for n in blocking_fails
            )
            return (
                f"Request was evaluated as BLOCKED due to {len(blocking_fails)} critical policy violation(s): "
                f"{fail_reasons}. This request cannot proceed to the approval workflow until underlying conditions are rectified."
            )

        if decision_state == DecisionState.NEEDS_REVIEW:
            review_reasons = "; ".join(
                f"{n.name} ({n.evidence.reason if n.evidence else 'Human review needed'})"
                for n in reviews
            )
            return (
                f"All mandatory critical policy constraints passed, but {len(reviews)} constraint(s) require human review: "
                f"{review_reasons}. The request has been flagged as NEEDS_REVIEW and routed to the designated reviewer with supporting evidence."
            )

        return (
            f"All {len(passes)} policy constraints evaluated with status PASS. "
            f"Evidence verifies employment status, policy allowances, balance/budget headroom, calendar rules, and unique documentation. "
            f"The request is ELIGIBLE and has entered the authorized multi-level approval pipeline."
        )
