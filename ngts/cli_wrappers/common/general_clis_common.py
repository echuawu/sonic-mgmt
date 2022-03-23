import logging
from ngts.cli_wrappers.interfaces.interface_general_clis import GeneralCliInterface

logger = logging.getLogger()


class GeneralCliCommon(GeneralCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """

    def __init__(self, engine):
        self.engine = engine

    def start_service(self, service):
        output = self.engine.run_cmd('sudo service {} start'.format(service), validate=True)
        return output

    def stop_service(self, service):
        output = self.engine.run_cmd('sudo service {} stop'.format(service), validate=True)
        return output

    def systemctl_start(self, service):
        output = self.engine.run_cmd(f'sudo systemctl start {service}', validate=True)
        return output

    def systemctl_stop(self, service):
        output = self.engine.run_cmd(f'sudo systemctl stop {service}', validate=True)
        return output

    def systemctl_restart(self, service):
        output = self.engine.run_cmd(f'sudo systemctl restart {service}', validate=True)
        return output

    def get_container_status(self, app_name):
        """
        Get specified container's status:
        Example:
            docker ps -a -f name=snmp$ --format "{'ID':'{{ .ID }}', 'Names':'{{ .Names }}', 'Status':'{{ .Status }}'}"
            {'ID':'bb2ef5fcd2b1', 'Names':'snmp', 'Status':'Up 3 hours'}
        :param app_name: ssh engine object
        :Return app container status, None if no container data
        """
        container_data_format = "{'ID':'{{ .ID }}', 'Names':'{{ .Names }}', 'Status':'{{ .Status }}'}"
        app_container_info = self.engine.run_cmd('docker ps -a -f name={}$ --format "{}" '.format(app_name, container_data_format), validate=True)
        logger.info("get {} container status:{}".format(app_name, app_container_info))
        app_container_status = None
        if app_container_info:
            app_container_status = eval(app_container_info)["Status"]
        return app_container_status

    def get_running_containers_names(self):
        """
        Returns the names of running Docker containers in the system.
        """
        return self.engine.run_cmd("docker ps --format '{{.Names}}'").splitlines()

    def hostname(self, flags=''):
        return self.engine.run_cmd(f'hostname {flags}')

    def echo(self, string, flags=''):
        return self.engine.run_cmd(f'echo {flags} {string}')

    def ls(self, path, flags=''):
        return self.engine.run_cmd(f'ls {flags} {path}')

    def mv(self, src_path, dst_path, flags=''):
        return self.engine.run_cmd(f'mv {flags} {src_path} {dst_path}')

    def cp(self, src_path, dst_path, flags=''):
        return self.engine.run_cmd(f'cp {flags} {src_path} {dst_path}')

    def rm(self, path, flags=''):
        return self.engine.run_cmd(f'rm {flags} {path}')

    def mkdir(self, path, flags=''):
        return self.engine.run_cmd(f'mkdir {flags} {path}')

    def which(self, path):
        return self.engine.run_cmd(f'which {path}')

    def sed(self, path, script, flags=''):
        return self.engine.run_cmd(f"sed {flags} '{script}' {path}")

    def chmod_by_mode(self, path, mode, flags=''):
        return self.engine.run_cmd(f'chmod {flags} {mode} {path}')

    def chmod_by_ref_file(self, path, ref_path, flags=''):
        return self.engine.run_cmd(f'chmod {flags} --reference={ref_path} {path}')

    def chown_by_user(self, path, user, group='', flags=''):
        if group:
            group = f':{group}'
        return self.engine.run_cmd(f'chown {flags} {user}{group} {path}')

    def chown_by_ref_file(self, path, ref_path, flags=''):
        return self.engine.run_cmd(f'chown {flags} --reference={ref_path} {path}')

    def apt_update(self, flags=''):
        return self.engine.run_cmd(f'apt {flags} update', validate=True)

    def apt_install(self, package, flags=''):
        return self.engine.run_cmd(f'apt {flags} install {package}', validate=True)

    def coverage_combine(self, flags=''):
        return self.engine.run_cmd(f'coverage combine {flags}', validate=True)

    def coverage_xml(self, outfile, flags=''):
        return self.engine.run_cmd(f'coverage xml -o {outfile} {flags}', validate=True)
