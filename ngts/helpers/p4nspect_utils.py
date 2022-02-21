import json
import ipaddress
import logging
from dotted_dict import DottedDict
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.constants.constants import P4ExamplesConsts


FEATURE_P4C_JSON_MAP = {"VXLAN_BM": "vxlan_bm.json"}


def get_p4nspect_query_parsed(engine, table_name="", controlblock_name="control_in_port"):
    """
    Run p4nspect query to get the entries added in P4.
    :param engine: ssh engine object
    :param controlblock_name: control block name
    :param table_name: table name
    :return: List of dictionary. Example: [{'key': 'Ethernet60 0xff/0xff', 'action': 'DoMirror', 'counters': 0, 'bytes':0}, ...],
                                          [{'key': '200.100.100.8 100.100.100.100 0x11, ', 'action': 'DoMirror', 'counters':0, 'bytes':0}, ...]
    the output of the cli command:
    ┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼
    │                                                               TABLE: control_in_port.table_port_sampling                                                              │
    ┼─────┼──────┼───┼─────────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼
    │ IDX │ PRIO │ A │           KEYS (Key | Value | Mask | Type)          │              ACTION             │            COUNTERS (Name | Type | Items | Value)            │
    ┼─────┼──────┼───┼─────────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼
    │  0  │  2   │ A │    std_meta.ingress_port     0x1            exact   │             DoMirror            │  control_in_port.dc_port_sampling  DIRECT  Pkts/Bts  (0, 0)  │
    │     │      │   │  headers.ipv4.hdr_checksum  0x100  0xffff  ternary  │  label_port         0x20        │                                                              │
    │     │      │   │                                                     │   src_mac    00:34:da:16:68:00  │                                                              │
    │     │      │   │                                                     │   dst_mac    00:42:a1:17:e6:fd  │                                                              │
    │     │      │   │                                                     │    src_ip         10.0.1.1      │                                                              │
    │     │      │   │                                                     │    dst_ip         10.0.1.2      │                                                              │
    │     │      │   │                                                     │     vlan            0x28        │                                                              │
    │     │      │   │                                                     │   is_trunc          0x1         │                                                              │
    │     │      │   │                                                     │  trunc_size        0x12c        │                                                              │
    ┼─────┼──────┼───┼─────────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼
    │  1  │  2   │ A │     std_meta.ingress_port    0x20           exact   │             DoMirror            │  control_in_port.dc_port_sampling  DIRECT  Pkts/Bts  (0, 0)  │
    │     │      │   │   headers.ipv4.hdr_checksum  0x1   0xffff  ternary  │  label_port         0x1         │                                                              │
    │     │      │   │                                                     │   src_mac    00:34:da:16:68:00  │                                                              │
    │     │      │   │                                                     │   dst_mac    00:42:a1:4b:0b:6c  │                                                              │
    │     │      │   │                                                     │    src_ip         50.0.0.1      │                                                              │
    │     │      │   │                                                     │    dst_ip         50.0.0.2      │                                                              │
    │     │      │   │                                                     │     vlan            0x28        │                                                              │
    │     │      │   │                                                     │   is_trunc          0x1         │                                                              │
    │     │      │   │                                                     │  trunc_size        0x12c        │                                                              │
    ┼─────┼──────┼───┼─────────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼
    │ 999 │  1   │ A │                                                     │             NoAction            │                                                              │
    │     │      │   │                                                     │                                 │                                                              │
    ┼─────┼──────┼───┼─────────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼

    ┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼
    │                                                                TABLE: control_in_port.table_flow_sampling                                                                │
    ┼─────┼──────┼───┼────────────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼
    │ IDX │ PRIO │ A │            KEYS (Key | Value | Mask | Type)            │              ACTION             │            COUNTERS (Name | Type | Items | Value)            │
    ┼─────┼──────┼───┼────────────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼
    │  0  │  2   │ A │    headers.ipv4.src_addr    10.0.1.2           exact   │             DoMirror            │  control_in_port.dc_flow_sampling  DIRECT  Pkts/Bts  (0, 0)  │
    │     │      │   │    headers.ipv4.dst_addr    50.0.1.1           exact   │  label_port         0x1         │                                                              │
    │     │      │   │    headers.ipv4.protocol      TCP              exact   │   src_mac    00:34:da:16:68:00  │                                                              │
    │     │      │   │     headers.tcp.src_port       20              exact   │   dst_mac    00:42:a1:4b:0b:6c  │                                                              │
    │     │      │   │     headers.tcp.dst_port       80              exact   │    src_ip         50.0.0.1      │                                                              │
    │     │      │   │  headers.ipv4.hdr_checksum   0x100    0xffff  ternary  │    dst_ip         50.0.0.2      │                                                              │
    │     │      │   │                                                        │     vlan            0x32        │                                                              │
    │     │      │   │                                                        │   is_trunc          0x1         │                                                              │
    │     │      │   │                                                        │  trunc_size        0x12c        │                                                              │
    ┼─────┼──────┼───┼────────────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼
    │  1  │  2   │ A │    headers.ipv4.src_addr    50.0.0.2           exact   │             DoMirror            │  control_in_port.dc_flow_sampling  DIRECT  Pkts/Bts  (0, 0)  │
    │     │      │   │    headers.ipv4.dst_addr    10.0.0.1           exact   │  label_port         0x20        │                                                              │
    │     │      │   │    headers.ipv4.protocol      TCP              exact   │   src_mac    00:34:da:16:68:00  │                                                              │
    │     │      │   │     headers.tcp.src_port       20              exact   │   dst_mac    00:42:a1:17:e6:fd  │                                                              │
    │     │      │   │     headers.tcp.dst_port       80              exact   │    src_ip         10.0.1.1      │                                                              │
    │     │      │   │  headers.ipv4.hdr_checksum    0x1     0xffff  ternary  │    dst_ip         10.0.1.2      │                                                              │
    │     │      │   │                                                        │     vlan            0x32        │                                                              │
    │     │      │   │                                                        │   is_trunc          0x1         │                                                              │
    │     │      │   │                                                        │  trunc_size        0x12c        │                                                              │
    ┼─────┼──────┼───┼────────────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼
    │ 999 │  1   │ A │                                                        │             NoAction            │                                                              │
    │     │      │   │                                                        │                                 │                                                              │
    ┼─────┼──────┼───┼────────────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼
    """

    docker_env_p4c_config = "P4NSPECT_P4C_CONFIG=/devtools/sampling.json"
    docker_env_backend_json_path = "P4NSPECT_BACKEND_JSON_PATH=/devtools/json"
    docker_name = "p4-sampling"
    p4nspect_cmd = "p4nspect query --controlblocks {} --tables {}".format(controlblock_name, table_name)
    cmd = "docker exec -e {} -e {} {} {}".format(docker_env_p4c_config, docker_env_backend_json_path,
                                                 docker_name, p4nspect_cmd)
    output = engine.run_cmd(cmd)
    error_msg = "p4nspect query: error:"
    if error_msg in output:
        raise Exception(output)
    if not output:
        return {}
    lines = output.splitlines()
    entry_splitter = lines[2]
    content_column_splitter = '│'
    entry_splitter_indices = get_entry_splitter_indices(lines, entry_splitter)
    entry_splitter_count = len(entry_splitter_indices)
    ret = {}
    port_configs = get_port_configs(engine)
    for i in range(1, entry_splitter_count - 1):
        entry_start_index = entry_splitter_indices[i]
        entry_end_index = entry_splitter_indices[i + 1]
        parse_entry_content(lines[entry_start_index + 1:entry_end_index], content_column_splitter, ret, port_configs)
    return ret


