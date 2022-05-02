from _pytest.pytester import RunResult


def run(pytester, *args):
    return pytester.runpytest("--metrics", *args)


class TestPrometheus:
    def test_all(self, pytester, set_env):
        """
            # HELP job_test_info Info test
            # TYPE job_test_info gauge
            job_test_info{detail="Passed=2 Failed=1 Skipped=1 Error=2",status="failed"} 1.0
            # HELP job_test_passed Number of passed tests
            # TYPE job_test_passed gauge
            job_test_passed{testname="job_test_test_pass"} 1.0
            job_test_passed{testname="job_test_test_error_teardown"} 1.0
            # HELP job_test_failed Number of failed tests
            # TYPE job_test_failed gauge
            job_test_failed{testname="job_test_test_fail"} 1.0
            # HELP job_test_error Number of errors tests
            # TYPE job_test_error gauge
            job_test_error{testname="job_test_test_error_setup"} 1.0
            job_test_error{testname="job_test_test_error_teardown"} 1.0
        """
        pytester.makepyfile(
            """
            import pytest
            def test_pass():
                pass
            def test_fail():
                assert False
            @pytest.mark.skip(reason="for testing")
            def test_skip():
                pass
            @pytest.fixture
            def fix_setup():
                raise Exception("for testing")
            def test_error_setup(fix_setup):
                pass
            @pytest.fixture
            def fix_teardown():
                yield
                raise Exception("for testing")
            def test_error_teardown(fix_teardown):
                pass
            """
        )
        result: RunResult = run(pytester)
        assert result.ret == result.ret.TESTS_FAILED
        assert "metrics sent on Prometheus PushGateway" in result.stdout.str()

    def test_2_fail(self, pytester, set_env):
        """
            # HELP job_test_info Info test
            # TYPE job_test_info gauge
            job_test_info{detail="Passed=2 Failed=2 Skipped=0 Error=0",status="failed"} 1.0
            # HELP job_test_passed Number of passed tests
            # TYPE job_test_passed gauge
            job_test_passed{testname="job_test_test_pass_1"} 1.0
            job_test_passed{testname="job_test_test_pass_2"} 1.0
            # HELP job_test_failed Number of failed tests
            # TYPE job_test_failed gauge
            job_test_failed{testname="job_test_test_fail_1"} 1.0
            job_test_failed{testname="job_test_test_fail_2"} 1.0
            # HELP job_test_error Number of errors tests
            # TYPE job_test_error gauge
        """
        pytester.makepyfile(
            """
            import pytest
            def test_pass_1():
                pass
            def test_pass_2():
                pass
            def test_fail_1():
                assert False
            def test_fail_2():
                assert False
            """
        )
        result: RunResult = run(pytester)
        assert result.ret == result.ret.TESTS_FAILED
        assert "metrics sent on Prometheus PushGateway" in result.stdout.str()

    def test_pass_with_extra_labels(self, pytester, set_extra_labels):
        pytester.makepyfile("def test_pass(): pass")
        result: RunResult = run(pytester)
        assert result.ret == result.ret.OK
        assert "metrics sent on Prometheus PushGateway" in result.stdout.str()

    def test_no_config(self, pytester):
        pytester.makepyfile("def test_no_config(): pass")
        result: RunResult = run(pytester)
        assert result.ret == result.ret.INTERNAL_ERROR

    def test_pass_hook(self, pytester, set_extra_labels):
        """
            # HELP job_test_info Info test
            # TYPE job_test_info gauge
            job_test_info{detail="Passed=1 Failed=0 Skipped=0 Error=0",html_report="report_url",status="succeeded",test="value",test1="value1"} 1.0
            # HELP job_test_passed Number of passed tests
            # TYPE job_test_passed gauge
            job_test_passed{test="value",test1="value1",testname="job_test_test_pass"} 1.0
            # HELP job_test_failed Number of failed tests
            # TYPE job_test_failed gauge
            # HELP job_test_error Number of errors tests
            # TYPE job_test_error gauge
        """
        pytester.makepyfile("def test_pass(): pass")
        # create a temporary conftest.py file
        pytester.makeconftest(
            """
                def pytest_metrics_add_labels(session, exitstatus) -> str:
                    return {"html_report": "report_url"}
        """
        )
        result: RunResult = run(pytester)
        assert result.ret == result.ret.OK
        assert "metrics sent on Prometheus PushGateway" in result.stdout.str()
