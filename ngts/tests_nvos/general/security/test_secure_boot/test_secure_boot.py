'''
Secure Boot Suite case:

In this test file we introduce different cases for secure boot feature.
Secure Boot is a feature that validates secure boot and only signed modules are running.

In order to run this test, you need to specify the following argument: kernel_module_path
'''
import re
import time
import random
import string
import logging

import py
from infra.tools.connection_tools.pexpect_serial_engine import PexpectSerialEngine
from infra.tools.linux_tools.linux_tools import scp_file
from ngts.conftest import TestToolkit
from ngts.nvos_tools.infra.Tools import RandomizationTool
from ngts.tests_nvos.conftest import DutUtilsTool, ProxySshEngine, System, serial_engine
from ngts.tests_nvos.general.security.test_secure_boot.conftest import restore_image_path
from ngts.tools.test_utils import allure_utils as allure
import pytest
import os
from ngts.tests_nvos.general.security.test_secure_boot.constants import ChainOfTrustNode, SecureBootConsts
from infra.tools.general_constants.constants import DefaultConnectionValues
from infra.tools.validations.traffic_validations.ping.send import ping_till_alive

logger = logging.getLogger(__name__)


@pytest.mark.checklist
@pytest.mark.secure_boot
def test_signed_kernel_module_load(serial_engine, remove_kernel_module, upload_kernel_module, kernel_module_filename,
                                   is_secure_boot_enabled):
    '''
    @summary: in this test case we want to validate successful
    load of secured kernel module
    '''
    with allure.step("Inserting signed kernel module using insmod"):
        logger.info("Inserting signed kernel module using insmod")
        serial_engine.run_cmd_and_get_output('sudo insmod {}/{}'.format(SecureBootConsts.TMP_FOLDER,
                                                                        kernel_module_filename))
    # assert
    filename_without_extension = kernel_module_filename.split('.')[0]
    lsmod_output = serial_engine.run_cmd_and_get_output(
        'lsmod | grep \"{}\"'.format(filename_without_extension))
    assert kernel_module_filename.split('.')[
        0] in lsmod_output, "secure kernel module: {}, is not showing in lsmod output".format(
        filename_without_extension)


@pytest.mark.checklist
@pytest.mark.secure_boot
def test_non_signed_kernel_module_load(serial_engine, remove_kernel_module, upload_kernel_module,
                                       kernel_module_filename, is_secure_boot_enabled):
    '''
    @summary: in this test case we want to validate unsuccessful load
    of unsigned kernel module
    '''
    with allure.step("Inserting non signed kernel module using insmod"):
        logger.info("Inserting non signed kernel module using insmod")
        serial_engine.run_cmd_and_get_output('sudo insmod {}/{}'.format(SecureBootConsts.TMP_FOLDER,
                                                                        kernel_module_filename))
    # assert
    lsmod_output = serial_engine.run_cmd_and_get_output('lsmod | grep \"unsecure_kernel_module\"')
    assert "unsecure_kernel_module" not in lsmod_output, "unsecure kernel module is showing in lsmod output"


