import allure
import os
import time
import logging
import pytest
import re

from infra.tools.general_constants.constants import DefaultTestServerCred, DefaultConnectionValues
from ngts.cli_wrappers.nvue.nvue_cli import NvueCli
from ngts.nvos_constants.constants_nvos import NvosConst
from ngts.nvos_tools.system.System import System

logger = logging.getLogger()
FETCH_THECHSURPORT_STATUS = False
# Because there is memory buffer limitation when use tee to get log by telnet， When syslog size is too larger,
# we cannot fetch all log one time, so define READ_LINE_STEP as the max line number to fetch syslog for every one time
READ_LINE_STEP = 10000


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
    src_file_path = '/var/log/libvirt/qemu/d-switch-001.log'
    dst_file_path = dumps_folder + '/{}_{}_simx_vm.log'.format(name_prefix, dut_name)
    hyper_engine = topology_obj.players['hypervisor']['engine']
    hyper_engine.username = DefaultTestServerCred.DEFAULT_USERNAME
    hyper_engine.password = DefaultTestServerCred.DEFAULT_PASS
    hyper_engine.run_cmd('sudo docker cp {}:{} {}'.format(dut_name, src_file_path, dst_file_path))

    logger.info('SIMX VM log file location: {}'.format(dst_file_path))


