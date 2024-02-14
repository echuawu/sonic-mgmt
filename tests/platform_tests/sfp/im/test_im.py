import pytest

from tests.platform_tests.sfp.im.helpers import *
from tests.common.config_reload import config_reload

cmd_interface_transceiver = "show interface transceiver eeprom"
cmd_sfputil_eeprom = "sudo sfputil show eeprom"
cmd_interface_transceiver_status = "show interfaces transceiver status"
cmd_redis_tranceiver_info = 'redis-cli -n 6 hgetall "TRANSCEIVER_INFO|{}"'
cmd_redis_tranceiver_status = 'redis-cli -n 6 hgetall "TRANSCEIVER_STATUS|{}"'

pytestmark = [
    pytest.mark.topology('any')
]


class TestIndependentModuleFunctional:

    @pytest.fixture(autouse=True)
    def setup(self, duthosts, enum_rand_one_per_hwsku_frontend_hostname, enum_frontend_asic_index, conn_graph_facts):
        self.duthost = duthosts[enum_rand_one_per_hwsku_frontend_hostname]
        self.enum_frontend_asic_index = enum_frontend_asic_index
        self.conn_graph_facts = conn_graph_facts
        self.im_port_list = get_ports_supporting_im(self.duthost, self.conn_graph_facts)

        # Check IM enabled in sai.profile. If not - whole test suite will be skipped
        check_im_sai_attribute_value(self.duthost)

    def test_im_check_show_interfaces_transceiver_eeprom(self):
        """
        @summary: Check SFP transceiver info using 'show interface transceiver eeprom'
        """
        for port in self.im_port_list:
            sfp_show_eeprom = self.duthost.command(f"{cmd_interface_transceiver} {port}")
            parsed_eeprom = parse_im_eeprom(sfp_show_eeprom["stdout"])
            redis_output = parse_sfp_info_from_redis(self.duthost, cmd_redis_tranceiver_info,
                                                     self.enum_frontend_asic_index, [port])

            # Compare information from eeprom and redis
            for cli_eeprom_key, redis_key in EEPROM_TO_REDIS_KEY_MAP.items():
                assert parsed_eeprom[cli_eeprom_key.replace("\\", "")] == redis_output[port][redis_key], \
                    f"Data from cli param {cli_eeprom_key} does not match data from redis" \
                    f" {redis_output[port][redis_key]}"

    def test_check_im_sfputil_eeprom_params(self):
        """
        @summary: Check sfputils eeprom output with  Independent Module enabled
        """

        for port in self.im_port_list:
            sfp_show_eeprom = self.duthost.command(f"{cmd_sfputil_eeprom} -p {port}")
            parsed_eeprom = parse_im_eeprom(sfp_show_eeprom["stdout"])
            redis_output = parse_sfp_info_from_redis(self.duthost, cmd_redis_tranceiver_info,
                                                     self.enum_frontend_asic_index, [port])

            # Compare information from eeprom and redis
            for cli_eeprom_key, redis_key in EEPROM_TO_REDIS_KEY_MAP.items():
                assert parsed_eeprom[cli_eeprom_key.replace("\\", "")] == redis_output[port][redis_key], \
                    f"Data from cli param {cli_eeprom_key} does not data from redis"

    def test_im_check_show_interfaces_transceiver_status(self):
        """
        @summary: Check SFP transceiver info using 'show interface transceiver status'
        """
        for port in self.im_port_list:
            show_transceiver_status = self.duthost.command(f"{cmd_interface_transceiver_status} {port}")
            parsed_tranceiver_status = parse_im_tranceiver_status(show_transceiver_status["stdout"])
            redis_output = parse_sfp_info_from_redis(self.duthost, cmd_redis_tranceiver_status,
                                                     self.enum_frontend_asic_index, [port])
            # Compare information from cli and redis
            for cli_eeprom_key, redis_key in TRANSCEIVER_STATUS_TO_REDIS_KEY_MAP.items():
                assert parsed_tranceiver_status[cli_eeprom_key] == redis_output[port][redis_key], \
                    f"Data from cli param {cli_eeprom_key} does not data from redis"

    def test_im_ber(self):
        """
        @summary: Check that BER per IM is not bigger than cable BER threshold
        """
        for port in self.im_port_list:
            mlxlink_output = get_mlxlink_ber(self.duthost, port)
            assert int(mlxlink_output[BER_EFFECTIVE_PHYSICAL_ERRORS]) == 0, f"{BER_EFFECTIVE_PHYSICAL_ERRORS} > 0 "
            assert mlxlink_output[BER_EFFECTIVE_PHYSICAL_BER] == '15E-255', f"{BER_EFFECTIVE_PHYSICAL_BER} > 15E-255"
