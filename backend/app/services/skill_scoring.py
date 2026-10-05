import ast
import json
import logging
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("app.services.skill_scoring")


def normalize_path(path_str: str) -> str:
    """
    Normalizes a relative path for consistent comparison:
    - Strips whitespace
    - Normalizes backslashes to forward slashes
    - Strips leading './' and leading '/'
    """
    if not isinstance(path_str, str):
        return ""
    p = path_str.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def is_test_file_path(path_str: str) -> bool:
    """
    Checks whether a path matches standard test file patterns:
    - Located within a tests/ or test/ directory
    - Prefix 'test_' in filename
    - Suffix '_test.py' in filename
    """
    p = normalize_path(path_str)
    if not p:
        return False
    return (
        p.startswith("tests/")
        or p.startswith("test/")
        or "/test_" in p
        or p.startswith("test_")
        or p.endswith("_test.py")
    )


# Calibrated baseline performance thresholds (in seconds per test case)
# Format: slug -> (t_optimal_per_test, t_naive_per_test)
CALIBRATED_PERFORMANCE_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    # High-workload performance challenges (scale collections, quadratic vs linear loops)
    "the-slow-report-generator": (0.15, 1.20),
    "slow-search-function": (0.10, 0.80),
    "duplicate-transaction-detector": (0.12, 1.00),
    # Standard algorithmic / backend challenges
    "fix-the-broken-calculator": (0.05, 0.50),
    "the-missing-api-data": (0.08, 0.60),
    "the-exposed-admin-endpoint": (0.06, 0.50),
    "add-two-numbers": (0.05, 0.40),
    "password-validator": (0.05, 0.40),
    "api-response-parser": (0.06, 0.50),
}

# Calibrated test classifications for known bug-fix and debugging challenges
DEBUGGING_TEST_CLASSIFICATION: Dict[str, Dict[str, Set[str]]] = {
    "fix-the-broken-calculator": {
        "regression": {"Basic Arithmetic"},
        "defect": {
            "Compound Expression",
            "Mixed Operations with Division",
            "Division by Zero Handling",
            "Chained Multi-Operator Expression",
        },
    },
    "add-two-numbers": {
        "regression": {"Basic Addition", "Zero"},
        "defect": {"Larger Numbers", "Negative Number", "Large Values"},
    },
    "password-validator": {
        "regression": {"Standard Valid Password", "Exactly 8 Characters"},
        "defect": {"Too Short Password", "Missing Digit", "Missing Uppercase"},
    },
    "api-response-parser": {
        "regression": {"Standard User Payload"},
        "defect": {"Missing Email Field", "Missing Name Field", "Empty JSON Object"},
    },
}

# Calibrated test classifications for known security challenges
SECURITY_TEST_CLASSIFICATION: Dict[str, Dict[str, Set[str]]] = {
    "the-exposed-admin-endpoint": {
        "authorized": {"Administrator access", "Public endpoint behavior"},
        "exploit": {
            "Restricted account access",
            "Missing authentication access",
            "Secondary non-admin role rejection",
        },
    },
}

# ==============================================================================
# Code Quality Calibration Constants & Rule Families
# ==============================================================================

# Maximum allowed deduction per category (capped to ensure balanced multi-factor scoring)
CATEGORY_MAX_DEDUCTIONS: Dict[str, int] = {
    "complexity": 35,
    "safety": 25,
    "hygiene": 25,
    "style": 15,
}

# Calibrated deductions for verified static analysis rule codes (Category, Penalty)
CALIBRATED_RULE_DEDUCTIONS: Dict[str, Tuple[str, int]] = {
    # 1. Complexity (C901, etc.)
    "C901": ("complexity", 10),  # Cyclomatic complexity exceeds threshold (> 6)

    # 2. Safety / Robustness / Defensive Coding (Bugbear, Pycodestyle safety, Simplify)
    "B006": ("safety", 10),      # Mutable default argument in function definition
    "B001": ("safety", 8),       # Do not use bare `except:`
    "E722": ("safety", 8),       # Do not use bare `except:` (pycodestyle)
    "A001": ("safety", 4),       # Variable / function shadows Python builtin
    "A002": ("safety", 4),       # Argument shadows Python builtin
    "SIM115": ("safety", 6),     # Use a context manager for opening files
    "B018": ("safety", 4),       # Found useless expression
    "B007": ("safety", 3),       # Loop control variable not used within loop body
    "B008": ("safety", 5),       # Do not perform function call in argument defaults
    "B027": ("safety", 4),       # Empty method in abstract base class without decorator

    # 3. Hygiene & Dead Code (Pyflakes)
    "F401": ("hygiene", 4),      # Module imported but unused
    "F841": ("hygiene", 4),      # Local variable is assigned to but never used
    "F601": ("hygiene", 5),      # Multi-value repeated key in dictionary
    "F704": ("hygiene", 6),      # Yield statement outside of function
    "F706": ("hygiene", 6),      # Return statement outside of function / method
    "F821": ("hygiene", 6),      # Undefined name
    "F811": ("hygiene", 4),      # Redefinition of unused name from line N

    # 4. Style & Consistency (PEP 8 naming, length, comparisons)
    "E501": ("style", 2),        # Line too long (> 120 characters)
    "N802": ("style", 2),        # Function name should be lowercase
    "N806": ("style", 2),        # Variable in function should be lowercase
    "N803": ("style", 2),        # Argument name should be lowercase
    "N801": ("style", 2),        # Class name should use CapWords convention
    "E711": ("style", 2),        # Comparison to None should be 'if cond is None:'
    "E712": ("style", 2),        # Comparison to True/False should be 'if cond:' or 'if not cond:'
}

