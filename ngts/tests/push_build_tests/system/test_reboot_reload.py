import allure
import logging
import pytest
import os
import re
import random
from retry.api import retry_call
from ngts.helpers.run_process_on_host import run_process_on_host
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from ngts.constants.constants import SonicConst
from dateutil.parser import parse as time_parse
from ngts.tests.nightly.app_extension.app_extension_helper import verify_app_container_up_and_repo_status_installed
from ngts.helpers.reboot_reload_helper import get_supported_reboot_reload_types_list, add_to_pytest_args_skip_tests, \
    add_to_pytest_args_disable_loganalyzer, remove_allure_server_project_id_arg, \
    prepare_pytest_cmd_with_custom_allure_dir, add_to_pytest_args_custom_cache_dir, generate_report, \
    add_to_pytest_args_disable_exporting_test_results_to_mars_db


logger = logging.getLogger()

simx_validation_types = ['reboot', 'config reload -y']
expected_traffic_loss_dict = {'fast-reboot': {'data': 60, 'control': 90},
                              'warm-reboot': {'data': 0, 'control': 90},
                              'reboot': {'data': 180, 'control': 180},
                              'config reload -y': {'data': 180, 'control': 180}
                              }


@pytest.mark.reboot_reload
@pytest.mark.disable_loganalyzer
def test_push_gate_reboot_policer(request, topology_obj, interfaces, engines, shared_params, platform_params):
    """
    This tests checks reboot according to test parameter. Test checks data and control plane traffic loss time.
    After reboot/reload finished - test doing functional validations(run PushGate tests)
    Add 3 verification for app extesnion
    1. Verify shutdown oder same to bgp->app(cpu-report)->swss, after warm/fast reboot
    2. Verify warm_restarted status is reconciled, after warm-reboot
    3. Verify app status is up, after config reload -y
    :param request: pytest build-in
    :param platform_params: platform_params fixture
    :param validation_type: validation type - which will be executed
    """
    try:
        test_reboot_reload = RebootReload(topology_obj, interfaces, engines, shared_params)
        if re.search('simx', platform_params.setup_name):
            validation_type = random.choice(simx_validation_types)
            test_reboot_reload.push_gate_reboot_simx_test_runner(request, validation_type)
        else:
            supported_reboot_reload_list = get_supported_reboot_reload_types_list(platform_params.platform)
            validation_type = random.choice(supported_reboot_reload_list)
            test_reboot_reload.push_gate_reboot_test_runner(request, validation_type)

    except Exception as err:
        raise AssertionError(err)


