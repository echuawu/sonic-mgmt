import allure
import logging

from ngts.helpers.interface_helpers import get_alias_number
from ngts.helpers.sonic_branch_helper import get_sonic_branch
from ngts.constants.constants import InfraConst, IndependentModuleConst, SonicConst

logger = logging.getLogger()


class SonicImClis:
    def __init__(self, engine, cli_obj):
        self.engine = engine
        self.cli_obj = cli_obj
        self.chassis_cli = self.cli_obj.chassis
        self.interface_cli = self.cli_obj.interface
        self.general_cli = self.cli_obj.general

    def is_system_supports_im(self):
        """
        @summary: This method is for check if system supports IM
        @return: True in case system is SPC3 or higher
        """
        if self.general_cli.is_spc1(self.cli_obj) or self.general_cli.is_spc2(self.cli_obj):
            return False
        else:
            return True

    def is_im_enabled(self):
        """
        @summary: This method is for check if SAI_INDEPENDENT_MODULE_MODE set to 1 in sai.profile
        @return: True in case SAI_INDEPENDENT_MODULE_MODE set to 1 else False
        """
        parse_platform_summary = self.chassis_cli.parse_platform_summary()
        platfrom = parse_platform_summary["Platform"]
        hwsku = parse_platform_summary["HwSKU"]

        im_sai_param = self.engine.run_cmd(
            f'sudo cat {SonicConst.SAI_PROFILE_FILE_PATH.format(PLATFORM=platfrom, HWSKU=hwsku)} | grep '
            f'{IndependentModuleConst.IM_SAI_ATTRIBUTE_NAME}')
        if im_sai_param:
            if im_sai_param.split("=")[1] == '1':
                return True
            else:
                return False

    def enable_im_in_sai(self):
        """
        @summary: This method is for set SAI_INDEPENDENT_MODULE_MODE to 1 in sai.profile
        """
        parse_platform_summary = self.chassis_cli.parse_platform_summary()
        platfrom = parse_platform_summary["Platform"]
        hwsku = parse_platform_summary["HwSKU"]

        if not self.is_im_enabled():
            logger.info(f'Set {IndependentModuleConst.IM_SAI_ATTRIBUTE_NAME} to 1 in '
                        f'{SonicConst.SAI_PROFILE_FILE_PATH.format(PLATFORM=platfrom, HWSKU=hwsku)}')
            self.engine.run_cmd(f'sudo bash -c \'echo "{IndependentModuleConst.IM_SAI_ATTRIBUTE_NAME}=1" >> '
                                f'{SonicConst.SAI_PROFILE_FILE_PATH.format(PLATFORM=platfrom, HWSKU=hwsku)}\'')
            self.general_cli.reload_configuration(force=True)
            self.general_cli.verify_dockers_are_up()

    def is_ms_hwsku(self):
        """
        @summary: This method is for checking if DUT having Microsoft HWSKU
        """
        parse_platform_summary = self.chassis_cli.parse_platform_summary()
        hwsku = parse_platform_summary["HwSKU"]
        return hwsku in IndependentModuleConst.MS_HWSKU

    def get_ports_supporting_im(self, dut_ports_number_dict):
        """
        @summary: This method is for get DUT ports supporting IM
        @return: list of IM ports supported
        """
        ports_with_im_support = []
        for port_name, port_number in dut_ports_number_dict.items():
            cmd = self.engine.run_cmd(
                f"sudo cat {IndependentModuleConst.IM_CONTROL_FILE_PATH.format(PORT_NUMBER=int(port_number) - 1)}")
            if int(cmd) == 1:
                ports_with_im_support.append(port_name)
        logger.info(f'Ports supporting IM are {ports_with_im_support}')
        return ports_with_im_support

    def disable_autoneg_on_ports_supporting_im(self, port_supporting_im):
        """
        @summary: This method is for disable auto negotiation at ports supporting IM
        """
        logger.info(f'Disabling autoneg for ports {port_supporting_im}')
        for port in port_supporting_im:
            self.interface_cli.config_auto_negotiation_mode(port, "disabled")
        self.general_cli.save_configuration()

    def enable_cmis_mgr_in_pmon_file(self, platform_params):
        """
        @summary: This method is for enable CMIS in pmon file
        @param: platform_params: platform_params fixture
        """
        skip_xcvrd_cmis_mgr_flag = 'skip_xcvrd_cmis_mgr'
        cmd = f'sudo sed -i \'s/"{skip_xcvrd_cmis_mgr_flag}": true/"{skip_xcvrd_cmis_mgr_flag}": false/\' ' \
              f'{SonicConst.PMON_DAEMON_CONTROL_JSON_PATH.format(PLATFORM=platform_params["platform"])}'
        self.engine.run_cmd(cmd)

    def dut_ports_number_dict(self, topology_obj, is_community=False):
        """
        @summary: This method is return logical to physical port mapping for topology active ports
        @param: topology_obj: topology_obj fixture
        @param: is_community: if function call for community setup
        """
        dut_ports_number_dict = {}
        ports_aliases_dict = self.interface_cli.parse_ports_aliases_on_sonic()
        if is_community:
            ports = self.interface_cli.get_admin_up_ports()
        else:
            ports = topology_obj.players_all_ports['dut']
        for port in ports:
            dut_ports_number_dict[port] = get_alias_number(ports_aliases_dict[port])
        return dut_ports_number_dict

    def upload_cmis_files(self, platform_params, chip_type):
        platform = platform_params['platform']
        hwsku = platform_params['hwsku']
        shared_cmis_path = InfraConst.MARS_CMIS_FOLDER_PATH

        logger.info("Copy Independent Module files")
        media_setting_file_path = f'{shared_cmis_path}{chip_type.lower()}_{IndependentModuleConst.MEDIA_SETTINGS_FILE_NAME}'

        logger.info(f'Copy file {media_setting_file_path} to /tmp directory on a switch')
        self.engine.copy_file(source_file=media_setting_file_path,
                              dest_file=IndependentModuleConst.MEDIA_SETTINGS_FILE_NAME,
                              file_system='/tmp/',
                              overwrite_file=True, verify_file=False)
        self.engine.run_cmd(f'sudo mv /tmp/{IndependentModuleConst.MEDIA_SETTINGS_FILE_NAME} '
                            f'{IndependentModuleConst.IM_INTERFACE_SETTINGS_FILE_PATH.format(PLATFORM=platform, HWSKU=hwsku)}')

        logger.info(f'Copy file {shared_cmis_path}{IndependentModuleConst.OPTICS_SI_SETTINGS_FILE_NAME} '
                    f'to /tmp directory on a switch')
        self.engine.copy_file(source_file=f'{shared_cmis_path}{IndependentModuleConst.OPTICS_SI_SETTINGS_FILE_NAME}',
                              dest_file=IndependentModuleConst.OPTICS_SI_SETTINGS_FILE_NAME, file_system='/tmp/',
                              overwrite_file=True, verify_file=False)
        self.engine.run_cmd(f'sudo mv /tmp/{IndependentModuleConst.OPTICS_SI_SETTINGS_FILE_NAME}'
                            f' {IndependentModuleConst.IM_INTERFACE_SETTINGS_FILE_PATH.format(PLATFORM=platform, HWSKU=hwsku)}')

    def enable_im(self, topology_obj, platform_params, chip_type, enable_im=True, is_community=False):
        """
        @summary: This method is for enable IM feature at DUT
        @param: topology_obj: topology_obj fixture
        @param: platform_params: platform_params fixture
        @param: chip_type: chip_type fixture
        @param: enable_im: flag for enable IM by default
        @param: is_community: if function call for community setup
        """
        with allure.step('Check if system supports IM'):
            sonic_branch = get_sonic_branch(topology_obj)
            skip_for_release = ['201911', '202012', '202205', '202211', '202305']
            with allure.step('Check if SPC3 or higher and is Microsoft SKU applied at system'):
                if self.is_system_supports_im() and self.is_ms_hwsku():
                    with allure.step('Check if setup having cables that supports IM'):
                        if platform_params.host_name in IndependentModuleConst.DUTS_SUPPORTING_IM:
                            with allure.step('Check if SONiC branch supports IM'):
                                if sonic_branch not in skip_for_release:
                                    with allure.step('Check if IM enabled by default, if not - enable it'):
                                        if enable_im and not self.is_im_enabled():
                                            self.enable_im_in_sai()
                                        with allure.step('Get all ports supporting IM'):
                                            if self.is_im_enabled():
                                                port_supporting_im = \
                                                    self.get_ports_supporting_im(
                                                        self.dut_ports_number_dict(topology_obj, is_community))
                                                if port_supporting_im:
                                                    with allure.step('Enable Independent Module feature at system:'
                                                                     ' Upload files, skip cmis_mgr, disable auto'
                                                                     ' neg at ports supporting IM'):
                                                        logger.info(f'Configure IM at DUT')
                                                        self.upload_cmis_files(platform_params, chip_type)
                                                        self.enable_cmis_mgr_in_pmon_file(platform_params)
                                                        self.disable_autoneg_on_ports_supporting_im(
                                                            port_supporting_im)
