from celery import shared_task


@shared_task(name="test_celery_task")
def test_celery_task(a: int, b: int) -> int:
    """A simple test task that adds two numbers together."""
    return a + b
