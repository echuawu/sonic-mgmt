import pytest
import allure
import logging
import random
import time
from retry.api import retry_call

from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from infra.tools.validations.traffic_validations.iperf.iperf_runner import IperfChecker
from ngts.common.checkers import is_feature_ready

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
BUFFER_CONFIGURATIONS_DICT = {'lossless_double_ipool': ['egress_lossy_pool',
                                                        'ingress_lossless_pool',
                                                        'ingress_lossy_pool'],
                              'lossless_single_ipool': ['egress_lossy_pool',
                                                        'ingress_lossless_pool'],
                              'lossy_double_ipool': ['egress_lossy_pool',
                                                     'ingress_lossy_pool',
                                                     'ingress_lossy_pool']
                              }
BUFFER_CONFIGURATIONS = list(BUFFER_CONFIGURATIONS_DICT.keys())
RANDOM_CONFIG = random.choice(BUFFER_CONFIGURATIONS)
ROCE_PG = 'PG3'
DEFAULT_PG = 'PG0'

WATERMARK_THRESHOLD = '1000'


class TestDoroce:
    @pytest.fixture(scope='module')
    def check_feature_status(self, cli_objects):
        """
        An autouse fixture to check if DoRoCE fixture is installed and enabled
        """
        with allure.step('Validating doroce feature is installed, enabled and the container is running'):
            status, msg = is_feature_ready(cli_objects, 'doroce', 'doroce')
            if not status:
                pytest.skip(f"{msg} Skipping the test.")

        with allure.step('Validating doroce docker is UP'):
            cli_objects.dut.general.verify_dockers_are_up(dockers_list=['doroce'])

    @pytest.fixture(scope='module', autouse=True)
    def setup(self, topology_obj, cli_objects, engines, players, interfaces, check_feature_status, is_simx):
        """
        This fixture will do:
        1. configure the DUT speeds to generate buffer drops
        2. disable the DoRoCE if was enabled
        3. check the default buffer configuration
        4. run traffic and check that the default configurations are affected
        5. at the cleanup, steps 3-4 executed again


            ha                  DUT                     hb
        __________          ____________             __________
        |         |         |           |            |         |
        |         |         |           |            |         |
        |         |---------| TD        |------------|         |
        |_________|   1G    |___________|    25G     |_________|

        """
        self.topology = topology_obj
        self.cli_objects = cli_objects
        self.engines = engines
        self.players = players
        self.interfaces = interfaces
        self.is_simx = is_simx
        self.doroce_conf_dict = {'lossless_double_ipool': self.cli_objects.dut.doroce.config_doroce_lossless_double_ipool,
                                 'lossless_single_ipool': self.cli_objects.dut.doroce.config_doroce_lossless_single_ipool,
                                 'lossy_double_ipool': self.cli_objects.dut.doroce.config_doroce_lossy_double_ipool}

        # variable below is required for correct interfaces speed cleanup
        dut_original_interfaces_speeds = cli_objects.dut.interface.get_interfaces_speed([interfaces.dut_ha_1,
                                                                                         interfaces.dut_hb_1])
        with allure.step("Configuring dut_ha_1 speed to be 1G, and dut_hb_1 to be 25G"):
            interfaces_config_dict = {
                'dut': [{'iface': interfaces.dut_ha_2, 'speed': '1G',
                         'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_ha_2, '1G')},
                        {'iface': interfaces.dut_hb_2, 'speed': '25G',
                         'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_hb_2, '25G')}
                        ]
            }
        InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)

        if 'enabled' in self.cli_objects.dut.doroce.show_doroce_status():
            self.cli_objects.dut.doroce.disable_doroce()

        with allure.step('Doing config save'):
            logger.info('Doing config save')
            cli_objects.dut.general.save_configuration()

        self.run_ping()

        self.check_default_configurations()

        yield

        cli_objects.dut.doroce.disable_doroce()
        self.check_default_configurations()
        # enable back for Interop with other features
        self.cli_objects.dut.doroce.config_doroce_lossless_double_ipool()
        InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)
        with allure.step('Doing config save after cleanup'):
            logger.info('Doing config save after cleanup')
            cli_objects.dut.general.save_configuration()

    @pytest.mark.parametrize("configuration", BUFFER_CONFIGURATIONS)
    @allure.title('DoRoCE test case')
    def test_doroce(self, configuration):
        """
        Parametrized test, which running base DoRoCE test with different parameters
        :param configuration: DoRoCE configurations. {config:[expected pools]}
        """
        pools = BUFFER_CONFIGURATIONS_DICT[configuration]
        self.do_doroce_test(configuration, pools)

    @allure.title('DoRoCE toggle ports test case')
    def test_doroce_toggle_ports(self):
        """
        The Test toggling the related for traffic ports before running base DoRoCE test.
            The test will use random DoRoCE configurations.
        """
        pools = BUFFER_CONFIGURATIONS_DICT[RANDOM_CONFIG]
        self.do_doroce_test(RANDOM_CONFIG, pools, toggle_ports=True)

    def do_doroce_test(self, conf, pools, toggle_ports=False):
        """
        Base DoRoCE test. Parametrized test, which running base DoRoCE test with different parameters
        :param conf: DoRoCE configurations.
        :param pools: expected buffer pools.
        :param toggle_ports: flag used by test_doroce_toggle_ports to toggle ports to the hosts after doroce config
        """
        doroce_configuration_method = self.doroce_conf_dict[conf]
        doroce_configuration_method()

        if toggle_ports:
            self.toggle_ports()

        self.cli_objects.dut.doroce.check_buffer_configurations(pools)
        self.run_ping()

        self.validate_iperf_traffic(ROCE_PG)
        self.validate_negative_config(doroce_configuration_method)

    def run_ping(self):
        with allure.step('Check connectivity by ping traffic'):
            ping_checker = PingChecker(self.players, PING_VALIDATION)
            retry_call(ping_checker.run_validation, fargs=[], tries=3, delay=3, logger=logger)

    def validate_iperf_traffic(self, prio_group=DEFAULT_PG):
        if self.is_simx:
            logger.info('Skip traffic validation for SIMX devices')
        else:
            with allure.step('Sending iPerf traffic'):
                self.run_traffic()
            with allure.step('Validate buffers'):
                retry_call(self.validate_buffer, fargs=[prio_group], tries=8, delay=10, logger=logger)

    def run_traffic(self):
        self.cli_objects.dut.watermark.clear_watermarkstat()
        logger.info('Sending iPerf traffic')
        IperfChecker(self.players, IPERF_VALIDATION).run_validation()

    def validate_buffer(self, prio_group):
        stat_results = self.cli_objects.dut.watermark.show_and_parse_watermarkstat()
        assert stat_results[self.interfaces.dut_hb_2][prio_group] > WATERMARK_THRESHOLD, \
            f'Unexpected watermarkstat value for ROCE traffic({prio_group}).' \
            f' Current: {stat_results[self.interfaces.dut_hb_2][prio_group]}. Expected threshold: {WATERMARK_THRESHOLD}'

    @staticmethod
    def validate_negative_config(configuration_method, exp_err_msg='RoCE is already enabled'):
        with allure.step('Run negative validation'):
            output = configuration_method()
            assert exp_err_msg in output, f'Negative validation failed.\nExpected error message:"{exp_err_msg}" '\
                                          f'not found in the output: {output}'
            logger.info('The negative validation passed')

    def toggle_ports(self):
        ports = [self.interfaces.dut_ha_2, self.interfaces.dut_hb_2]
        logger.info("Toggle ports: {}".format(ports))
        for port in ports:
            self.cli_objects.dut.interface.disable_interface(port)
            self.cli_objects.dut.interface.enable_interface(port)
        self.cli_objects.dut.interface.check_link_state(ports)

    def check_default_configurations(self):
        with allure.step('Validate buffers'):
            self.cli_objects.dut.doroce.check_buffer_configurations()
            self.validate_iperf_traffic()
