import pytest
import logging
import os
import allure
import math
from ngts.constants.constants import PytestConst
from ngts.tools.allure_report.allure_report_attacher import collect_stored_cmds_then_attach_to_allure_report, clean_stored_cmds_with_fixture_scope_list

logger = logging.getLogger()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Techsupport creator. Will be executed as part of teardown.
    """

    os.environ[PytestConst.GET_DUMP_AT_TEST_FALIURE] = "True"

    outcome = yield
    rep = outcome.get_result()

    if rep.when == 'teardown':
        is_teardown_failed = item.rep_teardown.failed  # if LA failed, but may be not only LA
        session_id = item.funcargs.get('session_id', '')
        if item.rep_setup.passed and (item.rep_call.failed or is_teardown_failed) and \
                os.environ.get(PytestConst.GET_DUMP_AT_TEST_FALIURE) == "True":
            if session_id:
                topology_obj = item.funcargs['topology_obj']
                dumps_folder = item.funcargs['dumps_folder']
                with allure.step('The test case has failed, generating a sysdump'):
                    dut_cli_object = topology_obj.players['dut']['cli']
                    dut_engine = topology_obj.players['dut']['engine']
                    duration = get_test_duration(item)
                    collect_stored_cmds_then_attach_to_allure_report(topology_obj)
                    remote_dump_path = dut_cli_object.general.generate_techsupport(duration)

                    dest_file = dumps_folder + '/sysdump_' + item.name + '.tar.gz'
                    logger.info('Copy dump {} to log folder {}'.format(remote_dump_path, dumps_folder))
                    dut_engine.copy_file(source_file=remote_dump_path,
                                         dest_file=dest_file,
                                         file_system='/',
                                         direction='get',
                                         overwrite_file=True,
                                         verify_file=False)
                    os.chmod(dest_file, 0o777)
            else:
                logger.info('###  Session ID was not provided, assuming this is manual run,'
                            ' sysdump will not be created  ###')
        topology_obj = item.funcargs.get('topology_obj')
        if topology_obj:
            clean_stored_cmds_with_fixture_scope_list(topology_obj)


def get_test_duration(item):
    """
    Get duration of test case. Init time + test body time + 120 seconds
    :param item: pytest buildin
    :return: integer, test duration
    """
    return math.ceil(item.rep_setup.duration) + math.ceil(item.rep_call.duration) + 120
