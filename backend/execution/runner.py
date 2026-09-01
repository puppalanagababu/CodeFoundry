import time
import docker
from requests.exceptions import ConnectionError, ReadTimeout


class ExecutionResult:
    def __init__(
        self,
        stdout="",
        stderr="",
        exit_code=0,
        execution_time=0.0,
        memory_used=0,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.execution_time = execution_time
        self.memory_used = memory_used

    def to_dict(self):
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "memory_used": self.memory_used,
        }

    def __repr__(self):
        return (
            f"ExecutionResult(stdout={self.stdout!r}, stderr={self.stderr!r}, "
            f"exit_code={self.exit_code}, execution_time={self.execution_time}, "
            f"memory_used={self.memory_used})"
        )


class CodeRunner:
    def run(self, code, language, stdin_data=None, timeout=None):
        raise NotImplementedError(
            "CodeRunner subclasses must implement run()."
        )


class DockerCodeRunner(CodeRunner):
    """
    Executes code in an isolated Docker container with resource constraints
    and security sandboxing.
    """

    DEFAULT_IMAGE = "python:3.11-slim"
    DEFAULT_TIMEOUT = 5  # seconds
    DEFAULT_MEM_LIMIT = "128m"
    DEFAULT_MEMSWAP_LIMIT = "128m"
    DEFAULT_NANO_CPUS = 1_000_000_000  # 1.0 CPU
    DEFAULT_PIDS_LIMIT = 64

    def __init__(
        self,
        image=DEFAULT_IMAGE,
        timeout=DEFAULT_TIMEOUT,
        mem_limit=DEFAULT_MEM_LIMIT,
        memswap_limit=DEFAULT_MEMSWAP_LIMIT,
        nano_cpus=DEFAULT_NANO_CPUS,
        pids_limit=DEFAULT_PIDS_LIMIT,
        client=None,
    ):
        self.image = image
        self.timeout = timeout
        self.mem_limit = mem_limit
        self.memswap_limit = memswap_limit
        self.nano_cpus = nano_cpus
        self.pids_limit = pids_limit
        self._client = client

    @property
    def client(self):
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def run(self, code, language, stdin_data=None, timeout=None):
        if not language or language.strip().lower() != "python":
            return ExecutionResult(
                stdout="",
                stderr=f"Unsupported language: '{language}'. Only 'Python' is currently supported.",
                exit_code=1,
                execution_time=0.0,
                memory_used=0,
            )

        effective_timeout = timeout if timeout is not None else self.timeout
        start_time = time.time()
        container = None
        stdout = ""
        stderr = ""
        exit_code = 0
        memory_used = 0

        try:
            stdin_open = bool(stdin_data is not None)
            container = self.client.containers.create(
                image=self.image,
                command=["python", "-u", "-c", code],
                network_disabled=True,
                mem_limit=self.mem_limit,
                memswap_limit=self.memswap_limit,
                nano_cpus=self.nano_cpus,
                pids_limit=self.pids_limit,
                privileged=False,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                stdin_open=stdin_open,
                detach=True,
            )

            sock = None
            if stdin_open:
                sock = container.attach_socket(params={"stdin": 1, "stream": 1})

            container.start()

            if stdin_open and sock is not None:
                if stdin_data:
                    data_bytes = stdin_data.encode("utf-8") if isinstance(stdin_data, str) else stdin_data
                    sock.sendall(data_bytes)
                sock.close()

            timed_out = False
            try:
                wait_result = container.wait(timeout=effective_timeout)
                exit_code = wait_result.get("StatusCode", 0)
            except (ReadTimeout, ConnectionError):
                timed_out = True
                try:
                    container.kill()
                except Exception:
                    pass
                exit_code = 124
                stderr = f"Execution timed out after {effective_timeout} seconds."

            if not timed_out:
                stdout = container.logs(stdout=True, stderr=False).decode(
                    "utf-8", errors="replace"
                )
                stderr = container.logs(stdout=False, stderr=True).decode(
                    "utf-8", errors="replace"
                )
                try:
                    stats = container.stats(stream=False)
                    memory_used = stats.get("memory_stats", {}).get(
                        "max_usage", 0
                    )
                except Exception:
                    memory_used = 0

        except Exception as e:
            exit_code = 1
            stderr = f"Execution error: {str(e)}"
        finally:
            execution_time = time.time() - start_time
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            execution_time=execution_time,
            memory_used=memory_used,
        )