def manipulate_signature(serial_engine, test_server_engine, filepath):
    '''
    @summary: this function will echo random string to the end of filename given
    and by that simulating signature change
    :param serial_engine: serial connection
    :param filepath: can be any absolute file on the SWITCH!, but will be used for these files:
        [grubx64.efi, mmx64.efi,  shimx64.efi], must be in the format /../../../filename
    '''
    # extract file name
    filename = os.path.split(filepath)[1]

    with allure.step("Uploading {} to {} directory on the local device in order to manipulate it locally".
                     format(filename, SecureBootConsts.LOCAL_SECURE_BOOT_DIR)):
        logger.info("Uploading {} to {} directory on the local device in order to manipulate it locally".
                    format(filename, SecureBootConsts.LOCAL_SECURE_BOOT_DIR))
        serial_engine.upload_file_using_scp(test_server_engine.username,
                                            test_server_engine.password,
                                            test_server_engine.ip,
                                            filepath,
                                            SecureBootConsts.LOCAL_SECURE_BOOT_DIR)

    # manipulate file sig
    with allure.step("manipulating signature to file {}".format(filename)):
        logger.info("manipulating signature to file {}".format(filename))
        test_server_engine.run_cmd('sudo chmod 777 {}/{}'.format(SecureBootConsts.LOCAL_SECURE_BOOT_DIR, filename))
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(5, 10)))
        fileObject = open(SecureBootConsts.LOCAL_SECURE_BOOT_DIR + '/{}'.format(filename), "ab")
        # manipulate sig in the [SIG_START,SIG_END] range
        fileObject.seek(random.randint(SecureBootConsts.SIG_START, SecureBootConsts.SIG_END), os.SEEK_END)
        fileObject.write(random_string.encode())
        fileObject.close()

    with allure.step("Uploading back {} to switch".format(filename)):
        logger.info("Uploading back {} to switch".format(filename))
        test_server_engine.upload_file_using_scp(serial_engine.username,
                                                 serial_engine.password,
                                                 serial_engine.ip,
                                                 SecureBootConsts.LOCAL_SECURE_BOOT_DIR + '/{}'.format(filename),
                                                 SecureBootConsts.TMP_FOLDER)
        serial_engine.run_cmd(SecureBootConsts.ROOT_PRIVILAGE)
        serial_engine.run_cmd('cp {}/{} {}'.format(SecureBootConsts.TMP_FOLDER, filename,
                                                   '/'.join(filepath.split('/')[0:-1])))


def recover_switch_after_secure_boot_violation_message(serial_engine, test_server_engine, restore_image_path):
    '''
    @summary: this function will recover the switch after receiving a secure boot
    violation message appear
    :param serial_engine: serial connection
    '''
    # check if the system is in NVOS already or not
    with allure.step("Recovering the switch"):
        logger.info("Recovering the switch")

    _, respond = serial_engine.run_cmd('\r', ["Please press Enter to activate this console",
                                              DefaultConnectionValues.LOGIN_REGEX,
                                              DefaultConnectionValues.DEFAULT_PROMPTS[0]],
                                       timeout=120)
    # it means it booted to NVOS, because for ONIE you will get first the "Please press enter to activate ..."
    if respond != 0:
        with allure.step("No need to recover switch, it is already working on NVOS image"):
            logger.info("No need to recover switch, it is already working on NVOS image")
        return

    # after receiving the error message we should press enter and get ONIE
    _, respond = serial_engine.run_cmd('\r',
                                       [DefaultConnectionValues.LOGIN_REGEX] + DefaultConnectionValues.DEFAULT_PROMPTS)
    if respond == 0:
        serial_engine.run_cmd(DefaultConnectionValues.ONIE_USERNAME, [DefaultConnectionValues.PASSWORD_REGEX] +
                              DefaultConnectionValues.DEFAULT_PROMPTS)
        serial_engine.run_cmd(DefaultConnectionValues.ONIE_PASSWORD, DefaultConnectionValues.DEFAULT_PROMPTS)
    _, respond = serial_engine.run_cmd('\r', DefaultConnectionValues.DEFAULT_PROMPTS)

    # stop onie discovery to reduce log messages
    serial_engine.run_cmd_and_get_output('onie-stop')

    with allure.step("Uploading restore image to {} on the switch".format(SecureBootConsts.TMP_FOLDER)):
        logger.info("Uploading restore image to {} on the switch".format(SecureBootConsts.TMP_FOLDER))
        test_server_engine.upload_file_using_scp(DefaultConnectionValues.ONIE_USERNAME,
                                                 DefaultConnectionValues.ONIE_PASSWORD,
                                                 serial_engine.ip,
                                                 restore_image_path,
                                                 SecureBootConsts.TMP_FOLDER,
                                                 timeout=300)
        image_filename = os.path.split(restore_image_path)[1]
        serial_engine.run_cmd('onie-nos-install {}/{}'.format(SecureBootConsts.TMP_FOLDER, image_filename),
                              'Installed.*base image.*successfully',
                              300)

    with allure.step("ping till down after ONIE install"):
        ping_till_alive(should_be_alive=False, destination_host=serial_engine.ip)

    with allure.step("ping till alive after system is down"):
        ping_till_alive(should_be_alive=True, destination_host=serial_engine.ip)

    with allure.step("Sleep {} secs to allow CLI bring up".format(SecureBootConsts.SLEEP_AFTER_ONIE_INSTALL)):
        logger.info("Sleep {} secs to allow CLI bring up".format(SecureBootConsts.SLEEP_AFTER_ONIE_INSTALL))
        time.sleep(SecureBootConsts.SLEEP_AFTER_ONIE_INSTALL)