def get_entry_splitter_indices(lines, splitter):
    """
    get all the entry splitter indices, the real content of the entry content start from the second splitter
    :param lines: the lines of output content of p4nspect
    :param splitter: the entry splitter
    :return: list of entry splitter index.
    """
    indices = []
    for i in range(len(lines)):
        if lines[i] == splitter:
            indices.append(i)
    return indices


def parse_entry_content(entry_content_lines, content_column_splitter, ret, port_configs):
    """
    get the entry content, and add the content into the dictionary, the key is the entry key,
    the value of the dictionary include the entry action, entry priority, and entry counters
    :param entry_content_lines: the content of one entry shown in the p4nspect
    :param content_column_splitter: column splitter
    :param ret: the dictionary which will be updated
    :return: None
    """
    key_list = []
    action_list = []
    byte_count = 0
    packet_count = 0
    priority = 0
    for i in range(len(entry_content_lines)):
        entry_content_line = entry_content_lines[i].strip(content_column_splitter)
        line_content = entry_content_line.split(content_column_splitter)
        line_pri_content = line_content[1].strip()
        line_key_content = line_content[3].strip()
        line_action_content = line_content[4].strip()
        line_counter_content = line_content[5].strip()
        if line_pri_content:
            priority = line_pri_content
        if line_counter_content:
            bytes_packets = ''.join(line_counter_content.split()[-2:]).strip('(').strip(')').split(',')
            byte_count = bytes_packets[1]
            packet_count = bytes_packets[0]
        if line_key_content:
            key_list.append(get_key_value(line_key_content, port_configs))
        if line_action_content:
            if i == 0:
                action_list.append(line_action_content)
            else:
                action_list.append(get_action_value(line_action_content, port_configs))

    keys = " ".join(key_list)
    values = DottedDict()
    values.action = " ".join(action_list)
    values.byte_count = byte_count
    values.packet_count = packet_count
    values.priority = priority
    if keys:
        ret[keys] = values


