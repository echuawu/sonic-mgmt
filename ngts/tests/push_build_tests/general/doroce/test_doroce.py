import pytest
import allure
import logging
import random
import time
from retry.api import retry_call

from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from infra.tools.validations.traffic_validations.iperf.iperf_runner import IperfChecker
from ngts.common.checkers import is_feature_installed
from ngts.constants.constants import AppExtensionInstallationConstants, SonicConst

logger = logging.getLogger()

"""

 DoRoCE Test Cases

 Documentation: https://confluence.nvidia.com/display/SW/SONiC+NGTS+DoRoCE+Documentation

"""

IPERF_VALIDATION = {
    'server': 'ha',
    'client': 'hb',
    'client_args': {
        'server_address': '40.0.0.2',
        'duration': '5',
        'protocol': 'UDP',
        'tos': '104'
    },
    'expect': [
        {
            'parameter': 'bandwidth',
            'operator': '>',
            'type': 'int',
            'value': '1'
        }
    ]
}
PING_VALIDATION = {'sender': 'hb', 'args': {'count': 3, 'dst': '40.0.0.2'}}
BUFFER_CONFIGURATIONS_DICT = {'lossless_double_ipool': ['egress_lossless_pool',
                                                        'egress_lossy_pool',
                                                        'ingress_lossless_pool',
                                                        'ingress_lossy_pool'],
                              'lossless_single_ipool': ['egress_lossless_pool',
                                                        'egress_lossy_pool',
                                                        'ingress_lossless_pool'],
                              'lossy_double_ipool': ['egress_lossy_pool',
                                                     'ingress_lossy_pool',
                                                     'roce_reserved_egress_pool',
                                                     'roce_reserved_ingress_pool']
                              }
BUFFER_CONFIGURATIONS = list(BUFFER_CONFIGURATIONS_DICT.keys())
RANDOM_CONFIG = random.choice(BUFFER_CONFIGURATIONS)
ROCE_PG = 'PG3'
NO_ROCE_PG = 'PG0'

WATERMARK_THRESHOLD = '1000'


@pytest.fixture(scope='module')
def check_feature_status(cli_objects):
    """
    A fixture to check if DoRoCE or DoAI is installed and enabled
    """
    def check_doai_installed():
        doai_status, msg = is_feature_installed(cli_objects, AppExtensionInstallationConstants.DOAI)
        return doai_status, msg, AppExtensionInstallationConstants.DOAI

    with allure.step('Validating doroce feature is installed'):
        status, msg, ext_name = check_doai_installed()
        if status:
            cli_objects.dut.app_ext.disable_app(ext_name)
            cli_objects.dut.app_ext.enable_app(ext_name)
            # TODO: workaround for the issue https://redmine.mellanox.com/issues/2834968
            # happens in push_gate with reload
            # when will be fixed, must be left only reload_qos
            cli_objects.dut.qos.clear_qos()
            time.sleep(10)
            cli_objects.dut.qos.reload_qos()
        else:
            pytest.skip(f"{msg} Skipping the test.")

    with allure.step(f'Validating {ext_name} docker is UP'):
        cli_objects.dut.general.verify_dockers_are_up(dockers_list=[ext_name])


@pytest.fixture(scope='module', autouse=True)
def pre_configuration_for_doroce(cli_objects, interfaces, check_feature_status):
    """
    This fixture is to config the a small shaper value on the egress port to create the buffer congestion.
    """
    port_scheduler = "port_scheduler"
    with allure.step("Config the shaper of the port"):
        cli_objects.dut.interface.config_port_scheduler(port_scheduler, SonicConst.MIN_SHAPER_RATE_BPS)
        cli_objects.dut.interface.config_port_qos_map(interfaces.dut_ha_2, port_scheduler)

    yield

    with allure.step("delete configured qos map and port scheduler"):
        cli_objects.dut.interface.del_port_qos_map(interfaces.dut_ha_2, port_scheduler)
        cli_objects.dut.interface.del_port_scheduler(port_scheduler)


@pytest.fixture(scope='module', autouse=True)
def check_no_roce_configuration(cli_objects, interfaces, players, is_simx, platform_params,
                                pre_configuration_for_doroce):
    check_no_roce_configurations(cli_objects, interfaces, players, is_simx, platform_params.hwsku)

    yield

    cli_objects.dut.doroce.disable_doroce()
    check_no_roce_configurations(cli_objects, interfaces, players, is_simx, platform_params.hwsku)


@pytest.fixture(scope='module')
def doroce_conf_dict(cli_objects):
    doroce_conf_dict = {'lossless_double_ipool': cli_objects.dut.doroce.config_doroce_lossless_double_ipool,
                        'lossless_single_ipool': cli_objects.dut.doroce.config_doroce_lossless_single_ipool,
                        'lossy_double_ipool': cli_objects.dut.doroce.config_doroce_lossy_double_ipool}
    return doroce_conf_dict