def unsigned_file_secure_boot(serial_engine, secure_component, test_server_engine, restore_image_path):
    '''
    @summary: this function will perform as the test body called by the different wrappers
    will perform the following:
        1. change the signature for secure boot component given by filename
        2. reboot
        3. validate 'invalid signature message appear'
    '''
    try:
        manipulate_signature(serial_engine, test_server_engine, secure_component)
        serial_engine.run_cmd(SecureBootConsts.REBOOT_CMD,
                              SecureBootConsts.INVALID_SIGNATURE,
                              timeout=180)
    except Exception as err:
        raise err
    finally:
        # pressing enter should lead us to ONIE install mode
        recover_switch_after_secure_boot_violation_message(serial_engine, test_server_engine, restore_image_path)


# @pytest.mark.checklist
# @pytest.mark.secure_boot
# def test_unsigned_shim_secure_boot(serial_engine, mount_uefi_disk_partition, test_server_engine, restore_image_path,
#                                      validate_all_dockers_are_up_after_nvos_boot, is_secure_boot_enabled):
#     '''
#     @summary: in this test case we want to simulate broken signature of shim
#     by manually changing it and then do reboot and see that it does not boot successfully
#     :param serial_engine: serial connection
#     '''
#     unsigned_file_secure_boot(serial_engine,
#                               secure_component=SecureBootConsts.SHIM_FILEPATH,
#                               test_server_engine=test_server_engine,
#                               restore_image_path=restore_image_path)


# @pytest.mark.checklist
# @pytest.mark.secure_boot
# def test_unsigned_grub_secure_boot(serial_engine, mount_uefi_disk_partition, test_server_engine, restore_image_path,
#                                      validate_all_dockers_are_up_after_nvos_boot, is_secure_boot_enabled):
#     '''
#     @summary: in this test case we want to simulate broken signature of grub
#     by manually changing it and then do reboot and see that it does not boot successfully
#     :param serial_engine: serial connection
#     '''
#     unsigned_file_secure_boot(serial_engine,
#                               secure_component=SecureBootConsts.GRUB_FILEPATH,
#                               test_server_engine=test_server_engine,
#                               restore_image_path=restore_image_path)


# @pytest.mark.checklist
# @pytest.mark.secure_boot
# def test_unsigned_vmlinuz_secure_boot(serial_engine, test_server_engine, restore_image_path, vmlinuz_filepath,
#                                         validate_all_dockers_are_up_after_nvos_boot, is_secure_boot_enabled):
#     '''
#     @summary: in this test case we want to simulate broken signature of vmiluz component
#     by manually changing it and then do reboot and see that it does not boot successfully
#     :param serial_engine: serial connection
#     '''
#     unsigned_file_secure_boot(serial_engine,
#                               secure_component=vmlinuz_filepath,
#                               test_server_engine=test_server_engine,
#                               restore_image_path=restore_image_path)


# -------------------- NEW --------------------

