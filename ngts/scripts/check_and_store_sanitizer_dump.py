import allure
import os
import logging
import pytest
from ngts.constants.constants import PytestConst
from ngts.helpers.sanitizer_helper import get_asan_apps, get_mail_address, disable_asan_apps,\
    check_sanitizer_and_store_dump, aggregate_asan_and_send_mail


logger = logging.getLogger()


@pytest.fixture(scope='function')
def test_name(request):
    """
    Method for getting the test name parameter for script check_and_store_sanitizer_dump.py,
    the script will check for sanitizer failures and store dump under test name
    :param request: pytest builtin
    :return: the test name, i.e, push_gate
    """
    return request.config.getoption('--test_name')


@pytest.fixture(scope='function')
def send_mail(request):
    """
    Method for getting the send_mail boolean parameter for script check_and_store_sanitizer_dump.py,
    true, to send the report by mail
    :param request: pytest builtin
    :return: True/False, True to send mail.
    """
    value = request.config.getoption('--send_mail')
    return True if value in ['t', 'T', 'True', 'true', 'TRUE'] else False


@pytest.mark.disable_loganalyzer
def test_sanitizer(topology_obj, cli_objects, dumps_folder, test_name, send_mail, setup_name):
    dut_engine = topology_obj.players['dut']['engine']
    asan_apps = get_asan_apps(topology_obj, cli_objects.dut)
    mail_address = get_mail_address()
    if topology_obj.players['dut']['sanitizer'] or asan_apps:
        os.environ[PytestConst.GET_DUMP_AT_TEST_FALIURE] = "False"
        disable_asan_apps(cli_objects, asan_apps)
        if topology_obj.players['dut']['sanitizer']:
            with allure.step(f'Reboot DUT'):
                dut_engine.reload([f'sudo reboot'])
        with allure.step(f'Check sanitizer output after reboot/disable of asan apps'):
            sanitizer_dump_path = check_sanitizer_and_store_dump(dut_engine, dumps_folder, test_name)
            if sanitizer_dump_path and send_mail:
                with allure.step(f'Sending mail with the sanitizer failures to {mail_address}'):
                    aggregate_asan_and_send_mail(mail_address, sanitizer_dump_path, dumps_folder, setup_name)
    else:
        logger.info("Image doesn't include sanitizer - script is not checking for sanitizer dumps")
