import re

from ngts.cli_wrappers.common.mac_clis_common import MacCliCommon
from ngts.helpers.network import generate_mac
from ngts.cli_util.cli_parsers import generic_sonic_output_parser

FDB_AGING_TIME_FILE = "swss:/etc/swss/config.d/switch.json"


class SonicMacCli(MacCliCommon):

    @staticmethod
    def show_mac(engine):
        """
        This method runs 'show mac' command
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('show mac')

    @staticmethod
    def generate_fdb_config(entries_num, vlan_id, iface, op, fdb_type="dynamic"):
        """ Generate FDB config.
        Generated config template:
        [
            {
                "FDB_TABLE:Vlan[VID]:XX-XX-XX-XX-XX-XX": {
                    "port": [Interface],
                    "type": "dynamic"
                },
                "OP": ["SET"|"DEL"]
            }
        ]
        :param entries_num: number of fdb entries
        :param vlan_id: VLAN name
        :param iface: interface name
        :param op: config DEL or SET operation
        :param fdb_type: fdb type (dynamic/static)
        """
        fdb_config_json = []
        entry_key_template = "FDB_TABLE:Vlan{vid}:{mac}"

        for mac_address in generate_mac(entries_num):
            fdb_entry_json = {entry_key_template.format(vid=vlan_id, mac=mac_address):
                              {"port": iface, "type": fdb_type},
                              "OP": op
                              }
            fdb_config_json.append(fdb_entry_json)
        return fdb_config_json

    @staticmethod
    def clear_fdb(engine):
        """
        This method is to clear fdb table
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('sudo sonic-clear fdb all', validate=True)

    @staticmethod
    def set_fdb_aging_time(engine, fdb_aging_time):
        """
        This method is to set fdb aging time
        :param engine: ssh engine object
        :param fdb_aging_time: fdb aging time
        :return: command output
        """
        cmd_copy_file_from_swss_to_switch = f"docker cp {FDB_AGING_TIME_FILE} /tmp/"
        engine.run_cmd(cmd_copy_file_from_swss_to_switch)

        replace_fdb_aging_time = f"sudo sed -i 's/ \"fdb_aging_time\": \".*\"/\"fdb_aging_time\": \"{fdb_aging_time}\"/' /tmp/switch.json"
        engine.run_cmd(replace_fdb_aging_time)

        cmd_copy_file_from_switch_to_swss = f"docker cp /tmp/switch.json {FDB_AGING_TIME_FILE}"
        engine.run_cmd(cmd_copy_file_from_switch_to_swss)
        cmd_config_swss_config = f"docker exec swss bash -c swssconfig {FDB_AGING_TIME_FILE}"
        engine.run_cmd(cmd_config_swss_config)

    @staticmethod
    def get_fdb_aging_time(engine):
        """
        This method is to set fdb aging time
        :param engine: ssh engine object
        :return: fdb aging time
        """
        regrex_time = re.compile(r'\"(?P<time>\d+)\"')
        cmd_get_fdb_aging_time = 'redis-cli -n 0 hget "SWITCH_TABLE:switch" fdb_aging_time'
        fdb_aging_time = regrex_time.search(engine.run_cmd(cmd_get_fdb_aging_time, validate=True))

        return fdb_aging_time.groupdict()["time"] if fdb_aging_time else "nil"

    @staticmethod
    def parse_mac_table(engine, option=""):
        """
        This method is to parse mac table info
        e.g.:
        No.    Vlan  MacAddress         Port         Type
        -----  ------  -----------------  -----------  -------
        1      40  98:03:9B:9B:3B:22  Ethernet248  Dynamic
        2      40  98:03:9B:9B:3B:23  Ethernet0    Dynamic
        3      40  0C:42:A1:C0:99:2E  Ethernet504  Dynamic

        :param engine: ssh engine object
        :param option: show mac option, such as -v or -p
        :return: command output like below
        {'1': {'No.': '1', 'Vlan': '40', 'MacAddress': '0C:42:A1:B4:CC:E8', 'Port': 'Ethernet0', 'Type': 'Dynamic'},
         '2': {'No.': '2', 'Vlan': '40', 'MacAddress': '0C:42:A1:B4:D7:E8', 'Port': 'Ethernet40', 'Type': 'Dynamic'},
         '3': {'No.': '3', 'Vlan': '40', 'MacAddress': '00:00:00:00:00:01', 'Port': 'Ethernet0', 'Type': 'Dynamic'},
        }
        """
        mac_table = engine.run_cmd(f'sudo show mac {option}', validate=True)
        mac_table_dict = generic_sonic_output_parser(mac_table,
                                                     headers_ofset=0,
                                                     len_ofset=1,
                                                     data_ofset_from_start=2,
                                                     data_ofset_from_end=-1,
                                                     column_ofset=2,
                                                     output_key='No.')
        return mac_table_dict