def get_key_value(line_key_content, port_configs):
    """
    get key value
    :param line_key_content: the key content, example: std_meta.ingress_port, headers.ipv4.hdr_checksum
    :param port_configs: port config get from the config_db.json
    :return: the key value
    """
    key_content_list = line_key_content.split()
    key_name = key_content_list[0].split('.')[-1]
    key_value = key_content_list[1]
    key_type = key_content_list[-1]
    key_mask = key_content_list[2]
    if key_type == "exact":
        return format_value_with_name(key_name, key_value, port_configs)
    elif key_type == "ternary":
        return "/".join([format_value_with_name(key_name, key_value, port_configs),
                         format_value_with_name(key_name, key_mask, port_configs)])


def get_action_value(line_action_content, port_configs):
    """
    :param line_action_content: action param content, example: label_port         0x1,  src_ip         50.0.0.1
    :param port_configs: port config get from the config_db.json
    :return: the action param value
    """
    action_content_list = line_action_content.split()
    action_name = action_content_list[0]
    action_value = action_content_list[1]
    return format_value_with_name(action_name, action_value, port_configs)


def format_value_with_name(name, value, port_configs):
    """
    Format the value according to the name. do some special process for the specific name
    :param name:  name of the value
    :param value: the origin value to be formatted
    :param port_configs: port config get from the config_db.json
    :return: the format value
    """
    hex_key_list = ['vlan', 'is_trunc', 'trunc_size', 'vni']
    ipv4_key_list = ['underlay_dip']
    label_port_key_list = ['ingress_port', 'label_port']
    logic_port_key_list = ['pbs_port']
    if name in label_port_key_list:
        return convert_label_port_to_physical(value, port_configs)
    if name in logic_port_key_list:
        return convert_log_port_to_physical(value, port_configs)
    if name == 'hdr_checksum':
        return "{:#06x}".format(int(value, 16))
    elif name == 'protocol':
        return convert_protocol_value(value)
    elif name in ipv4_key_list:
        return convert_hex_to_ipv4_addr(value)
    elif name in hex_key_list:
        return "{}".format(int(value, 16))
    return "{}".format(value)


def convert_label_port_to_physical(label_port, port_configs):
    """
    convert label_port port to physical port
    :param label_port: label port value
    :param port_configs: port config get from the config_db.json
    :return: physical port
    """
    for port in port_configs.keys():
        port_config = port_configs.get(port)
        if port_config.get('index') == "{}".format(int(label_port, 16)):
            return port
    return label_port


def convert_log_port_to_physical(log_port, port_configs):
    """
    convert logic port to physical port
    :param log_port: logic port value
    :param port_configs: port config get from the config_db.json
    :return: physical port
    """
    label_port = log_port >> 22
    for port in port_configs.keys():
        port_config = port_configs.get(port)
        if port_config.get('index') == "{}".format(int(label_port, 16)):
            return port
    return label_port


def convert_protocol_value(protocol):
    if protocol == "TCP":
        return '6'
    return protocol


def convert_hex_to_ipv4_addr(ipv4_address_hex):
    """
    Converts hex string to an IPv4 address
    :param ipv4_address_hex: the hex string value
    :return: A dot-notation IPv4 address, Example::print(hex_to_ipv4_addr('0x1'))  # Will print 0.0.0.1
    """
    hex_base = 16
    ipv4_address_hex_max_len = 8
    if ipv4_address_hex.startswith('0x'):
        ipv4_address_hex = ipv4_address_hex[2:]  # Remove '0x' prefix

    if len(ipv4_address_hex) > ipv4_address_hex_max_len:
        raise ValueError("The input ipv4 address hex value is not correct, the length should not be more than 8")

    return str(ipaddress.IPv4Address(int(ipv4_address_hex.zfill(ipv4_address_hex_max_len), hex_base)))


