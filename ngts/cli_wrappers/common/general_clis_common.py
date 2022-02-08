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
    def systemctl_start(engine, service):
        output = engine.run_cmd(f'sudo systemctl start {service}', validate=True)
        return output

    @staticmethod
    def systemctl_stop(engine, service):
        output = engine.run_cmd(f'sudo systemctl stop {service}', validate=True)
        return output

    @staticmethod
    def systemctl_restart(engine, service):
        output = engine.run_cmd(f'sudo systemctl restart {service}', validate=True)
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

    @staticmethod
    def get_running_containers_names(engine):
        """
        Returns the names of running Docker containers in the system.
        :param engine: the engine to use.
        """
        return engine.run_cmd("docker ps --format '{{.Names}}'").splitlines()

    @staticmethod
    def hostname(engine, flags=''):
        return engine.run_cmd(f'hostname {flags}')

    @staticmethod
    def echo(engine, string, flags=''):
        return engine.run_cmd(f'echo {flags} {string}')

    @staticmethod
    def ls(engine, path, flags=''):
        return engine.run_cmd(f'ls {flags} {path}')

    @staticmethod
    def mv(engine, src_path, dst_path, flags=''):
        return engine.run_cmd(f'mv {flags} {src_path} {dst_path}')

    @staticmethod
    def cp(engine, src_path, dst_path, flags=''):
        return engine.run_cmd(f'cp {flags} {src_path} {dst_path}')

    @staticmethod
    def rm(engine, path, flags=''):
        return engine.run_cmd(f'rm {flags} {path}')

    @staticmethod
    def mkdir(engine, path, flags=''):
        return engine.run_cmd(f'mkdir {flags} {path}')

    @staticmethod
    def which(engine, path):
        return engine.run_cmd(f'which {path}')

    @staticmethod
    def sed(engine, path, script, flags=''):
        return engine.run_cmd(f"sed {flags} '{script}' {path}")

    @staticmethod
    def chmod_by_mode(engine, path, mode, flags=''):
        return engine.run_cmd(f'chmod {flags} {mode} {path}')

    @staticmethod
    def chmod_by_ref_file(engine, path, ref_path, flags=''):
        return engine.run_cmd(f'chmod {flags} --reference={ref_path} {path}')

    @staticmethod
    def chown_by_user(engine, path, user, group='', flags=''):
        if group:
            group = f':{group}'
        return engine.run_cmd(f'chown {flags} {user}{group} {path}')

    @staticmethod
    def chown_by_ref_file(engine, path, ref_path, flags=''):
        return engine.run_cmd(f'chown {flags} --reference={ref_path} {path}')

    @staticmethod
    def apt_update(engine, flags=''):
        return engine.run_cmd(f'apt {flags} update', validate=True)

    @staticmethod
    def apt_install(engine, package, flags=''):
        return engine.run_cmd(f'apt {flags} install {package}', validate=True)

    @staticmethod
    def coverage_combine(engine, flags=''):
        return engine.run_cmd(f'coverage combine {flags}', validate=True)

    @staticmethod
    def coverage_xml(engine, outfile, flags=''):
        return engine.run_cmd(f'coverage xml -o {outfile} {flags}', validate=True)
