import allure
import os
import logging
import pytest
from ngts.constants.constants import PytestConst, InfraConst
from ngts.helpers.sanitizer_helper import get_asan_apps, get_sanitizer_dumps
from ngts.helpers.bug_handler.bug_handler_helper import handle_sanitizer_dumps, create_summary_html_report, \
    review_bug_handler_results
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon

logger = logging.getLogger()


@pytest.mark.disable_loganalyzer
def test_sanitizer_bug_handler(topology_obj, setup_name, engines, cli_objects, dumps_folder):
    dut_engine = engines.dut
    asan_apps = get_asan_apps(topology_obj, cli_objects.dut)
    branch = topology_obj.players['dut']['branch']
    cli_type = os.environ.get('CLI_TYPE')
    version = GeneralCliCommon(dut_engine).get_version(cli_type)
    session_id = os.environ.get(InfraConst.ENV_SESSION_ID)
    sanitizer_dumps_paths = get_sanitizer_dumps(dumps_folder)
    os.environ[PytestConst.GET_DUMP_AT_TEST_FALIURE] = "False"
    if sanitizer_dumps_paths:
        with allure.step("Call bug handler on found sanitizer dumps"):
            bug_handler_dumps_results = handle_sanitizer_dumps(sanitizer_dumps_paths, cli_type, branch, version,
                                                               setup_name, topology_obj)
            bug_handler_summary = create_summary_html_report(session_id, setup_name, dumps_folder,
                                                             bug_handler_dumps_results)
            allure.attach.file(bug_handler_summary,
                               attachment_type=allure.attachment_type.HTML,
                               name="bug_handler_summary_report.html")
            review_bug_handler_results(bug_handler_dumps_results)
    else:
        if topology_obj.players['dut']['sanitizer'] or asan_apps:
            with allure.step("No sanitizer leaks were detected in previous reboots or disable the apps"):
                return InfraConst.RC_SUCCESS
        else:
            with allure.step("Image doesn't include sanitizer"):
                return InfraConst.RC_SUCCESS