def get_port_configs(engine):
    config_db = SonicGeneralCli().get_config_db(engine)
    port_configs = config_db.get('PORT')
    return port_configs


def get_p4nspect_query_json(engine, docker_name=P4ExamplesConsts.APP_NAME, feature_name="", table_name="", controlblock_name=""):
    """
    get the output of the p4nspect query
    :param engine: ssh engine object
    :param docker_name: the docker name in which the p4nspect will be executed
    :param feature_name: feature name in the docker
    :param table_name: table name
    :param controlblock_name: controlblock name
    :return: the output of p4nspect query command in json format,
            Examples: the list count depends on the table count, if table name is specified, then only one element in
            the list. inside each element, 1st element is table name info, 2nd element is default entry info, from 3rd,
            they are user added entries info
            [
                [
                    {
                        "TABLE": "control_in_port.table_overlay_router"
                    },
                    {
                        "IDX": 0,
                        "PRIO": "LOWEST",
                        "A": "A",
                        "KEYS (Key | Value | Mask | Type)": [],
                        "ACTION": {
                            "name": "NoAction",
                            "params": {}
                        },
                        "COUNTERS (Name | Type | Items | Value)": [
                            {
                                "Name": "p4nspect_debug_counter[0]",
                                "Type": "DEBUG",
                                "Items": "Pkts/Bts",
                                "Value": [
                                    32,
                                    7864
                                ]
                            }
                        ]
                    },
                    {
                        "IDX": 1,
                        "PRIO": "2",
                        "A": "A",
                        "KEYS (Key | Value | Mask | Type)": [
                            {
                                "Key": "headers.ipv4.dst_addr",
                                "Value": "192.168.1.3",
                                "Mask": "",
                                "Type": "exact"
                            }
                        ],
                        "ACTION": {
                            "name": "tunnel_encap",
                            "params": {
                                "underlay_dip": "0x2020202",
                                "vni": "0x6"
                            }
                        },
                        "COUNTERS (Name | Type | Items | Value)": [
                            {
                                "Name": "p4nspect_debug_counter[1]",
                                "Type": "DEBUG",
                                "Items": "Pkts/Bts",
                                "Value": [
                                    0,
                                    0
                                ]
                            }
                        ]
                    },
                    {
                        "IDX": 2,
                        "PRIO": "2",
                        "A": "A",
                        "KEYS (Key | Value | Mask | Type)": [
                            {
                                "Key": "headers.ipv4.dst_addr",
                                "Value": "193.168.1.4",
                                "Mask": "",
                                "Type": "exact"
                            }
                        ],
                        "ACTION": {
                            "name": "tunnel_encap",
                            "params": {
                                "underlay_dip": "0x3030303",
                                "vni": "0x8"
                            }
                        },
                        "COUNTERS (Name | Type | Items | Value)": [
                            {
                                "Name": "p4nspect_debug_counter[2]",
                                "Type": "DEBUG",
                                "Items": "Pkts/Bts",
                                "Value": [
                                    0,
                                    0
                                ]
                            }
                        ]
                    }
                ]
            ]
    """
    p4nspect_cmd = "p4nspect --json query "
    cmd = get_p4nspect_full_cmd(docker_name, feature_name, p4nspect_cmd, table_name, controlblock_name)
    output = engine.run_cmd(cmd)
    return json.loads(output)


def get_p4nspect_query_json_parsed(engine, docker_name=P4ExamplesConsts.APP_NAME, feature_name="", table_name="", controlblock_name=""):
    """
    get the output of the p4nspect query
    :param engine: ssh engine object
    :param docker_name: the docker name in which the p4nspect will be executed
    :param feature_name: feature name in the docker
    :param table_name: table name
    :param controlblock_name:controlblock name
    :return: Dictionary of entries get from the sdk Examples:
                                                    if table_name is given:{"192.168.1.3": {"action": "tunnel_encap",
                                                                               "underlay_dip": "2.2.2.2",
                                                                                "vni": "6"}}
                                                    if table_name is not given:
                                                    {
                                                        "control_in_port.table_overlay_router":
                                                            {"192.168.1.3": {"action": "tunnel_encap",
                                                                                   "underlay_dip": "2.2.2.2",
                                                                                    "vni": "6"}
                                                            }
                                                    }
    """
    ret = {}
    tables_content = get_p4nspect_query_json(engine, docker_name=docker_name, feature_name=feature_name,
                                             table_name=table_name)
    for table_content in tables_content:
        controlblock, table, entry_dict = parse_entry_in_one_table(engine, table_content)
        if table == table_name:
            return entry_dict
        ret[".".join([controlblock, table])] = entry_dict
    return ret


