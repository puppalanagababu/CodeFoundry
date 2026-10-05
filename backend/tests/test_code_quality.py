import pytest
from unittest.mock import patch
import subprocess
from app.models.challenge import Challenge, ChallengeFile
from app.services.skill_scoring import (
    SkillScoringService,
    analyze_code_quality,
    CATEGORY_MAX_DEDUCTIONS,
    CALIBRATED_RULE_DEDUCTIONS,
)


@pytest.fixture
def scoring_service():
    return SkillScoringService()


# 1. Clean Code
def test_code_quality_clean_code(scoring_service):
    clean_code = """
def calculate_total(price: float, tax_rate: float) -> float:
    tax_amount = price * tax_rate
    return price + tax_amount


def format_currency(amount: float) -> str:
    return f"${amount:.2f}"
"""
    result = scoring_service.analyze_code_quality(code=clean_code)
    assert result["score"] == 100
    assert isinstance(result["evidence"], dict)
    assert result["evidence"]["status"] == "measured"
    assert result["evidence"]["findings_count"] == 0
    assert result["evidence"]["total_deductions"] == 0


# 2. Unused Import (F401)
def test_code_quality_unused_import(scoring_service):
    code = """
import sys
import os

def get_status() -> str:
    return os.name

def get_version() -> str:
    return "1.0"
"""
    result = scoring_service.analyze_code_quality(code=code)
    assert result["score"] == 96  # 100 - 4 (F401)
    assert isinstance(result["evidence"], dict)
    assert result["evidence"]["findings_count"] == 1
    assert result["evidence"]["findings"][0]["rule"] == "F401"
    assert result["evidence"]["findings"][0]["category"] == "hygiene"


# 3. Unused Local Variable (F841)
def test_code_quality_unused_local_variable(scoring_service):
    code = """
def compute_metrics(x: int, y: int) -> int:
    unused_intermediate = x * 2
    return x + y

def helper() -> int:
    return 42
"""
    result = scoring_service.analyze_code_quality(code=code)
    assert result["score"] == 96  # 100 - 4 (F841)
    assert isinstance(result["evidence"], dict)
    assert result["evidence"]["findings_count"] == 1
    assert result["evidence"]["findings"][0]["rule"] == "F841"
    assert result["evidence"]["findings"][0]["category"] == "hygiene"


# 4. Mutable Default Argument (B006)
def test_code_quality_mutable_default(scoring_service):
    code = """
def append_item(item: str, target_list: list = []) -> list:
    target_list.append(item)
    return target_list

def helper() -> int:
    return 10
"""
    result = scoring_service.analyze_code_quality(code=code)
    assert result["score"] == 90  # 100 - 10 (B006)
    assert isinstance(result["evidence"], dict)
    assert result["evidence"]["findings_count"] == 1
    assert result["evidence"]["findings"][0]["rule"] == "B006"
    assert result["evidence"]["findings"][0]["category"] == "safety"


# 5. Bare Except (E722 / B001)
def test_code_quality_bare_except(scoring_service):
    code = """
def parse_int_safely(value_str: str) -> int:
    try:
        return int(value_str)
    except:
        return 0

def helper() -> int:
    return 1
"""
    result = scoring_service.analyze_code_quality(code=code)
    assert result["score"] <= 92  # 100 - 8 (E722 / B001)
    assert isinstance(result["evidence"], dict)
    rules = [f["rule"] for f in result["evidence"]["findings"]]
    assert "E722" in rules or "B001" in rules
    assert result["evidence"]["category_deductions"]["safety"] >= 8


# 6. Builtin Shadowing (A001 / A002)
def test_code_quality_builtin_shadowing(scoring_service):
    code = """
def format_items(id: int, list: list) -> list:
    return [id] + list

def helper() -> int:
    return 0
"""
    result = scoring_service.analyze_code_quality(code=code)
    assert result["score"] < 100
    assert isinstance(result["evidence"], dict)
    categories = [f["category"] for f in result["evidence"]["findings"]]
    assert "safety" in categories


# 7. High Cyclomatic Complexity (C901)
def test_code_quality_high_complexity(scoring_service):
    code = """
def complex_dispatcher(action: str, value: int) -> int:
    if action == "add":
        return value + 1
    elif action == "sub":
        return value - 1
    elif action == "mul":
        return value * 2
    elif action == "div":
        return value // 2
    elif action == "mod":
        return value % 2
    elif action == "pow":
        return value ** 2
    elif action == "abs":
        return abs(value)
    return value
"""
    result = scoring_service.analyze_code_quality(code=code)
    assert isinstance(result["evidence"], dict)
    rules = [f["rule"] for f in result["evidence"]["findings"]]
    assert "C901" in rules
    assert result["evidence"]["category_deductions"]["complexity"] >= 10