class RebootReload:

    def __init__(self, topology_obj, interfaces, engines, shared_params):
        self.topology_obj = topology_obj
        self.dut_engine = engines.dut
        self.cli_object = self.topology_obj.players['dut']['cli']
        self.interfaces = interfaces
        self.ping_sender_iface = '{}.40'.format(self.interfaces.ha_dut_2)
        self.dut_vlan40_int_ip = '40.0.0.1'
        self.dut_port_channel_ip = '30.0.0.1'
        self.hb_vlan40_ip = '40.0.0.3'
        self.is_support_app_ext = shared_params.app_ext_is_app_ext_supported
        self.app_name = shared_params.app_ext_app_name
        self.version = shared_params.app_ext_version

    @pytest.mark.disable_loganalyzer
    def push_gate_reboot_test_runner(self, request, validation_type):
        """
        This tests checks reboot according to test parameter. Test checks data and control plane traffic loss time.
        After reboot/reload finished - test doing functional validations(run PushGate tests)
        Add 3 verification for app extesnion
        1. Verify shutdown oder same to bgp->app(cpu-report)->swss, after warm/fast reboot
        2. Verify warm_restarted status is reconciled, after warm-reboot
        3. Verify app status is up, after config reload -y
        :param request: pytest build-in
        :param validation_type: validation type - which will be executed
        """
        allowed_data_loss_time = expected_traffic_loss_dict[validation_type]['data']
        allowed_control_loss_time = expected_traffic_loss_dict[validation_type]['control']
        failed_validations = {}

        if validation_type in ['fast-reboot', 'warm-reboot']:
           # Step below required, if no ARP for 30.0.0.2 warm/fast reboot will not work
            with allure.step('Resolve ARP on DUT for IP 30.0.0.2 in case of warm/fast reboot validation'):
                self.resolve_arp_static_route()

        with allure.step('Starting background validation for control plane traffic'):
            control_plane_checker = self.start_control_plane_validation(validation_type, allowed_control_loss_time)

        with allure.step('Starting background validation for data plane traffic'):
            data_plane_checker = self.start_data_plane_validation(validation_type, allowed_data_loss_time)

        self.cli_object.general.reboot_reload_flow(self.dut_engine, r_type=validation_type,
                                                   topology_obj=self.topology_obj, wait_after_ping=0)

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

        # add 3 test cases for app extension
        if self.is_support_app_ext:
            self.verify_app_ext_test_cases(validation_type, failed_validations)

        # Wait until warm-reboot finished
        if validation_type == 'warm-reboot':
            with allure.step('Checking warm-reboot status'):
                retry_call(SonicGeneralCli().check_warm_reboot_status, fargs=[self.dut_engine, 'inactive'], tries=24,
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

    @pytest.mark.disable_loganalyzer
    def push_gate_reboot_simx_test_runner(self, request, validation_type):
        """
        Test checks control plane traffic loss time on simx platforms.
        After reboot/reload finished - test doing functional validations(run PushGate tests)
        Add 3 verification for app extension
        1. Verify shutdown oder same to bgp->app(cpu-report)->swss
        3. Verify app status is up, after config reload -y
        :param request: pytest build-in
        :param validation_type: validation type - which will be executed
        """
        allowed_control_loss_time = expected_traffic_loss_dict[validation_type]['control']
        failed_validations = {}

        with allure.step('Starting background validation for control plane traffic'):
            control_plane_checker = self.start_control_plane_validation(validation_type, allowed_control_loss_time)

        self.cli_object.general.reboot_reload_flow(self.dut_engine, r_type=validation_type,
                                                   topology_obj=self.topology_obj, wait_after_ping=0)

        try:
            with allure.step('Checking control plane traffic loss'):
                logger.info('Checking that control plane traffic loss not more '
                            'than: {}'.format(allowed_control_loss_time))
                control_plane_checker.complete_validation()
        except Exception as err:
            failed_validations['control_plane'] = err

        # add 3 test cases for app extension
        if self.is_support_app_ext:
            self.verify_app_ext_test_cases(validation_type, failed_validations)

        # Wait until warm-reboot finished
        if validation_type == 'warm-reboot':
            with allure.step('Checking warm-reboot status'):
                retry_call(SonicGeneralCli().check_warm_reboot_status, fargs=[self.dut_engine, 'inactive'], tries=24,
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
                                             'count': 2000, 'dst': self.dut_vlan40_int_ip,
                                             'interval': 0.1,
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

    @staticmethod
    def do_func_validations(request):
        pytest_args_list = list(request.config.invocation_params.args)
        pytest_run_cmd = prepare_pytest_args(pytest_args_list)
        out, err, rc = run_process_on_host(pytest_run_cmd, timeout=3600)
        generate_report(out, err)
        if rc:
            raise AssertionError('Functional validation failed, please check logs')

    def verify_app_shutdown_order(self, validation_type):
        """
        Verify all app are up, and shutdown order is bgp-> app -> swss:

        """
        with allure.step("Verify all docker container is up"):
            SonicGeneralCli().verify_dockers_are_up(self.dut_engine, SonicConst.DOCKERS_LIST.append(self.app_name))
        with allure.step("Verify app shutdown order: bgp-> {} -> swss".format(self.app_name)):
            bgp_shutdown_time = time_parse(
                self.dut_engine.run_cmd("docker inspect --format='{{.State.FinishedAt}}' bgp"))
            app_shutdown_time = time_parse(
                self.dut_engine.run_cmd("docker inspect --format='{{.State.FinishedAt}}' %s " % self.app_name))
            swss_shutdown_time = time_parse(
                self.dut_engine.run_cmd("docker inspect --format='{{.State.FinishedAt}}' swss"))
            assert bgp_shutdown_time < app_shutdown_time < swss_shutdown_time, "Container shutdown oder is not correct"

    def verify_app_warm_restart_state(self, validation_type):
        """
        Verify warm restart state of app is
        """
        with allure.step("Verify warm_restart state of {} is reconciled".format(self.app_name)):
            assert SonicGeneralCli().show_warm_restart_state(self.dut_engine)[self.app_name]["state"] == "reconciled", "Warm_restart state is not reconciled"

    def verify_app_and_container_up_after_config_reload(self, validation_type):
        with allure.step("Verify container are up"):
            SonicGeneralCli().verify_dockers_are_up(self.dut_engine, SonicConst.DOCKERS_LIST)
        with allure.step("Verify app is up and repo stat is installed"):
            verify_app_container_up_and_repo_status_installed(self.dut_engine, self.app_name, self.version)

    def verify_app_ext_test_cases(self, validation_type, failed_validations):
        if validation_type in ["warm-reboot", "fast-reboot"]:
            try:
                # comment it due to the code for Warm/fast reboot support is not merged yet to master
                # self.verify_app_shutdown_order(validation_type)
                logger.info("skip check due to the code for Warm/fast reboot support is not merged yet to master")
            except Exception as err:
                failed_validations['app_ext_shutdown'] = err

        if validation_type == "warm-reboot":
            try:
                self.verify_app_warm_restart_state(validation_type)
            except Exception as err:
                failed_validations['app_ext_warm_restart_state'] = err

        if validation_type == "config reload -y":
            try:
                self.verify_app_and_container_up_after_config_reload(validation_type)
            except Exception as err:
                failed_validations['app_ext_config_reload'] = err


def prepare_pytest_args(pytest_args_list):
    """
    This method prepare pytest run command with arguments
    :param pytest_args_list: list with pytest arguments
    :return: pytest run cmd
    """
    skip_test_list = ["test_push_gate_reboot_policer", "test_validate_config_db_json_during_upgrade"]
    pytest_args_list = add_to_pytest_args_skip_tests(pytest_args_list, skip_test_list)
    pytest_args_list = add_to_pytest_args_disable_loganalyzer(pytest_args_list)
    # Disable export tests data to SQLm in case of failure after reboot, the desired behaviour is to list only
    # the parent test in the failed results and not any subtest.
    pytest_args_list = add_to_pytest_args_disable_exporting_test_results_to_mars_db(pytest_args_list)
    pytest_args_list = remove_allure_server_project_id_arg(pytest_args_list)
    pytest_args_list = add_to_pytest_args_custom_cache_dir(pytest_args_list)
    cmd = prepare_pytest_cmd_with_custom_allure_dir(pytest_args_list, "/tmp/allure_reboot_reload")

    return cmd
