from dotted_dict import DottedDict
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


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
    hex_key_list = ['vlan', 'is_trunc', 'trunc_size']
    port_key_list = ['ingress_port', 'label_port']
    if name in port_key_list:
        return convert_label_port_to_physical(value, port_configs)
    if name == 'hdr_checksum':
        return "{:#06x}".format(int(value, 16))
    elif name == 'protocol':
        return convert_protocol_value(value)
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


def convert_protocol_value(protocol):
    if protocol == "TCP":
        return '6'
    return protocol


def get_port_configs(engine):
    config_db = SonicGeneralCli.get_config_db(engine)
    port_configs = config_db.get('PORT')
    return port_configs