def parse_entry_in_one_table(engine, table_content):
    """
    parse the one table content in the output of the p4nspect --json query
    :param engine: ssh engine object
    :param table_content: table content in the output of the p4nspect --json query
    :return: Dictionary of entries for the table Examples: {"192.168.1.3": {"action": "tunnel_encap",
                                                                               "underlay_dip": "2.2.2.2",
                                                                                "vni": "6"}}
    """
    table_name_index = 0
    default_entry_index = 1
    entry_dict = {}
    port_configs = get_port_configs(engine)
    for i, entry in enumerate(table_content):
        if i == table_name_index:
            full_table_name = table_content[table_name_index]["TABLE"]
            controlblock_name = full_table_name.split(".")[0]
            table_name = full_table_name.split(".")[1]
            continue
        if i == default_entry_index:
            continue
        key = entry["KEYS (Key | Value | Mask | Type)"][0]["Value"]
        values = {}
        action_name = entry["ACTION"]['name']
        values['action'] = action_name
        action_param = entry["ACTION"]['params']
        for param_key, param_value in action_param.items():
            values[param_key] = format_value_with_name(param_key, param_value, port_configs)
        values['priority'] = entry["PRIO"]
        for counter in entry["COUNTERS (Name | Type | Items | Value)"]:
            counter_value = counter["Value"]
            values['byte_count'] = counter_value[1]
            values['packet_count'] = counter_value[0]
        entry_dict[key] = values
    return controlblock_name, table_name, entry_dict


def attach_counters(engine, docker_name=P4ExamplesConsts.APP_NAME, feature_name="", table_name="", controlblock_name=""):
    """
    Attach counter for a table
    :param engine: ssh engine object
    :param docker_name: the docker name in which the p4nspect will be executed
    :param feature_name: the p4 examples feature name
    :param table_name: the table name
    :param controlblock_name:
    """
    p4nspect_cmd = "p4nspect debug-counters attach"
    cmd = get_p4nspect_full_cmd(docker_name, feature_name, p4nspect_cmd, table_name, controlblock_name)
    return engine.run_cmd(cmd)


def detach_counters(engine, docker_name=P4ExamplesConsts.APP_NAME, feature_name="", table_name="", controlblock_name=""):
    """
    Detach the counters for the specified table
    :param engine: ssh engine object
    :param docker_name: the docker name in which the p4nspect will be executed
    :param feature_name: the p4 examples feature name
    :param table_name: the table name
    :param controlblock_name:
    """
    p4nspect_cmd = "p4nspect debug-counters detach"
    cmd = get_p4nspect_full_cmd(docker_name, feature_name, p4nspect_cmd, table_name, controlblock_name)
    return engine.run_cmd(cmd)


def clear_counters(engine, docker_name=P4ExamplesConsts.APP_NAME, feature_name="", table_name="", controlblock_name=""):
    """
    Clear counters for the specified counter
    :param engine: ssh engine object
    :param docker_name: the docker name in which the p4nspect will be executed
    :param feature_name: the p4 examples feature name
    :param table_name: the table name
    """
    p4nspect_cmd = "p4nspect debug-counters reset"
    cmd = get_p4nspect_full_cmd(docker_name, feature_name, p4nspect_cmd, table_name, controlblock_name)
    return engine.run_cmd(cmd)


def get_p4nspect_full_cmd(docker_name, feature_name, p4nspect_cmd, table_name="", controlblock_name=""):
    """
    Get the full p4nspect cmd
    :param docker_name: the docker name in which the p4nspect will be executed
    :param feature_name: the p4 examples feature name
    :param p4nspect_cmd: the basic p4nspect command
    :param table_name: the table name
    :param controlblock_name: control block names
    :return: the command string
    """
    try:
        json_file = FEATURE_P4C_JSON_MAP[feature_name]
    except KeyError:
        logging.error(f"feature name {feature_name} is not supported")
        raise KeyError(f"feature name {feature_name} is not supported")
    docker_env_p4c_config = f"P4NSPECT_P4C_CONFIG=/devtools/{json_file}"
    if table_name:
        p4nspect_cmd = "{} --tables {}".format(p4nspect_cmd, table_name)
    if controlblock_name:
        p4nspect_cmd = "{} --controlblocks {}".format(p4nspect_cmd, controlblock_name)
    return "docker exec -e {} {} {}".format(docker_env_p4c_config, docker_name, p4nspect_cmd)
