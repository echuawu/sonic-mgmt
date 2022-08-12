"""
Run this script, and will help you to generate all the config used in the mars configuration for 201911, 202012, develop branch
When there is new db added to the regression, need to update this file
How to run: python sonic-tool/mars/generate_mars_orchestration_config_file.py
"""
import os
# Here are the definition for the db files that should be used for every branch, every mars scenario.
# Community dbs in the develop branch

community_develop_set_1_dbs = [
    'pretest.db',
    'routes.db',
    'dhcp.db',
    'pfcwd.db',
    'layer3.db',
    'link.db',
    'wjh.db',
    'fast_reboot.db',
    'warm_reboot.db',
    'span.db'
]

community_develop_rpc_dbs = [
    'pre_rpc.db',
    'rpc_qos.db',
    'rpc_pfc_asym_and_copp.db',
    'post_rpc.db'
]

community_develop_set_2_dbs = [
    'pretest.db',
    'bfd.db',
    'layer2.db',
    'radv.db',
    'acl.db',
    'ecmp.db',
    'ip_neigh.db',
    'resources.db',
    'tunnel.db',
    'counters.db',
    'techsupport.db',
    'interfaces.db',
    'sub_port_interfaces.db',
    'system_health.db',
    'sflow.db',
    'bgp.db',
    'pbh.db',
    'generic_config_updater.db',
    'cold_reboot.db',
    'autorestart.db'
]

community_develop_generic_dbs = [
    'system.db',
    'mgmtvrf.db',
    'tacacs.db',
]

# Community dbs in the 202012 branch
community_202012_set_1_dbs = [
    'pretest.db',
    'routes.db',
    'dhcp.db',
    'pfcwd.db',
    'layer3.db',
    'link.db',
    'wjh.db',
    'fast_reboot.db',
    'warm_reboot.db',
    'span.db',
]

community_202012_rpc_dbs = [
    'pre_rpc.db',
    'rpc_qos.db',
    'rpc_pfc_asym_and_copp.db',
    'post_rpc.db'
]

community_202012_set_2_dbs = [
    'pretest.db',
    'layer2.db',
    'radv.db',
    'acl.db',
    'ecmp.db',
    'ip_neigh.db',
    'resources.db',
    'tunnel.db',
    'counters.db',
    'techsupport.db',
    'interfaces.db',
    'sub_port_interfaces.db',
    'system_health.db',
    'sflow.db',
    'bgp.db',
    'pbh.db',
    'cold_reboot.db',
    'autorestart.db'
]

community_202012_generic_dbs = [
    'system.db',
    'mgmtvrf.db',
    'tacacs.db',
]

# Community dbs in the 201911 branch
community_201911_set_1_dbs = [
    'routes.db',
    'dhcp.db',
    'pfcwd.db',
    'layer3.db',
    'link.db',
    'wjh.db',
    'fast_reboot.db',
    'warm_reboot.db',
]

community_201911_rpc_dbs = [
    'pre_rpc.db',
    'rpc_qos_copp.db',
    'rpc_pfc_asym.db',
    'post_rpc.db'
]

community_201911_set_2_dbs = [
    'routes.db',
    'layer2.db',
    'acl.db',
    'ecmp.db',
    'ip_neigh.db',
    'resources.db',
    'tunnel.db',
    'counters.db',
    'techsupport.db',
    'interfaces.db',
    'system_health.db',
    'bgp.db',
    'cold_reboot.db'
]

community_201911_generic_dbs = None

# Canonical dbs for develop branch
canonical_develop_dbs = [
    'canonical/pretest.db',
    'platform.db',
    'canonical/nightly.db',
    'canonical/push_gate_with_upgrade.db',
    'dynamic_buffer.db',
    'techsupport_any_topo.db',
    'platform_fwutil.db'

]

# Canonical dbs for 202012 branch
canonical_202012_dbs = [
    'canonical/pretest.db',
    'platform.db',
    'canonical/nightly.db',
    'canonical/push_gate_with_upgrade.db',
    'dynamic_buffer.db',
    'techsupport_any_topo.db',
    'platform_fwutil.db'
]

