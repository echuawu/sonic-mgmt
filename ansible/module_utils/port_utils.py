def _port_alias_to_name_map_50G(all_ports, s100G_ports,):
    new_map = {}
    # 50G ports
    s50G_ports = list(set(all_ports) - set(s100G_ports))

    for i in s50G_ports:
        new_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
        new_map["Ethernet%d/3" % i] = "Ethernet%d" % ((i - 1) * 4 + 2)

    for i in s100G_ports:
        new_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)

    return new_map

def get_port_alias_to_name_map(hostname, hwsku, asic_id=None):
    try:
        from sonic_py_common import multi_asic
        from ansible.module_utils.multi_asic_utils  import load_db_config
        load_db_config()
        namespace_list = multi_asic.get_all_namespaces()
        for key, list in namespace_list.items():
            asic_ids = []
            for ns in list:
                asic_ids.append(multi_asic.get_asic_id_from_name(ns))
            namespace_list[key] = asic_ids
    except ImportError:
        namespace_list = ['']
    port_alias_to_name_map = {}
    port_alias_asic_map = {}
    if hwsku == "Force10-S6000":
        for i in range(0, 128, 4):
            port_alias_to_name_map["fortyGigE0/%d" % i] = "Ethernet%d" % i
    elif hwsku == "Force10-S6100":
        for i in range(0, 4):
            for j in range(0, 16):
                port_alias_to_name_map["fortyGigE1/%d/%d" % (i + 1, j + 1)] = "Ethernet%d" % (i * 16 + j)
    elif hwsku == "Force10-Z9100":
        for i in range(0, 128, 4):
            port_alias_to_name_map["hundredGigE1/%d" % (i / 4 + 1)] = "Ethernet%d" % i
    # TODO: Come up with a generic formula for generating etp style aliases based on number of ports and lanes
    elif hwsku == "DellEMC-Z9332f-M-O16C64":
        # 100G ports
        s100G_ports = [x for x in range(0, 96, 2)] + [x for x in range(128, 160, 2)]

        # 400G ports
        s400G_ports = [x for x in range(96, 128, 8)] + [x for x in range(160, 256, 8)]

        # 10G ports
        s10G_ports = [x for x in range(256, 258)]

        for i in s100G_ports:
            alias = "etp{}{}".format(((i + 8) // 8), chr(ord('a') + (i // 2) % 4))
            port_alias_to_name_map[alias] = "Ethernet{}".format(i)
        for i in s400G_ports:
            alias = "etp{}".format((i // 8) + 1)
            port_alias_to_name_map[alias] = "Ethernet{}".format(i)
        for i in s10G_ports:
            alias = "etp{}".format(33 if i == 256 else 34)
            port_alias_to_name_map[alias] = "Ethernet{}".format(i)
    elif hwsku == "DellEMC-Z9332f-O32":
        for i in range(0, 256, 8):
            alias = "etp{}".format((i // 8) + 1)
            port_alias_to_name_map[alias] = "Ethernet{}".format(i)
        for i in range(256, 258):
            alias = "etp{}".format(33 if i == 256 else 34)
            port_alias_to_name_map[alias] = "Ethernet{}".format(i)
    elif hwsku == "Arista-7050-QX32":
        for i in range(1, 25):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
        for i in range(25, 33):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Arista-7050-QX-32S":
        for i in range(0, 4):
            port_alias_to_name_map["Ethernet1/%d" % (i + 1)] = "Ethernet%d" % i
        for i in range(6, 29):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 5) * 4)
        for i in range(29, 37):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % ((i - 5) * 4)
    elif hwsku == "Arista-7280CR3-C40":
        for i in range(1, 33):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
        for i in range(33, 41, 2):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
            port_alias_to_name_map["Ethernet%d/5" % i] = "Ethernet%d" % (i * 4)
    elif hwsku == "Arista-7260CX3-C64" or hwsku == "Arista-7170-64C":
        for i in range(1, 65):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Arista-7060CX-32S-C32" or hwsku == "Arista-7060CX-32S-Q32" or hwsku == "Arista-7060CX-32S-C32-T1" or hwsku == "Arista-7170-32CD-C32" \
        or hwsku == "Arista-7050CX3-32S-C32":
        for i in range(1, 33):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Mellanox-SN2700-D40C8S8":
        # 10G ports
        s10G_ports = range(0, 4) + range(8, 12)

        # 50G ports
        s50G_ports = [x for x in range(16, 24, 2)] + [x for x in range(40, 88, 2)] + [x for x in range(104, 128, 2)]

        # 100G ports
        s100G_ports = [x for x in range(24, 40, 4)] + [x for x in range(88, 104, 4)]

        for i in s10G_ports:
            alias = "etp%d" % (i / 4 + 1) + chr(ord('a') + i % 4)
            port_alias_to_name_map[alias] = "Ethernet%d" % i
        for i in s50G_ports:
            alias = "etp%d" % (i / 4 + 1) + ("a" if i % 4 == 0 else "b")
            port_alias_to_name_map[alias] = "Ethernet%d" % i
        for i in s100G_ports:
            alias = "etp%d" % (i / 4 + 1)
            port_alias_to_name_map[alias] = "Ethernet%d" % i
    elif hwsku == "Mellanox-SN2700-D48C8":
        # 50G ports
        s50G_ports = [x for x in range(0, 24, 2)] + [x for x in range(40, 88, 2)] + [x for x in range(104, 128, 2)]

        # 100G ports
        s100G_ports = [x for x in range(24, 40, 4)] + [x for x in range(88, 104, 4)]

        for i in s50G_ports:
            alias = "etp%d" % (i / 4 + 1) + ("a" if i % 4 == 0 else "b")
            port_alias_to_name_map[alias] = "Ethernet%d" % i
        for i in s100G_ports:
            alias = "etp%d" % (i / 4 + 1)
            port_alias_to_name_map[alias] = "Ethernet%d" % i
    elif (hwsku == "Mellanox-SN2700" or hwsku == "ACS-MSN2700") or \
         (hwsku == "ACS-MSN3700") or (hwsku == "ACS-MSN3700C") or \
         (hwsku == "ACS-MSN3800") or (hwsku == "Mellanox-SN3800-D112C8") or \
         (hwsku == "ACS-MSN4700") or (hwsku == "ACS-MSN4600C") or (hwsku == "Mellanox-SN4600C-D112C8") or (hwsku == "Mellanox-SN4600C-C64") or \
         (hwsku == "ACS-MSN3420"):
        if hostname == "arc-switch1038":
            for i in range(1, 17):
                port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 4)

            port_alias_to_name_map["etp17a"] = "Ethernet64"
            port_alias_to_name_map["etp17b"] = "Ethernet65"
            port_alias_to_name_map["etp17c"] = "Ethernet66"
            port_alias_to_name_map["etp17d"] = "Ethernet67"
            port_alias_to_name_map["etp21a"] = "Ethernet80"
            port_alias_to_name_map["etp21b"] = "Ethernet82"

            for i in range(23, 33):
                port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 4)
        elif hostname == "r-tigris-04" or hostname == "r-tigris-13":
            port_alias_to_name_map["etp1a"] = "Ethernet0"
            port_alias_to_name_map["etp1b"] = "Ethernet2"
            port_alias_to_name_map["etp2a"] = "Ethernet4"
            port_alias_to_name_map["etp2b"] = "Ethernet6"
            port_alias_to_name_map["etp3a"] = "Ethernet8"
            port_alias_to_name_map["etp3b"] = "Ethernet10"
            port_alias_to_name_map["etp4a"] = "Ethernet12"
            port_alias_to_name_map["etp4b"] = "Ethernet14"
            port_alias_to_name_map["etp5a"] = "Ethernet16"
            port_alias_to_name_map["etp5b"] = "Ethernet18"
            port_alias_to_name_map["etp6a"] = "Ethernet20"
            port_alias_to_name_map["etp6b"] = "Ethernet22"
            port_alias_to_name_map["etp7a"] = "Ethernet24"
            port_alias_to_name_map["etp7b"] = "Ethernet26"
            port_alias_to_name_map["etp8a"] = "Ethernet28"
            port_alias_to_name_map["etp8b"] = "Ethernet30"
            port_alias_to_name_map["etp9a"] = "Ethernet32"
            port_alias_to_name_map["etp9b"] = "Ethernet34"
            port_alias_to_name_map["etp10a"] = "Ethernet36"
            port_alias_to_name_map["etp10b"] = "Ethernet38"
            port_alias_to_name_map["etp11a"] = "Ethernet40"
            port_alias_to_name_map["etp11b"] = "Ethernet42"
            port_alias_to_name_map["etp12a"] = "Ethernet44"
            port_alias_to_name_map["etp12b"] = "Ethernet46"
            port_alias_to_name_map["etp13a"] = "Ethernet48"
            port_alias_to_name_map["etp13b"] = "Ethernet50"
            port_alias_to_name_map["etp14a"] = "Ethernet52"
            port_alias_to_name_map["etp14b"] = "Ethernet54"
            port_alias_to_name_map["etp15a"] = "Ethernet56"
            port_alias_to_name_map["etp15b"] = "Ethernet58"
            port_alias_to_name_map["etp16a"] = "Ethernet60"
            port_alias_to_name_map["etp16b"] = "Ethernet62"
            port_alias_to_name_map["etp17a"] = "Ethernet64"
            port_alias_to_name_map["etp17b"] = "Ethernet66"
            port_alias_to_name_map["etp18a"] = "Ethernet68"
            port_alias_to_name_map["etp18b"] = "Ethernet70"
            port_alias_to_name_map["etp19a"] = "Ethernet72"
            port_alias_to_name_map["etp19b"] = "Ethernet74"
            port_alias_to_name_map["etp20a"] = "Ethernet76"
            port_alias_to_name_map["etp20b"] = "Ethernet78"
            port_alias_to_name_map["etp21a"] = "Ethernet80"
            port_alias_to_name_map["etp21b"] = "Ethernet82"
            port_alias_to_name_map["etp22a"] = "Ethernet84"
            port_alias_to_name_map["etp22b"] = "Ethernet86"
            port_alias_to_name_map["etp23a"] = "Ethernet88"
            port_alias_to_name_map["etp23b"] = "Ethernet90"
            port_alias_to_name_map["etp24a"] = "Ethernet92"
            port_alias_to_name_map["etp24b"] = "Ethernet94"
            port_alias_to_name_map["etp25"] = "Ethernet96"
            port_alias_to_name_map["etp26"] = "Ethernet100"
            port_alias_to_name_map["etp27a"] = "Ethernet104"
            port_alias_to_name_map["etp27b"] = "Ethernet106"
            port_alias_to_name_map["etp28a"] = "Ethernet108"
            port_alias_to_name_map["etp28b"] = "Ethernet110"
            port_alias_to_name_map["etp29"] = "Ethernet112"
            port_alias_to_name_map["etp30"] = "Ethernet116"
            port_alias_to_name_map["etp31a"] = "Ethernet120"
            port_alias_to_name_map["etp31b"] = "Ethernet122"
            port_alias_to_name_map["etp32a"] = "Ethernet124"
            port_alias_to_name_map["etp32b"] = "Ethernet126"
            port_alias_to_name_map["etp33"] = "Ethernet128"
            port_alias_to_name_map["etp34"] = "Ethernet132"
            port_alias_to_name_map["etp35a"] = "Ethernet136"
            port_alias_to_name_map["etp35b"] = "Ethernet138"
            port_alias_to_name_map["etp36a"] = "Ethernet140"
            port_alias_to_name_map["etp36b"] = "Ethernet142"
            port_alias_to_name_map["etp37"] = "Ethernet144"
            port_alias_to_name_map["etp38"] = "Ethernet148"
            port_alias_to_name_map["etp39a"] = "Ethernet152"
            port_alias_to_name_map["etp39b"] = "Ethernet154"
            port_alias_to_name_map["etp40a"] = "Ethernet156"
            port_alias_to_name_map["etp40b"] = "Ethernet158"
            port_alias_to_name_map["etp41a"] = "Ethernet160"
            port_alias_to_name_map["etp41b"] = "Ethernet162"
            port_alias_to_name_map["etp42a"] = "Ethernet164"
            port_alias_to_name_map["etp42b"] = "Ethernet166"
            port_alias_to_name_map["etp43a"] = "Ethernet168"
            port_alias_to_name_map["etp43b"] = "Ethernet170"
            port_alias_to_name_map["etp44a"] = "Ethernet172"
            port_alias_to_name_map["etp44b"] = "Ethernet174"
            port_alias_to_name_map["etp45a"] = "Ethernet176"
            port_alias_to_name_map["etp45b"] = "Ethernet178"
            port_alias_to_name_map["etp46a"] = "Ethernet180"
            port_alias_to_name_map["etp46b"] = "Ethernet182"
            port_alias_to_name_map["etp47a"] = "Ethernet184"
            port_alias_to_name_map["etp47b"] = "Ethernet186"
            port_alias_to_name_map["etp48a"] = "Ethernet188"
            port_alias_to_name_map["etp48b"] = "Ethernet190"
            port_alias_to_name_map["etp49a"] = "Ethernet192"
            port_alias_to_name_map["etp49b"] = "Ethernet194"
            port_alias_to_name_map["etp50a"] = "Ethernet196"
            port_alias_to_name_map["etp50b"] = "Ethernet198"
            port_alias_to_name_map["etp51a"] = "Ethernet200"
            port_alias_to_name_map["etp51b"] = "Ethernet202"
            port_alias_to_name_map["etp52a"] = "Ethernet204"
            port_alias_to_name_map["etp52b"] = "Ethernet206"
            port_alias_to_name_map["etp53a"] = "Ethernet208"
            port_alias_to_name_map["etp53b"] = "Ethernet210"
            port_alias_to_name_map["etp54a"] = "Ethernet212"
            port_alias_to_name_map["etp54b"] = "Ethernet214"
            port_alias_to_name_map["etp55a"] = "Ethernet216"
            port_alias_to_name_map["etp55b"] = "Ethernet218"
            port_alias_to_name_map["etp56a"] = "Ethernet220"
            port_alias_to_name_map["etp56b"] = "Ethernet222"
            port_alias_to_name_map["etp57a"] = "Ethernet224"
            port_alias_to_name_map["etp57b"] = "Ethernet226"
            port_alias_to_name_map["etp58a"] = "Ethernet228"
            port_alias_to_name_map["etp58b"] = "Ethernet230"
            port_alias_to_name_map["etp59a"] = "Ethernet232"
            port_alias_to_name_map["etp59b"] = "Ethernet234"
            port_alias_to_name_map["etp60a"] = "Ethernet236"
            port_alias_to_name_map["etp60b"] = "Ethernet238"
            port_alias_to_name_map["etp61a"] = "Ethernet240"
            port_alias_to_name_map["etp61b"] = "Ethernet242"
            port_alias_to_name_map["etp62a"] = "Ethernet244"
            port_alias_to_name_map["etp62b"] = "Ethernet246"
            port_alias_to_name_map["etp63a"] = "Ethernet248"
            port_alias_to_name_map["etp63b"] = "Ethernet250"
            port_alias_to_name_map["etp64a"] = "Ethernet252"
            port_alias_to_name_map["etp64b"] = "Ethernet254"
        elif hostname == "r-tigon-04":
            port_alias_to_name_map["etp1a"] = "Ethernet0"
            port_alias_to_name_map["etp1b"] = "Ethernet2"
            port_alias_to_name_map["etp2a"] = "Ethernet4"
            port_alias_to_name_map["etp2b"] = "Ethernet6"
            port_alias_to_name_map["etp3a"] = "Ethernet8"
            port_alias_to_name_map["etp3b"] = "Ethernet10"
            port_alias_to_name_map["etp4a"] = "Ethernet12"
            port_alias_to_name_map["etp4b"] = "Ethernet14"
            port_alias_to_name_map["etp5a"] = "Ethernet16"
            port_alias_to_name_map["etp5b"] = "Ethernet18"
            port_alias_to_name_map["etp6a"] = "Ethernet20"
            port_alias_to_name_map["etp6b"] = "Ethernet22"
            port_alias_to_name_map["etp7a"] = "Ethernet24"
            port_alias_to_name_map["etp7b"] = "Ethernet26"
            port_alias_to_name_map["etp8a"] = "Ethernet28"
            port_alias_to_name_map["etp8b"] = "Ethernet30"
            port_alias_to_name_map["etp9a"] = "Ethernet32"
            port_alias_to_name_map["etp9b"] = "Ethernet34"
            port_alias_to_name_map["etp10a"] = "Ethernet36"
            port_alias_to_name_map["etp10b"] = "Ethernet38"
            port_alias_to_name_map["etp11a"] = "Ethernet40"
            port_alias_to_name_map["etp11b"] = "Ethernet42"
            port_alias_to_name_map["etp12a"] = "Ethernet44"
            port_alias_to_name_map["etp12b"] = "Ethernet46"
            port_alias_to_name_map["etp13a"] = "Ethernet48"
            port_alias_to_name_map["etp13b"] = "Ethernet50"
            port_alias_to_name_map["etp14a"] = "Ethernet52"
            port_alias_to_name_map["etp14b"] = "Ethernet54"
            port_alias_to_name_map["etp15a"] = "Ethernet56"
            port_alias_to_name_map["etp15b"] = "Ethernet58"
            port_alias_to_name_map["etp16a"] = "Ethernet60"
            port_alias_to_name_map["etp16b"] = "Ethernet62"
            port_alias_to_name_map["etp17a"] = "Ethernet64"
            port_alias_to_name_map["etp17b"] = "Ethernet66"
            port_alias_to_name_map["etp18a"] = "Ethernet68"
            port_alias_to_name_map["etp18b"] = "Ethernet70"
            port_alias_to_name_map["etp19a"] = "Ethernet72"
            port_alias_to_name_map["etp19b"] = "Ethernet74"
            port_alias_to_name_map["etp20a"] = "Ethernet76"
            port_alias_to_name_map["etp20b"] = "Ethernet78"
            port_alias_to_name_map["etp21a"] = "Ethernet80"
            port_alias_to_name_map["etp21b"] = "Ethernet82"
            port_alias_to_name_map["etp22a"] = "Ethernet84"
            port_alias_to_name_map["etp22b"] = "Ethernet86"
            port_alias_to_name_map["etp23a"] = "Ethernet88"
            port_alias_to_name_map["etp23b"] = "Ethernet90"
            port_alias_to_name_map["etp24a"] = "Ethernet92"
            port_alias_to_name_map["etp24b"] = "Ethernet94"
            port_alias_to_name_map["etp25"] = "Ethernet96"
            port_alias_to_name_map["etp26"] = "Ethernet100"
            port_alias_to_name_map["etp27a"] = "Ethernet104"
            port_alias_to_name_map["etp27b"] = "Ethernet106"
            port_alias_to_name_map["etp28a"] = "Ethernet108"
            port_alias_to_name_map["etp28b"] = "Ethernet110"
            port_alias_to_name_map["etp29"] = "Ethernet112"
            port_alias_to_name_map["etp30"] = "Ethernet116"
            port_alias_to_name_map["etp31a"] = "Ethernet120"
            port_alias_to_name_map["etp31b"] = "Ethernet122"
            port_alias_to_name_map["etp32a"] = "Ethernet124"
            port_alias_to_name_map["etp32b"] = "Ethernet126"
            port_alias_to_name_map["etp33"] = "Ethernet128"
            port_alias_to_name_map["etp34"] = "Ethernet132"
            port_alias_to_name_map["etp35a"] = "Ethernet136"
            port_alias_to_name_map["etp35b"] = "Ethernet138"
            port_alias_to_name_map["etp36a"] = "Ethernet140"
            port_alias_to_name_map["etp36b"] = "Ethernet142"
            port_alias_to_name_map["etp37"] = "Ethernet144"
            port_alias_to_name_map["etp38"] = "Ethernet148"
            port_alias_to_name_map["etp39a"] = "Ethernet152"
            port_alias_to_name_map["etp39b"] = "Ethernet154"
            port_alias_to_name_map["etp40a"] = "Ethernet156"
            port_alias_to_name_map["etp40b"] = "Ethernet158"
            port_alias_to_name_map["etp41a"] = "Ethernet160"
            port_alias_to_name_map["etp41b"] = "Ethernet162"
            port_alias_to_name_map["etp42a"] = "Ethernet164"
            port_alias_to_name_map["etp42b"] = "Ethernet166"
            port_alias_to_name_map["etp43a"] = "Ethernet168"
            port_alias_to_name_map["etp43b"] = "Ethernet170"
            port_alias_to_name_map["etp44a"] = "Ethernet172"
            port_alias_to_name_map["etp44b"] = "Ethernet174"
            port_alias_to_name_map["etp45a"] = "Ethernet176"
            port_alias_to_name_map["etp45b"] = "Ethernet178"
            port_alias_to_name_map["etp46a"] = "Ethernet180"
            port_alias_to_name_map["etp46b"] = "Ethernet182"
            port_alias_to_name_map["etp47a"] = "Ethernet184"
            port_alias_to_name_map["etp47b"] = "Ethernet186"
            port_alias_to_name_map["etp48a"] = "Ethernet188"
            port_alias_to_name_map["etp48b"] = "Ethernet190"
            port_alias_to_name_map["etp49a"] = "Ethernet192"
            port_alias_to_name_map["etp49b"] = "Ethernet194"
            port_alias_to_name_map["etp50a"] = "Ethernet196"
            port_alias_to_name_map["etp50b"] = "Ethernet198"
            port_alias_to_name_map["etp51a"] = "Ethernet200"
            port_alias_to_name_map["etp51b"] = "Ethernet202"
            port_alias_to_name_map["etp52a"] = "Ethernet204"
            port_alias_to_name_map["etp52b"] = "Ethernet206"
            port_alias_to_name_map["etp53a"] = "Ethernet208"
            port_alias_to_name_map["etp53b"] = "Ethernet210"
            port_alias_to_name_map["etp54a"] = "Ethernet212"
            port_alias_to_name_map["etp54b"] = "Ethernet214"
            port_alias_to_name_map["etp55a"] = "Ethernet216"
            port_alias_to_name_map["etp55b"] = "Ethernet218"
            port_alias_to_name_map["etp56a"] = "Ethernet220"
            port_alias_to_name_map["etp56b"] = "Ethernet222"
            port_alias_to_name_map["etp57a"] = "Ethernet224"
            port_alias_to_name_map["etp57b"] = "Ethernet226"
            port_alias_to_name_map["etp58a"] = "Ethernet228"
            port_alias_to_name_map["etp58b"] = "Ethernet230"
            port_alias_to_name_map["etp59a"] = "Ethernet232"
            port_alias_to_name_map["etp59b"] = "Ethernet234"
            port_alias_to_name_map["etp60a"] = "Ethernet236"
            port_alias_to_name_map["etp60b"] = "Ethernet238"
            port_alias_to_name_map["etp61a"] = "Ethernet240"
            port_alias_to_name_map["etp61b"] = "Ethernet242"
            port_alias_to_name_map["etp62a"] = "Ethernet244"
            port_alias_to_name_map["etp62b"] = "Ethernet246"
            port_alias_to_name_map["etp63a"] = "Ethernet248"
            port_alias_to_name_map["etp63b"] = "Ethernet250"
            port_alias_to_name_map["etp64a"] = "Ethernet252"
            port_alias_to_name_map["etp64b"] = "Ethernet254"
        elif hostname in ["r-tigon-11", "r-tigon-20"]:
            for i in range(1, 65):
                port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 4)
        elif hostname in ["r-leopard-01" , "r-leopard-58"]:
            for i in range(1, 33):
                port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 8)
        else:
            for i in range(1, 33):
                port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Arista-7060CX-32S-D48C8":
        # All possible breakout 50G port numbers:
        all_ports = [x for x in range(1, 33)]

        # 100G ports
        s100G_ports = [x for x in range(7, 11)]
        s100G_ports += [x for x in range(23, 27)]

        port_alias_to_name_map = _port_alias_to_name_map_50G(all_ports, s100G_ports)
    elif hwsku == "Arista-7260CX3-D108C8":
        # All possible breakout 50G port numbers:
        all_ports = [x for x in range(1, 65)]

        # 100G ports
        s100G_ports = [x for x in range(13, 21)]

        port_alias_to_name_map = _port_alias_to_name_map_50G(all_ports, s100G_ports)
    elif hwsku == "INGRASYS-S9100-C32":
        for i in range(1, 33):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "INGRASYS-S9100-C32" or hwsku == "INGRASYS-S9130-32X" or hwsku == "INGRASYS-S8810-32Q":
        for i in range(1, 33):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "INGRASYS-S8900-54XC":
        for i in range(1, 49):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % (i - 1)
        for i in range(49, 55):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 49) * 4 + 48)
    elif hwsku == "INGRASYS-S8900-64XC":
        for i in range(1, 49):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % (i - 1)
        for i in range(49, 65):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 49) * 4 + 48)
    elif hwsku == "Accton-AS7712-32X":
        for i in range(1, 33):
            port_alias_to_name_map["hundredGigE%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Celestica-DX010-C32":
        for i in range(1, 33):
            port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Seastone-DX010":
        for i in range(1, 33):
            port_alias_to_name_map["Eth%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku in ["Celestica-E1031-T48S4", "Nokia-7215", "Nokia-M0-7215"]:
        for i in range(1, 53):
            port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1))
    elif hwsku == "et6448m":
        for i in range(0, 52):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % i
    elif hwsku == "Nokia-IXR7250E-36x400G":
        if asic_id is not None:
            asic_offset = int(asic_id) * 18
            for i in range(0, 18):
                port_alias_to_name_map["Ethernet%d" % (asic_offset + i)] = "Ethernet%d" % ((asic_offset + i))
                port_alias_asic_map["Eth%d-ASIC%d" % (i, int(asic_id))] = "Ethernet%d" % ((asic_offset + i))
        else:
            for i in range(0, 36):
                port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % i
    elif hwsku == 'Nokia-IXR7250E-SUP-10':
        port_alias_to_name_map = {}
    elif hwsku == "newport":
        for i in range(0, 256, 8):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % i
    elif hwsku == "32x100Gb":
        for i in range(0, 32):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % i
    elif hwsku == "36x100Gb":
        for i in range(0, 36):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % i
    elif hwsku == "64x100Gb":
        for i in range(0, 64):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % i
    elif hwsku == "8800-LC-48H-O":
        for j in range(0,8):
            for i in range(0, 13):
                port_alias_to_name_map["Eth%d/0/%d" % (j,i)] = "Ethernet%d" % i
            for i in range(13,47,3):
                if i > 15:
                    port_alias_to_name_map["Eth%d/0/%d" % (j,i-1)] = "Ethernet%d" % (i-1)
                for i in range(i,i+2):
                    port_alias_to_name_map["Eth%d/1/%d" % (j,i)] = "Ethernet%d" % i
        for i in range(0, 13):
            port_alias_asic_map["Eth%d-ASIC0" % i] = "Ethernet%d" % i
        for i in range(13,47,3):
            if i > 15:
                port_alias_asic_map["Eth%d-ASIC0" % (i-1)] = "Ethernet%d" % (i-1)
            for i in range(i,i+2):
                port_alias_asic_map["Eth%d-ASIC1" % i] = "Ethernet%d" % i
        port_alias_to_name_map["Eth2064-ASIC0"] = "Ethernet-BP2064"
        for i in range(2154,2264,2):
            port_alias_to_name_map["Eth%d-ASIC0" % i] = "Ethernet-BP%d" % i
        port_alias_to_name_map["Eth2320-ASIC1"] = "Ethernet-BP2320"
        for i in range(2410,2520,2):
            port_alias_to_name_map["Eth%d-ASIC1" % i] = "Ethernet-BP%d" % i
    elif hwsku == "msft_multi_asic_vs":
        if asic_id is not None and asic_id in namespace_list['front_ns']:
            asic_offset = int(asic_id) * 16
            backplane_offset = 15
            for i in range(1, 17):
                port_alias_to_name_map["Ethernet1/%d"%(asic_offset+i)] = "Ethernet%d"%((asic_offset + i -1) *4)
                port_alias_asic_map["Eth%d-ASIC%d"%(i-1, int(asic_id))] = "Ethernet%d"%((asic_offset + i -1) *4)
                port_alias_to_name_map["Eth%d-ASIC%d"%((backplane_offset+i), int(asic_id))] = "Ethernet-BP%d"%((asic_offset + i -1) *4)
                port_alias_asic_map["Eth%d-ASIC%d"%((backplane_offset+i), int(asic_id))] = "Ethernet-BP%d"%((asic_offset + i -1) *4)
        elif asic_id is not None  and asic_id in namespace_list['back_ns']:
            asic_offset = 32 * (int(asic_id) - 2)
            for i in range(1, 33):
                port_alias_asic_map["Eth%d-ASIC%d"%(i-1, int(asic_id))] = "Ethernet-BP%d"%((asic_offset + i -1) *4)
                port_alias_to_name_map["Eth%d-ASIC%d"%(i-1, int(asic_id))] = "Ethernet-BP%d"%((asic_offset + i -1) *4)
        else:
            for i in range(1,65):
                port_alias_to_name_map["Ethernet1/%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "msft_four_asic_vs":
        if asic_id is not None and asic_id in namespace_list['front_ns']:
            asic_offset = int(asic_id) * 4
            backplane_offset = 3
            for i in range(1, 5):
                port_alias_to_name_map["Ethernet1/%d"%(asic_offset+i)] = "Ethernet%d"%((asic_offset + i -1) *4)
                port_alias_asic_map["Eth%d-ASIC%d"%(i-1, int(asic_id))] = "Ethernet%d"%((asic_offset + i -1) *4)
                port_alias_to_name_map["Eth%d-ASIC%d"%((backplane_offset+i), int(asic_id))] = "Ethernet-BP%d"%((asic_offset + i -1) *4)
                port_alias_asic_map["Eth%d-ASIC%d"%((backplane_offset+i), int(asic_id))] = "Ethernet-BP%d"%((asic_offset + i -1) *4)
        elif asic_id is not None  and asic_id in namespace_list['back_ns']:
            asic_offset = 8 * (int(asic_id) -1)
            for i in range(1, 9):
                port_alias_asic_map["Eth%d-ASIC%d"%(i-1, int(asic_id))] = "Ethernet-BP%d"%((asic_offset + i -1) *4)
                port_alias_to_name_map["Eth%d-ASIC%d"%(i-1, int(asic_id))] = "Ethernet-BP%d"%((asic_offset + i -1) *4)
        else:
            for i in range(1,9):
                port_alias_to_name_map["Ethernet1/%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "B6510-48VS8CQ" or hwsku == "RA-B6510-48V8C":
        for i in range(1,49):
            port_alias_to_name_map["twentyfiveGigE0/%d" % i] = "Ethernet%d" % i
        for i in range(49,57):
            port_alias_to_name_map["hundredGigE0/%d" % (i-48)] = "Ethernet%d" % i
    elif hwsku == "RA-B6910-64C":
        for i in range(1,65):
            port_alias_to_name_map["hundredGigE%d" % i] = "Ethernet%d" % i
    else:
        for i in range(0, 128, 4):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % i

    return port_alias_to_name_map, port_alias_asic_map


def get_port_indices_for_asic(asic_id, port_name_list_sorted):
    front_end_port_name_list = [p for p in port_name_list_sorted if 'BP' not in p]
    back_end_port_name_list = [p for p in port_name_list_sorted if 'BP' in p]
    index_offset = 0
   # Create mapping between port alias and physical index
    port_index_map = {}
    if asic_id:
        index_offset = int(asic_id) *len(front_end_port_name_list)
    for idx, val in enumerate(front_end_port_name_list, index_offset):
        port_index_map[val] = idx
    for idx, val in enumerate(back_end_port_name_list, index_offset):
        port_index_map[val] = idx

    return port_index_map
