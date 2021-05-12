import allure
import logging
import pytest
import os
import sys
import re
from retry.api import retry_call

from ngts.tools.skip_test.skip import ngts_skip
from ngts.helpers.run_process_on_host import run_process_on_host
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from ngts.constants.constants import PytestConst

logger = logging.getLogger()

validation_types = ['fast-reboot', 'warm-reboot', 'reboot', 'config reload -y']
expected_traffic_loss_dict = {'fast-reboot': {'data': 60, 'control': 90},
                              'warm-reboot': {'data': 0, 'control': 90},
                              'reboot': {'data': 180, 'control': 180},
                              'config reload -y': {'data': 180, 'control': 180}
                              }


class TestRebootReload:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, interfaces, engines):
        self.topology_obj = topology_obj
        self.dut_engine = engines.dut
        self.cli_object = self.topology_obj.players['dut']['cli']
        self.interfaces = interfaces
        self.ping_sender_iface = '{}.40'.format(self.interfaces.ha_dut_2)
        self.dut_vlan40_int_ip = '40.0.0.1'
        self.dut_port_channel_ip = '30.0.0.1'
        self.hb_vlan40_ip = '40.0.0.3'

    @pytest.fixture(autouse=True)
    def ignore_expected_loganalyzer_exceptions(self, loganalyzer):
        """
        expanding the ignore list of the loganalyzer for these tests because of reboot.
        :param loganalyzer: loganalyzer utility fixture
        :return: None
        """
        if loganalyzer:
            ignore_regex_list = loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                                   "..", "..", "..",
                                                                                   "tools", "loganalyzer", "reboot_loganalyzer_ignore.txt")))
            loganalyzer.ignore_regex.extend(ignore_regex_list)

    @pytest.mark.disable_loganalyzer
    @pytest.mark.ngts_skip({'platform_prefix_list': ['simx']})
    @pytest.mark.parametrize('validation_type', validation_types)
    def test_push_gate_reboot(self, request, platform_params, validation_type):
        """
        This tests checks reboot according to test parameter. Test checks data and control plane traffic loss time.
        After reboot/reload finished - test doing functional validations(run PushGate tests)
        :param request: pytest build-in
        :param platform_params: platform_params fixture
        :param validation_type: validation type - which will be executed
        """
        if validation_type == 'warm-reboot':
            # Issue below cause swss docker down state and portchannel iface in down state
            ngts_skip(platform_params.platform, rm_ticket_list=[2637874])

        allowed_data_loss_time = expected_traffic_loss_dict[validation_type]['data']
        allowed_control_loss_time = expected_traffic_loss_dict[validation_type]['control']
        failed_validations = {}

        # Step below required, if no ARP for 30.0.0.2 warm/fast reboot will not work
        with allure.step('Resolve ARP on DUT for IP 30.0.0.2'):
            self.resolve_arp_static_route()

        with allure.step('Starting background validation for control plane traffic'):
            control_plane_checker = self.start_control_plane_validation(validation_type, allowed_control_loss_time)

        with allure.step('Starting background validation for data plane traffic'):
            data_plane_checker = self.start_data_plane_validation(validation_type, allowed_data_loss_time)

        self.do_reboot_or_reload_action(action=validation_type)

        try:
            with allure.step('Checking control plane traffic loss'):
                logger.info('Checking that control plane traffic loss not more '
                            'than: {}'.format(allowed_control_loss_time))
                control_plane_checker.complete_validation()
        except Exception as err:
            failed_validations['control_plane'] = err

        try:
            with allure.step('Checking data plane traffic loss'):
                logger.info('Checking that data plane traffic loss not more than: {}'.format(allowed_data_loss_time))
                data_plane_checker.complete_validation()
        except Exception as err:
            failed_validations['data_plane'] = err

        # Wait until warm-reboot finished
        if validation_type == 'warm-reboot':
            with allure.step('Checking warm-reboot status'):
                retry_call(SonicGeneralCli.check_warm_reboot_status, fargs=[self.dut_engine, 'inactive'], tries=24,
                           delay=10, logger=logger)

        # Step below required - to check that PortChannel0001 iface are UP
        with allure.step('Checking that possible to ping PortChannel iface 30.0.0.1'):
            self.resolve_arp_static_route()

        try:
            with allure.step('Running functional validations after reboot/reload'):
                logger.info('Running functional validations after reboot/reload')
                self.do_func_validations(request)
        except Exception as err:
            failed_validations['functional_validation'] = err
        finally:
            # Disconnect engine, otherwise the following error will pop-up "OSError: Socket is closed"
            self.dut_engine.disconnect()

        assert not failed_validations, 'We have failed validations during test run. ' \
                                       'Test result errors dict: {}'.format(failed_validations)

    def resolve_arp_static_route(self):
        validation = {'sender': 'ha', 'args': {'iface': 'bond0', 'count': 3, 'dst': self.dut_port_channel_ip}}
        ping_checker = PingChecker(self.topology_obj.players, validation)
        logger.info('Sending 3 ping packets to {}'.format(self.dut_port_channel_ip))
        retry_call(ping_checker.run_validation, fargs=[], tries=12, delay=10, logger=logger)

    def start_control_plane_validation(self, validation_type, allowed_control_loss_time):
        validation_control_plane = {'sender': 'ha',
                                    'name': 'control_plane_{}'.format(validation_type),
                                    'background': 'start',
                                    'args': {'interface': self.ping_sender_iface,
                                             'count': 200, 'dst': self.dut_vlan40_int_ip,
                                             'allowed_traffic_loss_time': allowed_control_loss_time},
                                    }
        control_plane_checker = PingChecker(self.topology_obj.players, validation_control_plane)
        logger.info('Starting background validation for control plane traffic')
        control_plane_checker.run_background_validation()
        return control_plane_checker

    def start_data_plane_validation(self, validation_type, allowed_data_loss_time):
        # Here we will send 1k pps - it allow to check traffic loss less than 1 second
        validation_data_plane = {'sender': 'ha',
                                 'name': 'data_plane_{}'.format(validation_type),
                                 'background': 'start',
                                 'args': {'interface': self.ping_sender_iface,
                                          'count': 200000, 'dst': self.hb_vlan40_ip,
                                          'interval': 0.001,
                                          'allowed_traffic_loss_time': allowed_data_loss_time}}
        data_plane_checker = PingChecker(self.topology_obj.players, validation_data_plane)
        logger.info('Starting background validation for data plane traffic')
        data_plane_checker.run_background_validation()
        return data_plane_checker

    def do_reboot_or_reload_action(self, action):
        if 'reload' in action:
            with allure.step('Reloading the DUT config using cmd: "config reload -y"'):
                self.cli_object.general.reload_configuration(self.dut_engine)
            self.cli_object.general.verify_dockers_are_up(self.dut_engine)
            self.cli_object.general.check_link_state(self.dut_engine, ifaces=self.topology_obj.players_all_ports['dut'])
        else:
            with allure.step('Rebooting the DUT using reboot cmd: "sudo {}"'.format(action)):
                self.cli_object.general.reboot_flow(self.dut_engine, reboot_type=action, topology_obj=self.topology_obj,
                                                    wait_after_ping=0)

    @staticmethod
    def do_func_validations(request):
        pytest_args_list = list(request.config.invocation_params.args)
        pytest_run_cmd = prepare_pytest_args(pytest_args_list)
        out, err, rc = run_process_on_host(pytest_run_cmd, timeout=1500)
        generate_report(out, err)
        if rc:
            raise AssertionError('Functional validation failed, please check logs')


