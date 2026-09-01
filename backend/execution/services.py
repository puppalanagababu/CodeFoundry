from .runner import CodeRunner, DockerCodeRunner


class ExecutionService:
    def __init__(self, runner=None):
        self.runner = runner or DockerCodeRunner()

    def execute(self, code, language, stdin_data=None, timeout=None):
        return self.runner.run(
            code=code,
            language=language,
            stdin_data=stdin_data,
            timeout=timeout,
        )