def dump_simx_syslog_data(topology_obj, dumps_folder, name_postfix=None):
    dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
    hyper_name = topology_obj.players['hypervisor']['attributes'].noga_query_data['attributes']['Common']['Name']

    hyper_engine = topology_obj.players['hypervisor']['engine']
    hyper_engine.username = DefaultTestServerCred.DEFAULT_USERNAME
    hyper_engine.password = DefaultTestServerCred.DEFAULT_PASS
    dut_user_name = DefaultConnectionValues.DEFAULT_USER
    dut_password = NvosConst.DEFAULT_PASS

    if not name_postfix:
        name_postfix = time.strftime('%Y_%b_%d_%H_%M_%S')

    telnet_port = get_telnet_port(topology_obj)
    if not telnet_port:
        raise Exception(f"Can not get telnet port. telnet_port_info is :{telnet_port_info}")

    if "no telnet" in hyper_engine.run_cmd("which telnet"):
        install_telnet_cmd = "sudo yum -y install telnet"
        logger.info("Telnet is not available on the hypervisor server, so install it with the command {}".format(
            install_telnet_cmd))
        hyper_engine.run_cmd(install_telnet_cmd)

    # Get syslog file name list from switch
    syslog_folder = f'{dut_name}_{name_postfix}'
    hyper_engine.run_cmd(f'mkdir /tmp/{syslog_folder}')
    temp_tee_log_full_name = f"/tmp/{syslog_folder}/temp_tee.log"
    echo_dut_user_name_password = f'echo {dut_user_name}; sleep 5; echo {dut_password}; sleep 5;'
    cmd_get_syslog_file_list = 'eval "{ ' + \
                               echo_dut_user_name_password + \
                               "echo 'ls /var/log/syslog* -l'; sleep 10;" + \
                               '}" | ' + \
                               f" telnet {hyper_name} {telnet_port} -E |  tee -i {temp_tee_log_full_name}"
    hyper_engine.run_cmd(cmd_get_syslog_file_list)
    syslog_file_list = []
    syslog_file_info = hyper_engine.run_cmd(f"cat {temp_tee_log_full_name} | grep /var/log/syslog")
    for line in syslog_file_info.split("\n"):
        if "ls /var/log/syslog* -l" not in line:
            syslog_file_list.append(line.split("/var/log/")[1].strip())

    logger.info(f'syslog file list:{syslog_file_list}')

    if not syslog_file_list:
        raise Exception(f"No syslog file found")

    # copy syslog file to /tmp/ folder in case syslog is changed, because fetch syslog will take much time
    # When deploy fails, there is only a little syslog usually,
    # and fetching syslog will take much time, so we just take at most two syslog files
    fetched_syslog_files = syslog_file_list if len(syslog_file_list) <= 2 else syslog_file_list[0:3]
    fetched_syslog_files_full_path = ''
    for file_name in fetched_syslog_files:
        fetched_syslog_files_full_path += f'/var/log/{file_name} '
    cp_syslog_to_tmp_folder = 'eval "{ ' + \
                              echo_dut_user_name_password + \
                              f"echo 'sudo cp {fetched_syslog_files_full_path}  /tmp/'; sleep 10;" + \
                              '}" | ' + \
                              f" telnet {hyper_name} {telnet_port} -E |  tee -i {temp_tee_log_full_name}"
    hyper_engine.run_cmd(cp_syslog_to_tmp_folder)
    logger.info(f"Copy {fetched_syslog_files_full_path} to /tmp/")

    for syslog_file_name in fetched_syslog_files:
        read_file_cmd = " cat"
        if syslog_file_name.endswith(".gz"):
            read_file_cmd = "zcat"

        get_file_line_number_cmd = 'eval "{ ' + \
                                   echo_dut_user_name_password + \
                                   f"echo ' sudo {read_file_cmd} /tmp/{syslog_file_name} | wc -l '; sleep 10;" + \
                                   '}" | ' + \
                                   f" telnet {hyper_name} {telnet_port} -E |  tee -i {temp_tee_log_full_name}"
        total_line_number = get_file_line_number(hyper_engine, get_file_line_number_cmd)

        start_line = 0
        end_line = READ_LINE_STEP
        new_syslog_file_name = syslog_file_name.replace('.gz', '')

        def fetch_syslog(start_line, end_line):
            logger.info(f"start line:{start_line}, end line:{end_line}")
            cmd_get_syslog_file_content = 'eval "{ ' + \
                                          echo_dut_user_name_password + \
                                          f"echo 'sudo {read_file_cmd} /tmp/{syslog_file_name} | head -n {end_line} | tail -n +{start_line}'; sleep 60;" + \
                                          '}" | ' + \
                                          f" telnet {hyper_name} {telnet_port} -E |  tee -i /tmp/{syslog_folder}/tmp_{new_syslog_file_name}"

            hyper_engine.run_cmd(cmd_get_syslog_file_content)
            match_number = hyper_engine.run_cmd(
                f"sed -n '/.*sudo .*cat \\/tmp\\/syslog.* \\| head -n \\d+ \\| tail -n +\\d+.*/=' /tmp/{syslog_folder}/tmp_{new_syslog_file_name}")
            hyper_engine.run_cmd(
                f" sed -n '{int(match_number) + 1},$p' /tmp/{syslog_folder}/tmp_{new_syslog_file_name} >> /tmp/{syslog_folder}/{new_syslog_file_name} ")

        if total_line_number <= READ_LINE_STEP:
            end_line = total_line_number
            fetch_syslog(start_line, end_line)

        else:
            while total_line_number >= end_line > start_line:
                fetch_syslog(start_line, end_line)
                start_line = end_line + 1
                end_line = total_line_number if end_line + READ_LINE_STEP > total_line_number else end_line + READ_LINE_STEP

    dest_folder = os.path.join(dumps_folder, syslog_folder)
    with allure.step(f'Simx syslog file location: {dest_folder}'):
        os.chmod(dumps_folder, 0o777)
        hyper_engine.run_cmd(f'sudo cp  -r /tmp/{syslog_folder} {dumps_folder}')
        logger.info(f'Simx syslog file location: {dest_folder}')


def get_telnet_port(topology_obj):
    serial_cmd = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['serial_conn_cmd']
    serial_cmd_arr = serial_cmd.split(' ')
    serial_port = serial_cmd_arr[len(serial_cmd_arr) - 1]
    return serial_port


def get_file_line_number(hyper_engine, get_file_line_number_cmd):
    line_number_content = hyper_engine.run_cmd(get_file_line_number_cmd)
    reg_get_line_number_cmd = r".*sudo  (cat|zcat) \/tmp\/syslog.* \| wc -l.*"
    reg_digit = r"^\d+$"
    is_find_get_line_number_cmd = False
    for content in line_number_content.split('\n'):
        content = content.strip()
        if is_find_get_line_number_cmd:
            if re.match(reg_digit, content):
                logger.info(f"syslog file total line is {content}")
                return int(content)
            else:
                return READ_LINE_STEP
        if re.match(reg_get_line_number_cmd, content):
            is_find_get_line_number_cmd = True
            logger.info(f"Find the get line cmd:{content}")

    return READ_LINE_STEP


