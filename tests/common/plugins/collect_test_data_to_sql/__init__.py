import re
import os
import pytest
import logging
import json

from ngts.tools.mars_test_cases_results.Connect_to_MSSQL import ConnectMSSQL
from ngts.constants.constants import DbConstants, CliType, RebootTestConstants

logger = logging.getLogger()


@pytest.fixture(autouse=True)
def collect_tests_data_to_sql(request):

    pytest_node_ids_which_should_be_collected = {
        'tests/push_build_tests/system/test_reboot_reload.py::test_push_gate_reboot_policer': NgtsPushGateRebootLossTimeCollector,
        'tests/push_build_tests/system/test_cpu_ram_hdd_usage.py::TestCpuRamHddUsage::test_cpu_usage': NgtsCpuRamUsageCollector,
        'tests/push_build_tests/system/test_cpu_ram_hdd_usage.py::TestCpuRamHddUsage::test_ram_usage': NgtsCpuRamUsageCollector,
        'platform_tests/test_advanced_reboot.py::test_fast_reboot': AdvancedRebootCollector,
        'platform_tests/test_advanced_reboot.py::test_warm_reboot': AdvancedRebootCollector
    }

    yield

    for test_prefix in pytest_node_ids_which_should_be_collected.keys():
        if test_prefix in request.node.nodeid:
            try:
                data_collector = pytest_node_ids_which_should_be_collected[test_prefix](request)
                data_collector.update_database_with_test_results()
            except Exception as err:
                logger.error('Unable to upload test: %s results to SQL DB. Got error: %s', request.node.nodeid, err)
            break


class SonicDataCollector(object):
    """
    Basic class from which all other collector classes will be inherited
    """

    def __init__(self, request):

        self.request = request
        self.test_name = self.request.node.nodeid
        self.is_canonical_setup = hasattr(self.request.config.option, 'setup_name')
        connections_params = DbConstants.CREDENTIALS[CliType.SONIC]
        self.mssql_connection_obj = ConnectMSSQL(connections_params['server'], connections_params['database'],
                                                 connections_params['username'], connections_params['password'])
        self.mssql_connection_obj.connect_db()

        self.setup_name = None
        self.topology = None
        self.dut_engine = None
        self.sonic_branch = None
        self.sonic_version = None
        self.hwsku = None
        self.get_general_setup_info()
        self.get_dut_engine()
        self.get_sonic_image_info()
        self.setup_extra_info = json.dumps({'hwsku': self.hwsku})
        self.test_data = None

    def get_dut_engine(self):
        if self.is_canonical_setup:
            self.dut_engine = self.request.getfixturevalue('engines')['dut']
        else:
            self.dut_engine = self.request.getfixturevalue('duthost')

    def get_sonic_image_info(self):
        if self.is_canonical_setup:
            self.sonic_branch = self.request.getfixturevalue('sonic_branch')
            self.sonic_version = self.request.getfixturevalue('sonic_version')
            self.hwsku = self.request.getfixturevalue('platform_params').hwsku
        else:
            self.sonic_branch = self.dut_engine.sonic_release
            self.sonic_version = self.dut_engine.os_version
            self.hwsku = self.dut_engine.facts['hwsku']

    def get_general_setup_info(self):
        if self.is_canonical_setup:
            self.setup_name = self.request.config.option.setup_name
            self.topology = 'ptf-any'
        else:
            self.setup_name = self.request.config.option.ansible_host_pattern
            testbed = self.request.config.option.testbed
            self.topology = testbed.split(self.setup_name)[-1].lstrip('-')  # example: get t0 from: 'arc-switch1004-t0'

    def update_database_with_test_results(self):

        self.get_test_results()

        if self.test_data:
            test_results = {'TestName': self.test_name,
                            'DUTImageVersion': self.sonic_version, 'DUTImageBranch': self.sonic_branch,
                            'Topology': self.topology, 'SetupName': self.setup_name,
                            'ExtraInfo': self.setup_extra_info, 'TestData': self.test_data}
            logger.info('Going to upload to SQL DB next data: \n{}\n'.format(test_results))

            insert_querry = 'INSERT INTO [dbo].[{}]'.format('test_results')
            insert_querry += '([Date], [TestName], [DUTImageVersion], [DUTImageBranch], [Topology], [SetupName], [SetupExtraInfo], [TestData]) '
            insert_querry += "VALUES (GETDATE(), '{TestName}', '{DUTImageVersion}', '{DUTImageBranch}', '{Topology}', '{SetupName}', '{SetupExtraInfo}', '{TestData}')".format(
                TestName=self.test_name, DUTImageVersion=self.sonic_version,
                DUTImageBranch=self.sonic_branch, Topology=self.topology, SetupName=self.setup_name,
                SetupExtraInfo=self.setup_extra_info, TestData=self.test_data)

            self.mssql_connection_obj.query_insert(insert_querry)
        else:
            logger.warning('Can not get test data to upload into SQL database')

    def get_test_results(self):
        raise NotImplementedError('This method must be implemented in child class')