# 8. Naming Violation (N802 / N806)
def test_code_quality_naming_violation(scoring_service):
    code = """
def BadFunctionName(input_value: int) -> int:
    InvalidVariableName = input_value * 2
    return InvalidVariableName

def valid_function() -> int:
    return 100
"""
    result = scoring_service.analyze_code_quality(code=code)
    assert isinstance(result["evidence"], dict)
    rules = [f["rule"] for f in result["evidence"]["findings"]]
    assert "N802" in rules or "N806" in rules
    assert result["evidence"]["category_deductions"]["style"] > 0


# 9. Egregious Line Length (E501)
def test_code_quality_line_length(scoring_service):
    code_with_long_code_line = (
        'def process_data() -> str:\n'
        '    return "This is a very long string that clearly exceeds the 120 character limit configured in the CodeFoundry Ruff isolated static analysis engine and should trigger E501"\n'
        '\n'
        'def helper() -> int:\n'
        '    return 1\n'
    )
    res = scoring_service.analyze_code_quality(code=code_with_long_code_line)
    assert isinstance(res["evidence"], dict)
    rules = [f["rule"] for f in res["evidence"]["findings"]]
    assert "E501" in rules
    assert res["evidence"]["category_deductions"]["style"] >= 2


# 10. # noqa Suppression Resistance
def test_code_quality_noqa_suppression_resistance(scoring_service):
    code_with_noqa = """
import sys  # noqa: F401
import os   # noqa

def compute(x: int, items: list = []) -> int:  # noqa: B006
    return x + len(items)

def helper() -> int:
    return 1
"""
    result = scoring_service.analyze_code_quality(code=code_with_noqa)
    assert isinstance(result["evidence"], dict)
    rules = [f["rule"] for f in result["evidence"]["findings"]]
    assert "F401" in rules
    assert "B006" in rules
    assert result["score"] < 90


# 11. Student Ruff Config Cannot Disable Rules
def test_code_quality_student_config_ignored(scoring_service):
    files = {
        "pyproject.toml": '[tool.ruff.lint]\nignore = ["ALL"]\n',
        "ruff.toml": 'ignore = ["ALL"]\n',
        ".ruff.toml": 'ignore = ["ALL"]\n',
        "solution.py": """
import sys

def calculate(item: str, items: list = []) -> int:
    return len(items)

def helper() -> int:
    return 0
""",
    }
    result = scoring_service.analyze_code_quality(files=files)
    assert isinstance(result["evidence"], dict)
    rules = [f["rule"] for f in result["evidence"]["findings"]]
    assert "F401" in rules
    assert "B006" in rules


# 12. Read-only File Excluded from Analysis
def test_code_quality_readonly_file_excluded(scoring_service):
    challenge_files = [
        ChallengeFile(id=1, path="starter_template.py", is_readonly=True, is_test=False),
        ChallengeFile(id=2, path="solution.py", is_readonly=False, is_test=False),
    ]
    files = {
        "starter_template.py": "import sys\nimport os\ndef bad_starter(x=[]): pass\n",
        "solution.py": "def add(a: int, b: int) -> int:\n    return a + b\n\ndef sub(a: int, b: int) -> int:\n    return a - b\n\ndef mul(a: int, b: int) -> int:\n    return a * b\n",
    }
    result = scoring_service.analyze_code_quality(files=files, challenge_files=challenge_files)
    assert result["score"] == 100
    assert "starter_template.py" not in result["evidence"]["analyzed_files"]
    assert "solution.py" in result["evidence"]["analyzed_files"]


# 13. Test File Excluded from Analysis
def test_code_quality_test_file_excluded(scoring_service):
    challenge_files = [
        ChallengeFile(id=1, path="solution.py", is_readonly=False, is_test=False),
        ChallengeFile(id=2, path="tests/test_solution.py", is_readonly=True, is_test=True),
    ]
    files = {
        "solution.py": "def multiply(a: int, b: int) -> int:\n    return a * b\n\ndef divide(a: int, b: int) -> int:\n    return a // b\n\ndef add(a: int, b: int) -> int:\n    return a + b\n",
        "tests/test_solution.py": "import sys\nimport pytest\ndef test_fn():\n    x = []\n    assert True\n",
        "helper_test.py": "import os\ndef test_helper(): pass\n",
    }
    result = scoring_service.analyze_code_quality(files=files, challenge_files=challenge_files)
    assert result["score"] == 100
    assert "tests/test_solution.py" not in result["evidence"]["analyzed_files"]
    assert "helper_test.py" not in result["evidence"]["analyzed_files"]
    assert "solution.py" in result["evidence"]["analyzed_files"]


