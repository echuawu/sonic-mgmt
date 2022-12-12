import logging
import pytest
import re
import time
import json
import os

from ngts.constants.constants import SonicConst

ALLOWED_DEVIATION = 0.05

logger = logging.getLogger()

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
    def setup(self, testdir, topology_obj, engines, platform_params, sonic_version):
        self.topology_obj = topology_obj
        self.dut_engine = engines.dut
        self.current_test_folder = testdir.request.fspath.dirname
        self.processes_list = SonicConst.CPU_RAM_CHECK_PROCESS_LIST
        self.platform_params = platform_params
        platform_index = 1
        self.platform = self.platform_params.hwsku.split('-')[platform_index]
        self.setup_name = platform_params.setup_name
        self.sonic_ver = sonic_version

    @pytest.mark.parametrize('partition_usage', partitions_and_expected_usage)
    def test_hdd_usage(self, partition_usage):
        """
        This tests checks HDD usage in specific partition
        Test doing "df {partition}" and then check usage and compare with expected usage from test parameters
        :param partition_usage: dictionary with partition name and expected usage: {'partition': '/', 'max_usage': 6000}
        """
        total_size, used_size, available_size = get_partition_disk_usage(self.dut_engine, partition_usage['partition'])
        max_usage = partition_usage['max_usage']

        try:
            assert used_size < max_usage, 'Used disk size: {} is more than expected: {}'.format(used_size, max_usage)

        except Exception as err:
            raise AssertionError(err)

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
        timeout_between_attempts = 5
        total_cpu_usage = 0
        cpu_usage_per_process = {}
        try:
            assertions_list = []
            for attempt in range(10):
                logger.info('Checking CPU utilization, attempt number: {}'.format(attempt))
                assertions_list = []
                total_cpu_usage, cpu_usage_per_process_dict = get_cpu_usage_and_processes(self.dut_engine)
                logger.info(f'DUT use: {total_cpu_usage} % of CPU')
                # CPU usage is integer and in %
                if total_cpu_usage > expected_cpu_usage_dict['total'] * (1 + ALLOWED_DEVIATION):
                    assertions_list.append({'total': total_cpu_usage})
                for process in self.processes_list:
                    try:
                        proc_cpu_usage = cpu_usage_per_process_dict[process]['cpu_usage']
                        cpu_usage_per_process[process] = proc_cpu_usage
                        logger.info(f'Process: {process} use {proc_cpu_usage} % of CPU')
                        if cpu_usage_per_process_dict[process]['cpu_usage'] > \
                                expected_cpu_usage_dict[process] * (1 + ALLOWED_DEVIATION):
                            assertions_list.append({process: cpu_usage_per_process_dict[process]['cpu_usage']})
                    except KeyError:
                        cpu_usage_per_process[process] = 0
                        logger.error('Can not find CPU usage for process: {} - process is not running'.format(process))
                if not assertions_list:
                    break
                else:
                    time.sleep(timeout_between_attempts)
            assert not assertions_list, 'CPU usage: {} \n is more than expected: \n {}'.format(assertions_list,
                                                                                               expected_cpu_usage_dict)

        except Exception as err:
            raise AssertionError(err)
        finally:
            cpu_usage_per_process.update({'total_cpu_usage': total_cpu_usage})
            store_results_into_file(filename=os.path.join('/tmp/', request.node.originalname),
                                    results_dict=cpu_usage_per_process)

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
        assertions_list = []
        total_ram_size_mb = 0
        used_ram_size_mb = 0
        ram_usage_per_process = {}
        try:
            _, cpu_usage_per_process_dict = get_cpu_usage_and_processes(self.dut_engine)

            for attempt in range(3):
                logger.info('Checking RAM utilization, attempt number: {}'.format(attempt))
                assertions_list = []
                free_output = self.dut_engine.run_cmd('sudo free')
                total_ram_size_mb = int(free_output.splitlines()[1].split()[1]) / 1024
                used_ram_size_mb = int(free_output.splitlines()[1].split()[2]) / 1024
                logger.info('DUT total RAM size: {} Mb'.format(total_ram_size_mb))
                logger.info('DUT use: {} Mb of RAM'.format(used_ram_size_mb))
                # RAM usage is integer and in Mb
                if used_ram_size_mb > expected_ram_usage_dict['total'] * (1 + ALLOWED_DEVIATION):
                    assertions_list.append({'total': used_ram_size_mb})
                for process in self.processes_list:
                    try:
                        process_pid = cpu_usage_per_process_dict[process]['pid']
                        cat_smaps_cmd = "sudo cat /proc/{}/smaps".format(process_pid)
                        get_ram_usage_cmd = cat_smaps_cmd + "| grep Pss | awk '{Total+=$2} END {print Total/1024}'"
                        used_ram_mb = float(self.dut_engine.run_cmd(get_ram_usage_cmd))
                        logger.info('Process: {} used {} Mb of RAM'.format(process, used_ram_mb))
                        ram_usage_per_process[process] = used_ram_mb
                        if used_ram_mb > expected_ram_usage_dict[process] * (1 + ALLOWED_DEVIATION):
                            assertions_list.append({process: used_ram_mb})
                    except KeyError:
                        ram_usage_per_process[process] = 0
                        logger.error('Can not find RAM usage for process: {} - process is not running'.format(process))
                if not assertions_list:
                    break

            assert not assertions_list, \
                'RAM usage: {} \n is more than expected: \n {}'.format(assertions_list, expected_ram_usage_dict)

        except Exception as err:
            raise AssertionError(err)
        finally:
            ram_usage_per_process.update({'total_ram_size': total_ram_size_mb, 'total_used_ram_size': used_ram_size_mb})
            store_results_into_file(filename=os.path.join('/tmp/', request.node.originalname),
                                    results_dict=ram_usage_per_process)


