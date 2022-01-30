import os

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture
def set_env():
    os.environ["PROMETHEUS_PUSHGATEWAY_URL"] = "https://enm1n5rid50yi.x.pipedream.net/"
    os.environ["PROMETHEUS_PUSHGATEWAY_JOB"] = "job"
    yield
    del os.environ["PROMETHEUS_PUSHGATEWAY_URL"]
    del os.environ["PROMETHEUS_PUSHGATEWAY_JOB"]

@pytest.fixture
def set_extra_labels(set_env):
    os.environ["PROMETHEUS_PUSHGATEWAY_EXTRA_LABEL"] = "{'test':'value','test1':'value1'}"
    yield
    del os.environ["PROMETHEUS_PUSHGATEWAY_EXTRA_LABEL"]
