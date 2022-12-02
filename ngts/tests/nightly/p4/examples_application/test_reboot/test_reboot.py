import os
import logging
import pytest
import allure
import random

from ngts.helpers.run_process_on_host import run_process_on_host
from ngts.helpers.reboot_reload_helper import add_to_pytest_args_disable_loganalyzer, add_to_pytest_args_skip_tests, \
    remove_allure_server_project_id_arg, prepare_pytest_cmd_with_custom_allure_dir, generate_report

logger = logging.getLogger()

REBOOT_LIST = ["reboot", "config reload -y"]


@pytest.mark.build
@pytest.mark.p4_examples
def test_p4_examples_reboot(request, cli_objects, engines, topology_obj):
    """
    reboot and then run all p4_examples test case which need to be verified after reboot
    :param request: request fixture
    :param engines: engines fixture
    :param topology_obj: topology_obj fixture
    """
    # TODO: for now the all the test case in except test_p4_examples_reboot itself will be executed after reboot,
    # TODO: later when the test case increase, need to check if all the test case need to be executed.
    r_type = random.choice(REBOOT_LIST)
    cli_objects.dut.general.save_configuration()
    cli_objects.dut.general.reboot_reload_flow(r_type=r_type, topology_obj=topology_obj)
    try:
        with allure.step('Running functional validations after reboot/reload'):
            logger.info('Running functional validations after reboot/reload')
            do_func_validations(request)
    except Exception as err:
        assert not err, f'We have failed validations during test run. Test result errors: {err}'
    finally:
        # Disconnect engine, otherwise the following error will pop-up "OSError: Socket is closed"
        engines.dut.disconnect()


def do_func_validations(request):
    pytest_args_list = list(request.config.invocation_params.args)
    # run all test case under this folder
    test_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    pytest_args_list[-1] = test_path
    pytest_run_cmd = prepare_pytest_args(pytest_args_list)
    logger.info('pytest_run_cmd: {}'.format(pytest_run_cmd))
    out, err, rc = run_process_on_host(pytest_run_cmd, timeout=1800)
    generate_report(out, err)
    if rc:
        raise AssertionError('Functional validation failed, please check logs')


def prepare_pytest_args(pytest_args_list):
    """
    This method prepare pytest run command with arguments
    :param pytest_args_list: list with pytest arguments
    :return: pytest run cmd
    """
    pytest_args_list = add_to_pytest_args_skip_tests(pytest_args_list, ['test_p4_examples_reboot'])
    pytest_args_list = add_to_pytest_args_disable_loganalyzer(pytest_args_list)
    pytest_args_list = remove_allure_server_project_id_arg(pytest_args_list)
    cmd = prepare_pytest_cmd_with_custom_allure_dir(pytest_args_list, "/tmp/allure_p4_examples_reboot")
    return cmd
