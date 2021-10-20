import allure
import os
import logging
import pytest

logger = logging.getLogger()


@pytest.fixture(scope='function')
def session_id_arg(request):
    """
    Method for get session id from pytest arguments
    :param request: pytest buildin
    :return: session id, i.e. 4973482
    """
    return request.config.getoption('--session_id')


@pytest.fixture(scope='function')
def duration(request):
    """
    Method for get techsupport duration from pytest arguments in secounds
    :param request: pytest buildin
    :return: techsupport duration, i.e. 7200
    """
    return request.config.getoption('--tech_support_duration')


@pytest.mark.disable_loganalyzer
def test_store_techsupport_on_not_success(topology_obj, duration, dumps_folder):
    with allure.step('Generating a sysdump'):
        dut_cli_object = topology_obj.players['dut']['cli']
        dut_engine = topology_obj.players['dut']['engine']
        tar_file = dut_cli_object.general.generate_techsupport(dut_engine, duration)
        logger.info("Dump was created at: {}".format(tar_file))
        tarball_file_name = str(tar_file.replace('/var/dump/', ''))

    with allure.step('Copy dump: {} to log folder {}'.format(tarball_file_name, dumps_folder)):
        dest_file = dumps_folder + '/sysdump_' + tarball_file_name
        logger.info('Copy dump {} to log folder {}'.format(tar_file, dumps_folder))
        dut_engine.copy_file(source_file=tar_file,
                             dest_file=dest_file,
                             file_system='/',
                             direction='get',
                             overwrite_file=True,
                             verify_file=False)
        os.chmod(dest_file, 0o777)
        logger.info('Dump file location: {}'.format(dest_file))

    logger.info("Script Finished")
