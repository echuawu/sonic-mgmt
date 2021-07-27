from ngts.cli_wrappers.common.mac_clis_common import MacCliCommon
from ngts.helpers.network import generate_mac


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
    def generate_fdb_config(entries_num, vlan_id, iface, op):
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
        """
        fdb_config_json = []
        entry_key_template = "FDB_TABLE:Vlan{vid}:{mac}"

        for mac_address in generate_mac(entries_num):
            fdb_entry_json = {entry_key_template.format(vid=vlan_id, mac=mac_address):
                {"port": iface, "type": "dynamic"},
                "OP": op
            }
            fdb_config_json.append(fdb_entry_json)
        return fdb_config_json
