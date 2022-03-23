import pytest
import allure
from ngts.constants.constants import P4SamplingConsts
from ngts.helpers.p4_sampling_utils import P4SamplingUtils


@pytest.mark.build
@pytest.mark.p4_sampling
class TestEntryBasic:

    @allure.title('Test entry added')
    def test_entry_added(self, engines, cli_objects, table_params):
        """
        Verify the entry added correctly
        :param engines: engines fixture object
        :param table_params: table_params fixture object
        :return: None
        """

        with allure.step('Get entries in table {} and {}, verify the entries are added correctly'.format(
                P4SamplingConsts.PORT_TABLE_NAME, P4SamplingConsts.FLOW_TABLE_NAME)):
            with allure.step('Verify the entries are added for {}'.format(P4SamplingConsts.PORT_TABLE_NAME)):
                P4SamplingUtils.verify_table_entry(engines.dut, cli_objects.dut, P4SamplingConsts.PORT_TABLE_NAME, table_params.port_entry)
            with allure.step('Verify the entries are added for {}'.format(P4SamplingConsts.FLOW_TABLE_NAME)):
                P4SamplingUtils.verify_table_entry(engines.dut, cli_objects.dut, P4SamplingConsts.FLOW_TABLE_NAME, table_params.flow_entry)

    @allure.title('Test entry hit')
    def test_entry_hit(self, topology_obj, engines, interfaces, table_params):
        """
        Verify the traffic which is expected to be match one of entry will be counted and mirrored correctly.
        :param topology_obj: topology_obj fixture object
        :param engines: engines fixture object
        :param interfaces: interfaces fixture object
        :param table_params: table_params fixture object
        :return:
        """
        cli_obj = topology_obj.players['dut']['cli']
        with allure.step("Verify the the packet that match entry key can be countered and mirrored"):
            with allure.step("Clear statistics and counters"):
                P4SamplingUtils.clear_statistics(cli_obj)
            with allure.step("Send packets and verify"):
                count = 20
                P4SamplingUtils.verify_traffic_hit(topology_obj, engines, interfaces, table_params, count, count)

    @allure.title('Test entry miss')
    def test_entry_miss(self, topology_obj, engines, interfaces, table_params):
        """
        Verify the traffic which is expected to be match any entries will not be counted and mirrored.
        :param topology_obj: topology_obj fixture object
        :param engines: engines fixture object
        :param interfaces: interfaces fixture object
        :param table_params: table_params fixture object
        :return:
        """
        cli_obj = topology_obj.players['dut']['cli']
        with allure.step("Verifying that the packet that dose not match entry key will not be countered"):
            with allure.step("Clear statistics and counters"):
                P4SamplingUtils.clear_statistics(cli_obj)
            with allure.step("Send packets and verify"):
                count = 20
                expect_count = 0
                P4SamplingUtils.verify_traffic_miss(topology_obj, engines, interfaces, table_params, count, expect_count)
