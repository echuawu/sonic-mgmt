import logging
import pytest
import csv

from ngts.tools.topology_tools.topology_by_setup import get_topology_by_setup_name_and_aliases
from ngts.cli_util.cli_parsers import parse_show_interfaces_transceiver_eeprom

logger = logging.getLogger()

COPPER_CABLES_LIST = ['MCP1600-C00AE30N', 'MCP1600-C001E30N', 'MCP1600-C01AE30N', 'MCP1600-C002E30N',
                      'MCP1600-C02AE30L', 'MCP1600-C003E30L', 'MCP1600-C02AE26N', 'MCP1600-C003E26N',
                      'MCP1600-C005E26L',
                      'MCP1650-V00AE30', 'MCP1650-V001E30', 'MCP1650-V01AE30', 'MCP1650-V002E26', 'MCP1650-V02AE26',
                      'MCP1650-V003E26',
                      'MCP2M00-A00AE30N', 'MCP2M00-A001E30N', 'MCP2M00-A01AE30N', 'MCP2M00-A002E30N',
                      'MCP2M00-A02AE30L', 'MCP2M00-A02AE26N', 'MCP2M00-A003E30L', 'MCP2M00-A003E26N',
                      'MCP2M00-A004E26L', 'MCP2M00-A005E26L',
                      'MCP2M00-A00A', 'MCP2M00-A001', 'MCP2M00-A01A', 'MCP2M00-A002', 'MCP2M00-A02A', 'MCP2M00-A003',
                      'MCP2M00-A004E26L', 'MCP2M00-A0054E26L',
                      'MCP1600-E00AE30', 'MCP1600-E001E30', 'MCP1600-E01AE30', 'MCP1600-E002E30', 'MCP1600-E02AE26',
                      'MCP1600-E003E26', 'MCP1600-E004E26', 'MCP1600-E005E26',
                      'MCP1650-H00AE30', 'MCP1650-H001E30', 'MCP1650-H01AE30', 'MCP1650-H002E26',
                      'MCP1600-E002', 'MCP1600-E00A',
                      'MCP7H00-G01AR', 'MCP7H00-G001R30N',
                      'MCP7H60-W001R30', 'MCP7H60-W01AR30', 'MCP7H60-W002R26', 'MCP7H60-W02AR26', 'MCP7H60-W003R26',
                      'MCP1600-E001', 'MCP7H00-G001', 'MCP1600-E01A', 'MCP1600-C00A', 'MCP1600-C001', 'MC2609125-005']

OPTIC_CABLES_LIST = ['MFA1A00-C003', 'MFA1A00-E003', 'MFA1A00-C005', 'MFS1200-C003', 'MFA7A20-C003', 'MFA1A00-C010']


@pytest.fixture()
def setups_list():

    # Canonical
    canonical_setups = ['sonic_leopard_r-leopard-41', 'sonic_panther_r-panther-13', 'sonic_anaconda_r-anaconda-15',
                        'sonic_moose_r-moose-02', 'sonic_alligator_r-alligator-04', 'sonic_leopard_r-leopard-56',
                        'sonic_tigon_r-tigon-15', 'sonic_liger_r-liger-02', 'sonic_tigris_r-tigris-22',
                        'sonic_ocelot_r-ocelot-02', 'sonic_spider_r-spider-05', 'sonic_bulldog_r-bulldog-02',
                        'sonic_boxer_r-boxer-sw01', 'sonic_panther_r-panther-36', 'sonic_panther_r-panther-03',
                        'sonic_leopard_r-leopard-32', 'sonic_lionfish_r-lionfish-16', 'sonic_ocelot_r-ocelot-07',
                        'sonic_bulldog_r-bulldog-03', 'sonic_panther_r-panther-23', 'sonic_lionfish_r-lionfish-14',
                        'sonic_bulldog_r-bulldog-04', 'sonic_lionfish_r-lionfish-07', 'sonic_anaconda_r-anaconda-51']

    # Community
    community_setups = ['r-moose-01_setup', 'r-tigon-11_setup', 'r-leopard-01_setup', 'r-tigris-04_setup',
                        'r-leopard-58_setup', 'r-tigris-13_setup', 'r-tigon-04_setup', 'arc-switch1004_setup',
                        'arc-switch1025_setup', 'r-tigon-21_setup', 'r-tigon-20_setup', 'r-leopard-72_setup',
                        'c-panther-01_setup', 'r-leopard-70_setup', 'r-tigris-25_setup', 'r-tigris-26_setup',
                        'mtbc-sonic-03-2700_setup']

    list_of_setups = canonical_setups + community_setups

    return list_of_setups


@pytest.mark.disable_loganalyzer
def test_collect_cables_info(setups_list):
    """
    This test will get info about connected cables from all setups which returned by 'setups_list' fixture
    At the end it will crete .csv with with all data, table format is:
    Cable OPN, Cable Type Copper/Optic, Cable length, Connected to switch type, Connected to setup
    :param setups_list: setups_list fixture
    """
    header = ['Cable OPN', 'Cable Type', 'Cable length', 'Connected to switch type', 'Connected to setup']
    sfputil_show_eeprom_cmd = 'sudo sfputil show eeprom'

    with open('cables_info.csv', 'w', encoding='UTF8') as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow(header)

        for setup_name in setups_list:
            topology_obj = get_topology_by_setup_name_and_aliases(setup_name, slow_cli=False)

            switch_type = \
                topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['switch_type']
            switch_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']

            try:
                dut_engine = topology_obj.players['dut']['engine']
            except Exception as err:
                logger.error(f'Unable to get SSH engine to setup: {setup_name}, got error: {err}')
                dut_engine = None

            if dut_engine:
                try:
                    sfputil_eeprom_output = dut_engine.run_cmd(sfputil_show_eeprom_cmd, validate=True)
                    parsed_eeprom_info_dict = parse_show_interfaces_transceiver_eeprom(sfputil_eeprom_output)
                except Exception as err:
                    logger.error(f'Unable to get SFPs info, got error: {err}')
                    parsed_eeprom_info_dict = None

                if parsed_eeprom_info_dict:
                    for interface in parsed_eeprom_info_dict:

                        status = parsed_eeprom_info_dict[interface].get('Status', '').strip()
                        cable_opn = parsed_eeprom_info_dict[interface].get('Vendor PN', '').strip()
                        cable_len = parsed_eeprom_info_dict[interface].get('Length Cable Assembly(m)', '').strip()
                        cable_interface_code = parsed_eeprom_info_dict[interface].get('Media Interface Code', '')
                        cable_spec = parsed_eeprom_info_dict[interface].get('Specification compliance', '')

                        if isinstance(cable_spec, dict):
                            cable_spec = cable_spec.get('Extended Specification Compliance', '')

                        cable_type = None

                        if 'RJ45' in status:
                            cable_type = 'RJ45'
                            cable_opn = 'N/A'
                            cable_len = 'N/A'

                        elif cable_opn in COPPER_CABLES_LIST:
                            cable_type = 'Copper'
                        elif cable_opn in OPTIC_CABLES_LIST:
                            cable_type = 'Optic'

                        elif 'optic' in cable_spec.lower():
                            cable_type = 'Optic'
                        elif 'copper' in cable_interface_code.lower():
                            cable_type = 'Copper'

                        if not cable_type:
                            cable_type = 'Unknown'

                        data = [cable_opn, cable_type, cable_len, switch_type, switch_name]

                        writer.writerow(data)

                dut_engine.disconnect()
            else:
                logger.error(f'Unable to get SSH engine to setup: {setup_name}')
