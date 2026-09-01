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

    def test_execution_service_default_runner(self):
        service = ExecutionService()
        self.assertIsInstance(service.runner, DockerCodeRunner)

        result = service.execute("print(10 + 32)", "Python")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "42")
        self.assertEqual(result.stderr, "")

