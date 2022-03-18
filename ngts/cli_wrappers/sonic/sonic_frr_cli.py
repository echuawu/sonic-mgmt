import os

from ngts.cli_wrappers.common.frr_clis_common import FrrCliCommon


class SonicFrrCli(FrrCliCommon):

    def __init__(self, engine):
        self.engine = engine

    def apply_frr_config(self, frr_config_name, frr_config_folder):
        """
        Apply FRR configuration from file to FRR running config
        :param frr_config_name: name of FRR config file
        :param frr_config_folder: path to folder where FRR config file placed
        """
        fs = '/tmp/'
        frr_conf_path = os.path.join(frr_config_folder, frr_config_name)
        self.engine.copy_file(source_file=frr_conf_path, dest_file=frr_config_name,
                              file_system=fs, overwrite_file=True, verify_file=False)

        self.engine.run_cmd('sudo mv {}{} /etc/sonic/frr/'.format(fs, frr_config_name))
        fs = '/etc/sonic/frr/'
        self.run_config_frr_cmd('copy {}{} running-config'.format(fs, frr_config_name))
