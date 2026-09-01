from django.core.management.base import BaseCommand
from django.db import transaction
from challenges.models import Challenge, ChallengeFile, TestCase


SEED_DATA = [
    {
        "title": "Add Two Numbers",
        "slug": "add-two-numbers",
        "difficulty": Challenge.Difficulty.BEGINNER,
        "challenge_type": Challenge.ChallengeType.BUG_FIX,
        "programming_language": "Python",
        "points": 100,
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
            "import sys\n\n"
            "def add_numbers():\n"
            "    # BUG: Reads inputs as strings without converting to integers\n"
            "    inputs = sys.stdin.read().split()\n"
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
                    "import sys\n\n"
                    "def add_numbers():\n"
                    "    # BUG: Reads inputs as strings without converting to integers\n"
                    "    inputs = sys.stdin.read().split()\n"
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
