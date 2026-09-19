from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.challenge import Challenge, ChallengeFile, TestCase
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission, SubmissionStatus
from app.services.achievement_service import AchievementService
from app.services.skill_scoring import SkillScoringService
from execution.services import ExecutionService

logger = logging.getLogger("app.services.evaluation")


def normalize_output(text: Optional[str]) -> str:
    """
    Normalizes string output for deterministic comparison:
    - Normalizes CRLF / CR to LF
    - Strips leading and trailing whitespace
    - Strips trailing whitespace per line
    """
    if text is None:
        return ""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").strip().split("\n")
    return "\n".join(line.rstrip() for line in lines).strip()


class EvaluationService:
    def __init__(
        self,
        execution_service: Optional[ExecutionService] = None,
        skill_scoring_service: Optional[SkillScoringService] = None,
        achievement_service: Optional[AchievementService] = None,
    ):
        self.execution_service = execution_service or ExecutionService()
        self.skill_scoring_service = skill_scoring_service or SkillScoringService()
        self.achievement_service = achievement_service or AchievementService()

    def evaluate(self, db: Session, submission: Submission) -> Evaluation:
        """
        Executes and evaluates a submission within an active SQLAlchemy session.
        """
        # Ensure relationships are loaded
        if not submission.challenge:
            submission = (
                db.query(Submission)
                .options(
                    joinedload(Submission.challenge).joinedload(Challenge.files),
                    joinedload(Submission.evaluation),
                )
                .filter(Submission.id == submission.id)
                .first()
            )

        evaluation = (
            db.query(Evaluation)
            .filter(Evaluation.submission_id == submission.id)
            .first()
        )
        if not evaluation:
            evaluation = Evaluation(
                submission_id=submission.id,
                status=EvaluationStatus.PENDING.value,
            )
            db.add(evaluation)
            db.commit()
            db.refresh(evaluation)

        evaluation.status = EvaluationStatus.RUNNING.value
        submission.status = SubmissionStatus.RUNNING.value
        db.commit()

        try:
            test_cases = (
                db.query(TestCase)
                .filter(
                    TestCase.challenge_id == submission.challenge_id,
                    TestCase.is_active == True,
                )
                .order_by(TestCase.id.asc())
                .all()
            )

            if not test_cases:
                evaluation.status = EvaluationStatus.FAILED.value
                evaluation.score = 0
                evaluation.tests_total = 0
                evaluation.tests_passed = 0
                evaluation.tests_failed = 0
                evaluation.stdout = ""
                evaluation.stderr = "Evaluation error: No active test cases configured for this challenge."
                evaluation.test_results = []
                evaluation.skill_breakdown = self.skill_scoring_service.calculate_skill_breakdown(
                    challenge=submission.challenge,
                    tests_total=0,
                    tests_passed=0,
                    tests_failed=0,
                    execution_time=0.0,
                    memory_used=0.0,
                )
                evaluation.evaluated_at = datetime.now(timezone.utc)

                submission.status = SubmissionStatus.FAILED.value
                submission.score = 0
                submission.test_results = []
                db.commit()

                return evaluation

            timeout = getattr(submission.challenge, "time_limit", 10) or 10
            tests_passed = 0
            tests_failed = 0
            total_score = 0
            test_results: List[Dict[str, Any]] = []
            total_execution_time = 0.0
            max_memory_used = 0.0
            stdout_logs: List[str] = []
            stderr_logs: List[str] = []

            # Check if this challenge is repository-based
            challenge_files = (
                db.query(ChallengeFile)
                .filter(ChallengeFile.challenge_id == submission.challenge_id)
                .all()
            )
            is_repo_challenge = bool(challenge_files) or bool(submission.files)

            repo_file_map: Dict[str, str] = {}
            entrypoint = ""

            if is_repo_challenge:
                for cf in challenge_files:
                    repo_file_map[cf.path] = cf.content

                # Apply student's submitted file overrides (excluding protected test files)
                submitted_files = submission.files
                if isinstance(submitted_files, dict):
                    for path, content in submitted_files.items():
                        if not path.startswith("tests/") and "test_" not in path:
                            repo_file_map[path] = content

                entrypoint = (
                    getattr(submission.challenge, "entrypoint", "")
                    or "app/calculator.py"
                )

            for test_case in test_cases:
                if is_repo_challenge:
                    result = self.execution_service.execute(
                        files=repo_file_map,
                        entrypoint=entrypoint,
                        language=submission.language,
                        stdin_data=test_case.input_data,
                        timeout=timeout,
                    )
                else:
                    result = self.execution_service.execute(
                        code=submission.code,
                        language=submission.language,
                        stdin_data=test_case.input_data,
                        timeout=timeout,
                    )

                actual_normalized = normalize_output(result.stdout)
                expected_normalized = normalize_output(test_case.expected_output)
                passed = (result.exit_code == 0) and (actual_normalized == expected_normalized)

                points_awarded = test_case.points if passed else 0
                if passed:
                    tests_passed += 1
                    total_score += points_awarded
                else:
                    tests_failed += 1

                total_execution_time += result.execution_time
                if result.memory_used > max_memory_used:
                    max_memory_used = result.memory_used

                if result.stdout:
                    stdout_logs.append(f"[{test_case.name}] {result.stdout.strip()}")
                if result.stderr:
                    stderr_logs.append(f"[{test_case.name}] {result.stderr.strip()}")

                test_results.append({
                    "test_case_id": test_case.id,
                    "name": test_case.name,
                    "passed": passed,
                    "is_hidden": test_case.is_hidden,
                    "points": points_awarded,
                    "max_points": test_case.points,
                    "execution_time": result.execution_time,
                    "memory_used": result.memory_used,
                    "exit_code": result.exit_code,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "expected_output": test_case.expected_output,
                    "input_data": test_case.input_data,
                })

            max_challenge_points = getattr(submission.challenge, "points", 100) or 100
            final_score = min(total_score, max_challenge_points)
            all_passed = (tests_failed == 0 and tests_passed > 0)

            # Calculate deterministic skill breakdown
            evaluation.skill_breakdown = self.skill_scoring_service.calculate_skill_breakdown(
                challenge=submission.challenge,
                tests_total=len(test_cases),
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                execution_time=total_execution_time,
                memory_used=max_memory_used,
            )

            # Update Evaluation
            evaluation.status = EvaluationStatus.COMPLETED.value
            evaluation.score = final_score
            evaluation.tests_total = len(test_cases)
            evaluation.tests_passed = tests_passed
            evaluation.tests_failed = tests_failed
            evaluation.execution_time = total_execution_time
            evaluation.memory_used = max_memory_used
            evaluation.stdout = "\n".join(stdout_logs)
            evaluation.stderr = "\n".join(stderr_logs)
            evaluation.test_results = test_results
            evaluation.evaluated_at = datetime.now(timezone.utc)

            # Update Submission
            submission.status = (
                SubmissionStatus.PASSED.value if all_passed else SubmissionStatus.FAILED.value
            )
            submission.score = final_score
            submission.execution_time = total_execution_time
            submission.memory_used = max_memory_used
            submission.test_results = test_results

            db.commit()

            # Automatic Achievement Awarding (Defensive)
            try:
                if submission.user_id:
                    self.achievement_service.award_for_user(db, submission.user_id)
            except Exception as ach_err:
                logger.exception("Error during automatic achievement evaluation: %s", ach_err)

        except Exception as e:
            logger.exception("Error during evaluation of submission %s: %s", submission.id, e)
            evaluation.status = EvaluationStatus.FAILED.value
            evaluation.stderr = f"Evaluation error: {str(e)}"
            evaluation.evaluated_at = datetime.now(timezone.utc)

            submission.status = SubmissionStatus.ERROR.value
            db.commit()

        return evaluation
