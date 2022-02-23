# pytest-prometheus-pushgateway

Pytest report plugin for [Prometheus PushGateway](https://github.com/prometheus/pushgateway)

Allow to send reports test results to a Prometheus PushGateway.

## installation

    pip install pytest-prometheus-pushgateway

## Configure via env var

    PROMETHEUS_PUSHGATEWAY_URL=""
    PROMETHEUS_PUSHGATEWAY_JOB=""

Basic Auth:

    PROMETHEUS_PUSHGATEWAY_BASIC_AUTH="true"
    PROMETHEUS_PUSHGATEWAY_USERNAME=""
    PROMETHEUS_PUSHGATEWAY_PASSWORD=""

Optional:

    PROMETHEUS_PUSHGATEWAY_METRIC_PREFIX=""
    PROMETHEUS_PUSHGATEWAY_EXTRA_LABEL="{'test':'value','test1':'value1'}"

## Add labels via hook

    def pytest_metrics_add_labels(session: Session, exitstatus: Union[int, ExitCode]) -> str:
        return {"html_report": report_url}

## Add option to send metrics

    pytest --metrics

## Dev

### Change version

edit

    pytest_prometheus_pushgateway/__init__.py

commit

    git commit -m "v0.1.0"

tag

    git tag v0.1.0

### Build package

    python -m build
    twine upload dist/*

### Test

Create endpoint on [requestbin](https://requestbin.com/)
and add the url to PROMETHEUS_PUSHGATEWAY_URL to set_env fixture into conftest.py

Use the runner in Pycharm.

    pytest test_pytest_prometheus.py::TestPrometheus
