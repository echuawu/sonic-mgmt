import allure
import logging
import pytest

from ngts.tests.nightly.fdb.fdb_helper import traffic_validation, gen_test_interface_data, \
    DUMMY_MACS, verify_mac_saved_to_fdb_table, verify_mac_not_in_fdb_table
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.vlan_config_template import VlanConfigTemplate

logger = logging.getLogger()


@pytest.mark.usefixtures("pre_configure_for_fdb_advance")
class TestFdbAdvance:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines, cli_objects, interfaces, players):
        self.topology_obj = topology_obj
        self.engines = engines
        self.interfaces = interfaces
        self.players = players
        self.src_mac = DUMMY_MACS[0]
        self.vlan_id1 = "40"
        self.vlan_id2 = "50"
        self.port1 = self.interfaces.dut_ha_1
        self.port2 = self.interfaces.dut_ha_2
        self.receive_packet_counts = [1]

    @allure.title('Test fdb item with same mac in different vlan')
    def test_fdb_with_same_mac_in_different_vlan(self):
        """
        Verify fdb item with same mac can exist in different vlan
        1. Clear fdb table
        2. Send packet from ha-dut-1, ha-dut-2 with the same source MAC
        3. Verify there are two fdb item with same mac in different vlan
        """
        with allure.step(f"Send packet from  ha-dut-1 with the source MAC:{self.src_mac}"):
            self.generate_dynamic_fdb_item(self.vlan_id1)
        with allure.step(f"Send packet from  ha-dut-2 with the source MAC:{self.src_mac}"):
            self.generate_dynamic_fdb_item(self.vlan_id2)
        with allure.step("Verify there are two fdb item with same mac in different vlan"):
            verify_mac_saved_to_fdb_table(self.engines, self.vlan_id1, self.src_mac, self.port1)
            verify_mac_saved_to_fdb_table(self.engines, self.vlan_id2, self.src_mac, self.port2)

    @allure.title('Test fdb item will be removed after shutdown the corresponding port')
    def test_fdb_item_be_removed_after_shutdown_corresponding_port(self):
        """
        Verify fdb item will be removed after the corresponding port is shutdown
        1. Clear fdb table
        2. Host A sends a packet to Host B
        3. Shutdown dut-ha-1
        4. Verify the fdb items related to dut-ha-1 are removed
        """
        try:
            with allure.step("Host A sends a packet to Host B"):
                self.generate_dynamic_fdb_item(self.vlan_id1)
                verify_mac_saved_to_fdb_table(self.engines, self.vlan_id1, self.src_mac, self.port1)
            with allure.step("Shutdown dut-ha-1"):
                SonicInterfaceCli.disable_interface(self.engines.dut, self.port1)
            with allure.step("Verify the fdb items related to dut-ha-1 are removed"):
                verify_mac_not_in_fdb_table(self.engines, self.vlan_id1, self.src_mac, self.port1)

        except Exception as err:
            raise AssertionError(err)
        finally:
            SonicInterfaceCli.enable_interface(self.engines.dut, self.port1)

    @allure.title('Test fdb item will be removed after removing the corresponding vlan')
    def test_fdb_item_be_removed_after_removing_corresponding_vlan(self):
        """
        Verify fdb item will not be removed after the corresponding vlan is removed
        1. Clear fdb table
        2. Host A sends a packet to Host B
        3. Remove the vlan related to the fdb item
        4. Verify the fdb item related to vlan is removed
        """
        vlan_config_dict = {
            'dut': [{'vlan_id': 40, 'vlan_members': [{self.interfaces.dut_ha_1: 'access'},
                                                     {self.interfaces.dut_hb_1: 'access'}]}
                    ],
        }
        try:
            with allure.step("Host A sends a packet to Host B"):
                self.generate_dynamic_fdb_item(self.vlan_id1)
                verify_mac_saved_to_fdb_table(self.engines, self.vlan_id1, self.src_mac, self.port1)
            with allure.step(f"Remove vlan {self.vlan_id1}"):
                VlanConfigTemplate.cleanup(self.topology_obj, vlan_config_dict)
            with allure.step(f"Verify the fdb item related to vlan {self.vlan_id1}  is removed from fdb table "):
                verify_mac_not_in_fdb_table(self.engines, self.vlan_id1, self.src_mac, self.port1)

        except Exception as err:
            raise AssertionError(err)
        finally:
            VlanConfigTemplate.configuration(self.topology_obj, vlan_config_dict)

    def generate_dynamic_fdb_item(self, vlan_id):
        """
        Generate dynamic fdb item
        """
        interface_data = gen_test_interface_data(self.engines, self.interfaces, vlan_id)
        traffic_validation(self.players, self.interfaces, interface_data, self.src_mac, "icmp", self.receive_packet_counts)
