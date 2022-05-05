import os

from _pytest.config import Config, PytestPluginManager
from _pytest.config.argparsing import Parser

from pytest_prometheus_pushgateway.prometheus import PrometheusReport, get_auth


def pytest_addhooks(pluginmanager: PytestPluginManager):
    from . import hooks

    pluginmanager.add_hookspecs(hooks)


def pytest_addoption(parser: Parser):
    parser.addoption(
        "--metrics",
        action="store_true",
        help="Send metrics over Prometheus PushGateway",
    )


def pytest_configure(config: Config):
    if config.getoption("--metrics") and not hasattr(config, "workerinput"):
        if not os.environ.get("PROMETHEUS_PUSHGATEWAY_URL") or not os.environ.get(
            "PROMETHEUS_PUSHGATEWAY_JOB"
        ):
            raise Exception(
                "You must set the environment variables for Prometheus PushGateway plugin"
            )
        if get_auth() and (
            not os.environ.get("PROMETHEUS_PUSHGATEWAY_USERNAME")
            or not os.environ.get("PROMETHEUS_PUSHGATEWAY_PASSWORD")
        ):
            raise Exception(
                "You must set the auth environment variables for Prometheus PushGateway plugin"
            )
        config._prometheus = PrometheusReport(config)
        config.pluginmanager.register(config._prometheus)


def pytest_unconfigure(config: Config):
    prometheus = getattr(config, "_prometheus", None)
    if prometheus:
        del config._prometheus
        config.pluginmanager.unregister(prometheus)
