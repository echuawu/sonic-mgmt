import re
import time
import pytest
import logging
from infra.tools.connection_tools.pexpect_serial_engine import PexpectSerialEngine
from infra.tools.general_constants.constants import DefaultConnectionValues
from infra.tools.validations.traffic_validations.ping.send import ping_till_alive
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.tests_nvos.general.security.test_secure_boot.constants import SecureBootConsts
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.tools.test_utils import allure_utils as allure
from ngts.tools.test_utils.nvos_general_utils import get_real_file_path

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def restore_image_path(request):
    '''
    @summary: return the path to restore image
    '''
    restore_to_image = request.config.getoption('restore_to_image')
    assert restore_to_image is not None, "Please specify restore image path"
    restore_to_image = get_real_file_path(restore_to_image)
    logger.info(f'After test will recover to image: {restore_to_image}')
    return restore_to_image


@pytest.fixture(scope='function')
def mount_uefi_disk_partition(serial_engine):
    '''
    @summary: will load the uefi disk partition
    :param serial_engine: serial connection
    '''
    logger.info("mounting UEFI disk partition at {}".format(SecureBootConsts.MOUNT_FOLDER))
    serial_engine.run_cmd_and_get_output(SecureBootConsts.ROOT_PRIVILAGE)
    serial_engine.run_cmd_and_get_output("mkdir {}".format(SecureBootConsts.MOUNT_FOLDER))
    output = serial_engine.run_cmd(SecureBootConsts.EFI_PARTITION_CMD,
                                   SecureBootConsts.LAST_OCCURENCE_REGEX.format('#'))[0]
    uefi_partition = re.findall('\\/dev\\/sda\\d', output)[0]
    serial_engine.run_cmd("mount -o rw,auto,user,fmask=0022,dmask=0000 {} {}".format(uefi_partition,
                                                                                     SecureBootConsts.MOUNT_FOLDER))
