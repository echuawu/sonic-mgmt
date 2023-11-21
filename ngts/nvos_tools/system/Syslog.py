import allure
import logging
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType, SyslogConsts
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
logger = logging.getLogger()


class Syslog(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/syslog')
        self.servers = Servers(self)
        self.format = Format(self)

    def set_trap(self, severity_level, expected_str='', apply=False, ask_for_confirmation=False):
        with allure.step("Set trap with severity level : {}".format(severity_level)):
            logging.info("Set trap with severity level : {}".format(severity_level))
            return self.set(op_param_name=SyslogConsts.TRAP, op_param_value=severity_level, expected_str=expected_str,
                            apply=apply, ask_for_confirmation=ask_for_confirmation)

    def unset_trap(self, apply=False, ask_for_confirmation=False):
        return self.unset(SyslogConsts.TRAP, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def get_syslog_field_value(self, field_name):
        output = OutputParsingTool.parse_json_str_to_dictionary(self.show()).get_returned_value()
        if field_name in output.keys():
            return output[field_name]
        return None

    def get_syslog_field_values(self, field_names=[SyslogConsts.FORMAT, SyslogConsts.SERVER, SyslogConsts.TRAP]):
        output = OutputParsingTool.parse_json_str_to_dictionary(self.show()).get_returned_value()
        values = {}
        for field_name in field_names:
            if field_name in output.keys():
                values[field_name] = output[field_name]
            else:
                values[field_name] = ""
        return values

    def verify_show_syslog_output(self, expected_dictionary):
        with allure.step("Verify show syslog output"):
            logging.info("Verify show syslog output")
            output = self.get_syslog_field_values()
            logger.info("Expected show syslog output:\n {}".format(expected_dictionary))
            ValidationTool.compare_dictionary_content(output, expected_dictionary).verify_result()

    def verify_server_in_show_syslog_output(self, server):
        with allure.step("Verify server {} exists in show syslog output".format(server)):
            logging.info("Verify server {} exists in show syslog output".format(server))
            output = self.get_syslog_field_values()
            assert server in output['server'], "server {} does not exist in the show syslog output".format(server)

    def verify_global_severity_level(self, expected_severity_level):
        actually_severity_level = self.get_syslog_field_value(SyslogConsts.TRAP)
        assert actually_severity_level == expected_severity_level, "The trap severity level is not as expected\n" \
                                                                   "Actual: {} \n" \
                                                                   "Expected: {}".format(actually_severity_level,
                                                                                         expected_severity_level)

    def verify_show_syslog_format_output(self, expected_dictionary):
        with allure.step("Verify show syslog format output"):
            logging.info("Verify show syslog format output")
            logger.info("Expected format output:\n {}".format(expected_dictionary))
            output = OutputParsingTool.parse_json_str_to_dictionary(self.format.show()).get_returned_value()
            ValidationTool.compare_dictionary_content(output, expected_dictionary).verify_result()


class Format(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/format')
        self.welf = WelfFormat(self)


class Servers(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/server')
        self.servers_dict = {}

    def set_server(self, server_id, expected_str='', apply=False, ask_for_confirmation=False):
        with allure.step("Set server with id : {}".format(server_id)):
            logging.info("Set server with id : {}".format(server_id))
            server_value = {} if TestToolkit.tested_api == ApiType.OPENAPI else ""
            self.set(op_param_name=server_id, op_param_value=server_value, expected_str=expected_str,
                     apply=apply, ask_for_confirmation=ask_for_confirmation)
            server = Server(self, server_id)
            self.servers_dict.update({server_id: server})
            return server

    def unset_server(self, server_id, apply=False, ask_for_confirmation=False):
        result_obj = self.servers_dict[server_id].unset(apply=apply, ask_for_confirmation=ask_for_confirmation)
        self.servers_dict.pop(server_id)
        return result_obj

    def verify_show_servers_list(self, expected_servers_list):
        with allure.step("Verify servers {} exists in show syslog server output".format(expected_servers_list)):
            logging.info("Verify servers {} exists in show syslog server output".format(expected_servers_list))
            output = OutputParsingTool.parse_json_str_to_dictionary(self.show()).get_returned_value()
            ValidationTool.validate_all_values_exists_in_list(expected_servers_list, output.keys()).verify_result()


class Server(BaseComponent):
    def __init__(self, parent_obj=None, server_id=''):
        BaseComponent.__init__(self, parent=parent_obj, path='/' + server_id)
        self.filter = Filter(self)
        self.server_id = server_id

    def set_vrf(self, vrf='default', expected_str='', apply=False, ask_for_confirmation=False):
        return self.set(op_param_name=SyslogConsts.VRF, op_param_value=vrf, expected_str=expected_str,
                        apply=apply, ask_for_confirmation=ask_for_confirmation)

    def unset_vrf(self, apply=False, ask_for_confirmation=False):
        return self.unset(SyslogConsts.VRF, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_protocol(self, protocol, expected_str='', apply=False, ask_for_confirmation=False):
        return self.set(op_param_name=SyslogConsts.PROTOCOL, op_param_value=protocol, expected_str=expected_str,
                        apply=apply, ask_for_confirmation=ask_for_confirmation)

    def unset_protocol(self, apply=False, ask_for_confirmation=False):
        return self.unset(SyslogConsts.PROTOCOL, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_port(self, port_str=SyslogConsts.DEFAULT_PORT, expected_str='', apply=False, ask_for_confirmation=False):
        return self.set(op_param_name=SyslogConsts.PORT, op_param_value=port_str, expected_str=expected_str,
                        apply=apply, ask_for_confirmation=ask_for_confirmation)

    def unset_port(self, apply=False, ask_for_confirmation=False):
        return self.unset(SyslogConsts.PORT, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_filter(self, filter, regex, expected_str='', apply=False, ask_for_confirmation=False):
        return self.filter.set(op_param_name=filter, op_param_value=regex, expected_str=expected_str,
                               apply=apply, ask_for_confirmation=ask_for_confirmation)

    def unset_filter(self, apply=False, ask_for_confirmation=False):
        return self.filter.unset(apply=apply, ask_for_confirmation=ask_for_confirmation)

    def verify_show_server_output(self, expected_dictionary):
        with allure.step("Verify show syslog server {} output".format(self.server_id)):
            logging.info("Verify show syslog server {} output".format(self.server_id))
            output = OutputParsingTool.parse_json_str_to_dictionary(self.show()).get_returned_value()
            logger.info("Expected show server output:\n {}".format(expected_dictionary))
            ValidationTool.compare_dictionary_content(output, expected_dictionary).verify_result()
            return output

    def verify_trap_severity_level(self, expected_severity_level):
        actually_severity_level = self.get_syslog_field_value(SyslogConsts.TRAP)
        assert actually_severity_level == expected_severity_level, "The trap severity level is not as expected\n" \
                                                                   "Actual: {} \n" \
                                                                   "Expected: {}".format(actually_severity_level,
                                                                                         expected_severity_level)


class WelfFormat(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/welf')

    def set_firewall_name(self, firewall_name, expected_str='', apply=False, ask_for_confirmation=False):
        with allure.step("Set welf firewall-name : {}".format(firewall_name)):
            logging.info("Set welf firewall-name : {}".format(firewall_name))
            res = self.set(op_param_name=SyslogConsts.FIREWAL_NAME, op_param_value=firewall_name,
                           expected_str=expected_str, apply=apply, ask_for_confirmation=ask_for_confirmation)
            return res

    def unset_firewall_name(self, apply=False, ask_for_confirmation=False):
        return self.unset(SyslogConsts.FIREWAL_NAME, apply=apply, ask_for_confirmation=ask_for_confirmation)


class Filter(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/filter')

    def set_include_filter(self, regex, expected_str='', apply=False, ask_for_confirmation=False):
        return self.set(SyslogConsts.INCLUDE, regex, expected_str=expected_str, apply=apply,
                        ask_for_confirmation=ask_for_confirmation)

    def set_exclude_filter(self, regex, expected_str='', apply=False, ask_for_confirmation=False):
        return self.set(SyslogConsts.EXCLUDE, regex, expected_str=expected_str, apply=apply,
                        ask_for_confirmation=ask_for_confirmation)

    def unset_filter(self, filter='', expected_str='', apply=False, ask_for_confirmation=False):
        return self.unset(filter, expected_str=expected_str, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def unset_include_filter(self, apply=False, expected_str='', ask_for_confirmation=False):    # illegal command - just for bad case check!
        return self.unset_filter(SyslogConsts.INCLUDE, expected_str=expected_str, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def unset_exclude_filter(self, apply=False, expected_str='', ask_for_confirmation=False):     # illegal command - just for bad case check!
        return self.unset_filter(SyslogConsts.EXCLUDE, expected_str=expected_str, apply=apply, ask_for_confirmation=ask_for_confirmation)