def get_system_chain_of_trust_node_file_switch_path(chain_of_trust_node: str,
                                                    serial_engine: PexpectSerialEngine) -> str:
    assert chain_of_trust_node in ChainOfTrustNode.ALL_NODES, f'chain of trust must be in: {ChainOfTrustNode.ALL_NODES}'
    if chain_of_trust_node == ChainOfTrustNode.SHIM:
        return SecureBootConsts.SHIM_FILEPATH
    elif chain_of_trust_node == ChainOfTrustNode.GRUB:
        return SecureBootConsts.GRUB_FILEPATH
    else:
        output = serial_engine.run_cmd_and_get_output(f'ls {SecureBootConsts.VMLINUZ_DIR}')
        path = re.findall(SecureBootConsts.VMLINUZ_REGEX, output)[0]
        return SecureBootConsts.VMLINUZ_DIR + path


def manipulate_nvos_system_file_signature(chain_of_trust_node: str, dut_engine: ProxySshEngine,
                                          serial_engine: PexpectSerialEngine):
    assert chain_of_trust_node in ChainOfTrustNode.ALL_NODES, f'chain of trust must be in: {ChainOfTrustNode.ALL_NODES}'

    with allure.step(f'Download orig {chain_of_trust_node} file from the switch'):
        system_file_switch_path = get_system_chain_of_trust_node_file_switch_path(chain_of_trust_node, serial_engine)
        filename = os.path.split(system_file_switch_path)[1]
        system_file_local_path = f'{SecureBootConsts.LOCAL_SECURE_BOOT_DIR}/{filename}'
        logging.info(f'Download using scp:\nSwitch (src) path: {system_file_switch_path}\nLocal (dst) path: {system_file_local_path}')
        scp_file(
            player=dut_engine,
            src_path=system_file_switch_path,
            dst_path=system_file_local_path,
            download_from_remote=True
        )

    with allure.step(f'Manipulate content in the end of {chain_of_trust_node} file'):
        rand_str = RandomizationTool.get_random_string(6)
        chars_from_end = 6
        with open(system_file_local_path, 'a') as file_obj:
            # Get the current file position
            file_obj.seek(0, 2)  # Seek to the end of the file
            # Calculate the position to insert the string
            insert_position = max(file_obj.tell() - chars_from_end, 0)
            # Seek to the insertion position
            file_obj.seek(insert_position)
            # Write the string at the desired position
            file_obj.write(rand_str)
            # file_obj.seek(random.randint(SecureBootConsts.SIG_START, SecureBootConsts.SIG_END), os.SEEK_END)
            # file_obj.write(rand_str)

    with allure.step(f'Update {chain_of_trust_node} file on the switch'):
        with allure.step(f'Upload new {chain_of_trust_node} file to the switch'):
            system_file_switch_tmp_path = f'{SecureBootConsts.TMP_FOLDER}/{filename}'
            logging.info(f'Upload using scp:\nLocal (src) path: {system_file_local_path}\nSwitch (dst) path: {system_file_switch_tmp_path}')
            scp_file(
                player=dut_engine,
                src_path=system_file_local_path,
                dst_path=system_file_switch_tmp_path,
                download_from_remote=False
            )
        with allure.step(f'Override orig {chain_of_trust_node} file with the new one'):
            logging.info(f'Copy file on switch:\nSwitch (src) path: {system_file_switch_tmp_path}\nSwitch (dst) path: {system_file_switch_path}')
            serial_engine.run_cmd(f'sudo cp -f {system_file_switch_tmp_path} {system_file_switch_path}')


