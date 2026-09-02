from django.test import SimpleTestCase
from .runner import DockerCodeRunner, ExecutionResult
from .services import ExecutionService


class DockerCodeRunnerTests(SimpleTestCase):
    def setUp(self):
        self.runner = DockerCodeRunner(timeout=5)

    def test_simple_python_program(self):
        code = "print('Hello, CodeFoundry!')"
        result = self.runner.run(code, "Python")

        self.assertIsInstance(result, ExecutionResult)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "Hello, CodeFoundry!")
        self.assertEqual(result.stderr, "")
        self.assertGreater(result.execution_time, 0)

    def test_syntax_error(self):
        code = "def invalid_syntax("
        result = self.runner.run(code, "Python")

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("SyntaxError", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_runtime_error(self):
        code = "1 / 0"
        result = self.runner.run(code, "Python")

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("ZeroDivisionError", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_unsupported_language(self):
        code = "console.log('Hello');"
        result = self.runner.run(code, "JavaScript")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Unsupported language", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_timeout(self):
        short_timeout_runner = DockerCodeRunner(timeout=2)
        code = "import time\ntime.sleep(10)"
        result = short_timeout_runner.run(code, "Python")

        self.assertEqual(result.exit_code, 124)
        self.assertIn("timed out", result.stderr.lower())

    def test_stdin_execution(self):
        code = "a, b = map(int, input().split())\nprint(a + b)"
        result = self.runner.run(code, "Python", stdin_data="2 3\n")

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "5")
        self.assertEqual(result.stderr, "")

    def test_stdin_incorrect_output(self):
        code = "a, b = map(int, input().split())\nprint(a * b)"
        result = self.runner.run(code, "Python", stdin_data="2 3\n")

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "6")

    def test_execution_service_default_runner(self):
        service = ExecutionService()
        self.assertIsInstance(service.runner, DockerCodeRunner)

        result = service.execute("print(10 + 32)", "Python")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "42")
        self.assertEqual(result.stderr, "")



class CeleryTaskTests(SimpleTestCase):
    def test_celery_task_execution(self):
        from .tasks import test_celery_task

        # Test direct call
        self.assertEqual(test_celery_task(3, 4), 7)

        # Test Celery apply (eager/local execution)
        async_result = test_celery_task.apply(args=[15, 25])
        self.assertEqual(async_result.get(), 40)
        self.assertEqual(async_result.status, "SUCCESS")

    def test_celery_task_registration(self):
        from config.celery import app

        self.assertIn("test_celery_task", app.tasks)


