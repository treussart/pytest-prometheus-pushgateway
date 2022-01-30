from _pytest.config import ExitCode
from _pytest.pytester import RunResult


def run(pytester, *args):
    return pytester.runpytest("--metrics", *args)


class TestPrometheus:
    def test_pass(self, pytester, set_env):
        pytester.makepyfile("def test_pass(): pass")
        result: RunResult = run(pytester)
        assert result.ret == 0
        assert "metrics sent on Prometheus PushGateway" in result.stdout.str()

    def test_pass_with_extra_labels(self, pytester, set_extra_labels):
        pytester.makepyfile("def test_pass(): pass")
        result: RunResult = run(pytester)
        assert result.ret == 0
        assert "metrics sent on Prometheus PushGateway" in result.stdout.str()

    def test_no_config(self, pytester):
        pytester.makepyfile("def test_no_config(): pass")
        result: RunResult = run(pytester)
        assert result.ret == ExitCode.INTERNAL_ERROR

    def test_pass_hook(self, pytester, set_extra_labels):
        pytester.makepyfile("def test_pass(): pass")
        # create a temporary conftest.py file
        pytester.makeconftest(
            """
                def pytest_metrics_add_labels(session, exitstatus) -> str:
                    return {"html_report": "report_url"}
        """
        )
        result: RunResult = run(pytester)
        assert result.ret == 0
        assert "metrics sent on Prometheus PushGateway" in result.stdout.str()