def reinstall_nvos_after_test(serial_engine: PexpectSerialEngine, restore_image_path: str):
    with allure.step('Press Enter to close error message'):
        time.sleep(1)
        serial_engine.run_cmd('\r', '.*')
    with allure.step('Press arrow-up twice to get to ONIE install mode'):
        time.sleep(1)
        serial_engine.run_cmd("\x1b[A", expected_value='.*', send_without_enter=True)
        serial_engine.run_cmd("\x1b[A", expected_value='.*', send_without_enter=True)
    with allure.step('Press Enter to enter ONIE install mode'):
        _, respond_index = serial_engine.run_cmd('\r', ["Please press Enter to activate this console",
                                                        DefaultConnectionValues.LOGIN_REGEX,
                                                        DefaultConnectionValues.DEFAULT_PROMPTS[0]],
                                                 timeout=120)

    with allure.step('Check switch state'):
        if respond_index != 0:
            logging.info('Switch could boot in NVOS. Not reinstalling')
            return

    with allure.step('Reinstall NVOS'):
        with allure.step('Press Enter ; Expect: login prompt'):
            serial_engine.run_cmd('\r', DefaultConnectionValues.LOGIN_REGEX)
        with allure.step('Enter username ; Expect: password prompt'):
            serial_engine.run_cmd(DefaultConnectionValues.ONIE_USERNAME, DefaultConnectionValues.PASSWORD_REGEX)
        with allure.step('Enter username ; Expect: ONIE prompt (#)'):
            serial_engine.run_cmd(DefaultConnectionValues.ONIE_PASSWORD, DefaultConnectionValues.DEFAULT_PROMPTS)
        with allure.step('Press Enter ; Expect: ONIE prompt (#)'):
            serial_engine.run_cmd('\r', DefaultConnectionValues.DEFAULT_PROMPTS)
        with allure.step(f'Run: {SecureBootConsts.ONIE_STOP_CMD} ; Expect: ONIE prompt (#)'):
            serial_engine.run_cmd(SecureBootConsts.ONIE_STOP_CMD, DefaultConnectionValues.DEFAULT_PROMPTS)
        with allure.step(
                f'Run: {SecureBootConsts.ONIE_NOS_INSTALL_CMD} ; Expect: {SecureBootConsts.INSTALL_SUCCESS_PATTERN}'):
            serial_engine.run_cmd(
                f'{SecureBootConsts.ONIE_NOS_INSTALL_CMD} {SecureBootConsts.NBU_NFS_PREFIX}{restore_image_path}',
                SecureBootConsts.INSTALL_SUCCESS_PATTERN,
                timeout=SecureBootConsts.NVOS_INSTALL_TIMEOUT
            )
        with allure.step('Ping switch until shutting down'):
            ping_till_alive(should_be_alive=False, destination_host=serial_engine.ip)
        with allure.step('Ping switch until back alive'):
            ping_till_alive(should_be_alive=True, destination_host=serial_engine.ip)
        with allure.step('Wait until switch is up'):
            TestToolkit.engines.dut.disconnect()  # force engines.dut to reconnect
            DutUtilsTool.wait_for_nvos_to_become_functional(engine=TestToolkit.engines.dut)


@pytest.mark.checklist
@pytest.mark.secure_boot
@pytest.mark.parametrize('tested_chain_of_trust_node', ChainOfTrustNode.ALL_NODES)
def test_secure_boot_unsigned_system_file(tested_chain_of_trust_node: str, serial_engine: PexpectSerialEngine,
                                          mount_uefi_disk_partition, engines, restore_image_path, is_secure_boot_enabled):
    assert tested_chain_of_trust_node in ChainOfTrustNode.ALL_NODES, \
        f'chain of trust must be in: {ChainOfTrustNode.ALL_NODES}'

    with allure.step(f'Manipulate signature of {tested_chain_of_trust_node} file on the switch'):
        manipulate_nvos_system_file_signature(
            chain_of_trust_node=tested_chain_of_trust_node,
            dut_engine=engines.dut,
            serial_engine=serial_engine
        )

    try:
        with allure.step('Reboot the system'):
            expected_messages = SecureBootConsts.INVALID_SIGNATURE
            _, respond_index = serial_engine.run_cmd(
                cmd='sudo reboot',
                expected_value=expected_messages,
                timeout=180
            )

        with allure.step(f'Verify got one of expected messages: {expected_messages}'):
            expected_indexes = list(range(len(expected_messages)))
            assert respond_index in expected_indexes, f'Wrong respond index.\nExpected: {expected_indexes}\n' \
                f'Actual: {respond_index}'
    finally:
        with allure.step('Recovery after test'):
            reinstall_nvos_after_test(serial_engine=serial_engine, restore_image_path=restore_image_path)
