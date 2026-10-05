from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.main import app
from app.models.user import User, UserRole
from app.services.auth_service import create_access_token, hash_password
from app.execution.runner import (
    CodeRunner,
    DockerCodeRunner,
    ExecutionResult,
    _validate_safe_relative_path,
)

from app.execution.services import ExecutionService


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user():
    session = SessionLocal()
    user = session.query(User).filter(User.username == "execution_test_user").first()
    if not user:
        user = User(
            username="execution_test_user",
            email="exec@example.com",
            password=hash_password("Pass123!"),
            role=UserRole.STUDENT.value,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    session.close()
    return user


def test_safe_relative_path_validation():
    # Valid relative paths
    assert _validate_safe_relative_path("src/main.py") == "src/main.py"
    assert _validate_safe_relative_path("app\\calculator.py") == "app/calculator.py"
    assert _validate_safe_relative_path("utils.py") == "utils.py"

    # Invalid paths must raise ValueError
    with pytest.raises(ValueError, match="path cannot be empty"):
        _validate_safe_relative_path("")

    with pytest.raises(ValueError, match="Absolute paths are not permitted"):
        _validate_safe_relative_path("/etc/passwd")

    with pytest.raises(ValueError, match="Windows drive paths are not permitted"):
        _validate_safe_relative_path("C:\\Windows\\System32")

    with pytest.raises(ValueError, match="UNC paths are not permitted"):
        _validate_safe_relative_path("\\\\server\\share\\file.py")

    with pytest.raises(ValueError, match="path traversal detected"):
        _validate_safe_relative_path("../secret.py")

    with pytest.raises(ValueError, match="path traversal detected"):
        _validate_safe_relative_path("src/../../etc/passwd")


def test_docker_runner_security_defaults():
    runner = DockerCodeRunner()
    assert runner.image == "python:3.11-slim"
    assert runner.timeout == 5
    assert runner.mem_limit == "128m"
    assert runner.memswap_limit == "128m"
    assert runner.nano_cpus == 1_000_000_000  # 1.0 CPU
    assert runner.pids_limit == 64


def test_execution_api_requires_auth(client: TestClient):
    res = client.post(
        "/api/execution/run/",
        json={"code": "print('Hello')"},
    )
    assert res.status_code == 401


def test_execution_api_validation(client: TestClient, test_user: User):
    token = create_access_token(test_user.id, test_user.role)
    # Missing code and files
    res = client.post(
        "/api/execution/run/",
        json={"code": "", "files": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


def test_execution_api_success(client: TestClient, test_user: User, monkeypatch):
    token = create_access_token(test_user.id, test_user.role)

    # Mock execution service runner for deterministic unit testing
    mock_runner = MagicMock(spec=CodeRunner)
    mock_runner.run.return_value = ExecutionResult(
        stdout="Hello, CodeFoundry!\n",
        stderr="",
        exit_code=0,
        execution_time=0.12,
        memory_used=12.5,
    )
    from app.routers import execution
    monkeypatch.setattr(execution, "execution_service", ExecutionService(runner=mock_runner))

    res = client.post(
        "/api/execution/run/",
        json={"code": "print('Hello, CodeFoundry!')", "stdin": "input_data"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["stdout"] == "Hello, CodeFoundry!\n"
    assert data["exit_code"] == 0
    assert data["execution_time"] == 0.12


def test_execution_api_syntax_error(client: TestClient, test_user: User, monkeypatch):
    token = create_access_token(test_user.id, test_user.role)

    mock_runner = MagicMock(spec=CodeRunner)
    mock_runner.run.return_value = ExecutionResult(
        stdout="",
        stderr="SyntaxError: invalid syntax",
        exit_code=1,
        execution_time=0.05,
        memory_used=8.0,
    )
    from app.routers import execution
    monkeypatch.setattr(execution, "execution_service", ExecutionService(runner=mock_runner))

    res = client.post(
        "/api/execution/run/",
        json={"code": "def invalid_syntax("},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FAILED"
    assert "SyntaxError" in data["stderr"]
    assert data["exit_code"] == 1


def test_execution_api_timeout(client: TestClient, test_user: User, monkeypatch):
    token = create_access_token(test_user.id, test_user.role)

    mock_runner = MagicMock(spec=CodeRunner)
    mock_runner.run.return_value = ExecutionResult(
        stdout="",
        stderr="Execution timed out after 5.0 seconds",
        exit_code=124,
        execution_time=5.0,
        memory_used=15.0,
    )
    from app.routers import execution
    monkeypatch.setattr(execution, "execution_service", ExecutionService(runner=mock_runner))

    res = client.post(
        "/api/execution/run/",
        json={"code": "while True: pass", "timeout": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FAILED"
    assert data["exit_code"] == 124
    assert "timed out" in data["stderr"].lower()


def test_execution_api_repository_files(client: TestClient, test_user: User, monkeypatch):
    token = create_access_token(test_user.id, test_user.role)

    mock_runner = MagicMock(spec=DockerCodeRunner)
    mock_runner.run_repository.return_value = ExecutionResult(
        stdout="Calculated: 42\n",
        stderr="",
        exit_code=0,
        execution_time=0.15,
        memory_used=14.0,
    )
    from app.routers import execution
    monkeypatch.setattr(execution, "execution_service", ExecutionService(runner=mock_runner))

    res = client.post(
        "/api/execution/run/",
        json={
            "files": {
                "app/calculator.py": "def add(a, b): return a + b\nprint('Calculated:', add(20, 22))"
            },
            "entrypoint": "app/calculator.py",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["stdout"] == "Calculated: 42\n"
    assert data["exit_code"] == 0


def test_docker_runner_run_repository_rejects_path_traversal():
    runner = DockerCodeRunner()
    # Path traversal in file keys
    result = runner.run_repository(
        files={"../secret.py": "print('exploit')", "main.py": "print('ok')"},
        entrypoint="main.py",
    )
    assert result.exit_code == 1
    assert "Security error" in result.stderr

