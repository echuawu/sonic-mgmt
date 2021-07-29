import logging
from ngts.cli_wrappers.interfaces.interface_general_clis import GeneralCliInterface

logger = logging.getLogger()


class GeneralCliCommon(GeneralCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """

    def __init__(self):
        pass

    @staticmethod
    def start_service(engine, service):
        output = engine.run_cmd('sudo service {} start'.format(service), validate=True)
        return output

    @staticmethod
    def stop_service(engine, service):
        output = engine.run_cmd('sudo service {} stop'.format(service), validate=True)
        return output

    @staticmethod
    def get_container_status(engine, app_name):
        """
        Get specified container's status:
        Example:
            docker ps -a -f name=snmp$ --format "{'ID':'{{ .ID }}', 'Names':'{{ .Names }}', 'Status':'{{ .Status }}'}"
            {'ID':'bb2ef5fcd2b1', 'Names':'snmp', 'Status':'Up 3 hours'}
        :param engine: ssh engine object
        :param app_name: ssh engine object
        :Return app container status, None if no container data
        """
        container_data_format = "{'ID':'{{ .ID }}', 'Names':'{{ .Names }}', 'Status':'{{ .Status }}'}"
        app_container_info = engine.run_cmd('docker ps -a -f name={}$ --format "{}" '.format(app_name, container_data_format), validate=True)
        logger.info("get {} container status:{}".format(app_name, app_container_info))
        app_container_status = None
        if app_container_info:
            app_container_status = eval(app_container_info)["Status"]
        return app_container_status