def prepare_pytest_args(pytest_args_list):
    """
    This method prepare pytest run command with arguments
    :param pytest_args_list: list with pytest arguments
    :return: pytest run cmd
    """
    pytest_args_list = add_to_pytest_args_skip_reboot_reload_test(pytest_args_list)
    cmd = prepare_pytest_cmd_with_custom_allure_dir(pytest_args_list)

    return cmd


def add_to_pytest_args_skip_reboot_reload_test(pytest_args_list):
    """
    This method adds ignore parameter for the TestRebootReload, otherwise the Reload tests will be called
    in an endless loop.
    :param pytest_args_list: list with pytest arguments
    :return: modified list with pytest arguments
    """
    keyword_expression_arg = '-k'
    skip_arg = 'not TestRebootReload'
    if keyword_expression_arg not in pytest_args_list:
        pytest_args_list.insert(-1, keyword_expression_arg)
        pytest_args_list.insert(-1, '"{}"'.format(skip_arg))
    else:
        index_k = pytest_args_list.index(keyword_expression_arg)
        available_data = pytest_args_list[index_k + 1]
        pytest_args_list.remove(available_data)
        available_data += ' and {}'.format(skip_arg)
        pytest_args_list.insert(index_k + 1, '"{}"'.format(available_data))

    return pytest_args_list


def prepare_pytest_cmd_with_custom_allure_dir(pytest_args_list):
    """
    This method appends the custom alluredir folder argument to the pytest cmd
    :param pytest_args_list: list with pytest arguments
    :return: pytest run cmd(example: 'pytest --run_test_only --setup_name=sonic_spider_r-spider-05
    --rootdir=/local/repos/sonic-mgmt/ngts -c /local/repos/sonic-mgmt/ngts/pytest.ini --log-level=INFO
    --clean-alluredir --alluredir=/tmp/allure_reboot_reload -k "not TestRebootReload"
    /local/repos/sonic-mgmt/ngts/tests/push_build_tests')
    """
    python_bin_folder = os.path.dirname(sys.executable)
    pytest_path = os.path.join(python_bin_folder, 'pytest')
    cmd = '{} {} '.format(pytest_path, PytestConst.run_test_only_arg)
    for arg in pytest_args_list:
        if '{}='.format(PytestConst.alluredir_arg) in arg:
            arg = '{}=/tmp/allure_reboot_reload'.format(PytestConst.alluredir_arg)
        cmd += '{} '.format(arg)

    return cmd


def generate_report(out, err):
    """
    This method generates report for functional validation step, it will attach allure url and logs to allure report
    :param out: pytest stdout
    :param err: stderror
    """
    allure.attach(out, 'stdout', allure.attachment_type.TEXT)
    allure.attach(err, 'stderr', allure.attachment_type.TEXT)
    try:
        allure_report_url = re.search(r'Allure\sreport\sURL\:\s(http://.*)', out.decode('utf-8')).group(1)
        allure.attach(bytes(allure_report_url, 'utf-8'), 'Allure report URL', allure.attachment_type.URI_LIST)
    except Exception as err:
        logger.error('Can not find and attach allure URL to allure report. Error: {}'.format(err))
