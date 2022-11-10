V4_CONFIG = {"dut_ha_1": "1.1.1.1", "ha_dut_1": "1.1.1.2",
             "dut_ha_2": "2.2.2.2", "ha_dut_2": "2.2.2.3",
             "dut_hb_1": "3.3.3.3", "hb_dut_1": "3.3.3.4",
             "dut_hb_2": "4.4.4.4", "hb_dut_2": "4.4.4.5",
             "vlan_300_dut_hb_2": "3.3.3.5",
             "vlan_200_bond1": "2.2.2.4"

             }
V6_CONFIG = {"dut_ha_1": "1000::1", "ha_dut_1": "1000::2",
             "dut_ha_2": "2000::1", "ha_dut_2": "2000::2",
             "dut_hb_1": "3000::1", "hb_dut_1": "3000::2",
             "dut_hb_2": "4000::1", "hb_dut_2": "4000::2",
             "vlan_300_dut_hb_2": "3000::3",
             "vlan_200_bond1": "2000::4"
             }

OUTER_NOLY_PACKET_BASIC_DATA = {"ip_type": 'ipv4',
                                "outer_dip": "50.50.50.51",
                                "outer_sip": "10.10.10.11",
                                "outer_proto": 6,
                                "outer_smac": "00:00:00:00:00:01",
                                "outer_dmac": "ec:0d:9a:60:39:00",
                                "outer_dport": 4789,
                                "outer_sport": 5555}

OUTER_INNER_PACKET_BASIC_DATA = {"ip_type": 'ipv4',
                                 "outer_dip": "50.50.50.51",
                                 "outer_sip": "10.10.10.11",
                                 "outer_proto": 17,
                                 "outer_smac": "00:00:00:00:00:01",
                                 "outer_dmac": "00:00:00:00:00:02",
                                 "outer_dport": 4789,
                                 "outer_sport": 5555,
                                 "inner_dip": "100.100.100.1",
                                 "inner_sip": "200.200.200.1",
                                 "inner_proto": 17,
                                 "inner_smac": "00:00:00:00:00:01",
                                 "inner_dmac": "00:00:00:00:00:02",
                                 "inner_dport": 6000,
                                 "inner_sport": 7000}

OUTER_NOLY_PACKET_V6_BASIC_DATA = {"ip_type": 'ipv6',
                                   "outer_dip": "5000::1",
                                   "outer_sip": "6000::1",
                                   "outer_next_header": 6,
                                   "outer_smac": "00:00:00:00:00:01",
                                   "outer_dmac": "ec:0d:9a:60:39:00",
                                   "outer_dport": 4789,
                                   "outer_sport": 5555}

OUTER_INNER_PACKET_V6_BASIC_DATA = {"ip_type": 'ipv6',
                                    "outer_dip": "5000::1",
                                    "outer_sip": "6000::1",
                                    "outer_next_header": 17,
                                    "outer_smac": "00:00:00:00:00:01",
                                    "outer_dmac": "00:00:00:00:00:02",
                                    "outer_dport": 4789,
                                    "outer_sport": 5555,
                                    "inner_dip": "7000::1",
                                    "inner_sip": "8000::1",
                                    "inner_next_header": 17,
                                    "inner_smac": "00:00:00:00:00:01",
                                    "inner_dmac": "00:00:00:00:00:02",
                                    "inner_dport": 6000,
                                    "inner_sport": 7000}

DATA_V4 = {"outer_dip": ["50.50.50.52", "50.50.50.53"],
           "outer_sip": ["10.10.10.21", "10.10.10.23"],
           "outer_smac": ["00:02:00:00:00:01", "00:0a:00:00:00:02"],
           "outer_dport": [4789, 4790],
           "outer_sport": [5555, 5556],
           "inner_dip": ["100.100.100.11", "100.100.100.12"],
           "inner_sip": ["200.200.200.11", "200.200.200.12"],
           "inner_proto": [6, 17],
           }

DATA_V6 = {"outer_dip": ["5000::2", "5000::3"],
           "outer_sip": ["6000::2", "6000::3"],
           "outer_smac": ["00:12:00:00:00:01", "00:13:00:00:00:02"],
           "outer_dport": [4789, 4790],
           "outer_sport": [5555, 5556],
           "inner_dip": ["7000::2", "7000::3"],
           "inner_sip": ["8000::2", "8000::3"],
           "inner_next_header": [6, 17],
           }

DEST_ROUTE_V4 = {"prefix": "50.50.50.0", "mask": 24}
DEST_ROUTE_V6 = {"prefix": "5000::", "mask": 64}