@pytest.mark.doroce
@pytest.mark.parametrize("configuration", BUFFER_CONFIGURATIONS)
@allure.title('DoRoCE test case')
def test_doroce(configuration, doroce_conf_dict, interfaces, cli_objects, players, is_simx):
    """
    Parametrized test, which running base DoRoCE test with different parameters
    :param configuration: DoRoCE configurations. {config:[expected pools]}
    :param doroce_conf_dict: dictionary with different doroce configuration methods
    :param interfaces: interfaces fixture
    :param cli_objects: cli_objects fixture
    :param players: players fixture
    :param is_simx: fixture, True if setup is SIMX, else False
    """
    pools = BUFFER_CONFIGURATIONS_DICT[configuration]
    do_doroce_test(configuration, pools, doroce_conf_dict, interfaces, cli_objects, players, is_simx)


@pytest.mark.doroce
@allure.title('DoRoCE toggle ports test case')
def test_doroce_toggle_ports(doroce_conf_dict, interfaces, cli_objects, players, is_simx):
    """
    The Test toggling the related for traffic ports before running base DoRoCE test.
        The test will use random DoRoCE configurations.
    :param doroce_conf_dict: dictionary with different doroce configuration methods
    :param interfaces: interfaces fixture
    :param cli_objects: cli_objects fixture
    :param players: players fixture
    :param is_simx: fixture, True if setup is SIMX, else False
    """
    pools = BUFFER_CONFIGURATIONS_DICT[RANDOM_CONFIG]
    do_doroce_test(RANDOM_CONFIG, pools, doroce_conf_dict, interfaces,
                   cli_objects, players, is_simx, do_toggle_ports=True)


def do_doroce_test(conf, pools, doroce_conf_dict, interfaces, cli_objects, players, is_simx, do_toggle_ports=False):
    """
    Base DoRoCE test. Parametrized test, which running base DoRoCE test with different parameters
    """
    doroce_configuration_method = doroce_conf_dict[conf]
    doroce_configuration_method()

    if do_toggle_ports:
        toggle_ports(interfaces, cli_objects)

    cli_objects.dut.doroce.check_buffer_configurations(pools)
    run_ping(players)

    retry_call(validate_iperf_traffic, fargs=[cli_objects, interfaces, players, is_simx, ROCE_PG],
               tries=4, delay=5, logger=logger)
    validate_negative_config(doroce_configuration_method)


def run_ping(players):
    with allure.step('Check connectivity by ping traffic'):
        ping_checker = PingChecker(players, PING_VALIDATION)
        retry_call(ping_checker.run_validation, fargs=[], tries=18, delay=5, logger=logger)


def validate_iperf_traffic(cli_objects, interfaces, players, is_simx, prio_group=NO_ROCE_PG):
    if is_simx:
        logger.info('Skip traffic validation for SIMX devices')
    else:
        with allure.step('Sending iPerf traffic'):
            run_traffic(cli_objects, players)
        with allure.step('Validate buffers'):
            retry_call(validate_buffer, fargs=[cli_objects, interfaces, prio_group], tries=8, delay=10, logger=logger)


def run_traffic(cli_objects, players):
    cli_objects.dut.watermark.clear_watermarkstat()
    logger.info('Sending iPerf traffic')
    IperfChecker(players, IPERF_VALIDATION).run_validation()


def validate_buffer(cli_objects, interfaces, prio_group):
    stat_results = cli_objects.dut.watermark.show_and_parse_watermarkstat()
    assert stat_results[interfaces.dut_hb_2][prio_group] > WATERMARK_THRESHOLD, \
        f'Unexpected watermark value for ROCE traffic({prio_group}).' \
        f' Current: {stat_results[interfaces.dut_hb_2][prio_group]}. Expected threshold: {WATERMARK_THRESHOLD}'


def validate_negative_config(configuration_method, exp_err_msg='RoCE is already enabled'):
    with allure.step('Run negative validation'):
        output = configuration_method()
        assert exp_err_msg in output, f'Negative validation failed.\nExpected error message:"{exp_err_msg}" '\
                                      f'not found in the output: {output}'
        logger.info('The negative validation passed')


def toggle_ports(interfaces, cli_objects):
    ports = [interfaces.dut_ha_2, interfaces.dut_hb_2]
    logger.info("Toggle ports: {}".format(ports))
    for port in ports:
        cli_objects.dut.interface.disable_interface(port)
        cli_objects.dut.interface.enable_interface(port)
    cli_objects.dut.interface.check_link_state(ports)


def check_no_roce_configurations(cli_objects, interfaces, players, is_simx, hwsku):
    with allure.step('Check no RoCE configurations'):
        cli_objects.dut.doroce.check_buffer_configurations(hwsku=hwsku)
        run_ping(players)
        retry_call(validate_iperf_traffic, fargs=[cli_objects, interfaces, players, is_simx],
                   tries=4, delay=5, logger=logger)
