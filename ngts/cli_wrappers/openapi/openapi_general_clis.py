import json
import logging
from .openapi_command_builder import OpenApiCommandHelper

logger = logging.getLogger()


class OpenApiGeneralCli:

    """
    Open API cli wrapper
    """

    def __init__(self):
        pass

    @staticmethod
    def apply_config(engine, ask_for_confirmation=False):
        """
        Apply configuration
        :param engine: ssh engine object
        """
        logging.info("Execute config apply using OpenApi")
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password, 'APPLY', engine.ip,
                                                   'system/config/apply')

    @staticmethod
    def save_config(engine):
        """
        Save configuration
        :param engine: ssh engine object
        """
        logging.info("Execute config save using OpenApi")
        resource_path = '/revision/applied'
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password, 'PATCH', engine.ip,
                                                   resource_path=resource_path, op_param_name="state", op_param_value="save")

    @staticmethod
    def show_config(engine, revision='applied', output_type='json'):
        """
        Save configuration
        :param engine: ssh engine object
        :param revision: applied / pending / startup
        :param output_type: json / str
        """
        logging.info("Execute config show using OpenApi")
        resource_path = '/?rev={revision}&filled=False'.format(revision=revision)
        res = OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password, 'GET', engine.ip,
                                                  resource_path=resource_path)

        if output_type == 'json':
            return json.dumps(res)
        else:
            return res

    @staticmethod
    def detach_config(engine, ask_for_confirmation=False):
        """
        Detach configuration
        :param engine: ssh engine object
        """
        logging.info("Execute config save using OpenApi")
        # TODO: not supported yet
        # return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password, 'DETACH',
        #                                            engine.ip, 'system/config/detach')
        return ""
