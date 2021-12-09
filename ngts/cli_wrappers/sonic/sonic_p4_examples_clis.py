from ngts.constants.constants import P4ExamplesConsts
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


class P4ExamplesCli:
    """
    This class defines SONiC P4 examples application related cli methods
    """

    @staticmethod
    def start_p4_example_feature(engine, feature_name):
        """
        Start p4 examples feature
        :param engine: ssh engine object
        :param feature_name: the feature name which will be started in the p4 examples application
        :return: the output of the cli command
        """
        return engine.run_cmd(f'sudo config {P4ExamplesConsts.APP_NAME} application name {feature_name}')

    @staticmethod
    def stop_p4_example_feature(engine):
        """
        Stop p4 examples feature
        :param engine: ssh engine object
        :return: the output of the cli command
        """
        P4ExamplesCli.start_p4_example_feature(engine, P4ExamplesConsts.NO_EXAMPLE)

    @staticmethod
    def show_p4_example_running_feature(engine):
        """
        Show running p4 examples running feature
        :param engine: ssh engine object
        :return: the output of the cli command
        """
        return engine.run_cmd(f"show {P4ExamplesConsts.APP_NAME} application")

    @staticmethod
    def get_p4_example_running_feature(engine):
        """
        Get the running feature name in the p4 examples docker
        :param engine: ssh engine object
        :return: the feature name
        """
        p4_example_feature_output = P4ExamplesCli.show_p4_example_running_feature(engine)
        p4_example_feature_output = generic_sonic_output_parser(p4_example_feature_output)
        the_only_element_index = 0
        return p4_example_feature_output[the_only_element_index]["NAME"]


class P4VxlanBMCli:
    """
    This class defines SONiC P4 VXLAN-BM example feature related cli methods
    """

    @staticmethod
    def add_encap_entry(engine, key, params):
        """
        Add entry for a encap table
        :param engine: ssh engine object
        :param key: the key of encap entry
        :param params: the parameters of the entry, in string format
               Example: '--vni 6 --underlay-ip 2.2.2.2 --priority 2 --action TUNNEL_ENCAP'
        :return: the output of the cli command
        """
        return engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_ENCAP_TABLE} add {key} {params}')

    @staticmethod
    def add_decap_entry(engine, key, params):
        """
        Add entry for a decap table
        :param engine: ssh engine object
        :param key: the key of decap entry
        :param params: the parameters of the entry, in string format
               Example: '--port Ethernet120 --action DO_FORWARD --priority 5'
        :return: the output of the cli command
        """
        return engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_DECAP_TABLE} add {key} {params}')

    @staticmethod
    def delete_encap_entry(engine, key):
        """
        Delete encap entry for a specified key
        :param engine: ssh engine object
        :param key: the key of encap entry
        :return: the output of the cli command
        """
        return engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_ENCAP_TABLE} delete {key}')

    @staticmethod
    def delete_decap_entry(engine, key):
        """
        Delete decap entry for the specified key
        :param engine: ssh engine object
        :param key: the key of decap entry
        :return: the output of the cli command
        """
        return engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_DECAP_TABLE} delete {key}')

    @staticmethod
    def update_encap_entry(engine, key, params):
        """
        Update encap entry params for the specified key
        :param engine: ssh engine object
        :param key: the key of encap entry
        :param params: the parameters of the entry, in string format
               Example: '--vni 6 --underlay-ip 2.2.2.2 --priority 2 --action TUNNEL_ENCAP'
        :return: the output of the cli command
        """
        return engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_ENCAP_TABLE} update {key} {params}')

    @staticmethod
    def update_decap_entry(engine, key, params):
        """
        Update decap entry params for the specified key
        :param engine: ssh engine object
        :param key: the key of decap entry
        :param params: the parameters of the entry, in string format
               Example: '--port Ethernet120 --action DO_FORWARD --priority 5'
        :return: the output of the cli command
        """
        return engine.run_cmd(f'sudo config {P4ExamplesConsts.VXLAN_BM_DECAP_TABLE} update {key} {params}')