class CodeExecutionAPITests(SimpleTestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIRequestFactory
        from .views import CodeExecutionView

        User = get_user_model()
        self.factory = APIRequestFactory()
        self.view = CodeExecutionView.as_view()
        self.user = User(id=1, username="teststudent")

    def test_unauthenticated_request_rejected(self):
        request = self.factory.post(
            "/api/execution/run/",
            {"code": "print(1)"},
            format="json",
        )
        response = self.view(request)
        from rest_framework import status

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_authenticated_valid_code_execution(self):
        from rest_framework.test import force_authenticate
        from rest_framework import status

        request = self.factory.post(
            "/api/execution/run/",
            {"code": "print(2 + 3)", "language": "Python"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "SUCCESS")
        self.assertEqual(response.data["stdout"].strip(), "5")
        self.assertEqual(response.data["exit_code"], 0)
        self.assertEqual(response.data["stderr"], "")
        self.assertGreater(response.data["execution_time"], 0)

    def test_authenticated_stdin_passed_correctly(self):
        from rest_framework.test import force_authenticate
        from rest_framework import status

        request = self.factory.post(
            "/api/execution/run/",
            {
                "code": "name = input()\nprint('Hello', name)",
                "language": "Python",
                "stdin": "Babu",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "SUCCESS")
        self.assertEqual(response.data["stdout"].strip(), "Hello Babu")

    def test_runtime_error_returns_structured_failure(self):
        from rest_framework.test import force_authenticate
        from rest_framework import status

        request = self.factory.post(
            "/api/execution/run/",
            {"code": "print(undefined_variable)"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "FAILED")
        self.assertNotEqual(response.data["exit_code"], 0)
        self.assertIn("NameError", response.data["stderr"])

    def test_missing_code_returns_bad_request(self):
        from rest_framework.test import force_authenticate
        from rest_framework import status

        request = self.factory.post(
            "/api/execution/run/",
            {"stdin": "123"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data)

    def test_authenticated_repository_execution_api(self):
        from rest_framework.test import force_authenticate
        from rest_framework import status

        request = self.factory.post(
            "/api/execution/run/",
            {
                "files": {
                    "app/calc.py": "def add(a, b): return a + b",
                    "main.py": "from app.calc import add\nimport sys\nprint('Total:', add(10, 20))",
                },
                "entrypoint": "main.py",
                "language": "Python",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "SUCCESS")
        self.assertEqual(response.data["stdout"].strip(), "Total: 30")


class RepositoryDockerExecutionTests(SimpleTestCase):
    def setUp(self):
        self.runner = DockerCodeRunner(timeout=5)

    def test_1_multi_file_import_and_execution(self):
        files = {
            "app/__init__.py": "",
            "app/math_helper.py": "def multiply(x, y): return x * y",
            "main.py": "from app.math_helper import multiply\nprint(multiply(6, 7))",
        }
        result = self.runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "42")
        self.assertEqual(result.stderr, "")

    def test_2_repository_stdin(self):
        files = {
            "calculator.py": "a, b = map(int, input().split())\nprint(a + b)"
        }
        result = self.runner.run_repository(
            files=files, entrypoint="calculator.py", stdin_data="10 25\n"
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "35")


    def test_3_path_traversal_forward_slash_rejected(self):
        files = {"../escaped.py": "print('escaped')", "main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("path traversal", result.stderr.lower())

    def test_4_path_traversal_backslash_rejected(self):
        files = {"..\\escaped.py": "print('escaped')", "main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("path traversal", result.stderr.lower())

    def test_5_absolute_unix_path_rejected(self):
        files = {"/etc/passwd": "root:x:0:0", "main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("absolute", result.stderr.lower())

    def test_6_windows_drive_letter_forward_slash_rejected(self):
        files = {"C:/Windows/system.ini": "[drivers]", "main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("windows drive", result.stderr.lower())

    def test_7_windows_drive_letter_backslash_rejected(self):
        files = {"C:\\Windows\\system.ini": "[drivers]", "main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("windows drive", result.stderr.lower())

    def test_8_unc_path_rejected(self):
        files = {"\\\\server\\share\\file.py": "print(1)", "main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("unc", result.stderr.lower())

    def test_9_dot_path_segment_rejected(self):
        files = {"app/./calc.py": "print(1)", "main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("invalid path segment", result.stderr.lower())

    def test_10_dotdot_nested_path_segment_rejected(self):
        files = {"app/../escaped.py": "print(1)", "main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("path traversal", result.stderr.lower())

    def test_11_valid_nested_repository_path(self):
        files = {
            "app/math/calc.py": "def double(n): return n * 2",
            "main.py": "from app.math.calc import double\nprint(double(21))",
        }
        result = self.runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "42")

    def test_12_invalid_entrypoint_outside_repository(self):
        files = {"main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="../outside.py")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("security error", result.stderr.lower())

    def test_13_invalid_non_python_entrypoint(self):
        files = {"README.md": "# Hello", "main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="README.md")
        self.assertEqual(result.exit_code, 1)
        self.assertIn(".py", result.stderr.lower())

    def test_14_missing_entrypoint_file(self):
        files = {"main.py": "print('ok')"}
        result = self.runner.run_repository(files=files, entrypoint="nonexistent.py")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("not found", result.stderr.lower())

    def test_15_valid_nested_python_entrypoint(self):
        files = {
            "pkg/__init__.py": "",
            "pkg/runner.py": "print('Nested entrypoint executed successfully!')",
        }
        result = self.runner.run_repository(files=files, entrypoint="pkg/runner.py")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "Nested entrypoint executed successfully!")

    def test_16_repository_timeout(self):
        short_runner = DockerCodeRunner(timeout=2)
        files = {"main.py": "import time\ntime.sleep(10)"}
        result = short_runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 124)
        self.assertIn("timed out", result.stderr.lower())


class SocketStdinCompatibilityTests(SimpleTestCase):
    def test_send_with_sendall(self):
        from .runner import _send_container_stdin

        class MockSocketSendall:
            def __init__(self):
                self.received = b""

            def sendall(self, data):
                self.received += data

        sock = MockSocketSendall()
        _send_container_stdin(sock, "hello sendall\n")
        self.assertEqual(sock.received, b"hello sendall\n")

    def test_send_without_sendall_underlying_send(self):
        """Simulates Linux Unix HTTP/Socket wrappers that only have send() on raw socket."""
        from .runner import _send_container_stdin

        class MockRawSocket:
            def __init__(self):
                self.received = b""

            def send(self, data):
                self.received += data
                return len(data)

        class MockSocketWrapper:
            def __init__(self):
                self._sock = MockRawSocket()

        sock = MockSocketWrapper()
        _send_container_stdin(sock, "hello raw send\n")
        self.assertEqual(sock._sock.received, b"hello raw send\n")

    def test_send_with_file_write(self):
        from .runner import _send_container_stdin

        class MockFileSocket:
            def __init__(self):
                self.received = b""
                self.flushed = False

            def write(self, data):
                self.received += data

            def flush(self):
                self.flushed = True

        sock = MockFileSocket()
        _send_container_stdin(sock, "hello file write\n")
        self.assertEqual(sock.received, b"hello file write\n")
        self.assertTrue(sock.flushed)

    def test_safe_socket_close(self):
        from .runner import _close_container_stdin

        class MockSocketClose:
            def __init__(self):
                self.closed = False
                self.shut = False

            def shutdown(self, how):
                self.shut = True

            def close(self):
                self.closed = True

        sock = MockSocketClose()
        _close_container_stdin(sock)
        self.assertTrue(sock.shut)
        self.assertTrue(sock.closed)

    def test_repository_execution_permissions_and_math_helper(self):
        runner = DockerCodeRunner()
        files = {
            "app/__init__.py": "",
            "app/math_helper.py": "def multiply(x, y):\n    return x * y\n",
            "main.py": "from app.math_helper import multiply\nprint(multiply(6, 7))\n",
        }
        result = runner.run_repository(files=files, entrypoint="main.py")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "42")
        self.assertEqual(result.stderr, "")