# Prefix fallback mappings for rules not explicitly in CALIBRATED_RULE_DEDUCTIONS
RULE_PREFIX_CATEGORIES: Dict[str, Tuple[str, int]] = {
    "C": ("complexity", 6),
    "B": ("safety", 5),
    "A": ("safety", 4),
    "F": ("hygiene", 4),
    "N": ("style", 2),
    "E": ("style", 2),
    "W": ("style", 2),
    "SIM": ("style", 2),
}


def get_performance_thresholds(challenge: Any, tests_total: int) -> Tuple[float, float]:
    """
    Resolves total (T_optimal, T_naive) execution thresholds in seconds across tests_total cases.
    Resolution priority:
    1. Explicit challenge model attributes (if configured): challenge.t_optimal, challenge.t_naive
    2. Calibrated slug registry mapping
    3. Principled default derived from challenge.time_limit (scaled per test case)
    """
    tests_count = max(1, tests_total)

    # 1. Explicit model attributes (forward-compatible with future schema extensions)
    t_opt_attr = getattr(challenge, "t_optimal", None)
    t_naive_attr = getattr(challenge, "t_naive", None)
    if (
        isinstance(t_opt_attr, (int, float))
        and isinstance(t_naive_attr, (int, float))
        and t_opt_attr > 0
        and t_naive_attr > t_opt_attr
    ):
        return float(t_opt_attr), float(t_naive_attr)

    # 2. Calibrated registry by slug
    slug = getattr(challenge, "slug", "")
    if slug and slug in CALIBRATED_PERFORMANCE_THRESHOLDS:
        opt_per_test, naive_per_test = CALIBRATED_PERFORMANCE_THRESHOLDS[slug]
        return (opt_per_test * tests_count, naive_per_test * tests_count)

    # 3. Principled baseline derived from challenge time_limit
    time_limit = getattr(challenge, "time_limit", 5) or 5
    time_limit_f = max(0.5, float(time_limit))

    # Standard optimal solution finishes in <= 0.10s per test case in Docker
    opt_per_test = min(0.15, max(0.02, time_limit_f * 0.05))
    # Naive solution ceiling before receiving 0 time credit
    naive_per_test = min(2.0, max(opt_per_test * 2.0, time_limit_f * 0.40))

    return (opt_per_test * tests_count, naive_per_test * tests_count)


