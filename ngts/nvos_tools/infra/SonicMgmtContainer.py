from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.nvos_constants.constants_nvos import SyslogConsts
import logging
import allure

logger = logging.getLogger()

remove_comment_sign = "s/#{text}/{text}/g"
add_comment_sign = "/^[^#]/s/{text}/#{text}/g"


class SonicMgmtContainer:

    @staticmethod
    def restart_rsyslog(sonic_mgmt_engine):
        with allure.step("Restart rsyslog over sonic-mgmt container"):
            logging.info("Restart rsyslog over sonic-mgmt container")
            sonic_mgmt_engine.run_cmd('sudo pkill rsyslogd')
            sonic_mgmt_engine.run_cmd('rm -f /var/run/rsyslogd.pid')
            sonic_mgmt_engine.run_cmd('rsyslogd -n &')

    @staticmethod
    def remove_comment_sign_from_rsyslog_conf_file(sonic_mgmt_engine, sentences_list):
        for sentence in sentences_list:
            logging.info("Remove \'#\' from the next sentence in the rsyslog.conf file : {}".format(sentence))
            GeneralCliCommon(sonic_mgmt_engine).sed(SyslogConsts.RSYSLOG_CONF_FILE,
                                                    remove_comment_sign.format(text=sentence), "-i")

    @staticmethod
    def add_comment_sign_to_rsyslog_conf_file(sonic_mgmt_engine, sentences_list):
        for sentence in sentences_list:
            logging.info("Add \'#\' to the next sentence in the rsyslog.conf file : {}".format(sentence))
            GeneralCliCommon(sonic_mgmt_engine).sed(SyslogConsts.RSYSLOG_CONF_FILE,
                                                    add_comment_sign.format(text=sentence), "-i")

    @staticmethod
    def enable_rsyslog(sonic_mgmt_engine, protocol, restart_rsyslog=True):
        '''
        enable rsyslog on sonic_mgmt_engine.
        update the rsyslog.conf file with the relevant protocol.
        :param sonic_mgmt_engine: engine object of sonic mgmt container
        :param protocol: rsyslog protocol - 'tcp' or 'udp'
        :param restart_rsyslog: bool, true to restart rsyslog after changing the rsyslog.conf file.
        '''
        with allure.step("Enable rsyslog over sonic-mgmt container, with {} protocol".format(protocol)):
            logging.info("Enable rsyslog over sonic-mgmt container, with {} protocol".format(protocol))
            if protocol == 'udp' or protocol == 'tcp':
                sentences_list = [SyslogConsts.MODULE_LINE.format(protocol=protocol),
                                  SyslogConsts.PORT_LINE.format(protocol=protocol, port=SyslogConsts.DEFAULT_PORT)]
                SonicMgmtContainer.remove_comment_sign_from_rsyslog_conf_file(sonic_mgmt_engine, sentences_list)
            else:
                raise Exception("Test issue - protocol must be udp or tcp, not {}".format(protocol))

            if restart_rsyslog:
                SonicMgmtContainer.restart_rsyslog(sonic_mgmt_engine)

    @staticmethod
    def change_rsyslog_port(sonic_mgmt_engine, old_port, new_port, protocol, restart_rsyslog=True):
        with allure.step("Change rsyslog port to {}".format(new_port)):
            logging.info("Change rsyslog port to {}".format(new_port))
            new_line = SyslogConsts.PORT_LINE.format(protocol=protocol, port=new_port)
            old_line = SyslogConsts.PORT_LINE.format(protocol=protocol, port=old_port)
            regex = "s/{old_line}/{new_line}/g".format(old_line=old_line, new_line=new_line)
            GeneralCliCommon(sonic_mgmt_engine).sed(SyslogConsts.RSYSLOG_CONF_FILE, regex, "-i")

            if restart_rsyslog:
                SonicMgmtContainer.restart_rsyslog(sonic_mgmt_engine)
