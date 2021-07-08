from ngts.cli_util.cli_parsers import generic_sonic_output_parser
from ngts.constants.constants import P4SamplingConsts
from ngts.constants.constants import P4SamplingEntryConsts


class P4SamplingCli:
    """
    This class defines SONiC P4 sampling cli methods
    """

    @staticmethod
    def add_entry_to_table(engine, table_name, params):
        """
        Add entry for a specified table
        :param engine: ssh engine object
        :param table_name: the table name in which the entry will be added
        :param params: the parameters of the entry, in string format
               example: 'table-flow-sampling key 100.100.100.8 100.100.100.100 17 123 456 0x43/0x21
               action DoMirror Ethernet0 01:12:23:34:45:56 01:A1:B1:C1:D1:1E 2.2.3.4 7.6.5.4 10 1 64 priority 12'
        :return: the output of the cli command
        """
        return engine.run_cmd(
            'sudo config p4-sampling add {} {} {}'.format(P4SamplingConsts.CONTTROL_IN_PORT, table_name, params))

    @staticmethod
    def add_entries_to_table(engine, table_name, params_list):
        """
        Add entries for specified table
        :param engine: ssh engine object
        :param table_name: the table name in which the entry will be added
        :param params_list: list of parameters of the entry, in string format
               example: ['key 100.100.100.8 100.100.100.100 17 123 456 0x43/0x21
               action DoMirror Ethernet0 01:12:23:34:45:56 01:A1:B1:C1:D1:1E 2.2.3.4 7.6.5.4 10 1 64 priority 12', ...]
        :return: the output of the cli command
        """

        cmd_list = []
        for params in params_list:
            cmd_list.append('sudo config p4-sampling add {} {} {}'.format(P4SamplingConsts.CONTTROL_IN_PORT,
                                                                          table_name, params))
        return engine.run_cmd_set(cmd_list)

    @staticmethod
    def delete_entry_from_table(engine, table_name, params):
        """
        Delete the entry from the specified table
        :param engine: ssh engine object
        :param table_name: the table name in which the entry will be deleted
        :param params: the parameters used to delete the entry, in string format
               example: 'table-flow-sampling key 100.100.100.8 100.100.100.100 17 123 456 0x43/0x21'
        :return: the output of the cli command
        """
        return engine.run_cmd(
            'sudo config p4-sampling remove {} {} {}'.format(P4SamplingConsts.CONTTROL_IN_PORT, table_name, params))

    @staticmethod
    def delete_entries_from_table(engine, table_name, params_list):
        """
        Delete the entries from the specified table
        :param engine: ssh engine object
        :param table_name: the table name in which the entry will be deleted
        :param params_list: the parameters used to delete the entry, in string format
               example: ['key 100.100.100.8 100.100.100.100 17 123 456 0x43/0x21', ...]
        :return: the output of the cli command
        """
        cmd_list = []
        for params in params_list:
            cmd_list.append('sudo config p4-sampling remove {} {} {}'.format(P4SamplingConsts.CONTTROL_IN_PORT,
                                                                             table_name, params))
        return engine.run_cmd_set(cmd_list)

    @staticmethod
    def show_table_entries(engine, table_name):
        """
        Get the output of the show entries
        :param engine: ssh engine object
        :param table_name: the table name from which the entries will be shown
               example: table_port_sampling
        :return: the output of the cli command
        """
        return engine.run_cmd(
            'show p4-sampling {} {} entries'.format(P4SamplingConsts.CONTTROL_IN_PORT, table_name))

    @staticmethod
    def show_table_counters(engine, table_name):
        """
        Get the output of the show counters
        :param engine: ssh engine object
        :param table_name: the table name from which the counters will be shown
               example: table_port_sampling
        :return: the output of the cli command
        """
        return engine.run_cmd(
            'show p4-sampling {} {} counters'.format(P4SamplingConsts.CONTTROL_IN_PORT, table_name))

    @staticmethod
    def show_and_parse_table_entries(engine, table_name, exclude_keys=[]):
        """
        parse the output of the show entries to list of dictionaries
        :param engine: ssh engine object
        :param table_name: the table name from which the entries will be shown
               example: table_port_sampling
        :param exclude_keys: the keys which will be excluded from the output
        :return: list of entries
                 example: [{'key': 'Ethernet60 0x0021/0x0043',
                            'action': 'DoMirror Ethernet0 00:00:00:00:00:03 0c:42:a1:5a:57:98 50.0.0.1 50.0.0.2 40 True 300',
                            'priority': '1'},
                            {...}, ....]
        """
        table_entries = P4SamplingCli.show_table_entries(
            engine, table_name)
        if not table_entries:
            return []
        table_entries = generic_sonic_output_parser(table_entries, headers_ofset=0, len_ofset=3, data_ofset_from_start=4,
                                                    data_ofset_from_end=None, column_ofset=2, header_line_number=3)

        key_headers = P4SamplingCli.get_key_headers(table_name)
        action_headers = P4SamplingCli.get_action_headers(table_name)
        priority_headers = P4SamplingEntryConsts.ENTRY_PRIORITY_HEADERS
        key_headers_map = {'key': key_headers, 'action': action_headers, 'priority': priority_headers}
        return P4SamplingCli.format_table_content(table_entries, key_headers_map)

    @staticmethod
    def show_and_parse_table_counters(engine, table_name):
        """
        parse the output of the show counters to list of dictionaries
        :param engine: ssh engine object
        :param table_name: the table name from which the counters will be shown
               example: table_port_sampling
        :return: list of counters,  example: [{'key': 'Ethernet60 0x0021/0x0043', 'packets':'20', 'bytes': '5120'}, ...]
        """
        entry_counters = P4SamplingCli.show_table_counters(
            engine, table_name)
        if not entry_counters:
            return []
        entry_counters = generic_sonic_output_parser(entry_counters, headers_ofset=0, len_ofset=3, data_ofset_from_start=4,
                                                     data_ofset_from_end=None, column_ofset=2, header_line_number=3)
        key_headers = P4SamplingCli.get_key_headers(table_name)
        packets_headers = P4SamplingEntryConsts.COUNTER_PACKETS_HEADERS
        bytes_headers = P4SamplingEntryConsts.COUNTER_BYTES_HEADERS
        key_headers_map = {'key': key_headers, 'packets': packets_headers, 'bytes': bytes_headers}
        return P4SamplingCli.format_table_content_dict(entry_counters, key_headers_map, 'key')

    @staticmethod
    def clear_table_counters(engine, table_name):
        """
        Clear the counters in the specified table name
        :param engine: ssh engine object
        :param table_name: the table name from which the counter will be cleared
               example: table_port_sampling
        :return: None
        """
        engine.run_cmd('show p4-sampling {} {} counters -c'.format(P4SamplingConsts.CONTTROL_IN_PORT, table_name),
                       validate=True)

    @staticmethod
    def clear_all_table_counters(engine):
        """
        Clear counters for all the tables in the p4-sampling
        :param engine: ssh engine object
        :return: None
        """
        engine.run_cmd('sudo sonic-clear p4-sampling', validate=True)

    @staticmethod
    def get_key_headers(table_name):
        """
        get the key headers for the specified table
        :param table_name: the table name that the key headers is in
        :return: list of key headers
        """
        if table_name == P4SamplingConsts.FLOW_TABLE_NAME:
            return P4SamplingEntryConsts.FLOW_ENTRY_KEY_HEADERS
        else:
            return P4SamplingEntryConsts.PORT_ENTRY_KEY_HEADERS

    @staticmethod
    def get_action_headers(table_name):
        """
        get the key headers for the specified table
        :param table_name: the table name that the action headers is in
        :return: list of action headers
        """
        if table_name == P4SamplingConsts.FLOW_TABLE_NAME:
            return P4SamplingEntryConsts.FLOW_ENTRY_ACTION_HEADERS
        else:
            return P4SamplingEntryConsts.PORT_ENTRY_ACTION_HEADERS

    @staticmethod
    def format_table_content(content_table, key_headers_map):
        """
        Convert the table content format to list of dictionary
        :param content_table: the table content
        :param key_headers_map: the map between dictionary key to the column headers of the table
        :return: list of counters,  example: [{'key': 'Ethernet60 0x0021/0x0043', 'packets':'20', 'bytes': '5120'}, ...]
        """
        content_list = []
        for row_content in content_table:
            row_dict = P4SamplingCli.create_row_dict(row_content, key_headers_map)
            content_list.append(row_dict)
        return content_list

    @staticmethod
    def format_table_content_dict(content_table, key_headers_map, out_key):
        """
        Convert the table content format to dictionary
        :param content_table: the table content
        :param key_headers_map: the map between dictionary key to the column headers of the table
        :return: list of counters,
                 example: {'Ethernet60 0x0021/0x0043':
                            {'key':'Ethernet60 0x0021/0x0043', 'packets':'20', 'bytes': '5120'} ...}, ...
        """
        content_dict = {}
        for row_content in content_table:
            row_dict = P4SamplingCli.create_row_dict(row_content, key_headers_map)
            content_dict[row_dict[out_key]] = row_dict
        return content_dict

    @staticmethod
    def create_row_dict(row_content, key_headers_map):
        row_dict = {}
        for key, headers in key_headers_map.items():
            value = ''
            for header in headers:
                if header == "Key Checksum Value/Mask":
                    value = value + row_content[header].lower() + ' '
                else:
                    value = value + row_content[header] + ' '
            row_dict[key] = value.strip()
        return row_dict
