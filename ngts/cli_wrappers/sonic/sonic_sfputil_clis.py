import logging

from ngts.cli_util.cli_parsers import generic_sonic_output_parser, parse_show_interfaces_transceiver_eeprom

logger = logging.getLogger()


class SonicSfputilCli:
    """
    This class hosts SONiC sfputil cli methods
    """
    def __init__(self, engine):
        self.engine = engine

    def get_sfputil_eeprom(self):
        """
        :return: sfputil show eeprom
        """
        return self.engine.run_cmd('sudo sfputil show eeprom')

    def parse_sfputil_eeprom(self, sfputil_eeprom_output=None):
        """
        Parse output 'sfputil show eeprom' as dictionary
        :param sfputil_eeprom_output: output 'sfputil show eeprom'
        :return: dict, example: {'Ethernet0': 'Present', 'Ethernet1': 'Present'...}
        """
        if not sfputil_eeprom_output:
            sfputil_eeprom_output = self.get_sfputil_eeprom()
        # the output must be the same as interfaces transceiver, use the same parser
        return parse_show_interfaces_transceiver_eeprom(sfputil_eeprom_output)

    def get_sfputil_presence(self):
        """
        :return: sfputil show presence,
        i.e, command output sample:
        Port       Presence
        ---------  -----------
        Ethernet0  Not present
        """
        return self.engine.run_cmd('sudo sfputil show presence')

    def parse_sfputil_presence(self, sfputil_presence_output=None):
        """
        Parse output 'sfputil show presence' as dictionary
        :param sfputil_presence_output: output 'show interfaces transceiver presence'
        :return: dict, example: {'Ethernet0': 'Present', 'Ethernet1': 'Present'...}
        """
        if not sfputil_presence_output:
            sfputil_presence_output = self.get_sfputil_presence()

        return generic_sonic_output_parser(sfputil_presence_output,
                                           headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Port')

    def get_sfputil_lpmode(self, validate=False):
        """
        :return: sfputil show lpmode,
        i.e, command output sample:
        Port       Low-power Mode
        ---------  ----------------
        Ethernet0  N/A
        """
        return self.engine.run_cmd('sudo sfputil show lpmode', validate=validate)

    def get_sfputil_error_status(self, validate=False):
        """
        :return: sfputil show error-status,
        i.e, command output sample:
        Port       Error Status
        ---------  --------------
        Ethernet0  N/A
        """
        return self.engine.run_cmd('sudo sfputil show error-status', validate=validate)

    def get_sfputil_fwversion(self, interface='', validate=False):
        """
        :param interface:  interfaces name, example: 'Ethernet0'
        :return: sfputil show fwversion,
        """
        return self.engine.run_cmd(f'sudo sfputil show fwversion {interface}', validate=validate)
