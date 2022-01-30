from typing import Union

from _pytest.config import ExitCode
from _pytest.main import Session


def pytest_metrics_add_labels(
    session: Session, exitstatus: Union[int, ExitCode]
) -> dict:
    """Called to add labels to metrics"""