# 14. Helper Python File Included in Analysis
def test_code_quality_helper_python_file_included(scoring_service):
    files = {
        "solution.py": "from utils.helpers import compute_value\n\ndef run() -> int:\n    return compute_value(10)\n\ndef check() -> bool:\n    return True\n",
        "utils/helpers.py": "import sys\n\ndef compute_value(x: int, items: list = []) -> int:\n    return x + len(items)\n\ndef helper() -> int:\n    return 0\n",
    }
    result = scoring_service.analyze_code_quality(files=files)
    assert isinstance(result["evidence"], dict)
    analyzed = result["evidence"]["analyzed_files"]
    assert "solution.py" in analyzed
    assert "utils/helpers.py" in analyzed
    rules = [f["rule"] for f in result["evidence"]["findings"]]
    assert "F401" in rules
    assert "B006" in rules


# 15. Non-Python File Excluded
def test_code_quality_non_python_file_excluded(scoring_service):
    files = {
        "solution.py": "def get_data() -> dict:\n    return {'status': 'ok'}\n\ndef is_ready() -> bool:\n    return True\n\ndef is_active() -> bool:\n    return False\n",
        "data.json": '{"unclosed": "syntax invalid',
        "README.md": "# Title\nInvalid python code def (",
    }
    result = scoring_service.analyze_code_quality(files=files)
    assert result["score"] == 100
    assert "data.json" not in result["evidence"]["analyzed_files"]
    assert "README.md" not in result["evidence"]["analyzed_files"]


# 16. Insufficient Data Handling (< 3 LLOC)
def test_code_quality_insufficient_data(scoring_service):
    tiny_code = "def a(): pass\n"
    result = scoring_service.analyze_code_quality(code=tiny_code)
    assert result["score"] is None
    assert result["evidence"] == "insufficient_data"
    assert result["details"]["lines_of_code"] < 3


# 17. Syntax Error Handled Distinctly (Score 0, status syntax_error)
def test_code_quality_syntax_error_handled_distinctly(scoring_service):
    broken_syntax = "def broken_fn(\n    if x == :\n"
    result = scoring_service.analyze_code_quality(code=broken_syntax)
    assert result["score"] == 0
    assert isinstance(result["evidence"], dict)
    assert result["evidence"]["status"] == "syntax_error"
    assert "SyntaxError" in result["evidence"]["message"]


# 18. Static Analysis Infrastructure Failure Handled Distinctly
def test_code_quality_infrastructure_failure_handled(scoring_service):
    code = "def add(a: int, b: int) -> int:\n    return a + b\n\ndef sub(a: int, b: int) -> int:\n    return a - b\n\ndef mul(a: int, b: int) -> int:\n    return a * b\n"
    with patch("subprocess.run", side_effect=subprocess.SubprocessError("Docker process crash")):
        result = scoring_service.analyze_code_quality(code=code)
        assert result["score"] is None
        assert result["evidence"] == "infrastructure_error"
        assert "error" in result["details"]


# 19. Functionally Failing but Clean Code Receives Independent Measurement
def test_code_quality_functionally_failing_clean_code(scoring_service):
    challenge = Challenge(id=1, slug="sample-challenge", challenge_type="ALGORITHMIC", time_limit=5)
    clean_failing_code = """
def solve_problem(target: int) -> int:
    intermediate_result = target * 10
    return intermediate_result + 42


def helper_transform(value: int) -> int:
    return value * 2
"""
    breakdown = scoring_service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=0,
        tests_failed=5,
        execution_time=0.1,
        code=clean_failing_code,
        language="Python",
    )
    # Problem solving is 0 due to failed tests, but Code Quality is 100!
    assert breakdown["scores"]["problem_solving"] == 0
    assert breakdown["scores"]["code_quality"] == 100
    assert breakdown["evidence"]["code_quality"]["status"] == "measured"


# 20. Functionally Passing but Poor-Quality Code Receives Deductions
def test_code_quality_functionally_passing_poor_quality_code(scoring_service):
    challenge = Challenge(id=1, slug="sample-challenge", challenge_type="ALGORITHMIC", time_limit=5)
    messy_passing_code = """
import sys
import os

def solve_problem(target: int, cache: list = []) -> int:
    try:
        x = 100
        return target + 1
    except:
        return 0

def helper() -> int:
    return 10
"""
    breakdown = scoring_service.calculate_skill_breakdown(
        challenge=challenge,
        tests_total=5,
        tests_passed=5,
        tests_failed=0,
        execution_time=0.05,
        code=messy_passing_code,
        language="Python",
    )
    # Problem solving is 100, but Code Quality received deductions for unused imports, mutable default, bare except, unused local
    assert breakdown["scores"]["problem_solving"] == 100
    assert breakdown["scores"]["code_quality"] is not None
    assert breakdown["scores"]["code_quality"] <= 80
    assert breakdown["evidence"]["code_quality"]["findings_count"] >= 3
