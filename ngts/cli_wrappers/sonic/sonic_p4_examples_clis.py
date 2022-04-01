from ngts.constants.constants import P4ExamplesConsts
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


class P4ExamplesCli:
    """
    This class defines SONiC P4 examples application related cli methods
    """

    def __init__(self, engine):
        self.engine = engine

    def start_p4_example_feature(self, feature_name):
        """
        Start p4 examples feature
        :param feature_name: the feature name which will be started in the p4 examples application
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f'sudo config {P4ExamplesConsts.APP_NAME} application name {feature_name}')

    def stop_p4_example_feature(self):
        """
        Stop p4 examples feature
        :return: the output of the cli command
        """
        self.start_p4_example_feature(P4ExamplesConsts.NO_EXAMPLE)

    def show_p4_example_running_feature(self):
        """
        Show running p4 examples running feature
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f"show {P4ExamplesConsts.APP_NAME} application")

    def get_p4_example_running_feature(self):
        """
        Get the running feature name in the p4 examples docker
        :return: the feature name
        """
        p4_example_feature_output = self.show_p4_example_running_feature()
        p4_example_feature_output = generic_sonic_output_parser(p4_example_feature_output)
        the_only_element_index = 0
        return p4_example_feature_output[the_only_element_index]["NAME"]


class P4VxlanBMCli:
    """
    This class defines SONiC P4 VXLAN-BM example feature related cli methods
    """

    def __init__(self, engine):
        self.engine = engine

    def add_encap_entry(self, key, params):
        """
        Add entry for a encap table
        :param key: the key of encap entry
        :param params: the parameters of the entry, in string format
               Example: '--vni 6 --underlay-ip 2.2.2.2 --priority 2 --action TUNNEL_ENCAP'
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_ENCAP_TABLE} add {key} {params}')

    def add_decap_entry(self, key, params):
        """
        Add entry for a decap table
        :param key: the key of decap entry
        :param params: the parameters of the entry, in string format
               Example: '--port Ethernet120 --action DO_FORWARD --priority 5'
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_DECAP_TABLE} add {key} {params}')

    def delete_encap_entry(self, key):
        """
        Delete encap entry for a specified key
        :param key: the key of encap entry
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_ENCAP_TABLE} delete {key}')

    def delete_decap_entry(self, key):
        """
        Delete decap entry for the specified key
        :param key: the key of decap entry
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_DECAP_TABLE} delete {key}')

    def update_encap_entry(self, key, params):
        """
        Update encap entry params for the specified key
        :param key: the key of encap entry
        :param params: the parameters of the entry, in string format
               Example: '--vni 6 --underlay-ip 2.2.2.2 --priority 2 --action TUNNEL_ENCAP'
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_ENCAP_TABLE} update {key} {params}')

    def update_decap_entry(self, key, params):
        """
        Update decap entry params for the specified key
        :param key: the key of decap entry
        :param params: the parameters of the entry, in string format
               Example: '--port Ethernet120 --action DO_FORWARD --priority 5'
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_DECAP_TABLE} update {key} {params}')


class P4GTPParserCli:
    """
    This class defines SONiC P4 GTP Parser example feature related cli methods
    """

    def __init__(self, engine):
        self.engine = engine

    def add_entry(self, key, params):
        """
        Add entry for a gtp parser table
        :param key: the key of gtp parser entry
        :param params: the parameters of the entry, in string format
               Example: '--port Ethernet0 --priority 2 --action ROUTE'
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f'sudo config {P4ExamplesConsts.GTP_PARSER_TABLE} add {key} {params}')

    def update_entry(self, key, params):
        """
        Update params for a gtp parser entry
        :param key: the key of gtp parser entry
        :param params: the parameters of the entry, in string format
               Example: '--port Ethernet0 --priority 2 --action ROUTE'
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f'sudo config {P4ExamplesConsts.GTP_PARSER_TABLE} update {key} {params}')

    def delete_entry(self, key):
        """
        Delete entry for a gtp parser table
        :param key: the key of gtp parser entry
        :return: the output of the cli command
        """
        return self.engine.run_cmd(f'sudo config {P4ExamplesConsts.GTP_PARSER_TABLE} delete {key}')

    def show_entries(self):
        """
        Show entries of a gtp parser table
        :return: the output of the cli command
        Example for output:
            IP                TEID  PORT       ACTION      PRIORITY

            --------------  ------  ---------  --------  ----------

            192.168.1.1/24   10000  Ethernet0  ROUTE              5
        """
        return self.engine.run_cmd(f'sudo show {P4ExamplesConsts.GTP_PARSER_TABLE}')

    def show_and_parse_entries(self):
        """
        Show entries and parser entries of a gtp parser table
        :return: Dictionary for entries, every entry is formatted to a dictionary
            Example or output:
            {"192.168.1.1/24 1000":
                {IP: "192.168.1.1/24", TEID: "1000", PORT: "Ethernet0", ACTION: "ROUTE", PRIORITY: "5"},
                 ...
            }
        """
        entries = self.show_entries()
        entry_list = generic_sonic_output_parser(entries, headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                                 data_ofset_from_end=None, column_ofset=2, header_line_number=1)
        entry_dict = {}
        key_headers = ["IP", "TEID"]
        for entry in entry_list:
            entry_key_values = [entry[key_header] for key_header in key_headers]
            entry_key_value = " ".join(entry_key_values)
            entry_dict[entry_key_value] = entry
        return entry_dict