def get_nvos_techsupport_info(dut_cli_object, duration, dumps_folder, dut_engine):
    """
    :param dut_cli_object:
    :param duration:
    :param dumps_folder:
    :return: dumps_folder: NVOS dump folders will be on a separated folder (not in the logs folder)
             tar_file: NVOS file name will include the session id
             tarball_file_name: the full path for dest + file name
    """
    with allure.step('get session_id and dumps folder name'):
        dump_folder = dumps_folder.split('/')[-1]
        session_id = dumps_folder.split('/')[-2]
        logger.info('session_id = {}, dump folder name = {}'.format(session_id, dump_folder))

    with allure.step('generate tarball file name'):
        dumps_folder = dumps_folder.rpartition('/')[:-2][0]
        dumps_folder = dumps_folder.rpartition('/')[:-2][0]
        dumps_folder = dumps_folder + '/' + dump_folder
        logger.info('NVOS dump folder path {}'.format(dumps_folder))

    with allure.step('generate the file name'):
        tar_file = dut_cli_object.general.generate_techsupport(duration)
        logger.info('NVOS tar_file {}'.format(tar_file))
        tarball_file_name = str(session_id) + '_' + tar_file.rpartition('/')[-1]
        logger.info('NVOS tarball_file_name {}'.format(tarball_file_name))

    with allure.step('testing the flow of NVOS commands'):
        system = System(None)
        temp_tar_file, duration = system.techsupport.action_generate(engine=dut_engine)
        logger.info('NVOS temp_tarball_file_name {}'.format(temp_tar_file))

    return dumps_folder, tar_file, tarball_file_name


@pytest.mark.disable_loganalyzer
def test_store_techsupport_on_not_success(topology_obj, duration, dumps_folder, is_simx, is_air):
    dut_cli_object_list = [topology_obj.players['dut']['cli']]
    dut_engine_list = [topology_obj.players['dut']['engine']]
    if topology_obj.players.get('dut-b'):
        dut_cli_object_list.append(topology_obj.players['dut-b']['cli'])
        dut_engine_list.append(topology_obj.players['dut-b']['engine'])

    for i in range(len(dut_cli_object_list)):
        with allure.step('Generating a sysdump'):
            if isinstance(dut_cli_object_list[i], NvueCli):
                dumps_folder, tar_file, tarball_file_name = get_nvos_techsupport_info(dut_cli_object_list[i], duration,
                                                                                      dumps_folder, dut_engine_list[i])
            else:
                tar_file = dut_cli_object_list[i].general.generate_techsupport(duration)
                tarball_file_name = str(tar_file.replace('/var/dump/', ''))

            logger.info("Dump was created at: {}".format(tar_file))

        with allure.step('Copy dump: {} to log folder {}'.format(tarball_file_name, dumps_folder)):
            dest_file = dumps_folder + '/sysdump_' + tarball_file_name
            logger.info('Copy dump {} to log folder {}'.format(tar_file, dumps_folder))
            dut_engine_list[i].copy_file(source_file=tar_file,
                                         dest_file=dest_file,
                                         file_system='/',
                                         direction='get',
                                         overwrite_file=True,
                                         verify_file=False)
            os.chmod(dest_file, 0o777)
            logger.info('Dump file location: {}'.format(dest_file))
    global FETCH_THECHSURPORT_STATUS
    FETCH_THECHSURPORT_STATUS = True

    if is_simx and not is_air:
        dump_simx_data(topology_obj, dumps_folder)

    logger.info("Script Finished")


@pytest.mark.disable_loganalyzer
def test_store_simx_dump_on_not_success(topology_obj, dumps_folder, is_simx, is_air):
    if is_simx and not is_air:
        dump_simx_data(topology_obj, dumps_folder)


@pytest.mark.disable_loganalyzer
def test_store_simx_dump_syslog_on_not_success(topology_obj, dumps_folder, is_simx, is_air):
    if not FETCH_THECHSURPORT_STATUS:
        if is_simx and not is_air:
            with allure.step('Fetch syslog for simx switch by telnet'):
                dump_simx_syslog_data(topology_obj, dumps_folder)
