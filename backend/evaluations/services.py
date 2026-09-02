from django.utils import timezone
from challenges.models import TestCase
from execution.services import ExecutionService
from submissions.models import Submission
from .models import Evaluation
from .skill_scoring import SkillScoringService


def normalize_output(text: str) -> str:
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
    def __init__(self, execution_service=None, skill_scoring_service=None):
        self.execution_service = execution_service or ExecutionService()
        self.skill_scoring_service = skill_scoring_service or SkillScoringService()


    def evaluate(self, submission: Submission) -> Evaluation:
        evaluation, _ = Evaluation.objects.get_or_create(submission=submission)

        evaluation.status = Evaluation.Status.RUNNING
        evaluation.save()

        submission.status = Submission.Status.RUNNING
        submission.save()

        try:
            test_cases = list(
                TestCase.objects.filter(
                    challenge=submission.challenge, is_active=True
                ).order_by("id")
            )


            if not test_cases:
                evaluation.status = Evaluation.Status.FAILED
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
                evaluation.evaluated_at = timezone.now()
                evaluation.save()


                submission.status = Submission.Status.FAILED
                submission.score = 0
                submission.test_results = []
                submission.save()

                return evaluation

            timeout = getattr(submission.challenge, "time_limit", 10)
            tests_passed = 0
            tests_failed = 0
            total_score = 0
            test_results = []
            total_execution_time = 0.0
            max_memory_used = 0.0
            stdout_logs = []
            stderr_logs = []

            # Check if this challenge is repository-based
            is_repo_challenge = False
            try:
                if hasattr(submission.challenge, "files"):
                    is_repo_challenge = bool(submission.challenge.files.exists())
            except Exception:
                is_repo_challenge = bool(getattr(submission, "files", None))

            repo_file_map = {}
            entrypoint = None

            if is_repo_challenge:
                try:
                    for cf in submission.challenge.files.all():
                        repo_file_map[cf.path] = cf.content
                except Exception:
                    pass

                # Apply student's submitted file overrides (excluding protected tests)
                submitted_files = getattr(submission, "files", None)
                if isinstance(submitted_files, dict):
                    for path, content in submitted_files.items():
                        if not path.startswith("tests/") and "test_" not in path:
                            repo_file_map[path] = content

                entrypoint = getattr(submission.challenge, "entrypoint", "") or "app/calculator.py"

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

            max_challenge_points = submission.challenge.points
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
            evaluation.status = Evaluation.Status.COMPLETED
            evaluation.score = final_score
            evaluation.tests_total = len(test_cases)
            evaluation.tests_passed = tests_passed
            evaluation.tests_failed = tests_failed
            evaluation.execution_time = total_execution_time
            evaluation.memory_used = max_memory_used
            evaluation.stdout = "\n".join(stdout_logs)
            evaluation.stderr = "\n".join(stderr_logs)
            evaluation.test_results = test_results
            evaluation.evaluated_at = timezone.now()
            evaluation.save()


            # Update Submission
            submission.status = (
                Submission.Status.PASSED if all_passed else Submission.Status.FAILED
            )
            submission.score = final_score
            submission.execution_time = total_execution_time
            submission.memory_used = max_memory_used
            submission.test_results = test_results
            submission.save()

        except Exception as e:
            evaluation.status = Evaluation.Status.FAILED
            evaluation.stderr = f"Evaluation error: {str(e)}"
            evaluation.evaluated_at = timezone.now()
            evaluation.save()

            submission.status = Submission.Status.ERROR
            submission.save()

        return evaluation

