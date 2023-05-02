import pytest
import sys

from infra.tools.redmine.redmine_api import is_redmine_issue_active
sys.path.append('/devts/tests/skynet')
from system.test_cpu_ram_hdd_usage import do_cpu_usage_test, do_ram_usage_test, do_hdd_usage_test  # noqa

partitions_and_expected_usage = [{'partition': '/', 'max_usage': 9000}, {'partition': '/var/log/', 'max_usage': 500}]


@pytest.fixture()
def skip_test_ram_usage_on_asan(topology_obj):
    """
    Fixture that skips test execution in case setup is running ASAN image
    """
    if topology_obj.players['dut']['sanitizer']:
        pytest.skip("Skipping execution of test on ASAN image because image "
                    "consumes more RAM then usually expected on dut")


class TestCpuRamHddUsage:

    @pytest.fixture(autouse=True)
    def setup(self, engines):
        self.dut_engine = engines.dut

    @pytest.mark.parametrize('partition_usage', partitions_and_expected_usage)
    def test_hdd_usage(self, partition_usage):
        """
        This tests checks HDD usage in specific partition
        Test doing "df {partition}" and then check usage and compare with expected usage from test parameters
        :param partition_usage: dictionary with partition name and expected usage: {'partition': '/', 'max_usage': 6000}
        """
        if is_redmine_issue_active([3454585]):
            if partition_usage['partition'] == '/var/log/':
                partition_usage['max_usage'] = 1000

        do_hdd_usage_test(self.dut_engine, partition_usage)

    @pytest.mark.build
    @pytest.mark.push_gate
    def test_cpu_usage(self, request, expected_cpu_usage_dict):
        """
        This tests checks CPU usage - total and per process
        Test doing command "top" - then parse output and check total cpu usage
        Also from "top" output test case find CPU usage for specific process
        If total CPU usage or by process CPU usage is bigger than expected - raise exception
        :param request: pytest build-in
        :param expected_cpu_usage_dict: expected_cpu_usage_dict fixture
        """
        do_cpu_usage_test(request.node.originalname, self.dut_engine, expected_cpu_usage_dict)

    @pytest.mark.build
    @pytest.mark.push_gate
    def test_ram_usage(self, request, expected_ram_usage_dict, skip_test_ram_usage_on_asan):
        """
        This tests checks RAM usage - total and per process
        Test doing command "top" - then parse output and check from it PIDs for running processes
        Then test doing command "free" and parse total RAM usage
        After it test check RAM usage by process using command:
        sudo cat /proc/{PID}/smaps | grep Pss | awk '{Total+=$2} END {print Total/1024}
        If total RAM usage or by process RAM usage is bigger than expected - raise exception
        :param request: pytest build-in
        :param expected_ram_usage_dict: expected_ram_usage_dict fixture
        """
        do_ram_usage_test(request.node.originalname, self.dut_engine, expected_ram_usage_dict)