def analyze_code_quality(
    code: Optional[str] = None,
    files: Optional[Dict[str, str]] = None,
    challenge_files: Optional[List[Any]] = None,
    language: Optional[str] = "Python",
) -> Dict[str, Any]:
    """
    Deterministically computes a Code Quality score (0-100) and evidence payload
    using Ruff static analysis with isolated configuration and anti-gaming protections.
    """
    if language and str(language).strip().lower() != "python":
        return {
            "score": None,
            "evidence": "not_measured",
            "details": {"reason": f"Language '{language}' is not supported for Code Quality static analysis."},
        }

    # 1. Identify and filter eligible Python source files
    readonly_paths: Set[str] = set()
    test_paths: Set[str] = set()

    if challenge_files:
        for cf in challenge_files:
            cf_path = getattr(cf, "path", "")
            norm_p = normalize_path(cf_path)
            if getattr(cf, "is_readonly", False):
                readonly_paths.add(norm_p)
                readonly_paths.add(cf_path)
            if getattr(cf, "is_test", False) or is_test_file_path(norm_p) or is_test_file_path(cf_path):
                test_paths.add(norm_p)
                test_paths.add(cf_path)

    analyzed_files: Dict[str, str] = {}

    if files and isinstance(files, dict):
        for raw_path, content in files.items():
            norm_p = normalize_path(raw_path)

            # Must be a Python file
            if not norm_p.endswith(".py"):
                continue

            # Must NOT be a test file
            if norm_p in test_paths or raw_path in test_paths or is_test_file_path(norm_p) or is_test_file_path(raw_path):
                continue

            # Must NOT be a readonly starter file
            if norm_p in readonly_paths or raw_path in readonly_paths:
                continue

            # Exclude build / cache artifacts
            if any(seg in norm_p.split("/") for seg in ["__pycache__", ".pytest_cache", ".venv", ".ruff_cache", ".git", "build", "dist"]):
                continue

            analyzed_files[norm_p] = content or ""
    elif code is not None:
        analyzed_files["solution.py"] = code or ""

    if not analyzed_files:
        return {
            "score": None,
            "evidence": "insufficient_data",
            "details": {
                "analyzed_files": [],
                "lines_of_code": 0,
                "reason": "No editable Python application files found.",
            },
        }

    # 2. Check for Syntax Errors via AST Parsing
    for filename, content in analyzed_files.items():
        try:
            ast.parse(content, filename=filename)
        except SyntaxError as syn_err:
            return {
                "score": 0,
                "evidence": {
                    "status": "syntax_error",
                    "message": f"SyntaxError in {filename}: {syn_err.msg} (line {syn_err.lineno})",
                    "analyzed_files": list(analyzed_files.keys()),
                    "lines_of_code": len([l for l in content.splitlines() if l.strip()]),
                    "findings_count": 1,
                    "findings": [{
                        "rule": "E999",
                        "category": "syntax",
                        "message": f"SyntaxError: {syn_err.msg}",
                        "file": filename,
                        "line": syn_err.lineno or 1,
                        "penalty": 100,
                    }],
                },
            }

    # 3. Insufficient Data Check (LLOC threshold)
    total_lloc = sum(
        len([line for line in content.splitlines() if line.strip() and not line.strip().startswith("#")])
        for content in analyzed_files.values()
    )

    if total_lloc < 3:
        return {
            "score": None,
            "evidence": "insufficient_data",
            "details": {
                "analyzed_files": list(analyzed_files.keys()),
                "lines_of_code": total_lloc,
                "reason": "Insufficient code volume for meaningful quality evaluation (< 3 non-comment LLOC).",
            },
        }

    # 4. Execute Ruff with Isolated Configuration
    with tempfile.TemporaryDirectory() as tmpdir:
        for rel_path, content in analyzed_files.items():
            full_path = os.path.join(tmpdir, rel_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        cmd = [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--isolated",
            "--ignore-noqa",
            "--no-cache",
            "--output-format",
            "json",
            "--select",
            "E,F,B,C901,SIM,N,A",
            "--config",
            "lint.mccabe.max-complexity=6",
            "--config",
            "lint.pycodestyle.max-line-length=120",
            tmpdir,
        ]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            raw_output = res.stdout.strip()
            raw_findings = json.loads(raw_output) if raw_output else []
        except Exception as tool_err:
            logger.warning("Ruff static analysis tool execution failed: %s", tool_err)
            return {
                "score": None,
                "evidence": "infrastructure_error",
                "details": {"error": str(tool_err)},
            }

    # 5. Map Findings to Categories and Calibrated Deductions
    findings: List[Dict[str, Any]] = []
    raw_category_deductions: Dict[str, int] = {cat: 0 for cat in CATEGORY_MAX_DEDUCTIONS}
    category_counts: Dict[str, int] = {cat: 0 for cat in CATEGORY_MAX_DEDUCTIONS}

    for item in raw_findings:
        rule_code = item.get("code", "")
        if not rule_code or rule_code in ["invalid-syntax", "E999"]:
            continue

        if rule_code in CALIBRATED_RULE_DEDUCTIONS:
            category, penalty = CALIBRATED_RULE_DEDUCTIONS[rule_code]
        else:
            # Fallback by rule code prefix
            matched = False
            for prefix, (cat, pen) in RULE_PREFIX_CATEGORIES.items():
                if rule_code.startswith(prefix):
                    category, penalty = cat, pen
                    matched = True
                    break
            if not matched:
                category, penalty = "style", 1

        raw_filename = item.get("filename", "")
        rel_filename = raw_filename.replace(tmpdir, "").lstrip("\\/").replace("\\", "/")

        findings.append({
            "rule": rule_code,
            "category": category,
            "message": item.get("message", ""),
            "file": rel_filename,
            "line": item.get("location", {}).get("row", 1),
            "penalty": penalty,
        })

        raw_category_deductions[category] += penalty
        category_counts[category] += 1

    # 6. Apply Category Caps and Calculate Bounded Score
    category_deductions: Dict[str, int] = {}
    for cat, max_cap in CATEGORY_MAX_DEDUCTIONS.items():
        category_deductions[cat] = min(raw_category_deductions.get(cat, 0), max_cap)

    total_deductions = sum(category_deductions.values())
    quality_score = max(0, min(100, 100 - total_deductions))

    return {
        "score": quality_score,
        "evidence": {
            "status": "measured",
            "lines_of_code": total_lloc,
            "analyzed_files": list(analyzed_files.keys()),
            "findings_count": len(findings),
            "category_counts": category_counts,
            "category_deductions": category_deductions,
            "total_deductions": total_deductions,
            "findings": findings[:50],
        },
    }



# ==============================================================================
# Testing Skill Calibration, Weights & Pre-Calibrated Mutant Catalog
# ==============================================================================

TESTING_CALIBRATION_WEIGHTS: Dict[str, float] = {
    "weight_mutation": 0.70,
    "weight_edge": 0.20,
    "weight_assertion": 0.10,
    "weight_mutation_no_edge": 0.85,
    "weight_assertion_no_edge": 0.15,
    "penalty_false_positive": 40.0,
    "per_mutant_timeout_seconds": 1.0,
    "baseline_timeout_seconds": 2.0,
}


class CalibratedMutant:
    def __init__(
        self,
        id: str,
        challenge_slug: str,
        target_file: str,
        category: str,
        original_code: str,
        mutated_code: str,
        description: str,
        is_valid: bool = True,
        is_equivalent: bool = False,
        is_edge_case: bool = False,
    ):
        self.id = id
        self.challenge_slug = challenge_slug
        self.target_file = target_file
        self.category = category
        self.original_code = original_code
        self.mutated_code = mutated_code
        self.description = description
        self.is_valid = is_valid
        self.is_equivalent = is_equivalent
        self.is_edge_case = is_edge_case

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "challenge_slug": self.challenge_slug,
            "target_file": self.target_file,
            "category": self.category,
            "description": self.description,
            "is_valid": self.is_valid,
            "is_equivalent": self.is_equivalent,
            "is_edge_case": self.is_edge_case,
        }


