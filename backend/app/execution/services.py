from app.execution.runner import CodeRunner, DockerCodeRunner


class ExecutionService:
    def __init__(self, runner=None):
        self.runner = runner or DockerCodeRunner()

    def execute(
        self,
        code=None,
        language="Python",
        stdin_data=None,
        timeout=None,
        files=None,
        entrypoint=None,
    ):
        if files:
            return self.runner.run_repository(
                files=files,
                language=language,
                entrypoint=entrypoint or "main.py",
                stdin_data=stdin_data,
                timeout=timeout,
            )
        return self.runner.run(
            code=code or "",
            language=language,
            stdin_data=stdin_data,
            timeout=timeout,
        )
