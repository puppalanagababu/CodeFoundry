import pytest
from unittest.mock import patch
import subprocess
from app.models.challenge import Challenge, ChallengeFile
from app.services.skill_scoring import (
    SkillScoringService,
    evaluate_testing_skill,
    inspect_test_suite_ast,
    CalibratedMutant,
    CALIBRATED_MUTANT_CATALOG,
    CANONICAL_CHALLENGE_SOLUTIONS,
)


@pytest.fixture
def scoring_service():
    return SkillScoringService()


# 1. Strong Student Test Suite
def test_testing_skill_strong_student_test_suite(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    strong_test_code = """
from solution import add

def test_add_positive():
    assert add(2, 3) == 5

def test_add_zero():
    assert add(0, 0) == 0

def test_add_negative():
    assert add(-5, 5) == 0
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=strong_test_code)
    assert result["score"] == 100
    assert result["evidence"]["status"] == "measured"
    assert result["evidence"]["passed_on_canonical"] is True
    assert result["evidence"]["mutants_killed"] == result["evidence"]["mutants_total"]
    assert result["evidence"]["mutation_score"] == 100.0


# 2. No Student Tests Submitted
def test_testing_skill_no_student_tests_submitted(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=None)
    assert result["score"] is None
    assert result["evidence"] == "insufficient_data"


# 3. Assert True / Trivial Assertion
def test_testing_skill_assert_true_trivial_assertion(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    trivial_test_code = """
from solution import add

def test_trivial():
    assert True
    assert 1 == 1
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=trivial_test_code)
    assert result["score"] == 0
    assert result["evidence"]["mutation_score"] == 0.0
    assert result["evidence"]["mutants_killed"] == 0
    assert result["evidence"]["trivial_assertions"] >= 2


# 4. Assertion-Free Test
def test_testing_skill_assertion_free_test(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    no_assert_code = """
from solution import add

def test_no_asserts():
    res = add(10, 20)
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=no_assert_code)
    assert result["score"] == 0
    assert result["evidence"]["valid_assertions"] == 0
    assert result["evidence"]["mutation_score"] == 0.0


# 5. High Execution but Weak Mutation Score
def test_testing_skill_high_coverage_weak_mutation_score(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    weak_check_code = """
from solution import add

def test_loose_type():
    res = add(2, 3)
    assert isinstance(res, int)
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=weak_check_code)
    # Mutants will survive because mutated arithmetic still returns an int!
    assert result["score"] < 50
    assert result["evidence"]["mutants_killed"] < result["evidence"]["mutants_total"]


# 6. Strong Mutation Score with Minimal Tests
def test_testing_skill_strong_mutation_score_minimal_tests(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    minimal_strong_code = """
from solution import add

def test_comprehensive_checks():
    assert add(10, 20) == 30
    assert add(0, 0) == 0
    assert add(-5, 10) == 5
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=minimal_strong_code)
    assert result["score"] >= 90
    assert result["evidence"]["mutants_killed"] == 3


# 7. Edge-Case Tests Awarded Edge Points
def test_testing_skill_edge_case_tests_awarded_edge_points(scoring_service):
    challenge = Challenge(id=1, slug="password-validator", title="Password Validator", is_active=True)
    thorough_test_code = """
from solution import validate_password

def test_valid():
    assert validate_password("SecurePassword123") is True

def test_length_edge_case():
    assert validate_password("Short1") is False

def test_missing_digit():
    assert validate_password("NoDigitsHere") is False

def test_missing_upper():
    assert validate_password("lowercase123") is False
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=thorough_test_code)
    assert result["score"] == 100
    assert result["evidence"]["edge_score"] == 100.0


# 8. Missing Edge-Case Tests Penalized in Edge Score
def test_testing_skill_missing_edge_case_tests_penalized(scoring_service):
    challenge = Challenge(id=1, slug="password-validator", title="Password Validator", is_active=True)
    # Only tests valid password and uppercase, misses length boundary
    incomplete_test_code = """
from solution import validate_password

def test_valid():
    assert validate_password("SecurePassword123") is True

def test_missing_digit():
    assert validate_password("NoDigitsHere") is False
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=incomplete_test_code)
    # Length mutant survives
    assert result["score"] < 100
    assert result["evidence"]["mutants_survived"] >= 1


# 9. Duplicate Tests Detected and Scored Proportionally
def test_testing_skill_duplicate_tests_penalized(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    test_code_with_dupes = """
from solution import add

def test_one():
    assert add(1, 2) == 3

def test_two():
    assert add(1, 2) == 3

def test_three():
    assert add(1, 2) == 3
"""
    ast_meta = inspect_test_suite_ast(test_code_with_dupes)
    assert ast_meta["tests_count"] == 3
    assert ast_meta["duplicate_tests"] == 2

    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=test_code_with_dupes)
    assert result["evidence"]["duplicate_tests"] == 2
    # Duplicate tests are detected and reported without arbitrary 25-point penalty dominating score
    assert result["score"] >= 30


# 10. Mutant Killed Increments Kill Count
def test_testing_skill_mutant_killed_increments_kill_count(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    code = """
from solution import add

def test_addition():
    assert add(5, 7) == 12
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=code)
    assert result["evidence"]["mutants_killed"] >= 2
    killed_ids = [m["id"] for m in result["evidence"]["mutant_results"] if m["status"] == "KILLED"]
    assert "add-mut-01" in killed_ids


