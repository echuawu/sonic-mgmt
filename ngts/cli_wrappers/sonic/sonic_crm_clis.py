import re
import logging

from ngts.cli_util.cli_parsers import generic_sonic_output_parser

logger = logging.getLogger()
CRM_DEFAULT_INTERVAL = 300


class CrmThresholdTypeError(Exception):
    pass


class CrmThresholdValueError(Exception):
    pass


class CrmThresholdResourceError(Exception):
    pass


class CRMHelper:
    """ Helper class for 'SonicCrmCli' class """
    @staticmethod
    def validate_threshold_type(th_type):
        theshold_types = ['percentage', 'used', 'free']

        if th_type not in theshold_types:
            raise CrmThresholdTypeError('Unsupported threshold type: \'{}\''.format(th_type))

    @staticmethod
    def validate_threshold_value(value):
        if not isinstance(value, int):
            raise CrmThresholdValueError('Value is not an integer type: {} {}'.format(value, type(value)))
        if not(0 <= value <= 100):
            raise CrmThresholdValueError('Value is out of range 0..100: \'{}\''.format(value))

    @classmethod
    def set_threshold_type(cls, engine, template, th_type):
        cls.validate_threshold_type(th_type)

        cmd = ' '.join([template, 'type', th_type])
        engine.run_cmd(cmd)

    @classmethod
    def set_threshold_value(cls, engine, template, value_type, value):
        cls.validate_threshold_value(value)

        cmd = ' '.join([template, value_type, str(value)])
        engine.run_cmd(cmd)

    @staticmethod
    def configure_threshold(engine, template, th_type=None, low=None, high=None):
        if th_type:
            CRMHelper.set_threshold_type(engine, template, th_type)
        if low:
            CRMHelper.set_threshold_value(engine, template, 'low', low)
        if high:
            CRMHelper.set_threshold_value(engine, template, 'high', high)