# Canonical dbs for 201911 branch
canonical_201911_dbs = [
    'platform.db',
    'canonical/nightly.db',
    'canonical/push_gate.db'
]

community_keys = ["additional_apps", "custom_tarball_name", "base_version", "rpc_image",
                  "skip_weekend_cases", "execution_block_generator"]

canonical_keys = ["additional_apps", "base_version", "custom_tarball_name", "send_takeover_notification",
                  "execution_block_generator"]
canonical_upgrade_keys = ["additional_apps", "base_version", "target_version", "custom_tarball_name",
                          "send_takeover_notification", "execution_block_generator"]


def print_configs(f, config_key_list, config_dict):
    f.write("{\n")
    last_key = config_key_list[-1]
    for config_key in config_key_list:
        if config_key == last_key:
            f.write("  \"{}\": \"{}\"".format(config_key, config_dict[config_key]))
        else:
            f.write("  \"{}\": \"{}\",".format(config_key, config_dict[config_key]))
        f.write("\n")
    f.write("}\n")


def gen_community_config(dbs):
    community_config = {
        "additional_apps": "/auto/sw_regression/system/SONIC/MARS/conf/deploy_configs/verification_app_pointers/main_branch_app_verification_pointer",
        "custom_tarball_name": "main_branch_verification_pointer.db.1.tgz",
        "base_version": "/auto/sw_system_release/sonic/main_branch_verification_pointer.bin",
        "rpc_image": "/auto/sw_system_release/sonic/main_branch_verification_pointer-rpc.bin",
        "run_rpc_image": "yes",
        "skip_weekend_cases": "yes",
    }
    execution_block_generator = [
        {'entry_points': 'SONIC_MGMT', 'tests_dbs_tarball': 'sonic-mgmt/sonic-tool/mars/dbs/community/{}'.format(db)}
        for db in dbs]
    community_config["execution_block_generator"] = str(execution_block_generator)

    return community_config


def gen_canonical_config(mars_branch, dbs, upgrade):
    caonical_config = {
        "additional_apps": f"/auto/sw_regression/system/SONIC/MARS/conf/deploy_configs/verification_app_pointers/{mars_branch}_app_verification_pointer",
        "base_version": f"/auto/sw_system_release/sonic/{mars_branch}_verification_pointer.bin",
        "custom_tarball_name": f"{mars_branch}_verification_pointer.db.1.tgz",
        "send_takeover_notification": "yes",
        "execution_block_generator": ""
    }

    base_version_for_upgrade = "/auto/sw_system_release/sonic/202012/202012_5/sonic-mellanox.bin"
    if upgrade:
        caonical_config["target_version"] = caonical_config["base_version"]
        caonical_config["base_version"] = base_version_for_upgrade

    execution_block_generator = []
    for db in dbs:
        if "canonical" in db:
            execution_block_generator.append({'entry_points': 'SONIC_MGMT',
                                              'tests_dbs_tarball': 'sonic-mgmt/sonic-tool/mars/dbs/{}'.format(db)})
        else:
            execution_block_generator.append({'entry_points': 'SONIC_MGMT',
                                              'tests_dbs_tarball': 'sonic-mgmt/sonic-tool/mars/dbs/community/{}'.format(
                                                  db)})
    caonical_config["execution_block_generator"] = str(execution_block_generator)
    return caonical_config


def print_community_configs(f, dbs):
    if dbs:
        mars_config_dict = gen_community_config(dbs)
        print_configs(f, community_keys, mars_config_dict)


def print_cononical_configs(f, mars_branch, dbs, upgrade):
    mars_config_dict = gen_canonical_config(mars_branch, dbs, upgrade)
    if upgrade:
        print_configs(f, canonical_upgrade_keys, mars_config_dict)
    else:
        print_configs(f, canonical_keys, mars_config_dict)


