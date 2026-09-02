from django.core.management.base import BaseCommand
from django.db import transaction
from challenges.models import Challenge, ChallengeFile, TestCase


SEED_DATA = [
    {
        "title": "Fix the Broken Calculator",
        "slug": "fix-the-broken-calculator",
        "difficulty": Challenge.Difficulty.BEGINNER,
        "challenge_type": Challenge.ChallengeType.BUG_FIX,
        "programming_language": "Python",
        "points": 100,
        "entrypoint": "app/main.py",
        "time_limit": 5,
        "memory_limit": 128,
        "description": (
            "You are a backend software engineer maintaining the calculation service for DevForge.\n\n"
            "Users have reported that the calculation CLI produces unexpected results on compound expressions, "
            "and crashes with unhandled exceptions when evaluating certain inputs.\n\n"
            "Your task is to inspect `app/calculator.py` and `app/main.py`, understand how expressions are processed, "
            "and fix the implementation so all test suites pass.\n\n"
            "Input format:\n"
            "Space-separated arithmetic expressions provided via standard input (e.g. `10 + 5 * 2`).\n\n"
            "Output format:\n"
            "The evaluated numeric result, or `Error: Division by zero` if a division or modulo by zero is attempted."
        ),
        "starter_code": (
            "# See app/calculator.py and app/main.py for the full repository implementation.\n"
        ),
        "test_cases": [
            {
                "name": "Basic Arithmetic",
                "input_data": "15 + 25\n",
                "expected_output": "40",
                "points": 20,
                "is_hidden": False,
            },
            {
                "name": "Compound Expression",
                "input_data": "10 + 5 * 2\n",
                "expected_output": "20",
                "points": 20,
                "is_hidden": False,
            },
            {
                "name": "Mixed Operations with Division",
                "input_data": "100 - 20 / 4\n",
                "expected_output": "95",
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Division by Zero Handling",
                "input_data": "42 / 0\n",
                "expected_output": "Error: Division by zero",
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Chained Multi-Operator Expression",
                "input_data": "50 + 10 * 3 - 20 / 4 + 8 % 3\n",
                "expected_output": "77",
                "points": 20,
                "is_hidden": True,
            },
        ],
        "files": [
            {
                "path": "README.md",
                "is_readonly": True,
                "is_test": False,
                "content": (
                    "# Calculator Service\n\n"
                    "## Role\n"
                    "You are a backend software engineer responsible for maintaining DevForge's arithmetic evaluation engine.\n\n"
                    "## Observed Behavior\n"
                    "The calculation service parses space-separated arithmetic expressions and prints the results. "
                    "However, recent bug reports indicate that:\n"
                    "1. Multi-operator expressions yield incorrect values compared to standard arithmetic rules.\n"
                    "2. Inputs with zero divisors cause unhandled runtime exceptions.\n\n"
                    "## Expected Behavior\n"
                    "1. Support the arithmetic operators: `+`, `-`, `*`, `/`, and `%`.\n"
                    "2. Expressions must evaluate according to standard mathematical order of operations.\n"
                    "3. When encountering a division or modulo by zero, return the string `Error: Division by zero`.\n"
                    "4. Integer results should be formatted as integers (e.g. `20`), while fractional results should maintain standard float representation (e.g. `7.5`).\n\n"
                    "## Acceptance Criteria\n"
                    "- All single and multi-operator expressions evaluate to their correct arithmetic results.\n"
                    "- Zero divisor conditions return `Error: Division by zero` without crashing.\n"
                    "- The test suite in `tests/test_calculator.py` passes completely.\n\n"
                    "## Execution\n"
                    "- Entrypoint: `app/main.py`\n"
                    "- Input: Space-separated tokens provided via standard input.\n"
                ),
            },
            {
                "path": "requirements.txt",
                "is_readonly": True,
                "is_test": False,
                "content": "# Standard Python environment dependencies\n",
            },
            {
                "path": "app/__init__.py",
                "is_readonly": False,
                "is_test": False,
                "content": '"""Calculator application package."""\n',
            },
            {
                "path": "app/calculator.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "class Calculator:\n"
                    "    \"\"\"\n"
                    "    Evaluates space-separated arithmetic expressions.\n"
                    "    \"\"\"\n\n"
                    "    PRECEDENCE = {\n"
                    "        '+': 1,\n"
                    "        '-': 1,\n"
                    "        '*': 2,\n"
                    "        '/': 2,\n"
                    "        '%': 2,\n"
                    "    }\n\n"
                    "    def _apply_operator(self, op: str, b: float, a: float):\n"
                    "        if op == '+':\n"
                    "            return a + b\n"
                    "        if op == '-':\n"
                    "            return a - b\n"
                    "        if op == '*':\n"
                    "            return a * b\n"
                    "        if op == '/':\n"
                    "            return a / b\n"
                    "        if op == '%':\n"
                    "            return a % b\n"
                    "        raise ValueError(f\"Unknown operator: {op}\")\n\n"
                    "    def evaluate(self, expression: str):\n"
                    "        tokens = expression.strip().split()\n"
                    "        if not tokens:\n"
                    "            return 0\n\n"
                    "        values = []\n"
                    "        operators = []\n\n"
                    "        try:\n"
                    "            for token in tokens:\n"
                    "                if token in self.PRECEDENCE:\n"
                    "                    while operators and self.PRECEDENCE.get(operators[-1], 0) < self.PRECEDENCE[token]:\n"
                    "                        op = operators.pop()\n"
                    "                        val2 = values.pop()\n"
                    "                        val1 = values.pop()\n"
                    "                        values.append(self._apply_operator(op, val2, val1))\n"
                    "                    operators.append(token)\n"
                    "                else:\n"
                    "                    values.append(float(token))\n\n"
                    "            while operators:\n"
                    "                op = operators.pop()\n"
                    "                val2 = values.pop()\n"
                    "                val1 = values.pop()\n"
                    "                values.append(self._apply_operator(op, val2, val1))\n\n"
                    "            res = values[0] if values else 0\n"
                    "            if isinstance(res, (int, float)) and res == int(res):\n"
                    "                return int(res)\n"
                    "            return res\n"
                    "        except ZeroDivisionError:\n"
                    "            return \"Error: Division by zero\"\n"
                ),
            },
            {
                "path": "app/main.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "import sys\n"
                    "from app.calculator import Calculator\n\n"
                    "def main():\n"
                    "    calc = Calculator()\n"
                    "    for line in sys.stdin:\n"
                    "        line = line.strip()\n"
                    "        if not line:\n"
                    "            continue\n"
                    "        result = calc.evaluate(line)\n"
                    "        print(result)\n\n"
                    "if __name__ == '__main__':\n"
                    "    main()\n"
                ),
            },
            {
                "path": "tests/__init__.py",
                "is_readonly": True,
                "is_test": True,
                "content": '"""Test suite package."""\n',
            },
            {
                "path": "tests/test_calculator.py",
                "is_readonly": True,
                "is_test": True,
                "content": (
                    "import unittest\n"
                    "from app.calculator import Calculator\n\n"
                    "class TestCalculator(unittest.TestCase):\n"
                    "    def setUp(self):\n"
                    "        self.calc = Calculator()\n\n"
                    "    def test_basic_arithmetic(self):\n"
                    "        self.assertEqual(self.calc.evaluate('15 + 25'), 40)\n\n"
                    "    def test_compound_expression(self):\n"
                    "        self.assertEqual(self.calc.evaluate('10 + 5 * 2'), 20)\n\n"
                    "if __name__ == '__main__':\n"
                    "    unittest.main()\n"
                ),
            },
        ],
    },

    {
        "title": "The Missing API Data",
        "slug": "the-missing-api-data",
        "difficulty": Challenge.Difficulty.INTERMEDIATE,
        "challenge_type": Challenge.ChallengeType.API,
        "programming_language": "Python",
        "points": 100,
        "entrypoint": "app/main.py",
        "time_limit": 5,
        "memory_limit": 128,
        "description": (
            "You are a backend software engineer maintaining a product catalog REST-style API service.\n\n"
            "Frontend client applications report that API responses for product listings return incomplete JSON objects, "
            "missing key data attributes required for display.\n\n"
            "Your task is to inspect the service architecture across `app/models.py`, `app/service.py`, `app/responses.py`, "
            "and `app/main.py`, identify why fields are being omitted or misformatted, and fix the service so that all endpoints "
            "strictly adhere to the API contract."
        ),
        "starter_code": (
            "# See app/main.py, app/service.py, app/models.py, and app/responses.py for the full service implementation.\n"
        ),
        "test_cases": [
            {
                "name": "Returns single product details",
                "input_data": "GET /api/products/1\n",
                "expected_output": '{"id": 1, "name": "Wireless Mechanical Keyboard", "category": "electronics", "price": 99.99, "in_stock": true}',
                "points": 20,
                "is_hidden": False,
            },
            {
                "name": "Handles resource not found",
                "input_data": "GET /api/products/999\n",
                "expected_output": '{"error": "Product not found"}',
                "points": 20,
                "is_hidden": False,
            },
            {
                "name": "Returns complete product collection",
                "input_data": "GET /api/products\n",
                "expected_output": '[{"id": 1, "name": "Wireless Mechanical Keyboard", "category": "electronics", "price": 99.99, "in_stock": true}, {"id": 2, "name": "Noise-Cancelling Headphones", "category": "electronics", "price": 149.5, "in_stock": true}, {"id": 3, "name": "Ergonomic Desk Chair", "category": "furniture", "price": 299.0, "in_stock": false}, {"id": 4, "name": "Stainless Steel Water Bottle", "category": "accessories", "price": 24.99, "in_stock": true}]',
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Filtered category collection query",
                "input_data": "GET /api/products?category=electronics\n",
                "expected_output": '[{"id": 1, "name": "Wireless Mechanical Keyboard", "category": "electronics", "price": 99.99, "in_stock": true}, {"id": 2, "name": "Noise-Cancelling Headphones", "category": "electronics", "price": 149.5, "in_stock": true}]',
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Preserves fields across collection items",
                "input_data": "GET /api/products/3\n",
                "expected_output": '{"id": 3, "name": "Ergonomic Desk Chair", "category": "furniture", "price": 299.0, "in_stock": false}',
                "points": 20,
                "is_hidden": True,
            },
        ],
        "files": [
            {
                "path": "README.md",
                "is_readonly": True,
                "is_test": False,
                "content": (
                    "# Product Catalog API Service\n\n"
                    "## Role\n"
                    "You are a backend software engineer maintaining the product catalog REST-style service used by the DevForge store frontend.\n\n"
                    "## Service Overview & Execution Model\n"
                    "The service is a Python application that reads REST-style HTTP request lines from standard input (e.g. `GET /api/products`, `GET /api/products/1`, `GET /api/products?category=electronics`) and outputs standard JSON responses to stdout.\n\n"
                    "## Observed Symptoms\n"
                    "Client applications report that product listing requests return incomplete data objects. While individual item lookups function as expected, list responses omit key commercial fields required by the user interface.\n\n"
                    "## Expected Behavior & API Contract\n"
                    "All endpoints must return valid JSON formatted according to the product contract:\n\n"
                    "1. `GET /api/products`\n"
                    "   Returns a JSON list of all products, where each product includes:\n"
                    "   - `id` (integer)\n"
                    "   - `name` (string)\n"
                    "   - `category` (string)\n"
                    "   - `price` (float / number)\n"
                    "   - `in_stock` (boolean)\n\n"
                    "2. `GET /api/products/<id>`\n"
                    "   Returns a single product object with all 5 attributes. If the product ID does not exist, return `{\"error\": \"Product not found\"}`.\n\n"
                    "3. `GET /api/products?category=<category_name>`\n"
                    "   Returns a filtered JSON list containing only products matching the requested category with all 5 attributes.\n\n"
                    "## Acceptance Criteria\n"
                    "- Both single product and collection responses contain the complete set of required fields (`id`, `name`, `category`, `price`, and `in_stock`).\n"
                    "- Category filtering functions accurately.\n"
                    "- Non-existent product IDs return `{\"error\": \"Product not found\"}`.\n"
                    "- All unit tests in `tests/test_api.py` pass.\n\n"
                    "## Execution\n"
                    "- Entrypoint: `app/main.py`\n"
                    "- Input: Request lines provided via standard input (e.g. `GET /api/products`).\n"
                ),
            },
            {
                "path": "requirements.txt",
                "is_readonly": True,
                "is_test": False,
                "content": "# Standard Python environment dependencies\n",
            },
            {
                "path": "app/__init__.py",
                "is_readonly": False,
                "is_test": False,
                "content": '"""Product Catalog API package."""\n',
            },
            {
                "path": "app/models.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "class Product:\n"
                    "    def __init__(self, id: int, name: str, category: str, price: float, in_stock: bool):\n"
                    "        self.id = id\n"
                    "        self.name = name\n"
                    "        self.category = category\n"
                    "        self.price = price\n"
                    "        self.in_stock = in_stock\n\n"
                    "    def to_dict(self):\n"
                    "        return {\n"
                    "            \"id\": self.id,\n"
                    "            \"name\": self.name,\n"
                    "            \"category\": self.category,\n"
                    "            \"price\": self.price,\n"
                    "            \"in_stock\": self.in_stock,\n"
                    "        }\n"
                ),
            },
            {
                "path": "app/responses.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "import json\n\n"
                    "class JsonResponse:\n"
                    "    @staticmethod\n"
                    "    def success(data):\n"
                    "        return json.dumps(data)\n\n"
                    "    @staticmethod\n"
                    "    def not_found(message=\"Product not found\"):\n"
                    "        return json.dumps({\"error\": message})\n"
                ),
            },
            {
                "path": "app/service.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "from app.models import Product\n"
                    "from app.responses import JsonResponse\n\n"
                    "class ProductService:\n"
                    "    def __init__(self):\n"
                    "        self.products = [\n"
                    "            Product(1, \"Wireless Mechanical Keyboard\", \"electronics\", 99.99, True),\n"
                    "            Product(2, \"Noise-Cancelling Headphones\", \"electronics\", 149.50, True),\n"
                    "            Product(3, \"Ergonomic Desk Chair\", \"furniture\", 299.00, False),\n"
                    "            Product(4, \"Stainless Steel Water Bottle\", \"accessories\", 24.99, True),\n"
                    "        ]\n\n"
                    "    def list_products(self, category=None):\n"
                    "        items = self.products\n"
                    "        if category:\n"
                    "            items = [p for p in items if p.category.lower() == category.lower()]\n\n"
                    "        serialized = []\n"
                    "        for p in items:\n"
                    "            serialized.append({\n"
                    "                \"id\": p.id,\n"
                    "                \"name\": p.name,\n"
                    "                \"category\": p.category,\n"
                    "                \"in_stock\": p.in_stock,\n"
                    "            })\n"
                    "        return JsonResponse.success(serialized)\n\n"
                    "    def get_product(self, product_id: int):\n"
                    "        product = next((p for p in self.products if p.id == product_id), None)\n"
                    "        if not product:\n"
                    "            return JsonResponse.not_found()\n"
                    "        return JsonResponse.success(product.to_dict())\n"
                ),
            },
            {
                "path": "app/main.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "import sys\n"
                    "import urllib.parse\n"
                    "from app.service import ProductService\n\n"
                    "def handle_request(request_line: str, service: ProductService) -> str:\n"
                    "    parts = request_line.strip().split()\n"
                    "    if not parts:\n"
                    "        return \"\"\n\n"
                    "    method = parts[0]\n"
                    "    path = parts[1] if len(parts) > 1 else \"/\"\n\n"
                    "    if method != \"GET\":\n"
                    "        return \"{\\\"error\\\": \\\"Method not allowed\\\"}\"\n\n"
                    "    parsed = urllib.parse.urlparse(path)\n"
                    "    path_only = parsed.path.rstrip(\"/\")\n"
                    "    query_params = urllib.parse.parse_qs(parsed.query)\n\n"
                    "    if path_only == \"/api/products\":\n"
                    "        category = query_params.get(\"category\", [None])[0]\n"
                    "        return service.list_products(category=category)\n"
                    "    elif path_only.startswith(\"/api/products/\"):\n"
                    "        try:\n"
                    "            product_id = int(path_only.split(\"/\")[-1])\n"
                    "            return service.get_product(product_id)\n"
                    "        except ValueError:\n"
                    "            return \"{\\\"error\\\": \\\"Invalid product ID\\\"}\"\n\n"
                    "    return \"{\\\"error\\\": \\\"Not found\\\"}\"\n\n"
                    "def main():\n"
                    "    service = ProductService()\n"
                    "    for line in sys.stdin:\n"
                    "        line = line.strip()\n"
                    "        if not line:\n"
                    "            continue\n"
                    "        response = handle_request(line, service)\n"
                    "        print(response)\n\n"
                    "if __name__ == '__main__':\n"
                    "    main()\n"
                ),
            },
            {
                "path": "tests/__init__.py",
                "is_readonly": True,
                "is_test": True,
                "content": '"""Test suite package."""\n',
            },
            {
                "path": "tests/test_api.py",
                "is_readonly": True,
                "is_test": True,
                "content": (
                    "import json\n"
                    "import unittest\n"
                    "from app.service import ProductService\n\n"
                    "class TestProductApi(unittest.TestCase):\n"
                    "    def setUp(self):\n"
                    "        self.service = ProductService()\n\n"
                    "    def test_single_product_fields(self):\n"
                    "        res_json = self.service.get_product(1)\n"
                    "        data = json.loads(res_json)\n"
                    "        self.assertEqual(data[\"id\"], 1)\n"
                    "        self.assertIn(\"price\", data)\n"
                    "        self.assertEqual(data[\"price\"], 99.99)\n"
                    "        self.assertEqual(data[\"in_stock\"], True)\n\n"
                    "    def test_product_not_found(self):\n"
                    "        res_json = self.service.get_product(999)\n"
                    "        data = json.loads(res_json)\n"
                    "        self.assertIn(\"error\", data)\n\n"
                    "if __name__ == '__main__':\n"
                    "    unittest.main()\n"
                ),
            },
        ],
    },

    {
        "title": "The Exposed Admin Endpoint",
        "slug": "the-exposed-admin-endpoint",
        "difficulty": Challenge.Difficulty.INTERMEDIATE,
        "challenge_type": Challenge.ChallengeType.SECURITY,
        "programming_language": "Python",
        "points": 100,
        "entrypoint": "app/main.py",
        "time_limit": 5,
        "memory_limit": 128,
        "description": (
            "You are a backend software engineer maintaining an internal administrative portal service.\n\n"
            "A recent security assessment reported an access-control vulnerability: non-administrator accounts are able "
            "to query and receive sensitive administrative operational reports.\n\n"
            "Your task is to inspect the service architecture across `app/auth.py`, `app/models.py`, `app/service.py`, "
            "`app/responses.py`, and `app/main.py`, understand how authentication and authorization decisions are enforced, "
            "and fix the access-control logic so that only verified administrators can access privileged resources."
        ),
        "starter_code": (
            "# See app/main.py, app/auth.py, app/service.py, app/models.py, and app/responses.py for the full service implementation.\n"
        ),
        "test_cases": [
            {
                "name": "Administrator access",
                "input_data": "GET /api/admin/reports Authorization: Bearer token_admin_secure_88\n",
                "expected_output": '{"report_id": "REP-8492", "system_health": "100%", "active_nodes": 12, "sensitive_audit_logs": 48}',
                "points": 20,
                "is_hidden": False,
            },
            {
                "name": "Public endpoint behavior",
                "input_data": "GET /api/public/status\n",
                "expected_output": '{"status": "operational", "version": "1.4.0"}',
                "points": 20,
                "is_hidden": False,
            },
            {
                "name": "Restricted account access",
                "input_data": "GET /api/admin/reports Authorization: Bearer token_member_basic_42\n",
                "expected_output": '{"error": "Forbidden: Administrator access required"}',
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Missing authentication access",
                "input_data": "GET /api/admin/reports\n",
                "expected_output": '{"error": "Unauthorized: Authentication token required"}',
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Secondary non-admin role rejection",
                "input_data": "GET /api/admin/reports Authorization: Bearer token_member_guest_15\n",
                "expected_output": '{"error": "Forbidden: Administrator access required"}',
                "points": 20,
                "is_hidden": True,
            },
        ],
        "files": [
            {
                "path": "README.md",
                "is_readonly": True,
                "is_test": False,
                "content": (
                    "# Internal Administration Service\n\n"
                    "## Role\n"
                    "You are a backend software engineer maintaining the internal administration API service for DevForge.\n\n"
                    "## Service Overview & Execution Model\n"
                    "The service is a Python application that reads REST-style request lines from standard input and prints standard JSON responses to stdout.\n"
                    "Requests may provide an authorization header in the format:\n"
                    "`<METHOD> <PATH> Authorization: Bearer <TOKEN>` or `<METHOD> <PATH>`.\n\n"
                    "## Observed Security Symptoms\n"
                    "A security audit reported that regular authenticated users who lack administrative privileges are currently able to retrieve sensitive operational reports from restricted endpoints.\n\n"
                    "## Access-Control Requirements & API Contract\n"
                    "1. `GET /api/public/status`\n"
                    "   Public health endpoint. Requires no authentication. Returns `{\"status\": \"operational\", \"version\": \"1.4.0\"}`.\n\n"
                    "2. `GET /api/admin/reports`\n"
                    "   Privileged administrator endpoint.\n"
                    "   - If no valid authentication token is provided, return: `{\"error\": \"Unauthorized: Authentication token required\"}`.\n"
                    "   - If the authenticated user is not an administrator, return: `{\"error\": \"Forbidden: Administrator access required\"}`.\n"
                    "   - If the user is an authorized administrator, return the report JSON object containing `report_id`, `system_health`, `active_nodes`, and `sensitive_audit_logs`.\n\n"
                    "## Acceptance Criteria\n"
                    "- Legitimate administrators with valid tokens receive the report data.\n"
                    "- Non-administrator members and guests are blocked with the forbidden error.\n"
                    "- Unauthenticated requests to protected endpoints are blocked with the unauthorized error.\n"
                    "- Public endpoints remain accessible.\n"
                    "- All unit tests in `tests/test_access.py` pass.\n\n"
                    "## Execution\n"
                    "- Entrypoint: `app/main.py`\n"
                    "- Input: Request lines provided via standard input.\n"
                ),
            },
            {
                "path": "requirements.txt",
                "is_readonly": True,
                "is_test": False,
                "content": "# Standard Python environment dependencies\n",
            },
            {
                "path": "app/__init__.py",
                "is_readonly": False,
                "is_test": False,
                "content": '"""Admin Service package."""\n',
            },
            {
                "path": "app/models.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "class User:\n"
                    "    def __init__(self, user_id: int, username: str, role: str):\n"
                    "        self.id = user_id\n"
                    "        self.username = username\n"
                    "        self.role = role\n"
                    "        self.is_admin = (role == \"admin\")\n"
                ),
            },
            {
                "path": "app/auth.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "from app.models import User\n\n"
                    "TOKEN_REGISTRY = {\n"
                    "    \"token_admin_secure_88\": User(1, \"alex_admin\", \"admin\"),\n"
                    "    \"token_member_basic_42\": User(2, \"sam_user\", \"member\"),\n"
                    "    \"token_member_guest_15\": User(3, \"jordan_guest\", \"guest\"),\n"
                    "}\n\n"
                    "class AuthService:\n"
                    "    def authenticate(self, token: str):\n"
                    "        if not token:\n"
                    "            return None\n"
                    "        return TOKEN_REGISTRY.get(token)\n\n"
                    "    def is_authorized_admin(self, user: User) -> bool:\n"
                    "        return bool(user)\n"
                ),
            },
            {
                "path": "app/responses.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "import json\n\n"
                    "class JsonResponse:\n"
                    "    @staticmethod\n"
                    "    def success(data):\n"
                    "        return json.dumps(data)\n\n"
                    "    @staticmethod\n"
                    "    def unauthorized(message=\"Unauthorized: Authentication token required\"):\n"
                    "        return json.dumps({\"error\": message})\n\n"
                    "    @staticmethod\n"
                    "    def forbidden(message=\"Forbidden: Administrator access required\"):\n"
                    "        return json.dumps({\"error\": message})\n\n"
                    "    @staticmethod\n"
                    "    def not_found(message=\"Endpoint not found\"):\n"
                    "        return json.dumps({\"error\": message})\n"
                ),
            },
            {
                "path": "app/service.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "from app.auth import AuthService\n"
                    "from app.responses import JsonResponse\n\n"
                    "class AdminService:\n"
                    "    def __init__(self, auth_service=None):\n"
                    "        self.auth_service = auth_service or AuthService()\n\n"
                    "    def get_public_status(self):\n"
                    "        return JsonResponse.success({\n"
                    "            \"status\": \"operational\",\n"
                    "            \"version\": \"1.4.0\",\n"
                    "        })\n\n"
                    "    def get_admin_reports(self, token: str):\n"
                    "        user = self.auth_service.authenticate(token)\n"
                    "        if not user:\n"
                    "            return JsonResponse.unauthorized()\n\n"
                    "        if not self.auth_service.is_authorized_admin(user):\n"
                    "            return JsonResponse.forbidden()\n\n"
                    "        return JsonResponse.success({\n"
                    "            \"report_id\": \"REP-8492\",\n"
                    "            \"system_health\": \"100%\",\n"
                    "            \"active_nodes\": 12,\n"
                    "            \"sensitive_audit_logs\": 48,\n"
                    "        })\n"
                ),
            },
            {
                "path": "app/main.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "import sys\n"
                    "from app.service import AdminService\n\n"
                    "def parse_request_line(line: str):\n"
                    "    parts = line.strip().split()\n"
                    "    if not parts:\n"
                    "        return None, None, None\n\n"
                    "    method = parts[0]\n"
                    "    path = parts[1] if len(parts) > 1 else \"/\"\n"
                    "    token = None\n\n"
                    "    for i, p in enumerate(parts):\n"
                    "        if p.lower() in (\"bearer\", \"token:\", \"bearer:\") and i + 1 < len(parts):\n"
                    "            token = parts[i + 1]\n"
                    "            break\n\n"
                    "    return method, path, token\n\n"
                    "def handle_request(request_line: str, service: AdminService) -> str:\n"
                    "    method, path, token = parse_request_line(request_line)\n"
                    "    if not method:\n"
                    "        return \"\"\n\n"
                    "    if method != \"GET\":\n"
                    "        return \"{\\\"error\\\": \\\"Method not allowed\\\"}\"\n\n"
                    "    if path == \"/api/public/status\":\n"
                    "        return service.get_public_status()\n"
                    "    elif path == \"/api/admin/reports\":\n"
                    "        return service.get_admin_reports(token)\n\n"
                    "    return \"{\\\"error\\\": \\\"Endpoint not found\\\"}\"\n\n"
                    "def main():\n"
                    "    service = AdminService()\n"
                    "    for line in sys.stdin:\n"
                    "        line = line.strip()\n"
                    "        if not line:\n"
                    "            continue\n"
                    "        response = handle_request(line, service)\n"
                    "        print(response)\n\n"
                    "if __name__ == '__main__':\n"
                    "    main()\n"
                ),
            },
            {
                "path": "tests/__init__.py",
                "is_readonly": True,
                "is_test": True,
                "content": '"""Test suite package."""\n',
            },
            {
                "path": "tests/test_access.py",
                "is_readonly": True,
                "is_test": True,
                "content": (
                    "import json\n"
                    "import unittest\n"
                    "from app.service import AdminService\n\n"
                    "class TestAccessControl(unittest.TestCase):\n"
                    "    def setUp(self):\n"
                    "        self.service = AdminService()\n\n"
                    "    def test_public_status_access(self):\n"
                    "        res_json = self.service.get_public_status()\n"
                    "        data = json.loads(res_json)\n"
                    "        self.assertEqual(data[\"status\"], \"operational\")\n\n"
                    "    def test_admin_access_with_valid_token(self):\n"
                    "        res_json = self.service.get_admin_reports(\"token_admin_secure_88\")\n"
                    "        data = json.loads(res_json)\n"
                    "        self.assertIn(\"report_id\", data)\n"
                    "        self.assertEqual(data[\"report_id\"], \"REP-8492\")\n\n"
                    "if __name__ == '__main__':\n"
                    "    unittest.main()\n"
                ),
            },
        ],
    },

    {
        "title": "The Slow Report Generator",
        "slug": "the-slow-report-generator",
        "difficulty": Challenge.Difficulty.INTERMEDIATE,
        "challenge_type": Challenge.ChallengeType.PERFORMANCE,
        "programming_language": "Python",
        "points": 100,
        "entrypoint": "app/main.py",
        "time_limit": 5,
        "memory_limit": 128,
        "description": (
            "You are a backend software engineer maintaining the transaction reporting and analytics pipeline for DevForge.\n\n"
            "The service generates unified transaction reports by joining transaction records with user account profiles. "
            "While the reporting engine works correctly for small datasets, it experiences severe performance degradation "
            "and timeouts when processing larger transaction batches.\n\n"
            "Your task is to inspect `app/generator.py`, `app/models.py`, and `app/main.py`, identify the performance bottleneck, "
            "and optimize the report generation process so that all workloads complete within the system execution limit while "
            "strictly preserving report accuracy."
        ),
        "starter_code": (
            "# See app/main.py, app/generator.py, and app/models.py for the full service implementation.\n"
        ),
        "test_cases": [
            {
                "name": "Generates transaction report",
                "input_data": '{"users": [{"id": 1, "name": "Alice Smith"}, {"id": 2, "name": "Bob Jones"}, {"id": 3, "name": "Carol White"}], "transactions": [{"id": 101, "user_id": 1, "amount": 120.5}, {"id": 102, "user_id": 2, "amount": 45.0}, {"id": 103, "user_id": 1, "amount": 89.99}, {"id": 104, "user_id": 3, "amount": 210.0}]}\n',
                "expected_output": '{"total_transactions": 4, "total_amount": 465.49, "unmatched_transactions": 0, "records": [{"transaction_id": 101, "user_id": 1, "user_name": "Alice Smith", "amount": 120.5}, {"transaction_id": 102, "user_id": 2, "user_name": "Bob Jones", "amount": 45.0}, {"transaction_id": 103, "user_id": 1, "user_name": "Alice Smith", "amount": 89.99}, {"transaction_id": 104, "user_id": 3, "user_name": "Carol White", "amount": 210.0}]}',
                "points": 20,
                "is_hidden": False,
            },
            {
                "name": "Handles unmatched records",
                "input_data": '{"users": [{"id": 10, "name": "David Miller"}, {"id": 20, "name": "Eva Green"}], "transactions": [{"id": 201, "user_id": 10, "amount": 15.0}, {"id": 202, "user_id": 99, "amount": 50.0}, {"id": 203, "user_id": 20, "amount": 35.75}]}\n',
                "expected_output": '{"total_transactions": 3, "total_amount": 100.75, "unmatched_transactions": 1, "records": [{"transaction_id": 201, "user_id": 10, "user_name": "David Miller", "amount": 15.0}, {"transaction_id": 202, "user_id": 99, "user_name": "Unknown User", "amount": 50.0}, {"transaction_id": 203, "user_id": 20, "user_name": "Eva Green", "amount": 35.75}]}',
                "points": 20,
                "is_hidden": False,
            },
            {
                "name": "Maintains aggregation integrity across medium datasets",
                "input_data": '{"users": [{"id": 1, "name": "Client_1"}, {"id": 2, "name": "Client_2"}, {"id": 3, "name": "Client_3"}, {"id": 4, "name": "Client_4"}, {"id": 5, "name": "Client_5"}, {"id": 6, "name": "Client_6"}, {"id": 7, "name": "Client_7"}, {"id": 8, "name": "Client_8"}, {"id": 9, "name": "Client_9"}, {"id": 10, "name": "Client_10"}, {"id": 11, "name": "Client_11"}, {"id": 12, "name": "Client_12"}, {"id": 13, "name": "Client_13"}, {"id": 14, "name": "Client_14"}, {"id": 15, "name": "Client_15"}, {"id": 16, "name": "Client_16"}, {"id": 17, "name": "Client_17"}, {"id": 18, "name": "Client_18"}, {"id": 19, "name": "Client_19"}, {"id": 20, "name": "Client_20"}, {"id": 21, "name": "Client_21"}, {"id": 22, "name": "Client_22"}, {"id": 23, "name": "Client_23"}, {"id": 24, "name": "Client_24"}, {"id": 25, "name": "Client_25"}, {"id": 26, "name": "Client_26"}, {"id": 27, "name": "Client_27"}, {"id": 28, "name": "Client_28"}, {"id": 29, "name": "Client_29"}, {"id": 30, "name": "Client_30"}], "transactions": [{"id": 2001, "user_id": 4, "amount": 16.75}, {"id": 2002, "user_id": 7, "amount": 18.5}, {"id": 2003, "user_id": 10, "amount": 20.25}, {"id": 2004, "user_id": 13, "amount": 22.0}, {"id": 2005, "user_id": 16, "amount": 23.75}, {"id": 2006, "user_id": 19, "amount": 25.5}, {"id": 2007, "user_id": 22, "amount": 27.25}, {"id": 2008, "user_id": 25, "amount": 29.0}, {"id": 2009, "user_id": 28, "amount": 30.75}, {"id": 2010, "user_id": 31, "amount": 32.5}, {"id": 2011, "user_id": 34, "amount": 34.25}, {"id": 2012, "user_id": 2, "amount": 36.0}, {"id": 2013, "user_id": 5, "amount": 37.75}, {"id": 2014, "user_id": 8, "amount": 39.5}, {"id": 2015, "user_id": 11, "amount": 41.25}, {"id": 2016, "user_id": 14, "amount": 43.0}, {"id": 2017, "user_id": 17, "amount": 44.75}, {"id": 2018, "user_id": 20, "amount": 46.5}, {"id": 2019, "user_id": 23, "amount": 48.25}, {"id": 2020, "user_id": 26, "amount": 50.0}, {"id": 2021, "user_id": 29, "amount": 51.75}, {"id": 2022, "user_id": 32, "amount": 53.5}, {"id": 2023, "user_id": 35, "amount": 55.25}, {"id": 2024, "user_id": 3, "amount": 57.0}, {"id": 2025, "user_id": 6, "amount": 58.75}, {"id": 2026, "user_id": 9, "amount": 60.5}, {"id": 2027, "user_id": 12, "amount": 62.25}, {"id": 2028, "user_id": 15, "amount": 64.0}, {"id": 2029, "user_id": 18, "amount": 65.75}, {"id": 2030, "user_id": 21, "amount": 67.5}, {"id": 2031, "user_id": 24, "amount": 69.25}, {"id": 2032, "user_id": 27, "amount": 71.0}, {"id": 2033, "user_id": 30, "amount": 72.75}, {"id": 2034, "user_id": 33, "amount": 74.5}, {"id": 2035, "user_id": 1, "amount": 76.25}, {"id": 2036, "user_id": 4, "amount": 78.0}, {"id": 2037, "user_id": 7, "amount": 79.75}, {"id": 2038, "user_id": 10, "amount": 81.5}, {"id": 2039, "user_id": 13, "amount": 83.25}, {"id": 2040, "user_id": 16, "amount": 85.0}, {"id": 2041, "user_id": 19, "amount": 86.75}, {"id": 2042, "user_id": 22, "amount": 88.5}, {"id": 2043, "user_id": 25, "amount": 90.25}, {"id": 2044, "user_id": 28, "amount": 92.0}, {"id": 2045, "user_id": 31, "amount": 93.75}, {"id": 2046, "user_id": 34, "amount": 95.5}, {"id": 2047, "user_id": 2, "amount": 97.25}, {"id": 2048, "user_id": 5, "amount": 99.0}, {"id": 2049, "user_id": 8, "amount": 100.75}, {"id": 2050, "user_id": 11, "amount": 102.5}, {"id": 2051, "user_id": 14, "amount": 104.25}, {"id": 2052, "user_id": 17, "amount": 106.0}, {"id": 2053, "user_id": 20, "amount": 107.75}, {"id": 2054, "user_id": 23, "amount": 109.5}, {"id": 2055, "user_id": 26, "amount": 111.25}, {"id": 2056, "user_id": 29, "amount": 113.0}, {"id": 2057, "user_id": 32, "amount": 114.75}, {"id": 2058, "user_id": 35, "amount": 116.5}, {"id": 2059, "user_id": 3, "amount": 118.25}, {"id": 2060, "user_id": 6, "amount": 120.0}, {"id": 2061, "user_id": 9, "amount": 121.75}, {"id": 2062, "user_id": 12, "amount": 123.5}, {"id": 2063, "user_id": 15, "amount": 125.25}, {"id": 2064, "user_id": 18, "amount": 127.0}, {"id": 2065, "user_id": 21, "amount": 128.75}, {"id": 2066, "user_id": 24, "amount": 130.5}, {"id": 2067, "user_id": 27, "amount": 132.25}, {"id": 2068, "user_id": 30, "amount": 134.0}, {"id": 2069, "user_id": 33, "amount": 135.75}, {"id": 2070, "user_id": 1, "amount": 137.5}, {"id": 2071, "user_id": 4, "amount": 139.25}, {"id": 2072, "user_id": 7, "amount": 141.0}, {"id": 2073, "user_id": 10, "amount": 142.75}, {"id": 2074, "user_id": 13, "amount": 144.5}, {"id": 2075, "user_id": 16, "amount": 146.25}, {"id": 2076, "user_id": 19, "amount": 148.0}, {"id": 2077, "user_id": 22, "amount": 149.75}, {"id": 2078, "user_id": 25, "amount": 151.5}, {"id": 2079, "user_id": 28, "amount": 153.25}, {"id": 2080, "user_id": 31, "amount": 155.0}]}\n',
                "expected_output": '{"total_transactions": 80, "total_amount": 6870.0, "unmatched_transactions": 11, "records": [{"transaction_id": 2001, "user_id": 4, "user_name": "Client_4", "amount": 16.75}, {"transaction_id": 2002, "user_id": 7, "user_name": "Client_7", "amount": 18.5}, {"transaction_id": 2003, "user_id": 10, "user_name": "Client_10", "amount": 20.25}, {"transaction_id": 2004, "user_id": 13, "user_name": "Client_13", "amount": 22.0}, {"transaction_id": 2005, "user_id": 16, "user_name": "Client_16", "amount": 23.75}, {"transaction_id": 2006, "user_id": 19, "user_name": "Client_19", "amount": 25.5}, {"transaction_id": 2007, "user_id": 22, "user_name": "Client_22", "amount": 27.25}, {"transaction_id": 2008, "user_id": 25, "user_name": "Client_25", "amount": 29.0}, {"transaction_id": 2009, "user_id": 28, "user_name": "Client_28", "amount": 30.75}, {"transaction_id": 2010, "user_id": 31, "user_name": "Unknown User", "amount": 32.5}, {"transaction_id": 2011, "user_id": 34, "user_name": "Unknown User", "amount": 34.25}, {"transaction_id": 2012, "user_id": 2, "user_name": "Client_2", "amount": 36.0}, {"transaction_id": 2013, "user_id": 5, "user_name": "Client_5", "amount": 37.75}, {"transaction_id": 2014, "user_id": 8, "user_name": "Client_8", "amount": 39.5}, {"transaction_id": 2015, "user_id": 11, "user_name": "Client_11", "amount": 41.25}, {"transaction_id": 2016, "user_id": 14, "user_name": "Client_14", "amount": 43.0}, {"transaction_id": 2017, "user_id": 17, "user_name": "Client_17", "amount": 44.75}, {"transaction_id": 2018, "user_id": 20, "user_name": "Client_20", "amount": 46.5}, {"transaction_id": 2019, "user_id": 23, "user_name": "Client_23", "amount": 48.25}, {"transaction_id": 2020, "user_id": 26, "user_name": "Client_26", "amount": 50.0}, {"transaction_id": 2021, "user_id": 29, "user_name": "Client_29", "amount": 51.75}, {"transaction_id": 2022, "user_id": 32, "user_name": "Unknown User", "amount": 53.5}, {"transaction_id": 2023, "user_id": 35, "user_name": "Unknown User", "amount": 55.25}, {"transaction_id": 2024, "user_id": 3, "user_name": "Client_3", "amount": 57.0}, {"transaction_id": 2025, "user_id": 6, "user_name": "Client_6", "amount": 58.75}, {"transaction_id": 2026, "user_id": 9, "user_name": "Client_9", "amount": 60.5}, {"transaction_id": 2027, "user_id": 12, "user_name": "Client_12", "amount": 62.25}, {"transaction_id": 2028, "user_id": 15, "user_name": "Client_15", "amount": 64.0}, {"transaction_id": 2029, "user_id": 18, "user_name": "Client_18", "amount": 65.75}, {"transaction_id": 2030, "user_id": 21, "user_name": "Client_21", "amount": 67.5}, {"transaction_id": 2031, "user_id": 24, "user_name": "Client_24", "amount": 69.25}, {"transaction_id": 2032, "user_id": 27, "user_name": "Client_27", "amount": 71.0}, {"transaction_id": 2033, "user_id": 30, "user_name": "Client_30", "amount": 72.75}, {"transaction_id": 2034, "user_id": 33, "user_name": "Unknown User", "amount": 74.5}, {"transaction_id": 2035, "user_id": 1, "user_name": "Client_1", "amount": 76.25}, {"transaction_id": 2036, "user_id": 4, "user_name": "Client_4", "amount": 78.0}, {"transaction_id": 2037, "user_id": 7, "user_name": "Client_7", "amount": 79.75}, {"transaction_id": 2038, "user_id": 10, "user_name": "Client_10", "amount": 81.5}, {"transaction_id": 2039, "user_id": 13, "user_name": "Client_13", "amount": 83.25}, {"transaction_id": 2040, "user_id": 16, "user_name": "Client_16", "amount": 85.0}, {"transaction_id": 2041, "user_id": 19, "user_name": "Client_19", "amount": 86.75}, {"transaction_id": 2042, "user_id": 22, "user_name": "Client_22", "amount": 88.5}, {"transaction_id": 2043, "user_id": 25, "user_name": "Client_25", "amount": 90.25}, {"transaction_id": 2044, "user_id": 28, "user_name": "Client_28", "amount": 92.0}, {"transaction_id": 2045, "user_id": 31, "user_name": "Unknown User", "amount": 93.75}, {"transaction_id": 2046, "user_id": 34, "user_name": "Unknown User", "amount": 95.5}, {"transaction_id": 2047, "user_id": 2, "user_name": "Client_2", "amount": 97.25}, {"transaction_id": 2048, "user_id": 5, "user_name": "Client_5", "amount": 99.0}, {"transaction_id": 2049, "user_id": 8, "user_name": "Client_8", "amount": 100.75}, {"transaction_id": 2050, "user_id": 11, "user_name": "Client_11", "amount": 102.5}, {"transaction_id": 2051, "user_id": 14, "user_name": "Client_14", "amount": 104.25}, {"transaction_id": 2052, "user_id": 17, "user_name": "Client_17", "amount": 106.0}, {"transaction_id": 2053, "user_id": 20, "user_name": "Client_20", "amount": 107.75}, {"transaction_id": 2054, "user_id": 23, "user_name": "Client_23", "amount": 109.5}, {"transaction_id": 2055, "user_id": 26, "user_name": "Client_26", "amount": 111.25}, {"transaction_id": 2056, "user_id": 29, "user_name": "Client_29", "amount": 113.0}, {"transaction_id": 2057, "user_id": 32, "user_name": "Unknown User", "amount": 114.75}, {"transaction_id": 2058, "user_id": 35, "user_name": "Unknown User", "amount": 116.5}, {"transaction_id": 2059, "user_id": 3, "user_name": "Client_3", "amount": 118.25}, {"transaction_id": 2060, "user_id": 6, "user_name": "Client_6", "amount": 120.0}, {"transaction_id": 2061, "user_id": 9, "user_name": "Client_9", "amount": 121.75}, {"transaction_id": 2062, "user_id": 12, "user_name": "Client_12", "amount": 123.5}, {"transaction_id": 2063, "user_id": 15, "user_name": "Client_15", "amount": 125.25}, {"transaction_id": 2064, "user_id": 18, "user_name": "Client_18", "amount": 127.0}, {"transaction_id": 2065, "user_id": 21, "user_name": "Client_21", "amount": 128.75}, {"transaction_id": 2066, "user_id": 24, "user_name": "Client_24", "amount": 130.5}, {"transaction_id": 2067, "user_id": 27, "user_name": "Client_27", "amount": 132.25}, {"transaction_id": 2068, "user_id": 30, "user_name": "Client_30", "amount": 134.0}, {"transaction_id": 2069, "user_id": 33, "user_name": "Unknown User", "amount": 135.75}, {"transaction_id": 2070, "user_id": 1, "user_name": "Client_1", "amount": 137.5}, {"transaction_id": 2071, "user_id": 4, "user_name": "Client_4", "amount": 139.25}, {"transaction_id": 2072, "user_id": 7, "user_name": "Client_7", "amount": 141.0}, {"transaction_id": 2073, "user_id": 10, "user_name": "Client_10", "amount": 142.75}, {"transaction_id": 2074, "user_id": 13, "user_name": "Client_13", "amount": 144.5}, {"transaction_id": 2075, "user_id": 16, "user_name": "Client_16", "amount": 146.25}, {"transaction_id": 2076, "user_id": 19, "user_name": "Client_19", "amount": 148.0}, {"transaction_id": 2077, "user_id": 22, "user_name": "Client_22", "amount": 149.75}, {"transaction_id": 2078, "user_id": 25, "user_name": "Client_25", "amount": 151.5}, {"transaction_id": 2079, "user_id": 28, "user_name": "Client_28", "amount": 153.25}, {"transaction_id": 2080, "user_id": 31, "user_name": "Unknown User", "amount": 155.0}]}',
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "High-volume transaction processing workload",
                "input_data": '{"benchmark": {"users": 20000, "transactions": 35000, "seed": 42}}\n',
                "expected_output": '{"total_transactions": 35000, "total_amount": 2515625.0, "unmatched_transactions": 786, "sample_records_count": 35000}',
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Processes sparse and non-contiguous record identifiers",
                "input_data": '{"users": [{"id": 105, "name": "Partner Alpha"}, {"id": 2048, "name": "Partner Beta"}, {"id": 99999, "name": "Partner Omega"}], "transactions": [{"id": 5001, "user_id": 105, "amount": 1500.0}, {"id": 5002, "user_id": 300, "amount": 250.0}, {"id": 5003, "user_id": 99999, "amount": 840.5}, {"id": 5004, "user_id": 2048, "amount": 320.0}, {"id": 5005, "user_id": 7777, "amount": 95.25}]}\n',
                "expected_output": '{"total_transactions": 5, "total_amount": 3005.75, "unmatched_transactions": 2, "records": [{"transaction_id": 5001, "user_id": 105, "user_name": "Partner Alpha", "amount": 1500.0}, {"transaction_id": 5002, "user_id": 300, "user_name": "Unknown User", "amount": 250.0}, {"transaction_id": 5003, "user_id": 99999, "user_name": "Partner Omega", "amount": 840.5}, {"transaction_id": 5004, "user_id": 2048, "user_name": "Partner Beta", "amount": 320.0}, {"transaction_id": 5005, "user_id": 7777, "user_name": "Unknown User", "amount": 95.25}]}',
                "points": 20,
                "is_hidden": True,
            },
        ],
        "files": [
            {
                "path": "README.md",
                "is_readonly": True,
                "is_test": False,
                "content": (
                    "# Transaction Report Generator\n\n"
                    "## Role\n"
                    "You are a backend software engineer maintaining the transaction reporting and analytics pipeline for DevForge.\n\n"
                    "## Service Overview & Execution Model\n"
                    "The service is a Python application that reads transaction and user datasets from standard input in JSON format and writes structured summary reports to standard output in JSON format.\n\n"
                    "## Input Specification\n"
                    "The service expects JSON objects on standard input matching either of the following structures:\n\n"
                    "1. **Standard Dataset Payload**:\n"
                    "```json\n"
                    "{\n"
                    "  \"users\": [\n"
                    "    {\"id\": 1, \"name\": \"Alice Smith\"},\n"
                    "    {\"id\": 2, \"name\": \"Bob Jones\"}\n"
                    "  ],\n"
                    "  \"transactions\": [\n"
                    "    {\"id\": 101, \"user_id\": 1, \"amount\": 120.50},\n"
                    "    {\"id\": 102, \"user_id\": 2, \"amount\": 45.00}\n"
                    "  ]\n"
                    "}\n"
                    "```\n\n"
                    "2. **Benchmark Workload Configuration**:\n"
                    "```json\n"
                    "{\n"
                    "  \"benchmark\": {\n"
                    "    \"users\": 20000,\n"
                    "    \"transactions\": 35000,\n"
                    "    \"seed\": 42\n"
                    "  }\n"
                    "}\n"
                    "```\n\n"
                    "## Output Specification\n"
                    "The generated JSON report contains:\n"
                    "- `total_transactions`: Total count of processed transactions (integer).\n"
                    "- `total_amount`: Total monetary sum rounded to 2 decimal places (float).\n"
                    "- `unmatched_transactions`: Number of transactions with unresolvable user identifiers (integer).\n"
                    "- For standard payloads: `records`: List of enriched transaction items containing `transaction_id`, `user_id`, `user_name`, and `amount`.\n"
                    "- If a `user_id` does not match any registered user, assign `user_name` as `\"Unknown User\"`.\n\n"
                    "## Acceptance Criteria\n"
                    "- Correctly associates transactions with user profiles.\n"
                    "- Correctly tallies totals, counts, and unmatched transactions.\n"
                    "- Processes both small and high-volume workloads within the standard 5-second system execution limit.\n"
                    "- All unit tests in `tests/test_generator.py` pass.\n\n"
                    "## Execution\n"
                    "- Entrypoint: `app/main.py`\n"
                    "- Input: JSON payload provided via standard input.\n"
                ),
            },
            {
                "path": "requirements.txt",
                "is_readonly": True,
                "is_test": False,
                "content": "# Standard Python environment dependencies\n",
            },
            {
                "path": "app/__init__.py",
                "is_readonly": False,
                "is_test": False,
                "content": '"""Report Generator package."""\n',
            },
            {
                "path": "app/models.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "class User:\n"
                    "    def __init__(self, id: int, name: str):\n"
                    "        self.id = id\n"
                    "        self.name = name\n\n"
                    "class Transaction:\n"
                    "    def __init__(self, id: int, user_id: int, amount: float):\n"
                    "        self.id = id\n"
                    "        self.user_id = user_id\n"
                    "        self.amount = amount\n"
                ),
            },
            {
                "path": "app/generator.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "from app.models import User, Transaction\n\n"
                    "class ReportGenerator:\n"
                    "    def find_user_by_id(self, users, user_id):\n"
                    "        for user in users:\n"
                    "            if user.id == user_id:\n"
                    "                return user\n"
                    "        return None\n\n"
                    "    def generate(self, users, transactions):\n"
                    "        records = []\n"
                    "        total_amount = 0.0\n"
                    "        unmatched_count = 0\n\n"
                    "        for tx in transactions:\n"
                    "            total_amount += tx.amount\n"
                    "            user = self.find_user_by_id(users, tx.user_id)\n"
                    "            if user:\n"
                    "                user_name = user.name\n"
                    "            else:\n"
                    "                user_name = \"Unknown User\"\n"
                    "                unmatched_count += 1\n\n"
                    "            records.append({\n"
                    "                \"transaction_id\": tx.id,\n"
                    "                \"user_id\": tx.user_id,\n"
                    "                \"user_name\": user_name,\n"
                    "                \"amount\": tx.amount,\n"
                    "            })\n\n"
                    "        return {\n"
                    "            \"total_transactions\": len(records),\n"
                    "            \"total_amount\": round(total_amount, 2),\n"
                    "            \"unmatched_transactions\": unmatched_count,\n"
                    "            \"records\": records,\n"
                    "        }\n"
                ),
            },
            {
                "path": "app/main.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "import os\n"
                    "import sys\n"
                    "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
                    "import json\n"
                    "from app.models import User, Transaction\n"
                    "from app.generator import ReportGenerator\n\n"
                    "def process_payload(payload_str: str, generator: ReportGenerator) -> str:\n"
                    "    if not payload_str.strip():\n"
                    "        return \"{}\"\n\n"
                    "    data = json.loads(payload_str)\n"
                    "    if \"benchmark\" in data:\n"
                    "        cfg = data[\"benchmark\"]\n"
                    "        u_count = cfg.get(\"users\", 1000)\n"
                    "        t_count = cfg.get(\"transactions\", 2000)\n"
                    "        seed = cfg.get(\"seed\", 42)\n"
                    "        users = [User(i, f\"User_{i}\") for i in range(1, u_count + 1)]\n"
                    "        transactions = [\n"
                    "            Transaction(\n"
                    "                id=i,\n"
                    "                user_id=((i * 7 + seed) % (u_count + 500)) + 1,\n"
                    "                amount=round(10.0 + ((i + seed) % 100) * 1.25, 2),\n"
                    "            )\n"
                    "            for i in range(1, t_count + 1)\n"
                    "        ]\n"
                    "        report = generator.generate(users, transactions)\n"
                    "        return json.dumps({\n"
                    "            \"total_transactions\": report[\"total_transactions\"],\n"
                    "            \"total_amount\": report[\"total_amount\"],\n"
                    "            \"unmatched_transactions\": report[\"unmatched_transactions\"],\n"
                    "            \"sample_records_count\": len(report[\"records\"]),\n"
                    "        })\n\n"
                    "    users = [User(u[\"id\"], u[\"name\"]) for u in data.get(\"users\", [])]\n"
                    "    transactions = [\n"
                    "        Transaction(t[\"id\"], t[\"user_id\"], float(t[\"amount\"]))\n"
                    "        for t in data.get(\"transactions\", [])\n"
                    "    ]\n"
                    "    report = generator.generate(users, transactions)\n"
                    "    return json.dumps(report)\n\n"
                    "def main():\n"
                    "    generator = ReportGenerator()\n"
                    "    line = sys.stdin.readline()\n"
                    "    if line and line.strip():\n"
                    "        print(process_payload(line, generator))\n\n"
                    "if __name__ == '__main__':\n"
                    "    main()\n"
                ),
            },
            {
                "path": "tests/__init__.py",
                "is_readonly": True,
                "is_test": True,
                "content": '"""Test suite package."""\n',
            },
            {
                "path": "tests/test_generator.py",
                "is_readonly": True,
                "is_test": True,
                "content": (
                    "import unittest\n"
                    "from app.models import User, Transaction\n"
                    "from app.generator import ReportGenerator\n\n"
                    "class TestReportGenerator(unittest.TestCase):\n"
                    "    def setUp(self):\n"
                    "        self.generator = ReportGenerator()\n\n"
                    "    def test_basic_report_generation(self):\n"
                    "        users = [User(1, \"Alice\"), User(2, \"Bob\")]\n"
                    "        txs = [Transaction(101, 1, 50.0), Transaction(102, 2, 75.0)]\n"
                    "        report = self.generator.generate(users, txs)\n"
                    "        self.assertEqual(report[\"total_transactions\"], 2)\n"
                    "        self.assertEqual(report[\"total_amount\"], 125.0)\n"
                    "        self.assertEqual(report[\"unmatched_transactions\"], 0)\n"
                    "        self.assertEqual(len(report[\"records\"]), 2)\n\n"
                    "    def test_unmatched_user_fallback(self):\n"
                    "        users = [User(1, \"Alice\")]\n"
                    "        txs = [Transaction(101, 999, 50.0)]\n"
                    "        report = self.generator.generate(users, txs)\n"
                    "        self.assertEqual(report[\"unmatched_transactions\"], 1)\n"
                    "        self.assertEqual(report[\"records\"][0][\"user_name\"], \"Unknown User\")\n\n"
                    "if __name__ == '__main__':\n"
                    "    unittest.main()\n"
                ),
            },
        ],
    },

    {
        "title": "Add Two Numbers",
        "slug": "add-two-numbers",




        "difficulty": Challenge.Difficulty.BEGINNER,
        "challenge_type": Challenge.ChallengeType.BUG_FIX,
        "programming_language": "Python",
        "points": 100,
        "entrypoint": "app/calculator.py",
        "time_limit": 5,
        "memory_limit": 128,

        "description": (
            "You are given two integers from standard input separated by whitespace. "
            "The existing implementation contains a bug. Fix the program so that it reads "
            "the two integers and prints their sum.\n\n"
            "Input format:\nTwo integers separated by whitespace on a single line (e.g. '2 3').\n\n"
            "Output format:\nA single integer representing the sum."
        ),
        "starter_code": (
            "def add_numbers():\n"
            "    # BUG: Reads inputs as strings without converting to integers\n"
            "    inputs = input().split()\n"
            "    if len(inputs) >= 2:\n"
            "        a = inputs[0]\n"
            "        b = inputs[1]\n"
            "        print(a + b)\n\n"
            "if __name__ == '__main__':\n"
            "    add_numbers()\n"
        ),
        "test_cases": [
            {
                "name": "Basic Addition",
                "input_data": "2 3\n",
                "expected_output": "5",
                "points": 20,
                "is_hidden": False,
            },
            {
                "name": "Larger Numbers",
                "input_data": "10 20\n",
                "expected_output": "30",
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Negative Number",
                "input_data": "-5 8\n",
                "expected_output": "3",
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Zero",
                "input_data": "0 10\n",
                "expected_output": "10",
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Large Values",
                "input_data": "100 250\n",
                "expected_output": "350",
                "points": 20,
                "is_hidden": True,
            },
        ],
        "files": [
            {
                "path": "README.md",
                "is_readonly": True,
                "is_test": False,
                "content": (
                    "# Add Two Numbers\n\n"
                    "## Objective\n"
                    "Fix the bug in `app/calculator.py` where input values are concatenated as strings instead of being summed as integers.\n\n"
                    "## Input / Output\n"
                    "- Input: Two space-separated integers (e.g. `2 3`)\n"
                    "- Output: Integer sum (e.g. `5`)\n"
                ),
            },
            {
                "path": "requirements.txt",
                "is_readonly": True,
                "is_test": False,
                "content": "# DevForge environment dependencies\n",
            },
            {
                "path": "app/__init__.py",
                "is_readonly": False,
                "is_test": False,
                "content": '"""Calculator application package."""\n',
            },
            {
                "path": "app/calculator.py",
                "is_readonly": False,
                "is_test": False,
                "content": (
                    "def add_numbers():\n"
                    "    # BUG: Reads inputs as strings without converting to integers\n"
                    "    inputs = input().split()\n"
                    "    if len(inputs) >= 2:\n"
                    "        a = inputs[0]\n"
                    "        b = inputs[1]\n"
                    "        print(a + b)\n\n"
                    "if __name__ == '__main__':\n"
                    "    add_numbers()\n"
                ),
            },


            {
                "path": "tests/__init__.py",
                "is_readonly": True,
                "is_test": True,
                "content": '"""Test suite package."""\n',
            },
            {
                "path": "tests/test_calculator.py",
                "is_readonly": True,
                "is_test": True,
                "content": (
                    "import unittest\n\n"
                    "class TestCalculator(unittest.TestCase):\n"
                    "    def test_basic_addition(self):\n"
                    "        # Automated test case\n"
                    "        pass\n"
                ),
            },
        ],
    },

    {
        "title": "Password Validator",
        "slug": "password-validator",
        "difficulty": Challenge.Difficulty.BEGINNER,
        "challenge_type": Challenge.ChallengeType.BUG_FIX,
        "programming_language": "Python",
        "points": 100,
        "time_limit": 5,
        "memory_limit": 128,
        "description": (
            "Fix the password validation function.\n\n"
            "A password is valid when:\n"
            "- Length is at least 8 characters\n"
            "- Contains at least one digit (0-9)\n"
            "- Contains at least one uppercase letter (A-Z)\n\n"
            "Input format:\nA single string password from standard input.\n\n"
            "Output format:\nPrint 'VALID' if valid, or 'INVALID' otherwise."
        ),
        "starter_code": (
            "import sys\n\n"
            "def validate_password(password: str) -> str:\n"
            "    # BUG: Checks islower() instead of isupper() and > 8 instead of >= 8\n"
            "    if len(password) > 8 and any(c.isdigit() for c in password) and any(c.islower() for c in password):\n"
            "        return 'VALID'\n"
            "    return 'INVALID'\n\n"
            "if __name__ == '__main__':\n"
            "    raw_input = sys.stdin.read().strip()\n"
            "    print(validate_password(raw_input))\n"
        ),
        "test_cases": [
            {
                "name": "Standard Valid Password",
                "input_data": "Secret123\n",
                "expected_output": "VALID",
                "points": 20,
                "is_hidden": False,
            },
            {
                "name": "Too Short Password",
                "input_data": "Pass1\n",
                "expected_output": "INVALID",
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Missing Digit",
                "input_data": "PasswordOnly\n",
                "expected_output": "INVALID",
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Missing Uppercase",
                "input_data": "secret1234\n",
                "expected_output": "INVALID",
                "points": 20,
                "is_hidden": True,
            },
            {
                "name": "Exactly 8 Characters",
                "input_data": "Pass1234\n",
                "expected_output": "VALID",
                "points": 20,
                "is_hidden": True,
            },
        ],
    },
    {
        "title": "API Response Parser",
        "slug": "api-response-parser",
        "difficulty": Challenge.Difficulty.INTERMEDIATE,
        "challenge_type": Challenge.ChallengeType.DEBUGGING,
        "programming_language": "Python",
        "points": 100,
        "time_limit": 5,
        "memory_limit": 128,
        "description": (
            "An application receives user information as JSON.\n\n"
            "Fix the existing code so it safely reads the user's name and email from a JSON object "
            "and prints them in the format: 'User: <name> | Email: <email>'.\n\n"
            "If 'email' is missing or null, default to 'N/A'.\n"
            "If 'name' is missing or null, default to 'Anonymous'.\n\n"
            "Input format:\nA JSON string from standard input.\n\n"
            "Output format:\nA single line in format: 'User: <name> | Email: <email>'."
        ),
        "starter_code": (
            "import sys\n"
            "import json\n\n"
            "def parse_user_payload():\n"
            "    # BUG: Direct dictionary access raises KeyError on missing fields\n"
            "    data = json.loads(sys.stdin.read().strip() or '{}')\n"
            "    name = data['name']\n"
            "    email = data['email']\n"
            "    print(f'User: {name} | Email: {email}')\n\n"
            "if __name__ == '__main__':\n"
            "    parse_user_payload()\n"
        ),
        "test_cases": [
            {
                "name": "Standard User Payload",
                "input_data": '{"name": "Alice", "email": "alice@example.com"}\n',
                "expected_output": "User: Alice | Email: alice@example.com",
                "points": 25,
                "is_hidden": False,
            },
            {
                "name": "Missing Email Field",
                "input_data": '{"name": "Bob"}\n',
                "expected_output": "User: Bob | Email: N/A",
                "points": 25,
                "is_hidden": True,
            },
            {
                "name": "Missing Name Field",
                "input_data": '{"email": "contact@test.org"}\n',
                "expected_output": "User: Anonymous | Email: contact@test.org",
                "points": 25,
                "is_hidden": True,
            },
            {
                "name": "Empty JSON Object",
                "input_data": "{}\n",
                "expected_output": "User: Anonymous | Email: N/A",
                "points": 25,
                "is_hidden": True,
            },
        ],
    },
    {
        "title": "Duplicate Transaction Detector",
        "slug": "duplicate-transaction-detector",
        "difficulty": Challenge.Difficulty.INTERMEDIATE,
        "challenge_type": Challenge.ChallengeType.DATABASE,
        "programming_language": "Python",
        "points": 100,
        "time_limit": 5,
        "memory_limit": 128,
        "description": (
            "A payment processing system receives transaction IDs.\n\n"
            "Due to retries, the same transaction ID may appear multiple times.\n"
            "Fix the implementation so that it counts the total number of duplicate/redundant occurrences.\n\n"
            "Input format:\nWhitespace-separated transaction ID strings from standard input.\n\n"
            "Output format:\nA single integer representing total duplicate count (total items - unique items)."
        ),
        "starter_code": (
            "import sys\n\n"
            "def count_duplicate_transactions():\n"
            "    # BUG: Prints unique items count instead of duplicate count\n"
            "    tx_ids = sys.stdin.read().split()\n"
            "    unique_ids = set(tx_ids)\n"
            "    print(len(unique_ids))\n\n"
            "if __name__ == '__main__':\n"
            "    count_duplicate_transactions()\n"
        ),
        "test_cases": [
            {
                "name": "Single Duplicate",
                "input_data": "tx1 tx2 tx3 tx1\n",
                "expected_output": "1",
                "points": 25,
                "is_hidden": False,
            },
            {
                "name": "No Duplicates",
                "input_data": "tx100 tx200 tx300 tx400\n",
                "expected_output": "0",
                "points": 25,
                "is_hidden": True,
            },
            {
                "name": "Multiple Duplicates",
                "input_data": "tx1 tx2 tx1 tx3 tx2 tx1\n",
                "expected_output": "3",
                "points": 25,
                "is_hidden": True,
            },
            {
                "name": "All Same ID",
                "input_data": "alpha alpha alpha alpha alpha\n",
                "expected_output": "4",
                "points": 25,
                "is_hidden": True,
            },
        ],
    },
    {
        "title": "Slow Search Function",
        "slug": "slow-search-function",
        "difficulty": Challenge.Difficulty.ADVANCED,
        "challenge_type": Challenge.ChallengeType.PERFORMANCE,
        "programming_language": "Python",
        "points": 100,
        "time_limit": 5,
        "memory_limit": 128,
        "description": (
            "Given a list of database record IDs and a list of query IDs, count how many queries "
            "exist in the database records.\n\n"
            "Input format:\n"
            "Line 1: Space-separated database record IDs.\n"
            "Line 2: Space-separated query IDs.\n\n"
            "Output format:\nA single integer representing total matching queries.\n\n"
            "Optimize the solution so it utilizes O(1) set lookups."
        ),
        "starter_code": (
            "import sys\n\n"
            "def count_matches():\n"
            "    lines = sys.stdin.read().strip().split('\\n')\n"
            "    if not lines or len(lines) < 2:\n"
            "        print(0)\n"
            "        return\n"
            "    db_records = lines[0].split()\n"
            "    queries = lines[1].split()\n"
            "    match_count = 0\n"
            "    # Inefficient list search\n"
            "    for q in queries:\n"
            "        if q in db_records:\n"
            "            match_count += 1\n"
            "    print(match_count)\n\n"
            "if __name__ == '__main__':\n"
            "    count_matches()\n"
        ),
        "test_cases": [
            {
                "name": "Basic Query Match",
                "input_data": "10 20 30 40 50\n20 50 99\n",
                "expected_output": "2",
                "points": 25,
                "is_hidden": False,
            },
            {
                "name": "No Matching Queries",
                "input_data": "apple banana cherry\norange grape\n",
                "expected_output": "0",
                "points": 25,
                "is_hidden": True,
            },
            {
                "name": "All Matching Queries",
                "input_data": "id1 id2 id3 id4\nid1 id3 id4\n",
                "expected_output": "3",
                "points": 25,
                "is_hidden": True,
            },
            {
                "name": "Repeated Queries",
                "input_data": "k1 k2 k3 k4 k5\nk2 k2 k5 k9 k2\n",
                "expected_output": "4",
                "points": 25,
                "is_hidden": True,
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed initial CodeFoundry challenges and test cases idempotently."

    def handle(self, *args, **options):
        created_challenges = []
        updated_challenges = []
        total_test_cases = 0

        with transaction.atomic():
            for item in SEED_DATA:
                test_cases_data = item.get("test_cases", [])
                challenge_defaults = {
                    "title": item["title"],
                    "difficulty": item["difficulty"],
                    "challenge_type": item["challenge_type"],
                    "programming_language": item["programming_language"],
                    "points": item["points"],
                    "entrypoint": item.get("entrypoint", ""),
                    "time_limit": item.get("time_limit", 5),
                    "memory_limit": item.get("memory_limit", 128),
                    "description": item["description"],
                    "starter_code": item["starter_code"],
                    "is_active": True,
                }


                challenge, created = Challenge.objects.update_or_create(
                    slug=item["slug"],
                    defaults=challenge_defaults,
                )

                if created:
                    created_challenges.append(challenge.title)
                else:
                    updated_challenges.append(challenge.title)

                # Synchronize test cases
                for tc_item in test_cases_data:
                    tc_defaults = {
                        "input_data": tc_item["input_data"],
                        "expected_output": tc_item["expected_output"],
                        "points": tc_item["points"],
                        "is_hidden": tc_item.get("is_hidden", False),
                        "is_active": True,
                    }

                    TestCase.objects.update_or_create(
                        challenge=challenge,
                        name=tc_item["name"],
                        defaults=tc_defaults,
                    )
                    total_test_cases += 1

                # Synchronize repository files
                for file_item in item.get("files", []):
                    ChallengeFile.objects.update_or_create(
                        challenge=challenge,
                        path=file_item["path"],
                        defaults={
                            "content": file_item.get("content", ""),
                            "is_test": file_item.get("is_test", False),
                            "is_readonly": file_item.get("is_readonly", False),
                        },
                    )


        self.stdout.write(self.style.SUCCESS("CodeFoundry challenge seeding complete."))
        if created_challenges:
            self.stdout.write("Created:")
            for title in created_challenges:
                self.stdout.write(f"  - {title}")
        if updated_challenges:
            self.stdout.write("Updated:")
            for title in updated_challenges:
                self.stdout.write(f"  - {title}")
        self.stdout.write(f"Test cases:\n  {total_test_cases} synchronized")