class NgtsPushGateRebootLossTimeCollector(SonicDataCollector):
    """
    Class which collects dataplane and controlplane loss for NGTS PushGate reboot test case
    """

    def __init__(self, request):
        super(NgtsPushGateRebootLossTimeCollector, self).__init__(request)

    def get_test_results(self):
        reboot_result_dict = {}
        validation_type = self.request.node.funcargs['validation_type']
        self.test_name = '{}[{}]'.format(self.test_name, validation_type)

        with open(RebootTestConstants.DATAPLANE_TRAFFIC_RESULTS_FILE) as dataplane:
            dataplane_results = json.load(dataplane)
            reboot_result_dict['dataplane'] = dataplane_results['actual_traffic_loss_time']

        with open(RebootTestConstants.CONTROLPLANE_TRAFFIC_RESULTS_FILE) as controlplane:
            controlplane_results = json.load(controlplane)
            reboot_result_dict['controlplane'] = controlplane_results['actual_traffic_loss_time']

        if reboot_result_dict:
            self.test_data = json.dumps(reboot_result_dict)


class NgtsCpuRamUsageCollector(SonicDataCollector):
    """
    Class which collects CPU/RAM usage for NGTS PushGate CPU/RAM usage test cases
    """

    def __init__(self, request):
        super(NgtsCpuRamUsageCollector, self).__init__(request)

    def get_test_results(self):

        test_report_filename = os.path.join('/tmp/', self.request.node.originalname)
        with open(test_report_filename) as test_report_file_obj:
            test_report_dict = json.load(test_report_file_obj)
            self.test_data = json.dumps(test_report_dict)


class AdvancedRebootCollector(SonicDataCollector):
    """
    Class which collects dataplane and controlplane loss for community AdvancedReboot reboot test case
    """

    def __init__(self, request):
        super(AdvancedRebootCollector, self).__init__(request)

        self.supported_tests_by_collector = ['platform_tests/test_advanced_reboot.py::test_fast_reboot',
                                             'platform_tests/test_advanced_reboot.py::test_warm_reboot']

        self.test_name = self.test_name.split('[')[0]  # Remove hostname ...boot.py::test_fast_reboot[arc-switch1004]
        self.ptfhost_engine = self.request.getfixturevalue('ptfhost')

    def get_test_results(self):

        if self.test_name not in self.supported_tests_by_collector:
            logger.info('Collecting test data not supported for test case: %s', self.test_name)
            return

        ptf_test_log_path = '/tmp/fast-reboot-report.json'
        if 'test_warm_reboot' in self.test_name:
            ptf_test_log_path = '/tmp/warm-reboot-report.json'

        try:
            ptf_test_report = self.ptfhost_engine.shell('cat {}'.format(ptf_test_log_path))['stdout']
            ptf_test_report_dict = json.loads(ptf_test_report)
            dataplane_downtime = ptf_test_report_dict['dataplane']['downtime']
            # Control plane downtime not available for fast-reboot tests(value empty), only available for warm-reboot
            controlplane_downtime = ptf_test_report_dict['controlplane']['downtime']

            self.test_data = json.dumps({'dataplane': dataplane_downtime, 'controlplane': controlplane_downtime})

        except Exception as err:
            logger.error('Can not get data/control plane loss for test: {}. Got err: {}'.format(self.test_name, err))