def print_mars_configs(branch):
    path = os.path.dirname(os.path.abspath(__file__))
    file_name = f"mars_config_{branch}.txt"
    community_set_1_general_dbs = eval(f"community_{branch}_set_1_dbs") + \
                                  eval(f"community_{branch}_rpc_dbs")

    community_set_1_full_dbs = eval(f"community_{branch}_set_1_dbs") + \
                               eval(f"community_{branch}_set_2_dbs")[1:] + \
                               eval(f"community_{branch}_rpc_dbs")
    if eval(f"community_{branch}_generic_dbs"):
        community_set_1_full_add_generic_dbs = eval(f"community_{branch}_set_1_dbs") + \
                                               eval(f"community_{branch}_set_2_dbs")[1:] + \
                                               eval(f"community_{branch}_generic_dbs") + \
                                               eval(f"community_{branch}_rpc_dbs")
    else:
        community_set_1_full_add_generic_dbs = None

    community_set_2_general_dbs = eval(f"community_{branch}_set_2_dbs")

    full_file_name = os.path.join(path, file_name)
    with open(full_file_name, 'w') as f:
        f.write("********************************Community**********************************************\n")
        f.write("#######################################################################################\n")
        f.write("#############################Notice here ##############################################\n")
        f.write("#############For weekend scenario,  Friday_Community_Regression_Set_1 #################\n")
        f.write("#############and Friday_Community_Regression_Set_2, need to update ####################\n")
        f.write("#############the value of skip_weekend_cases from 'no' to 'yes' #######################\n")
        f.write("#######################################################################################\n")
        f.write("++++++++++++++++++++++++++++++++Community_Regression_Set_1 start+++++++++++++++++++++++\n")
        f.write("################################general config#########################################\n")
        print_community_configs(f, community_set_1_general_dbs)
        f.write("################################full config############################################\n")
        if branch == "201911":
            f.write("########################## needed by r-leopard-01 and r-leopard-58#####################\n")
        else:
            f.write("########################## needed by r-leopard-01######################################\n")
        print_community_configs(f, community_set_1_full_dbs)
        if community_set_1_full_add_generic_dbs:
            f.write("################################ full_and_generic######################################\n")
            f.write("########################## needed by r-leopard-58######################################\n")
            print_community_configs(f, community_set_1_full_add_generic_dbs)
        f.write("++++++++++++++++++++++++++++++++Community_Regression_Set_1 end+++++++++++++++++++++++++\n")
        f.write("++++++++++++++++++++++++++++++++Community_Regression_Set_2 start+++++++++++++++++++++++\n")
        print_community_configs(f, community_set_2_general_dbs)
        f.write("++++++++++++++++++++++++++++++++Community_Regression_Set_2 end+++++++++++++++++++++++++\n")

        f.write("***************************************************************************************\n")

        f.write("\n\n")
        f.write("*******************************Canonical***********************************************\n")
        canonical_dbs = eval(f"canonical_{branch}_dbs")
        f.write("++++++++++++++++++++++++++++++++ canonical_full_regression_main_branch ++++++++++++++++\n")
        print_cononical_configs(f, "main_branch", canonical_dbs, False)
        if branch != "201911":
            f.write("########## canonical_full_regression_main_branch, for setups which has upgrade ########\n")
            f.write("## sonic_lionfish_r-lionfish-07, sonic_spider_r-spider-05, sonic_leopard_r-leopard-56##\n")
            print_cononical_configs(f, "main_branch", canonical_dbs, True)
        f.write("+++++++++++++++++++++++++++++++ canonical_partial_regression_side_branch_1 ++++++++++++\n")
        print_cononical_configs(f, "side_branch_1", canonical_dbs, False)
        f.write("+++++++++++++++++ canonical_partial_regression_side_branch_2_US_team_setups +++++++++++\n")
        print_cononical_configs(f, "side_branch_2", canonical_dbs, False)
        f.write("***************************************************************************************\n")


if __name__ == "__main__":
    branch_list = ["201911", "202012", "develop"]
    for branch in branch_list:
        print_mars_configs(branch)
