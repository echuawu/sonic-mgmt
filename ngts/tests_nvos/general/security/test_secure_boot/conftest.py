import re
import pytest
import logging
from infra.tools.connection_tools.pexpect_serial_engine import PexpectSerialEngine
from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.tests_nvos.general.security.test_secure_boot.constants import SecureBoootConsts
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit


logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """
    secure boot NVOS pytest options
    :param parser: pytest buildin
    """
    parser.addoption('--kernel_module_path', action='store',
                     help='Kernel modules path to test')


@pytest.fixture(scope='function')
def serial_engine(topology_obj):
    """
    :return: serial connection
    """
    att = topology_obj.players['dut_serial']['attributes'].noga_query_data['attributes']
    # add connection options to pass connection problems
    extended_rcon_command = att['Specific']['serial_conn_cmd']
    serial_engine = PexpectSerialEngine(ip=att['Specific']['ip'],
                                        username=att['Topology Conn.']['CONN_USER'],
                                        password=att['Topology Conn.']['CONN_PASSWORD'],
                                        rcon_command=extended_rcon_command,
                                        timeout=30)
    serial_engine.create_serial_engine()
    return serial_engine


@pytest.fixture(scope='function')
def kernel_module_path(request):
    '''
    @summary: in this fixture we want to uplaod the kernel module
    to the duthost and after test run we want to clean it
    '''
    kernel_moudle_path = request.config.getoption('kernel_module_path')
    assert (kernel_moudle_path, "Please specify the path to the kernel module to the test")
    return kernel_moudle_path


@pytest.fixture(scope='function')
def kernel_module_filename(kernel_module_path):
    '''
    @summary: extracting the kernel module filenmae
    :param kernel_module_path: the path
    :return: the filename
    '''
    kernel_module_filename = kernel_module_path.split('/')[-1]
    return kernel_module_filename


@pytest.fixture(scope='function')
def remove_kernel_module(kernel_module_filename, serial_engine):
    '''
    @summary: will remove kernel module if it is installed before and after test run
    :param kernel_module_path:
    '''
    logger.info("Unloading kernel module {} if it exists before running the test".format(kernel_module_filename))
    serial_engine.run_cmd_and_get_output('sudo rmmod {}'.format(kernel_module_filename.split('.')[0]))

    yield

    logger.info("Unloading kernel module {} if it exists after running the test".format(kernel_module_filename))
    serial_engine.run_cmd_and_get_output('sudo rmmod {}'.format(kernel_module_filename.split('.')[0]))


@pytest.fixture(scope='function')
def restore_image_path(request):
    '''
    @summary: return the path to restore image
    '''
    restore_to_image = request.config.getoption('restore_to_image')
    assert restore_to_image is not None, "Please specify restore image path"
    return restore_to_image


@pytest.fixture(scope='function')
def test_server_engine(engines, serial_engine):
    '''
    @summary: will return the sonic-mgmt-test server engine
    '''
    player = engines['sonic_mgmt']
    return player


@pytest.fixture(scope='function')
def upload_kernel_module(kernel_module_path, test_server_engine, serial_engine):
    '''
    @summary: in this fixture we will upload the kernel module path
    and delete it as a cleanup
    :param kernel_module_path: kernel module path
    '''
    logger.info("Uploading the kernel module at {} to switch under {}".format(kernel_module_path,
                                                                              SecureBoootConsts.TMP_FOLDER))
    # player engine will used to upload the kernel modules files
    test_server_engine.upload_file_using_scp(serial_engine.username, serial_engine.password, serial_engine.ip,
                                             kernel_module_path, SecureBoootConsts.TMP_FOLDER)
    kernel_module_filename = kernel_module_path.split('/')[-1]
    logger.info("Validating file is successfully uploaded")
    serial_engine.run_cmd_and_get_output('ls {} | grep {}'.format(SecureBoootConsts.TMP_FOLDER,
                                                                  kernel_module_filename))

    yield kernel_module_filename

    logger.info("Deleting upload kernel file")
    serial_engine.run_cmd('sudo rm -f {}/{}'.format(SecureBoootConsts.TMP_FOLDER, kernel_module_filename))


@pytest.fixture(scope='function')
def vmiluz_filepath(serial_engine):
    '''
    @summary: will return the filepath of vmlinuz
    :param serial_engine:
    '''
    output = serial_engine.run_cmd_and_get_output('ls {}'.format(SecureBoootConsts.VMILUNZ_DIR)).decode('utf-8')
    path = re.findall(SecureBoootConsts.VMILUNZ_REGEX, output)[0]
    return SecureBoootConsts.VMILUNZ_DIR + path


@pytest.fixture(scope='function')
def mount_uefi_disk_partition(serial_engine):
    '''
    @summary: will load the uefi disk partition
    :param serial_engine: serial connection
    '''
    logger.info("mounting UEFI disk partition at {}".format(SecureBoootConsts.MOUNT_FOLDER))
    serial_engine.run_cmd_and_get_output(SecureBoootConsts.ROOT_PRIVILAGE)
    serial_engine.run_cmd_and_get_output("mkdir {}".format(SecureBoootConsts.MOUNT_FOLDER))
    output = serial_engine.run_cmd(SecureBoootConsts.EFI_PARTITION_CMD,
                                   SecureBoootConsts.LAST_OCCURENCE_REGEX.format('#'))[0].decode('utf-8')
    uefi_partition = re.findall('\\/dev\\/sda\\d', output)[0]
    serial_engine.run_cmd("mount -o rw,auto,user,fmask=0022,dmask=0000 {} {}".format(uefi_partition,
                                                                                     SecureBoootConsts.MOUNT_FOLDER))


@pytest.fixture(scope='function')
def validate_all_dockers_are_up_after_nvos_boot(serial_engine, cli_objects):
    '''
    @summary: validating all dockers are up
    '''
    yield

    # verify dockers are up
    TestToolkit.engines.dut.disconnect()
    nvue_cli = NvueGeneralCli(TestToolkit.engines.dut)
    nvue_cli.verify_dockers_are_up()
