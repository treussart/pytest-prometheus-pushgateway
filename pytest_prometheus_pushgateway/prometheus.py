import json
import logging
import os
import re
from typing import Union

import pytest
from _pytest.config import Config, ExitCode
from _pytest.main import Session
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Info
from prometheus_client.exposition import basic_auth_handler


log = logging.getLogger(__name__)


def my_auth_handler(url, method, timeout, headers, data):
    username = os.environ.get("PROMETHEUS_PUSHGATEWAY_USERNAME")
    password = os.environ.get("PROMETHEUS_PUSHGATEWAY_PASSWORD")
    return basic_auth_handler(url, method, timeout, headers, data, username, password)


class PrometheusReport:
    def __init__(self, config: Config):
        self.config = config
        self.pushgateway_url = os.environ.get("PROMETHEUS_PUSHGATEWAY_URL")
        self.job_name = os.environ.get("PROMETHEUS_PUSHGATEWAY_JOB")
        self.prefix = self._get_prefix()
        self.extra_labels = self._get_extra_labels()
        self.registry = CollectorRegistry()
        self.passed = []
        self.failed = []
        self.skipped = []
        self.errors = []

    @staticmethod
    def _get_prefix() -> str:
        prefix = os.environ.get("PROMETHEUS_PUSHGATEWAY_METRIC_PREFIX")
        if prefix:
            return prefix
        return f"{os.environ.get('PROMETHEUS_PUSHGATEWAY_JOB')}_"

    @staticmethod
    def _get_extra_labels() -> dict:
        labels = os.environ.get("PROMETHEUS_PUSHGATEWAY_EXTRA_LABEL")
        if labels:
            try:
                return json.loads(labels.replace("'", '"'))
            except:
                return {}
        return {}

    @staticmethod
    def _format_detail(
        stats: dict,
    ) -> str:
        return (
            f"Passed={len(stats.get('passed', []))} Failed={len(stats.get('failed', []))} "
            f"Skipped={len(stats.get('skipped', []))} Error={len(stats.get('error', []))}"
        )

    def _make_metric_name(self, name: str) -> str:
        unsanitized_name = "{prefix}{name}".format(prefix=self.prefix, name=name)
        # Valid names can only contain these characters, replace all others with _
        # https://prometheus.io/docs/concepts/data_model/#metric-names-and-labels
        pattern = r"[^a-zA-Z0-9_]"
        replacement = "_"
        return re.sub(pattern, replacement, unsanitized_name)

    def _make_labels(self, test_name: str) -> dict:
        ret = self.extra_labels.copy()
        ret["testname"] = test_name
        return ret

    def _get_label_names(self):
        return self._make_labels("").keys()

    def add_metrics_for_tests(self, metric: Gauge, test_names: list):
        for test_name in test_names:
            labels = self._make_labels(test_name)
            metric.labels(**labels).inc()

    def pytest_runtest_logreport(self, report: TestReport):
        # https://docs.pytest.org/en/latest/reference.html#_pytest.runner.TestReport.when
        # 'call' is the phase when the test is being ran
        if report.when == "call":
            funcname = report.location[2]
            name = self._make_metric_name(funcname)

            if report.outcome == "passed":
                self.passed.append(name)
            elif report.outcome == "skipped":
                self.skipped.append(name)
            elif report.outcome == "failed":
                self.failed.append(name)
            elif report.outcome == "errors":
                self.errors.append(name)

    def send_metrics(self, session: Session, exitstatus: Union[int, ExitCode]):
        status = "succeeded"
        if exitstatus != 0:
            status = "failed"
        reporter: TerminalReporter = session.config.pluginmanager.get_plugin(
            "terminalreporter"
        )
        default_labels = {
            "status": status,
            "detail": self._format_detail(reporter.stats),
        }
        default_labels.update(self.extra_labels)
        added_labels = session.config.hook.pytest_metrics_add_labels(
            session=session, exitstatus=exitstatus
        )
        if added_labels:
            labels = {**added_labels[0], **default_labels}
        else:
            labels = default_labels
        i = Info(
            os.environ.get("PROMETHEUS_PUSHGATEWAY_JOB"),
            "Info test",
            registry=self.registry,
        )
        i.info(labels)

        passed_metric = Gauge(
            self._make_metric_name("passed"),
            "Number of passed tests",
            labelnames=self._get_label_names(),
            registry=self.registry,
        )
        self.add_metrics_for_tests(passed_metric, self.passed)

        failed_metric = Gauge(
            self._make_metric_name("failed"),
            "Number of failed tests",
            labelnames=self._get_label_names(),
            registry=self.registry,
        )
        self.add_metrics_for_tests(failed_metric, self.failed)

        skipped_metric = Gauge(
            self._make_metric_name("skipped"),
            "Number of skipped tests",
            labelnames=self._get_label_names(),
            registry=self.registry,
        )
        self.add_metrics_for_tests(skipped_metric, self.skipped)

        error_metric = Gauge(
            self._make_metric_name("error"),
            "Number of errors tests",
            labelnames=self._get_label_names(),
            registry=self.registry,
        )
        self.add_metrics_for_tests(error_metric, self.errors)

        try:
            if os.environ.get("PROMETHEUS_PUSHGATEWAY_BASIC_AUTH"):
                push_to_gateway(
                    self.pushgateway_url,
                    registry=self.registry,
                    job=self.job_name,
                    handler=my_auth_handler,
                )
            else:
                push_to_gateway(
                    self.pushgateway_url, registry=self.registry, job=self.job_name
                )
        except Exception as e:
            log.error(
                f"push_to_gateway error: {self.pushgateway_url} - {e}"
            )

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: Session, exitstatus: Union[int, ExitCode]):
        try:
            self.send_metrics(session, exitstatus)
        except Exception as e:
            log.error(
                f"Prometheus send_metrics error: {self.pushgateway_url} - {e}"
            )

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(
        self,
        terminalreporter: TerminalReporter,
        exitstatus: Union[int, ExitCode],
        config: Config,
    ):
        terminalreporter.write_sep(
            "-", f"metrics sent on Prometheus PushGateway at {self.pushgateway_url}"
        )
