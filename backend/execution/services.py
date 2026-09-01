from .runner import CodeRunner, DockerCodeRunner


class ExecutionService:
    def __init__(self, runner=None):
        self.runner = runner or DockerCodeRunner()

    def execute(self, code, language):
        return self.runner.run(code, language)