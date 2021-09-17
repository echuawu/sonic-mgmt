import pytest
import logging
import allure
from ngts.cli_wrappers.sonic.sonic_p4_sampling_clis import P4SamplingCli
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from dotted_dict import DottedDict
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.constants.constants import P4SamplingConsts
from ngts.constants.constants import P4SamplingEntryConsts
import ngts.helpers.p4_sampling_fixture_helper as fixture_helper
logger = logging.getLogger()

pytestmark = [
    pytest.mark.disable_loganalyzer,  # disable automatic loganalyzer
]

PORT_TABLE_NAME = P4SamplingConsts.PORT_TABLE_NAME
FLOW_TABLE_NAME = P4SamplingConsts.FLOW_TABLE_NAME
ACTION_NAME = P4SamplingConsts.ACTION_NAME


@pytest.mark.build
@pytest.mark.usefixtures('skipping_p4_sampling_test_case_for_spc1')
@pytest.mark.p4_sampling
class TestNegativeConfig:

    @pytest.fixture(scope='class')
    def table_params(self, interfaces, engines, topology_obj, hb_dut_1_mac):
        """
        Fixture used to create the TableParams object which contains some params used in the testcases
        :param interfaces: interfaces fixture
        :param:engines : engines object fixture
        :param: topology_obj: topology_obj object fixture
        :param hb_dut_1_mac: hb_dut_1_mac object fixture
        """
        table_param_data = DottedDict()

        table_param_data.l3_mirror_vlan = 40
        table_param_data.l3_mirror_is_truc = 'True'
        table_param_data.l3_mirror_truc_size = 300
        table_param_data.chksum_expect_value = 0x21
        table_param_data.chksum_mask = 0x43
        cli_object = topology_obj.players['dut']['cli']
        duthb1_mac = cli_object.mac.get_mac_address_for_interface(
            engines.dut, topology_obj.ports['dut-ha-1'])
        table_param_data.port_key = '{} {}/{}'.format(interfaces.dut_ha_2,
                                                      table_param_data.chksum_expect_value,
                                                      table_param_data.chksum_mask)
        table_param_data.port_action_param = '{} {} {} {} {} {} {} {}'.format(interfaces.dut_hb_1, duthb1_mac, hb_dut_1_mac,
                                                                              P4SamplingEntryConsts.duthb1_ip, P4SamplingEntryConsts.hbdut1_ip,
                                                                              table_param_data.l3_mirror_vlan,
                                                                              table_param_data.l3_mirror_is_truc,
                                                                              table_param_data.l3_mirror_truc_size)
        table_param_data.port_priority = 12
        protocol = 6
        src_port = 20
        dst_port = 20
        table_param_data.flow_key = '{} {} {} {} {} {}/{}'.format(P4SamplingEntryConsts.hadut2_ip, P4SamplingEntryConsts.hbdut2_ip, protocol, src_port,
                                                                  dst_port, table_param_data.chksum_expect_value, table_param_data.chksum_mask)
        table_param_data.flow_action_param = '{} {} {} {} {} {} {} {}'.format(interfaces.dut_hb_1, duthb1_mac, hb_dut_1_mac,
                                                                              P4SamplingEntryConsts.duthb1_ip, P4SamplingEntryConsts.hbdut1_ip,
                                                                              table_param_data.l3_mirror_vlan, table_param_data.l3_mirror_is_truc,
                                                                              table_param_data.l3_mirror_truc_size)
        table_param_data.flow_priority = 12
        return table_param_data

    @allure.title('Test P4 sampling command, such as add, delete, show when the p4-sampling feature is disabled')
    def test_sampling_cmd_with_disabled(self, engines, table_params):
        """
        Verify the add, remove and show command when the p4-sampling is disabled.
        :param engines: engines fixture
        :param table_params: table_params fixture
        """
        expect_error_msg = 'Error: "p4-sampling" feature is disabled, run "config feature state p4-sampling enabled"'
        with allure.step('Disable {}'.format(P4SamplingConsts.APP_NAME)):
            SonicGeneralCli.set_feature_state(
                engines.dut, P4SamplingConsts.APP_NAME, 'disabled')

        with allure.step('Verify add, delete and show command for the table_port_sampling'):
            port_table_entry_params = "key {} action {} {} priority {}".format(
                table_params.port_key,
                ACTION_NAME,
                table_params.port_action_param,
                table_params.port_priority)
            with allure.step('Verify add entry to port table output'):
                verify_show_cmd(P4SamplingCli.add_entry_to_table(engines.dut, PORT_TABLE_NAME, port_table_entry_params),
                                expected_output_list=[(r'{}'.format(expect_error_msg), True)])
            with allure.step('Verifying remove entry from port table output'):
                verify_show_cmd(P4SamplingCli.delete_entry_from_table(engines.dut, PORT_TABLE_NAME, "key {}".format(table_params.port_key)),
                                expected_output_list=[(r'Error: "p4-sampling" feature is disabled, run "config feature '
                                                       r'state p4-sampling enabled"', True)])
            with allure.step('Verifying show entries of port table output'):
                verify_show_cmd(P4SamplingCli.show_table_entries(engines.dut, PORT_TABLE_NAME),
                                expected_output_list=[(r'Error: "p4-sampling" feature is disabled, run "config feature '
                                                       r'state p4-sampling enabled"', True)])
            with allure.step('Verifying show counters of port table output'):
                verify_show_cmd(P4SamplingCli.show_table_counters(engines.dut, PORT_TABLE_NAME),
                                expected_output_list=[(r'Error: "p4-sampling" feature is disabled, run "config feature '
                                                       r'state p4-sampling enabled"', True)])

        with allure.step('Verify add, delete and show command for the table_flow_sampling'):

            flow_table_entry_params = "key {} action {} {} priority {}".format(table_params.flow_key, ACTION_NAME,
                                                                               table_params.flow_action_param, table_params.flow_priority)
            with allure.step('Verify add entry to flow table output'):
                verify_show_cmd(P4SamplingCli.add_entry_to_table(engines.dut, FLOW_TABLE_NAME,
                                                                 flow_table_entry_params),
                                expected_output_list=[(r'Error: "p4-sampling" feature is disabled, run "config feature '
                                                       r'state p4-sampling enabled"', True)])
            with allure.step('Verify remove entry from flow table output'):
                verify_show_cmd(P4SamplingCli.delete_entry_from_table(engines.dut, FLOW_TABLE_NAME,
                                                                      "key {}".format(table_params.flow_key)),
                                expected_output_list=[(r'Error: "p4-sampling" feature is disabled, run "config feature '
                                                       r'state p4-sampling enabled"', True)])
            with allure.step('Verify show entries of flow table output'):
                verify_show_cmd(P4SamplingCli.show_table_entries(engines.dut, FLOW_TABLE_NAME),
                                expected_output_list=[(r'Error: "p4-sampling" feature is disabled, run "config feature '
                                                       r'state p4-sampling enabled"', True)])
            with allure.step('Verify show counters of flow table output'):
                verify_show_cmd(P4SamplingCli.show_table_counters(engines.dut, FLOW_TABLE_NAME),
                                expected_output_list=[(r'Error: "p4-sampling" feature is disabled, run "config feature '
                                                       r'state p4-sampling enabled"', True)])

        with allure.step('Enable {}'.format(P4SamplingConsts.APP_NAME)):
            SonicGeneralCli.set_feature_state(
                engines.dut, P4SamplingConsts.APP_NAME, 'enabled')

    @allure.title('Test P4 sampling add, delete entry with negative keys')
    def test_sampling_entry_with_negative_key(self, engines, table_params):
        """
        Verify p4-sampling add, remove entry related cli command with wrong key specified.
        :param engines: engines fixture
        :param table_params: table_params fixture
        """
        with allure.step('Verify add, delete and show command for the table_port_sampling'):
            expect_error_msg_list = ['Error: Invalid value for "key": Illegal key keyword \\S+. Use "key" keyword',
                                     'Error: Invalid value for "<key_port>": Illegal port \\S+. '
                                     'Only physical.*ports are supported',
                                     'Error: Invalid value for "<key_checksum_value/key_checksum_mask>": '
                                     'Illegal key_checksum_value/key_checksum_mask \\S+. Value/mask are 2 Hex Bytes']

            port_table_entry_params_list = ["action {} {} priority {}".format(ACTION_NAME, table_params.port_action_param,
                                                                              table_params.port_priority),
                                            "key {} action {} {} priority {}".format(table_params.port_key.split()[1],
                                                                                     ACTION_NAME,
                                                                                     table_params.port_action_param,
                                                                                     table_params.port_priority),
                                            "key {} action {} {} priority {}".format(table_params.port_key.split()[0],
                                                                                     ACTION_NAME,
                                                                                     table_params.port_action_param,
                                                                                     table_params.port_priority)
                                            ]
            for expect_error_msg, port_table_entry_params in zip(
                    expect_error_msg_list, port_table_entry_params_list):
                with allure.step('Verify add entry to port table output with negative key: {}'.format(port_table_entry_params)):
                    verify_show_cmd(
                        P4SamplingCli.add_entry_to_table(
                            engines.dut, PORT_TABLE_NAME, port_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
            expect_delete_error_msg_list = ['Error: Missing argument "key"',
                                            'Error: Invalid value for "<key_port>": Illegal port \\S+. '
                                            'Only physical.*ports are supported',
                                            'Error: Missing argument "<key_checksum_value/key_checksum_mask>"']

            port_table_key_param_list = ["", "key {}".format(table_params.port_key.split()[1]),
                                         "key {}".format(table_params.port_key.split()[0])]

            for expect_error_msg, port_table_key_param in zip(
                    expect_delete_error_msg_list, port_table_key_param_list):
                with allure.step('Verify remove entry from port table output with negative key: {}'.format(port_table_key_param)):
                    verify_show_cmd(
                        P4SamplingCli.delete_entry_from_table(
                            engines.dut, PORT_TABLE_NAME, port_table_key_param),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])

        with allure.step('Verify add, delete and show command for the table_flow_sampling'):
            expect_error_msg_list = ['Error: Invalid value for "key": Illegal key keyword \\S+. Use "key" keyword',
                                     'Error: Invalid value for "<key_dst_ip>": Invalid IPv4 address \\S+',
                                     'Error: Invalid value for "<key_l4_dst_port>": \\S+ is not a valid integer',
                                     'Error: Invalid value for "<key_checksum_value/key_checksum_mask>": '
                                     'Illegal key_checksum_value/key_checksum_mask \\S+. Value/mask are 2 Hex Bytes']

            flow_table_entry_params_list = ["action {} {} priority {}".format(ACTION_NAME, table_params.flow_action_param,
                                                                              table_params.flow_priority),
                                            "key {} action {} {} priority {}".format(' '.join(table_params.flow_key.split()[1:6]),
                                                                                     ACTION_NAME,
                                                                                     table_params.flow_action_param,
                                                                                     table_params.flow_priority),
                                            "key {} action {} {} priority {}".format(
                ' '.join(table_params.flow_key.split()[
                         :4] + [table_params.flow_key.split()[5]]),
                                                ACTION_NAME,
                                                table_params.flow_action_param,
                                                table_params.flow_priority),
                "key {} action {} {} priority {}".format(' '.join(table_params.flow_key.split()[:5]),
                                                         ACTION_NAME,
                                                         table_params.flow_action_param,
                                                         table_params.flow_priority)
            ]

            for expect_error_msg, flow_table_entry_params in zip(
                    expect_error_msg_list, flow_table_entry_params_list):
                with allure.step('Verify add entry to port table output with negative key: {}'.format(flow_table_entry_params)):
                    verify_show_cmd(
                        P4SamplingCli.add_entry_to_table(
                            engines.dut, FLOW_TABLE_NAME, flow_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])

            expect_delete_error_msg_list = ['Error: Missing argument "key"',
                                            'Error: Invalid value for "<key_dst_ip>": Invalid IPv4 address \\S+',
                                            'Error: Invalid value for "<key_l4_dst_port>": \\S+ is not a valid integer',
                                            'Error: Missing argument "<key_checksum_value/key_checksum_mask>"']

            flow_table_key_param_list = ["",
                                         "key {}".format(
                                             ' '.join(table_params.flow_key.split()[1:6])),
                                         "key {}".format(
                                             ' '.join(table_params.flow_key.split()[:4] + [table_params.flow_key.split()[5]])),
                                         "key {}".format(' '.join(table_params.flow_key.split()[:5]))]

            for expect_error_msg, flow_table_key_param in zip(
                    expect_delete_error_msg_list, flow_table_key_param_list):
                with allure.step('Verify remove entry from port table output with negative key: {}'.format(flow_table_key_param)):
                    verify_show_cmd(
                        P4SamplingCli.delete_entry_from_table(
                            engines.dut, FLOW_TABLE_NAME, flow_table_key_param),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])

    @allure.title('Test P4 sampling add entry with negative action')
    def test_sampling_entry_with_negative_action(self, engines, table_params):
        """
        Verify p4-sampling add entry related cli command with wrong action specified.
        :param engines: engines fixture
        :param table_params: table_params fixture
        """
        with allure.step('Verify add entry for the table_port_sampling'):
            expect_error_msg_list = ['Invalid value for "action": Illegal action keyword \\S+. Use "action" keyword',
                                     'Error: Invalid value for "<action_name>": Illegal action_name \\S+. '
                                     'Only "DoMirror" action is supported',
                                     'Error: Invalid value for "<l3_mirror_port>": Illegal port \\S+. '
                                     'Only physical.*ports are supported',
                                     'Error: Invalid value for "<l3_mirror_port>": Illegal port \\S+. '
                                     'Only physical.*ports are supported',
                                     'Error: Invalid value for "<l3_mirror_dmac>": Invalid MAC address \\S+',
                                     'Error: Invalid value for "<l3_mirror_dip>": Invalid IPv4 address \\S+',
                                     'Error: Invalid value for "<l3_mirror_truc_size>": \\S+ is not a valid integer',
                                     'Error: Missing argument "priority"']

            port_table_entry_params_list = ["key {} priority {}".format(table_params.port_key, table_params.port_priority),
                                            "key {} action {} priority {}".format(
                table_params.port_key, table_params.port_action_param, table_params.port_priority),
                "key {} action {} priority {}".format(table_params.port_key, ACTION_NAME,
                                                      table_params.port_priority),
                "key {} action {} {} priority {}".format(table_params.port_key,
                                                         ACTION_NAME,
                                                         " ".join(
                                                             table_params.port_action_param.split()[1:]),
                                                         table_params.port_priority),
                "key {} action {} {} priority {}".format(table_params.port_key,
                                                         ACTION_NAME,
                                                         " ".join([table_params.port_action_param.split()[
                                                             0]] + table_params.port_action_param.split()[2:8]),
                                                         table_params.port_priority),
                "key {} action {} {} priority {}".format(table_params.port_key,
                                                         ACTION_NAME,
                                                         " ".join(
                                                             table_params.port_action_param.split()[:3] +
                                                             table_params.port_action_param.split()[4:8]),
                                                         table_params.port_priority),
                "key {} action {} {} priority {}".format(table_params.port_key,
                                                         ACTION_NAME,
                                                         " ".join(table_params.port_action_param.split()[
                                                             :7]), table_params.port_priority),
                "key {} action {} {}".format(table_params.port_key,
                                             ACTION_NAME,
                                             " ".join(table_params.port_action_param.split()[
                                                 :8]))
            ]

            for expect_error_msg, port_table_entry_params in zip(
                    expect_error_msg_list, port_table_entry_params_list):
                with allure.step('Verify add entry to port table output with negative action: {}'.format(port_table_entry_params)):
                    verify_show_cmd(
                        P4SamplingCli.add_entry_to_table(
                            engines.dut, PORT_TABLE_NAME, port_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])

        with allure.step('Verify add entry for the table_flow_sampling'):
            expect_error_msg_list = ['Invalid value for "action": Illegal action keyword \\S+. Use "action" keyword',
                                     'Error: Invalid value for "<action_name>": Illegal action_name \\S+. '
                                     'Only "DoMirror" action is supported',
                                     'Error: Invalid value for "<l3_mirror_port>": Illegal port \\S+. '
                                     'Only physical.*ports are supported',
                                     'Error: Invalid value for "<l3_mirror_port>": Illegal port \\S+. '
                                     'Only physical.*ports are supported',
                                     'Error: Invalid value for "<l3_mirror_dmac>": Invalid MAC address \\S+',
                                     'Error: Invalid value for "<l3_mirror_dip>": Invalid IPv4 address \\S+',
                                     'Error: Invalid value for "<l3_mirror_truc_size>": \\S+ is not a valid integer',
                                     'Error: Missing argument "priority"']

            flow_table_entry_params_list = ["key {} priority {}".format(table_params.flow_key,
                                                                        table_params.flow_priority),
                                            "key {} action {} priority {}".format(table_params.flow_key,
                                                                                  table_params.flow_action_param,
                                                                                  table_params.flow_priority),
                                            "key {} action {} priority {}".format(table_params.flow_key, ACTION_NAME,
                                                                                  table_params.flow_priority),
                                            "key {} action {} {} priority {}".format(table_params.flow_key, ACTION_NAME,
                                                                                     " ".join(
                                                                                         table_params.flow_action_param.split()[
                                                                                             1:]),
                                                                                     table_params.flow_priority),
                                            "key {} action {} {} priority {}".format(table_params.flow_key,
                                                                                     ACTION_NAME,
                                                                                     " ".join(
                                                                                         [table_params.flow_action_param.split()[
                                                                                             0]] +
                                                                                         table_params.flow_action_param.split()[
                                                                                             2:8]),
                                                                                     table_params.flow_priority),
                                            "key {} action {} {} priority {}".format(table_params.flow_key,
                                                                                     ACTION_NAME,
                                                                                     " ".join(
                                                                                         table_params.flow_action_param.split()[
                                                                                             :3] +
                                                                                         table_params.flow_action_param.split()[
                                                                                             4:8]),
                                                                                     table_params.flow_priority),
                                            "key {} action {} {} priority {}".format(table_params.flow_key, ACTION_NAME,
                                                                                     " ".join(table_params.flow_action_param.split()[:7]),
                                                                                     table_params.flow_priority),
                                            "key {} action {} {}".format(table_params.flow_key, ACTION_NAME,
                                                                         " ".join(table_params.flow_action_param.split()[:8]))
                                            ]

            for expect_error_msg, flow_table_entry_params in zip(
                    expect_error_msg_list, flow_table_entry_params_list):
                with allure.step('Verify add entry to flow table output with negative action: {}'.format(
                        flow_table_entry_params)):
                    verify_show_cmd(
                        P4SamplingCli.add_entry_to_table(
                            engines.dut, FLOW_TABLE_NAME, flow_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])

    @allure.title('Test P4 sampling add entry with negative priority')
    def test_sampling_entry_with_negative_priority(
            self, engines, table_params):
        """
        Verify p4-sampling add entry related cli command with wrong priority specified.
        :param engines: engines fixture
        :param table_params: table_params fixture
        """
        with allure.step('Verify add entry for the table_port_sampling'):
            expect_error_msg_list = ['Error: Missing argument "priority"',
                                     'Error: Missing argument "<priority>"',
                                     'Error: Invalid value for "priority": Illegal priority keyword \\S+. '
                                     'Use "priority" keyword',
                                     'Error: Invalid value for "<priority>": \\S+ is not a valid integer']

            port_table_entry_params_list = ["key {} action {} {}".format(table_params.port_key, ACTION_NAME,
                                                                         table_params.port_action_param),
                                            "key {} action {} {} priority".format(table_params.port_key, ACTION_NAME,
                                                                                  table_params.port_action_param),
                                            "key {} action {} {} priorityy {}".format(table_params.port_key, ACTION_NAME,
                                                                                      table_params.port_action_param,
                                                                                      table_params.port_priority),
                                            "key {} action {} {} priority {}".format(table_params.port_key, ACTION_NAME,
                                                                                     table_params.port_action_param,
                                                                                     True)]

            for expect_error_msg, port_table_entry_params in zip(
                    expect_error_msg_list, port_table_entry_params_list):
                with allure.step('Verify add entry to port table output with negative priority: {}'.format(
                        port_table_entry_params)):
                    verify_show_cmd(
                        P4SamplingCli.add_entry_to_table(
                            engines.dut, PORT_TABLE_NAME, port_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])

        with allure.step('Verify add entry for the table_flow_sampling'):
            expect_error_msg_list = ['Error: Missing argument "priority"',
                                     'Error: Missing argument "<priority>"',
                                     'Error: Invalid value for "priority": Illegal priority keyword \\S+. '
                                     'Use "priority" keyword',
                                     'Error: Invalid value for "<priority>": \\S+ is not a valid integer']
            flow_table_entry_params_list = ["key {} action {} {}".format(table_params.flow_key, ACTION_NAME,
                                                                         table_params.flow_action_param),
                                            "key {} action {} {} priority".format(table_params.flow_key, ACTION_NAME,
                                                                                  table_params.flow_action_param),
                                            "key {} action {} {} priorityy {}".format(table_params.flow_key, ACTION_NAME,
                                                                                      table_params.flow_action_param,
                                                                                      table_params.flow_priority),
                                            "key {} action {} {} priority {}".format(table_params.flow_key, ACTION_NAME,
                                                                                     table_params.flow_action_param,
                                                                                     True)]

            for expect_error_msg, flow_table_entry_params in zip(
                    expect_error_msg_list, flow_table_entry_params_list):
                with allure.step('Verify add entry to flow table output with negative action: {}'.format(
                        flow_table_entry_params)):
                    verify_show_cmd(
                        P4SamplingCli.add_entry_to_table(
                            engines.dut, FLOW_TABLE_NAME, flow_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])

    @allure.title('Test P4 sampling add, delete, show entry and show counters with negative table name')
    def test_sampling_entry_with_negative_table(self, engines, table_params):
        """
        Verify p4-sampling add, remove, show entry related cli command with wrong table name specified.
        :param engines: engines fixture
        :param table_params: table_params fixture
        """
        with allure.step('Verify add\\delete\\show entry with wrong table name'):
            expect_error_msg_list = ['Error: No such command \\S+',
                                     'Error: No such command \\S+']
            table_name_list = ['', 'table-t-sampling']
            port_table_entry_params = "key {} action {} {} priority {}".format(table_params.port_key.split()[1],
                                                                               ACTION_NAME,
                                                                               table_params.port_action_param,
                                                                               table_params.port_priority)
            flow_table_entry_params = "key {} action {} {} priority {}".format(table_params.flow_key,
                                                                               ACTION_NAME,
                                                                               table_params.flow_action_param,
                                                                               table_params.flow_priority)
            for expect_error_msg, table_name in zip(
                    expect_error_msg_list, table_name_list):
                with allure.step('Verify add entry to table output with negative table name: {} and port table params'.format(
                        table_name)):
                    verify_show_cmd(
                        P4SamplingCli.add_entry_to_table(
                            engines.dut, table_name, port_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step(
                        'Verify add entry to table output with negative table name: {} and flow table params'.format(
                            table_name)):
                    verify_show_cmd(
                        P4SamplingCli.add_entry_to_table(
                            engines.dut, table_name, flow_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step(
                        'Verify remove entry from table output with negative table name: {} and port table keys'.format(
                            table_name)):
                    verify_show_cmd(
                        P4SamplingCli.delete_entry_from_table(
                            engines.dut, table_name, "key {}".format(table_params.port_key)),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step(
                        'Verify remove entry from table output with negative table name: {} and flow table keys'.format(
                            table_name)):
                    verify_show_cmd(
                        P4SamplingCli.delete_entry_from_table(
                            engines.dut, table_name, "key {}".format(table_params.flow_key)),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step('Verify show entries of table output with negative table name: {}'.format(table_name)):
                    verify_show_cmd(
                        P4SamplingCli.show_table_entries(
                            engines.dut, table_name),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step('Verify show counters of table output with negative table name: {}'.format(table_name)):
                    verify_show_cmd(
                        P4SamplingCli.show_table_counters(
                            engines.dut, table_name),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])

    @allure.title('Test P4 sampling add, delete, show entry and show counters with more args')
    def test_sampling_entry_with_more_args(self, engines, table_params):
        """
        Verify p4-sampling add, remove, show entry related cli command with more args specified.
        :param engines: engines fixture
        :param table_params: table_params fixture
        """
        expect_error_msg_list = ['Error: Got unexpected extra argument \\S+',
                                 'Error: no such option: \\S+']
        extra_arg_liist = ['extra', '-extra']
        with allure.step('Verify add entry for the table_port_sampling'):
            for expect_error_msg, extra_arg in zip(
                    expect_error_msg_list, extra_arg_liist):
                port_table_entry_params = "key {} action {} {} priority {} {}".format(table_params.port_key, ACTION_NAME,
                                                                                      table_params.port_action_param,
                                                                                      table_params.port_priority, extra_arg)
                with allure.step('Verify add entry to port table output with extra args: {}'.format(extra_arg)):
                    verify_show_cmd(
                        P4SamplingCli.add_entry_to_table(
                            engines.dut, PORT_TABLE_NAME, port_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step('Verify remove entry from port table output with extra args: {}'.format(extra_arg)):
                    verify_show_cmd(
                        P4SamplingCli.delete_entry_from_table(
                            engines.dut, PORT_TABLE_NAME, "key {} {}".format(
                                table_params.port_key, extra_arg)),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step('Verify show entries of port table output with extra args: {}'.format(extra_arg)):
                    verify_show_cmd(
                        engines.dut.run_cmd(
                            'show p4-sampling {} {} entries {}'.format(P4SamplingConsts.CONTTROL_IN_PORT,
                                                                       PORT_TABLE_NAME, extra_arg)),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step('Verify show counters of port table output with extra args: {}'.format(extra_arg)):
                    verify_show_cmd(
                        engines.dut.run_cmd(
                            'show p4-sampling {} {} counters {}'.format(P4SamplingConsts.CONTTROL_IN_PORT,
                                                                        PORT_TABLE_NAME, extra_arg)),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])

        with allure.step('Verify add entry for the table_flow_sampling'):
            for expect_error_msg, extra_arg in zip(
                    expect_error_msg_list, extra_arg_liist):
                flow_table_entry_params = "key {} action {} {} priority {} {}".format(table_params.flow_key, ACTION_NAME,
                                                                                      table_params.flow_action_param,
                                                                                      table_params.flow_priority,
                                                                                      extra_arg)
                with allure.step('Verify add entry to flow table output with extra args: {}'.format(extra_arg)):
                    verify_show_cmd(
                        P4SamplingCli.add_entry_to_table(
                            engines.dut, FLOW_TABLE_NAME, flow_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step('Verify remove entry from flow table output with extra args: {}'.format(extra_arg)):
                    verify_show_cmd(
                        P4SamplingCli.delete_entry_from_table(engines.dut, FLOW_TABLE_NAME,
                                                              "key {} {}".format(table_params.flow_key, extra_arg)),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step('Verify show entries of flow table output with extra args: {}'.format(extra_arg)):
                    verify_show_cmd(
                        engines.dut.run_cmd(
                            'show p4-sampling {} {} entries {}'.format(P4SamplingConsts.CONTTROL_IN_PORT,
                                                                       FLOW_TABLE_NAME, extra_arg)),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
                with allure.step('Verify show counters of flow table output with extra args: {}'.format(extra_arg)):
                    verify_show_cmd(
                        engines.dut.run_cmd(
                            'show p4-sampling {} {} counters {}'.format(P4SamplingConsts.CONTTROL_IN_PORT,
                                                                        FLOW_TABLE_NAME, extra_arg)),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])

    @allure.title('Test P4 sampling add entry with non physical port as ingress port or mirror port')
    def test_sampling_entry_with_non_physical_port(
            self, engines, topology_obj, table_params, lag_port):
        """
        Verify p4-sampling add, remove, show entry related cli command with non physical port specified.
        :param engines: engines fixture
        :param topology_obj: topology_obj fixture
        :param table_params: table_params fixture
        :param lag_port: lag_port fixture
        """

        for port in [lag_port, topology_obj.ports['dut-lb-splt4-p1-1']]:
            expect_error_msg = 'Error: Invalid value for "<key_port>": Illegal port \\S+. Only physical.*ports are supported'
            port_key = ' '.join([port, table_params.port_key.split()[1]])
            port_table_entry_params = "key {} action {} {} priority {}".format(port_key, ACTION_NAME,
                                                                               table_params.port_action_param,
                                                                               table_params.port_priority)
            with allure.step('Verify add entry to flow table output with non-physical port for ingress port: {}'.format(port)):
                verify_show_cmd(
                    P4SamplingCli.add_entry_to_table(
                        engines.dut, PORT_TABLE_NAME, port_table_entry_params),
                    expected_output_list=[(r'{}'.format(expect_error_msg), True)])

            expect_error_msg = 'Error: Invalid value for "<l3_mirror_port>": Illegal port \\S+. ' \
                               'Only physical.*ports are supported'
            port_action_param = ' ' .join(
                [port] + table_params.port_action_param.split()[1:])
            port_table_entry_params = "key {} action {} {} priority {}".format(table_params.port_key, ACTION_NAME,
                                                                               port_action_param,
                                                                               table_params.port_priority)
            with allure.step('Verify add entry to port table output with non-physical port for mirror: {}'.format(port)):
                verify_show_cmd(
                    P4SamplingCli.add_entry_to_table(
                        engines.dut, PORT_TABLE_NAME, port_table_entry_params),
                    expected_output_list=[(r'{}'.format(expect_error_msg), True)])

            expect_error_msg = 'Error: Invalid value for "<l3_mirror_port>": Illegal port \\S+. ' \
                               'Only physical.*ports are supported'
            flow_action_param = ' '.join(
                [port] + table_params.flow_action_param.split()[1:])
            flow_table_entry_params = "key {} action {} {} priority {}".format(table_params.flow_key, ACTION_NAME,
                                                                               flow_action_param,
                                                                               table_params.flow_priority)
            with allure.step(
                    'Verify add entry to flow table output with non-physical port for mirror: {}'.format(port)):
                verify_show_cmd(
                    P4SamplingCli.add_entry_to_table(
                        engines.dut, FLOW_TABLE_NAME, flow_table_entry_params),
                    expected_output_list=[(r'{}'.format(expect_error_msg), True)])

    @pytest.fixture()
    def lag_port(self, topology_obj):
        """
        add one lag port, and after test, remove it
        :param topology_obj: topology object fixture
        :return: the lag port
        """
        lag_port = "PortChannel2222"
        engine = topology_obj.players['dut']['engine']
        engine.run_cmd('sudo config portchannel add {}'.format(lag_port))
        yield lag_port
        engine.run_cmd('sudo config portchannel add {}'.format(lag_port))


@pytest.mark.build
def test_p4_sampling_not_support_on_spc1(engines, table_params, platform_params):
    if fixture_helper.is_p4_sampling_supported(platform_params):
        pytest.skip("Skip it due to the device is not SPC1")
    with allure.step(
            'Verify {} not support on SPC1'.format(P4SamplingConsts.APP_NAME)):
        expect_error_msg = "feature is not supported on device type"
        SonicGeneralCli.set_feature_state(engines.dut, P4SamplingConsts.APP_NAME, 'enabled')
        flow_entry = table_params.flow_entry
        flow_entry_key = list(flow_entry.keys())[0]
        params = flow_entry[flow_entry_key]
        flow_table_entry_params = 'key {} action {} {} priority {}'.format(flow_entry_key, ACTION_NAME, params.action,
                                                                           params.priority)
        verify_show_cmd(P4SamplingCli.add_entry_to_table(engines.dut, FLOW_TABLE_NAME, flow_table_entry_params),
                        expected_output_list=[(r'{}'.format(expect_error_msg), True)])