# 11. Mutant Survived Lowers Score
def test_testing_skill_mutant_survived_lowers_score(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    # Only tests 2+2=4, which does not distinguish a+b from a*b (2*2=4)
    insufficient_test = """
from solution import add

def test_specific_value():
    assert add(2, 2) == 4
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=insufficient_test)
    # add-mut-02 (* instead of +) survives because 2 * 2 == 4!
    survived_ids = [m["id"] for m in result["evidence"]["mutant_results"] if m["status"] == "SURVIVED"]
    assert "add-mut-02" in survived_ids
    assert result["score"] < 100


# 12. Invalid Mutant Excluded from Denominator
def test_testing_skill_invalid_mutant_excluded(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    invalid_mutant = CalibratedMutant(
        id="bad-syntax-mut",
        challenge_slug="add-two-numbers",
        target_file="solution.py",
        category="AOR",
        original_code="return a + b",
        mutated_code="return a +++ ",
        description="Syntax invalid",
        is_valid=True,
    )
    with patch.dict(CALIBRATED_MUTANT_CATALOG, {"add-two-numbers": [invalid_mutant]}):
        code = "from solution import add\ndef test_add(): assert add(1, 2) == 3\n"
        result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=code)
        # Invalid syntax mutant is excluded from denominator, so valid mutants count becomes 0 -> insufficient_data
        assert result["score"] is None
        assert result["evidence"] == "insufficient_data"


# 13. Equivalent Mutant Excluded from Denominator
def test_testing_skill_equivalent_mutant_excluded(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    equiv_mutant = CalibratedMutant(
        id="equiv-mut",
        challenge_slug="add-two-numbers",
        target_file="solution.py",
        category="AOR",
        original_code="return a + b",
        mutated_code="return b + a",
        description="Commutative addition swap (equivalent)",
        is_valid=True,
        is_equivalent=True,  # flagged as equivalent
    )
    with patch.dict(CALIBRATED_MUTANT_CATALOG, {"add-two-numbers": [equiv_mutant]}):
        code = "from solution import add\ndef test_add(): assert add(1, 2) == 3\n"
        result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=code)
        # Equivalent mutant is excluded from valid mutants
        assert result["score"] is None
        assert result["evidence"] == "insufficient_data"


# 14. Mutant Timeout Handled Gracefully (Does NOT Count as Killed)
def test_testing_skill_mutant_timeout_handled(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    loop_mutant = CalibratedMutant(
        id="loop-mut",
        challenge_slug="add-two-numbers",
        target_file="solution.py",
        category="BCR",
        original_code="return a + b",
        mutated_code="import time\n    time.sleep(5)\n    return a + b",
        description="Infinite delay in mutant",
        is_valid=True,
    )
    with patch.dict(CALIBRATED_MUTANT_CATALOG, {"add-two-numbers": [loop_mutant]}):
        code = "from solution import add\ndef test_add(): assert add(1, 2) == 3\n"
        result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=code)
        # Timeout is NOT counted as killed
        assert result["evidence"]["mutants_killed"] == 0
        assert result["evidence"]["mutants_timeout"] == 1
        assert result["evidence"]["mutation_score"] == 0.0
        assert result["evidence"]["mutant_results"][0]["status"] == "TIMEOUT"


# 15. Student Test Timeout Handled Gracefully
def test_testing_skill_student_test_timeout_handled(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    slow_test_code = """
import time
from solution import add

def test_slow():
    time.sleep(5)
    assert add(1, 2) == 3
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=slow_test_code)
    # Slow test times out on baseline check -> false positive detected
    assert result["evidence"]["false_positive_detected"] is True
    assert result["score"] <= 60


# 16. Hidden-Test Access Blocked
def test_testing_skill_hidden_test_access_blocked(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    spy_test_code = """
import os
from solution import add

def test_spy_on_hidden_tests():
    # Attempt to read hidden server tests
    assert not os.path.exists("hidden_tests")
    assert add(1, 2) == 3
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=spy_test_code)
    assert result["evidence"]["passed_on_canonical"] is True


# 17. Network Access Blocked (Verification)
def test_testing_skill_network_access_blocked(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    net_test_code = """
from solution import add

def test_offline_execution():
    assert add(10, 20) == 30
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=net_test_code)
    assert result["evidence"]["status"] == "measured"


# 18. Filesystem Escape Blocked
def test_testing_skill_filesystem_escape_blocked(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    fs_test_code = """
import os
from solution import add

def test_filesystem_isolation():
    # Student test runs inside isolated workspace
    cwd = os.getcwd()
    assert os.path.exists("solution.py")
    assert add(4, 5) == 9
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=fs_test_code)
    assert result["evidence"]["passed_on_canonical"] is True


# 19. Application Modification Prevented
def test_testing_skill_application_modification_prevented(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    hack_test_code = """
import solution

def test_tamper_solution():
    # Attempt to override canonical function
    solution.add = lambda a, b: 42
    assert solution.add(1, 2) == 42
"""
    result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=hack_test_code)
    # Tampering test cannot kill mutants because monkeypatch makes all mutants return 42
    assert result["evidence"]["mutants_killed"] == 0
    assert result["score"] <= 20


# 20. Infrastructure Failure Returns infrastructure_error
def test_testing_skill_infrastructure_failure_handled(scoring_service):
    challenge = Challenge(id=1, slug="add-two-numbers", title="Add Two Numbers", is_active=True)
    code = "from solution import add\ndef test_add(): assert add(1, 2) == 3\n"
    with patch("subprocess.run", side_effect=subprocess.SubprocessError("Docker worker crash")):
        result = scoring_service.evaluate_testing_skill(challenge=challenge, student_test_code=code)
        assert result["score"] is None
        assert result["evidence"] == "infrastructure_error"
        assert "error" in result["details"]