# Server-authoritative Canonical Solutions for challenges
CANONICAL_CHALLENGE_SOLUTIONS: Dict[str, Dict[str, str]] = {
    "fix-the-broken-calculator": {
        "app/calculator.py": (
            "class Calculator:\n"
            "    PRECEDENCE = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2}\n"
            "    def _apply_operator(self, op: str, b: float, a: float):\n"
            "        if op == '+': return a + b\n"
            "        if op == '-': return a - b\n"
            "        if op == '*': return a * b\n"
            "        if op == '/':\n"
            "            if b == 0: raise ZeroDivisionError('Division by zero')\n"
            "            return a / b\n"
            "        if op == '%':\n"
            "            if b == 0: raise ZeroDivisionError('Division by zero')\n"
            "            return a % b\n"
            "        raise ValueError(f'Unknown operator: {op}')\n"
            "    def evaluate(self, expression: str):\n"
            "        tokens = expression.strip().split()\n"
            "        if not tokens: return 0\n"
            "        values, operators = [], []\n"
            "        try:\n"
            "            for token in tokens:\n"
            "                if token in self.PRECEDENCE:\n"
            "                    while operators and self.PRECEDENCE.get(operators[-1], 0) >= self.PRECEDENCE[token]:\n"
            "                        op = operators.pop()\n"
            "                        val2 = values.pop()\n"
            "                        val1 = values.pop()\n"
            "                        values.append(self._apply_operator(op, val2, val1))\n"
            "                    operators.append(token)\n"
            "                else:\n"
            "                    values.append(float(token))\n"
            "            while operators:\n"
            "                op = operators.pop()\n"
            "                val2 = values.pop()\n"
            "                val1 = values.pop()\n"
            "                values.append(self._apply_operator(op, val2, val1))\n"
            "            res = values[0] if values else 0\n"
            "            if isinstance(res, (int, float)) and res == int(res): return int(res)\n"
            "            return res\n"
            "        except ZeroDivisionError:\n"
            "            return 'Error: Division by zero'\n"
        ),
        "app/__init__.py": "",
    },
    "add-two-numbers": {
        "solution.py": (
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n"
        )
    },
    "password-validator": {
        "solution.py": (
            "def validate_password(password: str) -> bool:\n"
            "    if not isinstance(password, str) or len(password) < 8:\n"
            "        return False\n"
            "    has_digit = any(c.isdigit() for c in password)\n"
            "    has_upper = any(c.isupper() for c in password)\n"
            "    return has_digit and has_upper\n"
        )
    },
    "api-response-parser": {
        "solution.py": (
            "def parse_user(payload: dict) -> dict:\n"
            "    if not isinstance(payload, dict) or not payload:\n"
            "        return {'error': 'empty_payload'}\n"
            "    user_id = payload.get('id')\n"
            "    name = payload.get('name', '')\n"
            "    email = payload.get('email', '')\n"
            "    if user_id is None or not name or not email:\n"
            "        return {'error': 'missing_fields'}\n"
            "    return {'id': user_id, 'name': name, 'email': email}\n"
        )
    },
}

# Pre-Calibrated Mutant Catalog for active challenges
CALIBRATED_MUTANT_CATALOG: Dict[str, List[CalibratedMutant]] = {
    "fix-the-broken-calculator": [
        CalibratedMutant(
            id="calc-mut-01",
            challenge_slug="fix-the-broken-calculator",
            target_file="app/calculator.py",
            category="AOR",
            original_code="if op == '+': return a + b",
            mutated_code="if op == '+': return a - b",
            description="Arithmetic operator swap: addition replaced with subtraction",
        ),
        CalibratedMutant(
            id="calc-mut-02",
            challenge_slug="fix-the-broken-calculator",
            target_file="app/calculator.py",
            category="AOR",
            original_code="if op == '*': return a * b",
            mutated_code="if op == '*': return a + b",
            description="Arithmetic operator swap: multiplication replaced with addition",
        ),
        CalibratedMutant(
            id="calc-mut-03",
            challenge_slug="fix-the-broken-calculator",
            target_file="app/calculator.py",
            category="BCR",
            original_code="if b == 0: raise ZeroDivisionError('Division by zero')",
            mutated_code="if b == 0: return 0.0",
            description="Boundary condition replacement: zero division error suppressed",
            is_edge_case=True,
        ),
        CalibratedMutant(
            id="calc-mut-04",
            challenge_slug="fix-the-broken-calculator",
            target_file="app/calculator.py",
            category="BCR",
            original_code="if not tokens: return 0",
            mutated_code="if not tokens: return -1",
            description="Boundary condition replacement: empty token list return value altered",
            is_edge_case=True,
        ),
        CalibratedMutant(
            id="calc-mut-05",
            challenge_slug="fix-the-broken-calculator",
            target_file="app/calculator.py",
            category="ROR",
            original_code="self.PRECEDENCE.get(operators[-1], 0) >= self.PRECEDENCE[token]",
            mutated_code="self.PRECEDENCE.get(operators[-1], 0) > self.PRECEDENCE[token]",
            description="Relational operator invert in precedence handling",
        ),
        CalibratedMutant(
            id="calc-mut-06",
            challenge_slug="fix-the-broken-calculator",
            target_file="app/calculator.py",
            category="AOR",
            original_code="if op == '%':",
            mutated_code="if op == '/':",
            description="Operator mapping corruption for modulo",
        ),
    ],
    "add-two-numbers": [
        CalibratedMutant(
            id="add-mut-01",
            challenge_slug="add-two-numbers",
            target_file="solution.py",
            category="AOR",
            original_code="return a + b",
            mutated_code="return a - b",
            description="Arithmetic operator swap: addition replaced with subtraction",
        ),
        CalibratedMutant(
            id="add-mut-02",
            challenge_slug="add-two-numbers",
            target_file="solution.py",
            category="AOR",
            original_code="return a + b",
            mutated_code="return a * b",
            description="Arithmetic operator swap: addition replaced with multiplication",
            is_edge_case=True,
        ),
        CalibratedMutant(
            id="add-mut-03",
            challenge_slug="add-two-numbers",
            target_file="solution.py",
            category="BCR",
            original_code="return a + b",
            mutated_code="return a + b + 1",
            description="Boundary constant shift: off-by-one added to sum",
        ),
    ],
    "password-validator": [
        CalibratedMutant(
            id="pwd-mut-01",
            challenge_slug="password-validator",
            target_file="solution.py",
            category="BCR",
            original_code="len(password) < 8",
            mutated_code="len(password) < 6",
            description="Boundary condition replacement: minimum length lowered to 6",
            is_edge_case=True,
        ),
        CalibratedMutant(
            id="pwd-mut-02",
            challenge_slug="password-validator",
            target_file="solution.py",
            category="SDL",
            original_code="has_digit = any(c.isdigit() for c in password)",
            mutated_code="has_digit = True",
            description="Statement deletion / bypass: digit requirement bypassed",
        ),
        CalibratedMutant(
            id="pwd-mut-03",
            challenge_slug="password-validator",
            target_file="solution.py",
            category="SDL",
            original_code="has_upper = any(c.isupper() for c in password)",
            mutated_code="has_upper = True",
            description="Statement deletion / bypass: uppercase requirement bypassed",
        ),
    ],
    "api-response-parser": [
        CalibratedMutant(
            id="api-mut-01",
            challenge_slug="api-response-parser",
            target_file="solution.py",
            category="BCR",
            original_code="if not isinstance(payload, dict) or not payload:",
            mutated_code="if not isinstance(payload, dict):",
            description="Boundary condition replacement: empty dict payload check removed",
            is_edge_case=True,
        ),
        CalibratedMutant(
            id="api-mut-02",
            challenge_slug="api-response-parser",
            target_file="solution.py",
            category="LCR",
            original_code="if user_id is None or not name or not email:",
            mutated_code="if user_id is None and not name and not email:",
            description="Logical connector replacement: OR changed to AND for missing fields",
        ),
        CalibratedMutant(
            id="api-mut-03",
            challenge_slug="api-response-parser",
            target_file="solution.py",
            category="SDL",
            original_code="return {'id': user_id, 'name': name, 'email': email}",
            mutated_code="return {'id': user_id, 'name': name}",
            description="Statement deletion: email field stripped from output",
        ),
    ],
}


