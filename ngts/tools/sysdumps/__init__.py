import pytest
import logging
import os
import allure
import math
from ngts.constants.constants import PytestConst
from ngts.tools.allure_report.allure_report_attacher import collect_stored_cmds_then_attach_to_allure_report, clean_stored_cmds_with_fixture_scope_list
from ngts.scripts.store_techsupport_on_not_success import dump_simx_data

logger = logging.getLogger()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Techsupport creator. Will be executed as part of teardown.
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when == 'teardown':
        os.environ.pop(item.name, None)
        session_id = item.funcargs.get('session_id', '')
        if (item.rep_setup.failed or (item.rep_setup.passed and (item.rep_call.failed or item.rep_teardown.failed))) \
                and os.environ.get(PytestConst.GET_DUMP_AT_TEST_FALIURE) == "True":
            if session_id:
                try:
                    topology_obj = item.funcargs['topology_obj']
                    dumps_folder = item.funcargs['dumps_folder']
                    with allure.step('The test case has failed, generating a sysdump'):
                        dut_cli_object = topology_obj.players['dut']['cli']
                        dut_engine = topology_obj.players['dut']['engine']
                        duration = get_test_duration(item)
                        collect_stored_cmds_then_attach_to_allure_report(topology_obj)
                        remote_dump_path = dut_cli_object.general.generate_techsupport(duration)

                    dest_file = dumps_folder + '/sysdump_' + item.name + '.tar.gz'
                    copy_msg = 'Copy dump {} to log folder {}'.format(remote_dump_path, dumps_folder)
                    with allure.step(copy_msg):
                        logger.info(copy_msg)
                        dut_engine.copy_file(source_file=remote_dump_path,
                                             dest_file=dest_file,
                                             file_system='/',
                                             direction='get',
                                             overwrite_file=True,
                                             verify_file=False)
                        os.chmod(dest_file, 0o777)
                    is_simx = item.funcargs.get('is_simx')
                    is_air = item.funcargs.get('is_air')
                    if is_simx and not is_air:
                        with allure.step('Dump SIMX VM logs'):
                            dump_simx_data(topology_obj, dumps_folder, name_prefix=item.name)
                    store_dest_file_path(dest_file, item.name)
                except BaseException as err:
                    error_message = f'Failed to generate/store techsupport dump.\nGot error: {err}'
                    logger.error(error_message)
            else:
                logger.info('###  Session ID was not provided, assuming this is manual run,'
                            ' sysdump will not be created  ###')
        topology_obj = item.funcargs.get('topology_obj')
        if topology_obj:
            clean_stored_cmds_with_fixture_scope_list(topology_obj)
        os.environ[PytestConst.GET_DUMP_AT_TEST_FALIURE] = "True"


def get_test_duration(item):
    """
    Get duration of test case. Init time + test body time + 120 seconds
    :param item: pytest build-in
    :return: integer, test duration
    """
    duration = math.ceil(item.rep_setup.duration) + 120
    if hasattr(item, "rep_call"):
        duration = duration + math.ceil(item.rep_call.duration)
    if hasattr(item, "rep_teardown"):
        duration = duration + math.ceil(item.rep_teardown.duration)
    return duration


def store_dest_file_path(dest_file, test_name):
    """
    Store the dump path to environment variables to later usage by pytest_terminal_summary
    :param dest_file: dump file
    :param test_name: test_name
    """
    os.environ[test_name] = dest_file
