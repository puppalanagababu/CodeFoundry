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