def inspect_test_suite_ast(code: str) -> Dict[str, Any]:
    """
    Deterministically inspects student test suite code via AST, detecting:
    - total test functions
    - valid assertions
    - trivial/constant assertions (assert True, assert 1 == 1)
    - assertionless test functions
    - duplicate test bodies
    """
    tree = ast.parse(code)
    test_functions = []
    total_valid_assertions = 0
    total_trivial_assertions = 0
    assertionless_tests = 0
    test_hashes: Set[str] = set()
    duplicate_tests = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            test_functions.append(node)
            assert_nodes = []
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    assert_nodes.append(child)
                elif isinstance(child, ast.Call) and getattr(child.func, "attr", "").startswith("assert"):
                    assert_nodes.append(child)

            if not assert_nodes:
                assertionless_tests += 1
                continue

            fn_valid_asserts = 0
            for a in assert_nodes:
                is_trivial = False
                if isinstance(a, ast.Assert):
                    if isinstance(a.test, ast.Constant):
                        is_trivial = True
                    elif isinstance(a.test, ast.Compare):
                        if isinstance(a.test.left, ast.Constant) and all(isinstance(c, ast.Constant) for c in a.test.comparators):
                            is_trivial = True
                    elif isinstance(a.test, ast.UnaryOp) and isinstance(a.test.operand, ast.Constant):
                        is_trivial = True
                elif isinstance(a, ast.Call):
                    if a.args and all(isinstance(arg, ast.Constant) for arg in a.args):
                        is_trivial = True

                if is_trivial:
                    total_trivial_assertions += 1
                else:
                    fn_valid_asserts += 1

            total_valid_assertions += fn_valid_asserts

            # Body signature (ignoring docstring)
            body_stmts = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
            body_dump = ast.dump(ast.Module(body=body_stmts, type_ignores=[]))
            if body_dump in test_hashes:
                duplicate_tests += 1
            else:
                test_hashes.add(body_dump)

    return {
        "tests_count": len(test_functions),
        "valid_assertions": total_valid_assertions,
        "trivial_assertions": total_trivial_assertions,
        "assertionless_tests": assertionless_tests,
        "duplicate_tests": duplicate_tests,
    }