def get_cpu_usage_and_processes(dut_engine):
    processes_data_start_index = 1
    pid_index = 0
    proc_name_index = -1
    cpu_usage_index = 8
    user_usage_group = 1
    kernel_usage_group = 2
    cpu_usage_line_index = 2
    processes_index = -1
    headers_index = -2

    top_cmd = 'sudo top -b -d 1 -n 2'
    top_cmd_output = dut_engine.run_cmd(top_cmd)
    top_cmd_output_splited_by_empty_line = top_cmd_output.split('\n\n')
    headers = top_cmd_output_splited_by_empty_line[headers_index].splitlines()
    processes = top_cmd_output_splited_by_empty_line[processes_index].splitlines()

    cpu_usage_user_and_kernel = re.search(r'%Cpu\(s\):\s+(\d+.\d)\s+us,\s+(\d+.\d)', headers[cpu_usage_line_index])
    user_space_usage = cpu_usage_user_and_kernel.group(user_usage_group)
    kernel_space_usage = cpu_usage_user_and_kernel.group(kernel_usage_group)

    total_cpu_usage = float(user_space_usage) + float(kernel_space_usage)

    num_of_cores = get_num_of_cpu_cores(dut_engine)
    # parser for top
    # example: {'sx_sdk': {'pid': '10143', 'cpu_usage': '37.3'}, 'syncd': {'pid': '10092', 'cpu_usage': '6.9'}...
    usage_dict = {}
    for process in processes[processes_data_start_index:]:
        splited_line = process.split()
        pid = splited_line[pid_index]
        proc = splited_line[proc_name_index]
        cpu_us_by_process = float(splited_line[cpu_usage_index]) / num_of_cores  # top show it for 1 core
        usage_dict[proc] = {'pid': pid, 'cpu_usage': cpu_us_by_process}

    return total_cpu_usage, usage_dict


def get_num_of_cpu_cores(dut_engine):
    num_of_cores = len(dut_engine.run_cmd('sudo cat /proc/cpuinfo | grep processor').splitlines())
    return num_of_cores


def get_partition_disk_usage(dut_engine, partition):
    data_line_index = 1
    column_total_size_index = 1
    column_used_index = 2
    column_available_index = 3

    df_output = dut_engine.run_cmd('sudo df {}'.format(partition))
    total_size = df_output.splitlines()[data_line_index].split()[column_total_size_index]
    used_size = df_output.splitlines()[data_line_index].split()[column_used_index]
    available_size = df_output.splitlines()[data_line_index].split()[column_available_index]
    # convert all to Mb(by default it Kb)
    total_size_mb = int(total_size) / 1024
    used_size_mb = int(used_size) / 1024
    available_size_mb = int(available_size) / 1024

    return total_size_mb, used_size_mb, available_size_mb


def store_results_into_file(filename, results_dict):
    with open(filename, 'w') as test_report_file_obj:
        json.dump(results_dict, test_report_file_obj)
