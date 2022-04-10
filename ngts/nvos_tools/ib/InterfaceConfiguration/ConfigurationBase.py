import logging
from .nvos_consts import InternalNvosConsts

logger = logging.getLogger()


class ConfigurationBase:
    port_obj = None
    label = ""
    description = ""
    field_name_in_db = {}

    def __init__(self, port_obj, label, description, field_name_in_db, output_hierarchy):
        self.port_obj = port_obj
        self.label = label
        self.description = description
        self.field_name_in_db = field_name_in_db
        self.output_hierarchy = output_hierarchy

    def get_operational(self, engine, renew_show_cmd_output=True):
        """
        Returns the operational value of the filed
        :param engine: ssh engine
        :param renew_show_cmd_output: If true - 'show' command will be executed before checking the value
                                      Else - results from the previous 'show' command will be used
        :return: the operational value of the filed
        """
        return self._get_value(engine, renew_show_cmd_output)

    def _get_value(self, engine, renew_show_cmd_output):
        """
        Returns operational/applied value
        :param engine: ssh engine
        :param renew_show_cmd_output: If true - 'show' command will be executed before checking the value
                                      Else - results from the previous 'show' command will be used
        :return:
        """
        raise Exception("Not Implemented")