def evaluate_testing_skill(
    challenge: Any,
    student_test_code: Optional[str] = None,
    files: Optional[Dict[str, str]] = None,
    challenge_files: Optional[List[Any]] = None,
    language: Optional[str] = "Python",
) -> Dict[str, Any]:
    """
    Deterministically evaluates student-authored test suites using mutation testing
    against server-authoritative Canonical Solutions and pre-calibrated mutants.
    """
    if language and str(language).strip().lower() != "python":
        return {
            "score": None,
            "evidence": "not_measured",
            "details": {"reason": f"Language '{language}' is not supported for Testing skill evaluation."},
        }

    # 1. Extract student test code
    test_code_to_run = student_test_code or ""
    if not test_code_to_run and files and isinstance(files, dict):
        for raw_path, content in files.items():
            norm_p = normalize_path(raw_path)
            if is_test_file_path(norm_p) or is_test_file_path(raw_path):
                test_code_to_run = content
                break

    if not test_code_to_run or not test_code_to_run.strip():
        return {
            "score": None,
            "evidence": "insufficient_data",
            "details": {"reason": "No student-authored test files submitted."},
        }

    # 2. Check AST and assertion quality of student tests
    try:
        ast_meta = inspect_test_suite_ast(test_code_to_run)
    except SyntaxError as syn_err:
        return {
            "score": 0,
            "evidence": {
                "status": "syntax_error",
                "message": f"SyntaxError in student tests: {syn_err.msg} (line {syn_err.lineno})",
                "tests_authored": 0,
            },
        }

    if ast_meta["tests_count"] == 0:
        return {
            "score": None,
            "evidence": "insufficient_data",
            "details": {"reason": "No test functions (def test_*) detected in submitted test code."},
        }

    # 3. Resolve server-authoritative Canonical Reference Solution
    slug = getattr(challenge, "slug", "")
    canonical_files_map: Dict[str, str] = {}
    if slug and slug in CANONICAL_CHALLENGE_SOLUTIONS:
        canonical_files_map = dict(CANONICAL_CHALLENGE_SOLUTIONS[slug])
    elif challenge_files:
        canonical_files_map = {
            cf.path: cf.content
            for cf in challenge_files
            if not (cf.is_test or is_test_file_path(cf.path))
        }

    if not canonical_files_map:
        return {
            "score": None,
            "evidence": "insufficient_data",
            "details": {"reason": f"No canonical reference solution configured for challenge '{slug}'."},
        }

    # 4. Baseline Execution against Canonical Solution
    baseline_timeout = TESTING_CALIBRATION_WEIGHTS.get("baseline_timeout_seconds", 2.0)
    per_mutant_timeout = TESTING_CALIBRATION_WEIGHTS.get("per_mutant_timeout_seconds", 1.0)
    passed_on_canonical = False
    false_positive_detected = False

    with tempfile.TemporaryDirectory() as tmpdir:
        for rel_path, content in canonical_files_map.items():
            full_p = os.path.join(tmpdir, rel_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(full_p), exist_ok=True)
            with open(full_p, "w", encoding="utf-8") as f:
                f.write(content)

        test_p = os.path.join(tmpdir, "tests", "test_student.py")
        os.makedirs(os.path.dirname(test_p), exist_ok=True)
        with open(test_p, "w", encoding="utf-8") as f:
            f.write(test_code_to_run)

        env = os.environ.copy()
        env["PYTHONPATH"] = tmpdir

        try:
            res_base = subprocess.run(
                [sys.executable, "-m", "pytest", "-o", "pythonpath=.", "tests/test_student.py"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                env=env,
                timeout=baseline_timeout,
            )
            passed_on_canonical = (res_base.returncode == 0)
            false_positive_detected = not passed_on_canonical
        except subprocess.TimeoutExpired:
            false_positive_detected = True
            passed_on_canonical = False
        except Exception as tool_err:
            logger.warning("Testing skill baseline execution failed: %s", tool_err)
            return {
                "score": None,
                "evidence": "infrastructure_error",
                "details": {"error": str(tool_err)},
            }

    # 5. Execute Student Tests against Pre-Calibrated Mutant Catalog
    mutants_list = CALIBRATED_MUTANT_CATALOG.get(slug, [])
    valid_candidates = [m for m in mutants_list if m.is_valid and not m.is_equivalent]

    verified_valid_mutants: List[Tuple[CalibratedMutant, str]] = []
    for mutant in valid_candidates:
        target_file = mutant.target_file
        orig_content = canonical_files_map.get(target_file, "")
        if mutant.original_code in orig_content:
            mutated_content = orig_content.replace(mutant.original_code, mutant.mutated_code, 1)
        else:
            mutated_content = mutant.mutated_code

        # Validate mutated syntax
        try:
            ast.parse(mutated_content)
            verified_valid_mutants.append((mutant, mutated_content))
        except SyntaxError:
            # Skip invalid mutant from denominator
            continue

    if not verified_valid_mutants:
        return {
            "score": None,
            "evidence": "insufficient_data",
            "details": {"reason": f"No valid calibrated mutants available for challenge '{slug}'."},
        }

    killed_mutants = 0
    survived_mutants = 0
    timeout_mutants = 0
    edge_mutants_killed = 0
    total_edge_mutants = sum(1 for m, _ in verified_valid_mutants if m.is_edge_case)
    mutant_results: List[Dict[str, Any]] = []

    for mutant, mutated_content in verified_valid_mutants:
        target_file = mutant.target_file

        with tempfile.TemporaryDirectory() as mut_dir:
            for rel_path, content in canonical_files_map.items():
                full_p = os.path.join(mut_dir, rel_path.replace("/", os.sep))
                os.makedirs(os.path.dirname(full_p), exist_ok=True)
                file_text = mutated_content if rel_path == target_file else content
                with open(full_p, "w", encoding="utf-8") as f:
                    f.write(file_text)

            test_p = os.path.join(mut_dir, "tests", "test_student.py")
            os.makedirs(os.path.dirname(test_p), exist_ok=True)
            with open(test_p, "w", encoding="utf-8") as f:
                f.write(test_code_to_run)

            env = os.environ.copy()
            env["PYTHONPATH"] = mut_dir

            try:
                res_mut = subprocess.run(
                    [sys.executable, "-m", "pytest", "-o", "pythonpath=.", "tests/test_student.py"],
                    capture_output=True,
                    text=True,
                    cwd=mut_dir,
                    env=env,
                    timeout=per_mutant_timeout,
                )
                if res_mut.returncode != 0:
                    killed_mutants += 1
                    if mutant.is_edge_case:
                        edge_mutants_killed += 1
                    mutant_results.append({
                        "id": mutant.id,
                        "category": mutant.category,
                        "status": "KILLED",
                        "description": mutant.description,
                    })
                else:
                    survived_mutants += 1
                    mutant_results.append({
                        "id": mutant.id,
                        "category": mutant.category,
                        "status": "SURVIVED",
                        "description": mutant.description,
                    })
            except subprocess.TimeoutExpired:
                timeout_mutants += 1
                mutant_results.append({
                    "id": mutant.id,
                    "category": mutant.category,
                    "status": "TIMEOUT",
                    "description": mutant.description,
                })
            except Exception as tool_err:
                logger.warning("Testing skill mutant %s execution error: %s", mutant.id, tool_err)
                mutant_results.append({
                    "id": mutant.id,
                    "category": mutant.category,
                    "status": "INFRASTRUCTURE_ERROR",
                    "description": mutant.description,
                })

    # 6. Compute Testing Score Components
    m_total = len(verified_valid_mutants)
    s_mutation = (killed_mutants / m_total * 100.0) if m_total > 0 else 0.0

    unique_test_count = max(1, ast_meta["tests_count"] - ast_meta["duplicate_tests"])
    if ast_meta["trivial_assertions"] > 0 and ast_meta["valid_assertions"] == 0:
        s_assertion = 0.0
    elif ast_meta["valid_assertions"] >= unique_test_count:
        s_assertion = 100.0
    else:
        assert_ratio = ast_meta["valid_assertions"] / unique_test_count
        s_assertion = min(100.0, assert_ratio * 100.0)

    p_false_pos = TESTING_CALIBRATION_WEIGHTS.get("penalty_false_positive", 40.0) if false_positive_detected else 0.0

    if total_edge_mutants > 0:
        s_edge = (edge_mutants_killed / total_edge_mutants) * 100.0
        w_mut = TESTING_CALIBRATION_WEIGHTS.get("weight_mutation", 0.70)
        w_edge = TESTING_CALIBRATION_WEIGHTS.get("weight_edge", 0.20)
        w_assert = TESTING_CALIBRATION_WEIGHTS.get("weight_assertion", 0.10)
        raw_score = (w_mut * s_mutation + w_edge * s_edge + w_assert * s_assertion) - p_false_pos
    else:
        s_edge = None
        w_mut = TESTING_CALIBRATION_WEIGHTS.get("weight_mutation_no_edge", 0.85)
        w_assert = TESTING_CALIBRATION_WEIGHTS.get("weight_assertion_no_edge", 0.15)
        raw_score = (w_mut * s_mutation + w_assert * s_assertion) - p_false_pos

    final_score = max(0, min(100, round(raw_score)))

    return {
        "score": final_score,
        "evidence": {
            "status": "measured",
            "tests_authored": ast_meta["tests_count"],
            "valid_assertions": ast_meta["valid_assertions"],
            "trivial_assertions": ast_meta["trivial_assertions"],
            "duplicate_tests": ast_meta["duplicate_tests"],
            "passed_on_canonical": passed_on_canonical,
            "false_positive_detected": false_positive_detected,
            "mutants_total": m_total,
            "mutants_killed": killed_mutants,
            "mutants_survived": survived_mutants,
            "mutants_timeout": timeout_mutants,
            "mutation_score": round(s_mutation, 1),
            "edge_score": round(s_edge, 1) if s_edge is not None else None,
            "assertion_score": round(s_assertion, 1),
            "mutant_results": mutant_results,
        },
    }


class SkillScoringService:
    """
    Computes an explainable, deterministic skill breakdown for completed evaluations
    based on test pass rates, challenge type, execution resource metrics, Code Quality,
    and Testing skill mutation sensitivity.
    Runs standalone without Django dependencies.
    """

    def analyze_code_quality(
        self,
        code: Optional[str] = None,
        files: Optional[Dict[str, str]] = None,
        challenge_files: Optional[List[Any]] = None,
        language: Optional[str] = "Python",
    ) -> Dict[str, Any]:
        return analyze_code_quality(
            code=code,
            files=files,
            challenge_files=challenge_files,
            language=language,
        )

    def evaluate_testing_skill(
        self,
        challenge: Any,
        student_test_code: Optional[str] = None,
        files: Optional[Dict[str, str]] = None,
        challenge_files: Optional[List[Any]] = None,
        language: Optional[str] = "Python",
    ) -> Dict[str, Any]:
        return evaluate_testing_skill(
            challenge=challenge,
            student_test_code=student_test_code,
            files=files,
            challenge_files=challenge_files,
            language=language,
        )

    def calculate_skill_breakdown(
        self,
        challenge: Any,
        tests_total: int,
        tests_passed: int,
        tests_failed: int,
        execution_time: Optional[float] = None,
        memory_used: Optional[float] = None,
        test_results: Optional[List[Dict[str, Any]]] = None,
        code: Optional[str] = None,
        files: Optional[Dict[str, str]] = None,
        challenge_files: Optional[List[Any]] = None,
        language: Optional[str] = "Python",
        student_test_code: Optional[str] = None,
    ) -> Dict[str, Dict[str, Optional[Any]]]:
        scores: Dict[str, Optional[int]] = {
            "problem_solving": None,
            "debugging": None,
            "security": None,
            "performance": None,
            "code_quality": None,
            "testing": None,
        }
        evidence: Dict[str, Any] = {
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

        # 2. Debugging (Defect Resolution x Regression Preservation)
        challenge_type = getattr(challenge, "challenge_type", "")
        if challenge_type in ["BUG_FIX", "DEBUGGING"]:
            if tests_total <= 0 or scores["problem_solving"] is None:
                scores["debugging"] = None
                evidence["debugging"] = "not_measured"
            elif not test_results:
                scores["debugging"] = scores["problem_solving"]
                evidence["debugging"] = "bug_fix_tests"
            else:
                slug = getattr(challenge, "slug", "")
                classifications = DEBUGGING_TEST_CLASSIFICATION.get(slug)

                defect_passed = 0
                defect_total = 0
                regression_passed = 0
                regression_total = 0

                for t_res in test_results:
                    t_name = t_res.get("name", "")
                    passed = bool(t_res.get("passed", False))

                    # 1. Explicit metadata check
                    is_defect = t_res.get("is_defect_test")
                    is_regression = t_res.get("is_regression_test")

                    if is_defect is True:
                        defect_total += 1
                        if passed:
                            defect_passed += 1
                    elif is_regression is True:
                        regression_total += 1
                        if passed:
                            regression_passed += 1
                    elif classifications:
                        # 2. Verified mapped classification
                        if t_name in classifications.get("defect", set()):
                            defect_total += 1
                            if passed:
                                defect_passed += 1
                        elif t_name in classifications.get("regression", set()):
                            regression_total += 1
                            if passed:
                                regression_passed += 1

                if defect_total > 0 and regression_total > 0:
                    defect_res = defect_passed / defect_total
                    reg_pres = regression_passed / regression_total
                    dbg_score = round(defect_res * reg_pres * 100)
                    scores["debugging"] = max(0, min(100, dbg_score))
                    evidence["debugging"] = "defect_and_regression_tests"
                elif defect_total > 0:
                    dbg_score = round((defect_passed / defect_total) * 100)
                    scores["debugging"] = max(0, min(100, dbg_score))
                    evidence["debugging"] = "defect_resolution_tests"
                else:
                    scores["debugging"] = None
                    evidence["debugging"] = "insufficient_data"
        else:
            scores["debugging"] = None
            evidence["debugging"] = "not_measured"

        # 3. Security (0.60 * Exploit Rejection + 0.40 * Authorized Behavior)
        if challenge_type == "SECURITY":
            if tests_total <= 0 or scores["problem_solving"] is None:
                scores["security"] = None
                evidence["security"] = "not_measured"
            elif not test_results:
                scores["security"] = scores["problem_solving"]
                evidence["security"] = "security_tests"
            else:
                slug = getattr(challenge, "slug", "")
                classifications = SECURITY_TEST_CLASSIFICATION.get(slug)

                exploit_passed = 0
                exploit_total = 0
                auth_passed = 0
                auth_total = 0

                for t_res in test_results:
                    t_name = t_res.get("name", "")
                    passed = bool(t_res.get("passed", False))

                    # 1. Explicit metadata check
                    is_negative = t_res.get("is_negative_test") or t_res.get("is_exploit_test")
                    is_auth = t_res.get("is_authorized_test")

                    if is_negative is True:
                        exploit_total += 1
                        if passed:
                            exploit_passed += 1
                    elif is_auth is True:
                        auth_total += 1
                        if passed:
                            auth_passed += 1
                    elif classifications:
                        # 2. Verified mapped classification
                        if t_name in classifications.get("exploit", set()):
                            exploit_total += 1
                            if passed:
                                exploit_passed += 1
                        elif t_name in classifications.get("authorized", set()):
                            auth_total += 1
                            if passed:
                                auth_passed += 1

                if exploit_total > 0 and auth_total > 0:
                    exploit_rej = exploit_passed / exploit_total
                    auth_beh = auth_passed / auth_total
                    sec_score = round((0.60 * exploit_rej + 0.40 * auth_beh) * 100)
                    scores["security"] = max(0, min(100, sec_score))
                    evidence["security"] = "exploit_and_authorization_tests"
                elif exploit_total > 0:
                    sec_score = round((exploit_passed / exploit_total) * 100)
                    scores["security"] = max(0, min(100, sec_score))
                    evidence["security"] = "exploit_rejection_tests"
                else:
                    scores["security"] = None
                    evidence["security"] = "insufficient_data"
        else:
            scores["security"] = None
            evidence["security"] = "not_measured"

        # 4. Calibrated Performance
        if (
            execution_time is not None
            and execution_time >= 0
            and tests_total > 0
        ):
            if tests_passed == 0:
                # Crashing execution, syntax error, or 0 passed tests receives 0 performance
                scores["performance"] = 0
                evidence["performance"] = "execution_metrics"
            else:
                t_optimal, t_naive = get_performance_thresholds(challenge, tests_total)

                # Guard against inverted or invalid threshold configurations
                if t_naive <= t_optimal:
                    t_naive = t_optimal + 1.0

                t_actual = float(execution_time)

                # Piecewise linear time score based on calibrated benchmarks
                if t_actual <= t_optimal:
                    time_score = 1.0
                elif t_actual >= t_naive:
                    time_score = 0.0
                else:
                    time_score = 1.0 - ((t_actual - t_optimal) / (t_naive - t_optimal))

                time_score = max(0.0, min(1.0, time_score))

                # Memory score calculation
                memory_limit = getattr(challenge, "memory_limit", None)
                if memory_limit and memory_limit > 0 and memory_used is not None and memory_used > 0:
                    m_limit = float(memory_limit)
                    m_used = float(memory_used)
                    # Optimal memory footprint accounts for Python runtime baseline (~25MB)
                    m_optimal = max(10.0, min(35.0, m_limit * 0.25))

                    if m_used <= m_optimal:
                        mem_score = 1.0
                    elif m_used >= m_limit:
                        mem_score = 0.0
                    else:
                        mem_score = 1.0 - ((m_used - m_optimal) / (m_limit - m_optimal))

                    mem_score = max(0.0, min(1.0, mem_score))
                    perf_value = round((0.75 * time_score + 0.25 * mem_score) * 100)
                else:
                    perf_value = round(time_score * 100)

                # Scale performance score by functional test pass ratio
                pass_ratio = tests_passed / tests_total
                perf_value = round(perf_value * pass_ratio)

                scores["performance"] = max(0, min(100, perf_value))
                evidence["performance"] = "execution_metrics"
        else:
            scores["performance"] = None
            evidence["performance"] = "not_measured"

        # 5. Code Quality (Deterministic AST & Ruff Static Analysis)
        if language and str(language).strip().lower() != "python":
            scores["code_quality"] = None
            evidence["code_quality"] = "not_measured"
        elif files is not None or code is not None:
            cq_res = self.analyze_code_quality(
                code=code,
                files=files,
                challenge_files=challenge_files,
                language=language,
            )
            scores["code_quality"] = cq_res.get("score")
            evidence["code_quality"] = cq_res.get("evidence", "not_measured")
        else:
            scores["code_quality"] = None
            evidence["code_quality"] = "not_measured"

        # 6. Testing Skill (Mutation Sensitivity & AST Assertion Inspection)
        if language and str(language).strip().lower() != "python":
            scores["testing"] = None
            evidence["testing"] = "not_measured"
        elif student_test_code or (files and any(is_test_file_path(p) for p in files)):
            testing_res = self.evaluate_testing_skill(
                challenge=challenge,
                student_test_code=student_test_code,
                files=files,
                challenge_files=challenge_files,
                language=language,
            )
            scores["testing"] = testing_res.get("score")
            evidence["testing"] = testing_res.get("evidence", "not_measured")
        else:
            scores["testing"] = None
            evidence["testing"] = "insufficient_data"

        return {
            "scores": scores,
            "evidence": evidence,
        }



