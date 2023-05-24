'''
Secure Boot Suite case:

In this test file we introduce different cases for secure boot feature.
Secure Boot is a feature that validates secure boot and only signed modules are running.

In order to run this test, you need to specify the following argument: kernel_module_path
'''
import time
import random
import string
import logging
import allure
import pytest
import os
from ngts.tests_nvos.general.security.test_secure_boot.constants import SecureBootConsts
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
    lsmod_output = serial_engine.run_cmd_and_get_output('lsmod | grep \"{}\"'.format(kernel_module_filename.split('.')[0]))
    assert kernel_module_filename.split('.')[0] in lsmod_output, "secure kernel module: {}, is not showing in lsmod output".format(kernel_module_filename.split('.')[0])


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
    _, respond = serial_engine.run_cmd('\r', [DefaultConnectionValues.LOGIN_REGEX] + DefaultConnectionValues.DEFAULT_PROMPTS)
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


@pytest.mark.checklist
@pytest.mark.secure_boot
def test_unsigned_shim_secure_boot(serial_engine, mount_uefi_disk_partition, test_server_engine, restore_image_path,
                                   validate_all_dockers_are_up_after_nvos_boot, is_secure_boot_enabled):
    '''
    @summary: in this test case we want to simulate broken signature of shim
    by manually changing it and then do reboot and see that it does not boot successfully
    :param serial_engine: serial connection
    '''
    unsigned_file_secure_boot(serial_engine,
                              secure_component=SecureBootConsts.SHIM_FILEPATH,
                              test_server_engine=test_server_engine,
                              restore_image_path=restore_image_path)


@pytest.mark.checklist
@pytest.mark.secure_boot
def test_unsigned_grub_secure_boot(serial_engine, mount_uefi_disk_partition, test_server_engine, restore_image_path,
                                   validate_all_dockers_are_up_after_nvos_boot, is_secure_boot_enabled):
    '''
    @summary: in this test case we want to simulate broken signature of grub
    by manually changing it and then do reboot and see that it does not boot successfully
    :param serial_engine: serial connection
    '''
    unsigned_file_secure_boot(serial_engine,
                              secure_component=SecureBootConsts.GRUB_FILEPATH,
                              test_server_engine=test_server_engine,
                              restore_image_path=restore_image_path)


@pytest.mark.checklist
@pytest.mark.secure_boot
def test_unsigned_vmlinuz_secure_boot(serial_engine, test_server_engine, restore_image_path, vmlinuz_filepath,
                                      validate_all_dockers_are_up_after_nvos_boot, is_secure_boot_enabled):
    '''
    @summary: in this test case we want to simulate broken signature of vmiluz component
    by manually changing it and then do reboot and see that it does not boot successfully
    :param serial_engine: serial connection
    '''
    unsigned_file_secure_boot(serial_engine,
                              secure_component=vmlinuz_filepath,
                              test_server_engine=test_server_engine,
                              restore_image_path=restore_image_path)
