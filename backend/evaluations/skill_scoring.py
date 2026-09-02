from typing import Any, Dict, Optional


class SkillScoringService:
    """
    Computes an explainable, deterministic skill breakdown for completed evaluations
    based on test pass rates, challenge type, and execution resource metrics.
    """

    def calculate_skill_breakdown(
        self,
        challenge: Any,
        tests_total: int,
        tests_passed: int,
        tests_failed: int,
        execution_time: Optional[float] = None,
        memory_used: Optional[float] = None,
    ) -> Dict[str, Dict[str, Optional[Any]]]:
        scores: Dict[str, Optional[int]] = {
            "problem_solving": None,
            "debugging": None,
            "security": None,
            "performance": None,
            "code_quality": None,
            "testing": None,
        }
        evidence: Dict[str, str] = {
            "problem_solving": "not_measured",
            "debugging": "not_measured",
            "security": "not_measured",
            "performance": "not_measured",
            "code_quality": "not_measured",
            "testing": "not_measured",
        }

        # 1. Problem Solving (Functional Correctness)
        if tests_total > 0:
            ps_score = round((tests_passed / tests_total) * 100)
            scores["problem_solving"] = max(0, min(100, ps_score))
            evidence["problem_solving"] = "functional_tests"
        else:
            scores["problem_solving"] = None
            evidence["problem_solving"] = "not_measured"

        # 2. Debugging
        challenge_type = getattr(challenge, "challenge_type", "")
        if challenge_type in ["BUG_FIX", "DEBUGGING"]:
            scores["debugging"] = scores["problem_solving"]
            evidence["debugging"] = (
                "bug_fix_tests" if scores["problem_solving"] is not None else "not_measured"
            )
        else:
            scores["debugging"] = None
            evidence["debugging"] = "not_measured"

        # 3. Security
        if challenge_type == "SECURITY":
            scores["security"] = scores["problem_solving"]
            evidence["security"] = (
                "security_tests" if scores["problem_solving"] is not None else "not_measured"
            )
        else:
            scores["security"] = None
            evidence["security"] = "not_measured"

        # 4. Performance
        time_limit = getattr(challenge, "time_limit", None)
        memory_limit = getattr(challenge, "memory_limit", None)

        if (
            execution_time is not None
            and time_limit is not None
            and time_limit > 0
            and tests_total > 0
        ):
            # Compare cumulative execution time against cumulative time limit (time_limit * tests_total)
            total_allowed_time = float(time_limit) * float(tests_total)
            time_ratio = float(execution_time) / total_allowed_time
            time_score = max(0.0, min(1.0, 1.0 - time_ratio))

            if memory_limit and memory_limit > 0 and memory_used and memory_used > 0:
                mem_ratio = float(memory_used) / float(memory_limit)
                mem_score = max(0.0, min(1.0, 1.0 - mem_ratio))
                perf_value = round((0.7 * time_score + 0.3 * mem_score) * 100)
            else:
                perf_value = round(time_score * 100)

            scores["performance"] = max(0, min(100, perf_value))
            evidence["performance"] = "execution_metrics"
        else:
            scores["performance"] = None
            evidence["performance"] = "not_measured"

        # 5. Code Quality & Testing (unsupported in current MVP)
        scores["code_quality"] = None
        evidence["code_quality"] = "not_measured"

        scores["testing"] = None
        evidence["testing"] = "not_measured"

        return {
            "scores": scores,
            "evidence": evidence,
        }
