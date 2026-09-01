import re
import time
import docker
from requests.exceptions import ConnectionError, ReadTimeout


def _validate_safe_relative_path(path_str: str, context_name: str = "path") -> str:
    """
    Strictly validates that a path is a safe relative path.
    Rejects:
      - Empty or non-string paths
      - Windows drive paths (e.g. C:, D:)
      - UNC network paths (e.g. \\server\share, //server/share)
      - Absolute paths (e.g. /etc/passwd, \Windows)
      - Traversal or dot segments (e.g. '..', '.')
    Returns the normalized relative path with forward slashes.
    """
    if not path_str or not isinstance(path_str, str) or not path_str.strip():
        raise ValueError(f"Invalid {context_name}: path cannot be empty.")

    raw = path_str.strip()

    # Reject UNC paths (starting with \\ or //)
    if raw.startswith("\\\\") or raw.startswith("//"):
        raise ValueError(
            f"Security error: UNC paths are not permitted in {context_name}: '{path_str}'"
        )

    # Reject Windows drive letters (e.g. C:, c:)
    if re.match(r"^[a-zA-Z]:", raw):
        raise ValueError(
            f"Security error: Windows drive paths are not permitted in {context_name}: '{path_str}'"
        )

    # Normalize backslashes to forward slashes
    normalized = raw.replace("\\", "/")

    # Reject absolute paths (starting with /)
    if normalized.startswith("/"):
        raise ValueError(
            f"Security error: Absolute paths are not permitted in {context_name}: '{path_str}'"
        )

    # Validate individual path segments
    segments = normalized.split("/")
    for seg in segments:
        if seg == "" or seg == "." or seg == "..":
            raise ValueError(
                f"Security error: Invalid path segment '{seg}' or path traversal detected in {context_name}: '{path_str}'"
            )

    return normalized



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
                try:
                    if hasattr(sock, "_sock") and sock._sock:
                        sock._sock.shutdown(1)
                except Exception:
                    pass
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

    def run_repository(
        self,
        files,
        language="Python",
        entrypoint="main.py",
        stdin_data=None,
        timeout=None,
    ):
        """
        Executes a multi-file repository workspace in an isolated Docker container.
        """
        if not language or language.strip().lower() != "python":
            return ExecutionResult(
                stdout="",
                stderr=f"Unsupported language: '{language}'. Only 'Python' is currently supported.",
                exit_code=1,
                execution_time=0.0,
                memory_used=0,
            )

        if not files:
            return ExecutionResult(
                stdout="",
                stderr="No repository files provided for execution.",
                exit_code=1,
                execution_time=0.0,
                memory_used=0,
            )

        import os
        import shutil
        import tempfile

        # Normalize files to dict {rel_path: content}
        file_map = {}
        if isinstance(files, dict):
            file_map = files
        elif isinstance(files, list):
            for item in files:
                if isinstance(item, dict) and "path" in item:
                    file_map[item["path"]] = item.get("content", "")

        temp_dir = tempfile.mkdtemp(prefix="devforge_repo_")
        effective_timeout = timeout if timeout is not None else self.timeout
        start_time = time.time()
        container = None
        stdout = ""
        stderr = ""
        exit_code = 0
        memory_used = 0

        try:
            real_temp_dir = os.path.realpath(temp_dir)

            # 1. Validate paths and write files safely into temp workspace
            normalized_file_map = {}
            for rel_path, content in file_map.items():
                clean_rel = _validate_safe_relative_path(rel_path, "repository file path")

                full_dest = os.path.realpath(os.path.join(real_temp_dir, clean_rel))
                # Strict path traversal prevention via canonical containment check
                if os.path.commonpath([real_temp_dir, full_dest]) != real_temp_dir:
                    raise ValueError(
                        f"Security error: path traversal attempt detected in '{rel_path}'"
                    )

                os.makedirs(os.path.dirname(full_dest), exist_ok=True)
                with open(full_dest, "w", encoding="utf-8") as f:
                    f.write(content or "")
                normalized_file_map[clean_rel] = content

            # 2. Validate entrypoint
            if not entrypoint or not str(entrypoint).strip():
                clean_entry = next(
                    (p for p in normalized_file_map.keys() if p.endswith(".py")), "main.py"
                )
            else:
                clean_entry = _validate_safe_relative_path(str(entrypoint), "entrypoint")

            if not clean_entry.endswith(".py"):
                raise ValueError(
                    f"Security error: entrypoint must be a Python (.py) file, got '{clean_entry}'"
                )

            if clean_entry not in normalized_file_map:
                raise ValueError(
                    f"Security error: entrypoint '{clean_entry}' not found in repository files"
                )

            full_entry = os.path.realpath(os.path.join(real_temp_dir, clean_entry))
            if os.path.commonpath([real_temp_dir, full_entry]) != real_temp_dir:
                raise ValueError(
                    f"Security error: invalid entrypoint '{entrypoint}'"
                )

            # 3. Create isolated container with workspace volume mount
            stdin_open = bool(stdin_data is not None)
            mount_path = os.path.abspath(real_temp_dir)


            container = self.client.containers.create(
                image=self.image,
                command=["python", "-u", clean_entry],
                working_dir="/workspace",
                volumes={
                    mount_path: {
                        "bind": "/workspace",
                        "mode": "rw",
                    }
                },
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
                    data_bytes = (
                        stdin_data.encode("utf-8")
                        if isinstance(stdin_data, str)
                        else stdin_data
                    )
                    sock.sendall(data_bytes)
                try:
                    if hasattr(sock, "_sock") and sock._sock:
                        sock._sock.shutdown(1)
                except Exception:
                    pass
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
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            execution_time=execution_time,
            memory_used=memory_used,
        )

