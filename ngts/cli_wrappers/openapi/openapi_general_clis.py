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
    def save_config(engine, ask_for_confirmation=False):
        """
        Save configuration
        :param engine: ssh engine object
        """
        logging.info("Execute config save using OpenApi")
        # TODO: not supported yet
        # return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password, 'SAVE', engine.ip,
        #                                            'system/config/save')
        return ""

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
