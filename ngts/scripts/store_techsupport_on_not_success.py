import allure
import os
import time
import logging
import pytest

from infra.tools.general_constants.constants import DefaultTestServerCred
from ngts.cli_wrappers.nvue.nvue_cli import NvueCli
from ngts.nvos_tools.system.System import System
logger = logging.getLogger()


@pytest.fixture(scope='function')
def session_id_arg(request):
    """
    Method for get session id from pytest arguments
    :param request: pytest builtin
    :return: session id, i.e. 4973482
    """
    return request.config.getoption('--session_id')


@pytest.fixture(scope='function')
def duration(request):
    """
    Method for get techsupport duration from pytest arguments in seconds
    :param request: pytest builtin
    :return: techsupport duration, i.e. 7200
    """
    return request.config.getoption('--tech_support_duration')


def dump_simx_data(topology_obj, dumps_folder, name_prefix=None):
    dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
    if not name_prefix:
        name_prefix = time.strftime('%Y_%b_%d_%H_%M_%S')
    src_file_path = '/var/log/libvirt/qemu/d-switch-001-sw.log'
    dst_file_path = dumps_folder + '/{}_{}_simx_vm.log'.format(name_prefix, dut_name)
    hyper_engine = topology_obj.players['hypervisor']['engine']
    hyper_engine.username = DefaultTestServerCred.DEFAULT_USERNAME
    hyper_engine.password = DefaultTestServerCred.DEFAULT_PASS
    hyper_engine.run_cmd('docker cp {}:{} {}'.format(dut_name, src_file_path, dst_file_path))

    logger.info('SIMX VM log file location: {}'.format(dst_file_path))


@pytest.mark.disable_loganalyzer
def test_store_techsupport_on_not_success(topology_obj, duration, dumps_folder, is_simx, is_air):
    with allure.step('Generating a sysdump'):
        dut_cli_object = topology_obj.players['dut']['cli']
        dut_engine = topology_obj.players['dut']['engine']
        if isinstance(dut_cli_object, NvueCli):
            system = System(None)
            tar_file = system.techsupport.action_generate(dut_engine)
            tarball_file_name = str(tar_file.replace('/host/dump/', ''))
        else:
            tar_file = dut_cli_object.general.generate_techsupport(duration)
            tarball_file_name = str(tar_file.replace('/var/dump/', ''))

        logger.info("Dump was created at: {}".format(tar_file))

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

    if is_simx and not is_air:
        dump_simx_data(topology_obj, dumps_folder)

    logger.info("Script Finished")


@pytest.mark.disable_loganalyzer
def test_store_simx_dump_on_not_success(topology_obj, dumps_folder, is_simx, is_air):
    if is_simx and not is_air:
        dump_simx_data(topology_obj, dumps_folder)