class SonicCrmCli:
    thresholds_cmd = 'crm config thresholds'

    def __init__(self, engine):
        self.engine = engine

    def set_threshold_ip(self, ip_ver, resource, th_type=None, low=None, high=None):
        """
        Configure CRM thresholds for 'ipv4/ipv6' 'neighbor', 'nexthop' or 'route' resources
        SONiC CLI configuration examples:
        crm config thresholds ipv4 --help
            neighbor  nexthop   route

        crm config thresholds ipv6 --help
            neighbor  nexthop   route

        crm config thresholds ipv4 route type percentage
        :param ip_ver: IP version 4 or 6 to choose between 'ipv4' or 'ipv6' CRM resources
        :param resource: crm 'ipv4/6' available resources - 'neighbor', 'nexthop' or 'route'
        :param th_type: crm threshold type: 'percentage', 'used' or 'free'
        :param low: crm low threshold 0..100
        :param high: crm high threshold 0..100
        """
        resources = ['neighbor', 'nexthop', 'route']
        if resource not in resources:
            raise CrmThresholdResourceError(
                'Unsupported resource specified - \'{}\'\nExpected - {}'.format(
                    resource, resources
                )
            )

        template = ' '.join([self.thresholds_cmd, 'ipv{}'.format(ip_ver), resource])
        CRMHelper.configure_threshold(self.engine, template, th_type, low, high)

    def set_threshold_nexthop_group(self, resource, th_type=None, low=None, high=None):
        """
        Configure CRM thresholds for 'nexthop group' resources.
        SONiC CLI command examples:
        crm config thresholds nexthop group --help
            Commands:
                member  CRM configuration for nexthop group member...
                object  CRM configuration for nexthop group resource

        crm config thresholds nexthop group member type percentage
        crm config thresholds nexthop group object low 5
        :param resource: crm 'ipv4/6' available resources - 'neighbor', 'nexthop' or 'route'
        :param th_type: crm threshold type: 'percentage', 'used' or 'free'
        :param low: crm low threshold 0..100
        :param high: crm high threshold 0..100
        """
        resources = ['member', 'object']
        if resource not in resources:
            raise CrmThresholdResourceError(
                'Unsupported resource specified - \'{}\'\nExpected - {}'.format(
                    resource, resources
                )
            )

        template = ' '.join([self.thresholds_cmd, 'nexthop group', resource])
        CRMHelper.configure_threshold(self.engine, template, th_type, low, high)

    def set_threshold_acl(self, resource, th_type=None, low=None, high=None):
        """
        Configure CRM thresholds for 'acl' resources
        SONiC CLI command examples:
        crm config thresholds acl table type percentage
        crm config thresholds acl group counter type percentage
        crm config thresholds acl group type percentage
        :param resource: crm 'ipv4/6' available resources - 'neighbor', 'nexthop' or 'route'
        :param th_type: crm threshold type: 'percentage', 'used' or 'free'
        :param low: crm low threshold 0..100
        :param high: crm high threshold 0..100
        """
        resources = ['table', 'group', 'group counter', 'group entry']
        if resource not in resources:
            raise CrmThresholdResourceError(
                'Unsupported resource specified - \'{}\'\nExpected - {}'.format(
                    resource, resources
                )
            )

        template = ' '.join([self.thresholds_cmd, 'acl', resource])
        CRMHelper.configure_threshold(self.engine, template, th_type, low, high)

    def set_threshold_fdb(self, th_type=None, low=None, high=None):
        """
        Configure CRM thresholds for 'fdb' resource
        SONiC CLI command examples:
        crm config thresholds fdb --help
            high  CRM high threshold configuration
            low   CRM low threshold configuration
            type  CRM threshold type configuration
        :param th_type: crm threshold type: 'percentage', 'used' or 'free'
        :param low: crm low threshold 0..100
        :param high: crm high threshold 0..100
        """
        template = ' '.join([self.thresholds_cmd, 'fdb'])
        CRMHelper.configure_threshold(self.engine, template, th_type, low, high)

    def get_polling_interval(self):
        """
        Return configured CRM polling interval
        """
        output = self.engine.run_cmd('crm show summary')
        if 'error' in output.lower():
            logger.warning('CRM was not enabled yet, returning default {} sec. interval'.format(CRM_DEFAULT_INTERVAL))
            return CRM_DEFAULT_INTERVAL
        else:
            return int(self.engine.run_cmd('crm show summary | awk \'{print $3}\'').strip())

    def set_polling_interval(self, interval):
        """
        Configure CRM polling interval
        :param interval: crm polling interval in seconds
        """
        self.engine.run_cmd('crm config polling interval {}'.format(interval))

    def parse_thresholds_table(self):
        """
        Parse output of 'crm show thresholds all'
        """
        output = self.engine.run_cmd("crm show thresholds all")
        result = generic_sonic_output_parser(output, headers_ofset=0,
                                             len_ofset=1,
                                             data_ofset_from_start=2,
                                             data_ofset_from_end=-1,
                                             column_ofset=2,
                                             output_key='Resource Name')
        return result

    def parse_resources_table(self):
        """
        Run output of 'crm show resources all'
        """
        result = {'main_resources': {}, 'acl_resources': [], 'table_resources': []}
        output = self.engine.run_cmd("crm show resources all")
        first_table, rest_output = self.extract_first_table_from_output(output)
        result['main_resources'] = generic_sonic_output_parser(first_table, headers_ofset=0,
                                                               len_ofset=1,
                                                               data_ofset_from_start=2,
                                                               data_ofset_from_end=0,
                                                               column_ofset=2,
                                                               output_key='Resource Name')

        first_table, rest_output = self.extract_first_table_from_output(rest_output)
        result['acl_resources'] = generic_sonic_output_parser(first_table, headers_ofset=0, len_ofset=1,
                                                              data_ofset_from_start=2,
                                                              data_ofset_from_end=0,
                                                              column_ofset=2,
                                                              output_key=None)

        result['table_resources'] = generic_sonic_output_parser(rest_output, headers_ofset=1, len_ofset=2,
                                                                data_ofset_from_start=3,
                                                                data_ofset_from_end=0,
                                                                column_ofset=2,
                                                                output_key=None)
        return result

    @staticmethod
    def extract_first_table_from_output(output):
        """
        Extracting first table from output of tables
        :param output: string of tables
        return first table in string type and rest output in string type
        """
        empty_line = ""
        split_output = output.splitlines()
        if split_output.index(empty_line) == 0:
            split_output = output.splitlines()[1:]
        if empty_line in split_output:
            first_table_end_index = split_output.index(empty_line)
            first_table = split_output[:first_table_end_index]
            rest_output = split_output[first_table_end_index + 1:]
        else:
            first_table = split_output
            rest_output = ''
        return '\n'.join(first_table), '\n'.join(rest_output)
