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
     ┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼
     │                                        TABLE: control_in_port.table_flow_sampling                                       │
     ┼─────┼────────────────────────────────────────────────────────────────┼──────────┼──────────────────────┼────────────────┼
     │ IDX │                KEYS (Key | Value | Mask | Type)                │  ACTION  │       COUNTERS       │ DEBUG-COUNTERS │
     ┼─────┼────────────────────────────────────────────────────────────────┼──────────┼──────────────────────┼────────────────┼
     │  0  │    headers.ip.ipv4.src_addr     100.100.100.8   None   exact   │ DoMirror │ Bytes: 0, Packets: 0 │                │
     │     │    headers.ip.ipv4.dst_addr    100.100.100.100  None   exact   │          │                      │                │
     │     │    headers.ip.ipv4.protocol          0x11       None   exact   │          │                      │                │
     │     │      headers.tcp.src_port            0x7b       None   exact   │          │                      │                │
     │     │      headers.tcp.dst_port           0x1c8       None   exact   │          │                      │                │
     │     │  headers.ip.ipv4.hdr_checksum        0x43       0x21  ternary  │          │                      │                │
     ┼─────┼────────────────────────────────────────────────────────────────┼──────────┼──────────────────────┼────────────────┼
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
    entry_spliter = lines[2]
    content_column_spliter = '│'
    entry_spliter_indexs = get_entry_spliter_indexs(lines, entry_spliter)
    entry_spliter_count = len(entry_spliter_indexs)
    ret = {}
    port_configs = get_port_configs(engine)
    for i in range(1, entry_spliter_count - 1):
        entry_start_index = entry_spliter_indexs[i]
        entry_end_index = entry_spliter_indexs[i + 1]
        parse_entry_content(engine, lines[entry_start_index + 1:entry_end_index], content_column_spliter, ret, port_configs)
    return ret


def get_entry_spliter_indexs(lines, spliter):
    """
    get all the entry spliter indices, the real content of the entry content start from the second spliter
    :param lines: the lines of output content of p4nspect
    :param spliter: the entry spliter
    :return: list of entry spliter index.
    """
    indices = []
    for i in range(len(lines)):
        if lines[i] == spliter:
            indices.append(i)
    return indices


def parse_entry_content(engine, lines, content_column_spliter, ret, port_configs):
    """
    get the entry content, and add the content into the dictionary
    :param engine: ssh engine object
    :param lines: the content of one entry shown in the p4nspect
    :param content_column_spliter: column spliter
    :param ret: the dictionary
    :return: None
    """
    key_list = []
    for i in range(len(lines)):
        line = lines[i].strip(' ' + content_column_spliter)
        if i == 0:
            line_content = line.split(content_column_spliter)
            action = line_content[2].strip()
            bytes_packets = line_content[3].strip().split(',')
            bytes = bytes_packets[0].split(':')[1].strip()
            packets = bytes_packets[1].split(':')[1].strip()
            debug_counters = line_content[-1].strip()
            key_list.append(get_key_value(engine, line_content[1], port_configs))
        else:
            key_list.append(get_key_value(engine, line, port_configs))
    keys = " ".join(key_list)
    values = DottedDict()
    values.action = action
    values.bytes = bytes
    values.packets = packets
    values.debug_counters = debug_counters
    ret[keys] = values


def get_key_value(engine, key_line_content, port_configs):
    """
    get key value
    :param engine: ssh engine object
    :param key_line_content: the key value in 1 line content
    :return: the key value
    """
    key_content = key_line_content.split()
    if key_content[-1] == "exact":
        return convert_key_value(engine, key_content[0], key_content[1], port_configs)
    elif key_content[-1] == "ternary":
        return "/".join([convert_key_value(engine, key_content[0], key_content[1], port_configs),
                         convert_key_value(engine, key_content[0], key_content[2], port_configs)])


def convert_key_value(engine, key_name, key_value, port_configs):
    """
    convert key value, for the ingress, the value should be converted from lable port to physical port, and some key
    value should be converted from hex to int
    :param engine: ssh engine object
    :param key_name: the full key name in the p4nspect
    :param key_value: the key value
    :return: the converted key value
    """
    key_name = key_name.split(".")[-1]
    if key_name == 'ingress_port':
        return convert_label_port_to_physical(engine, key_value, port_configs)
    if key_name == 'hdr_checksum':
        return "{:#06x}".format(int(key_value, 16))
    elif key_name == 'protocol' or key_name == 'src_port' or key_name == 'dst_port':
        return "{}".format(int(key_value, 16))
    return key_value


def convert_label_port_to_physical(engine, label_port, port_configs):
    """
    convert label_port port to physical port
    :param engine: ssh engine object
    :param label_port: lable port value
    :return: physical port
    """
    for port in port_configs.keys():
        port_config = port_configs.get(port)
        if port_config.get('index') == label_port:
            return port
    return label_port


def get_port_configs(engine):
    config_db = SonicGeneralCli.get_config_db(engine)
    port_configs = config_db.get('PORT')
    return port_configs
