package vars

def pre(name) {
    return true
}

def set_sonic_bin(topic_map, project) {
    if (topic_map["IMAGE_BRANCH"] && NGCITools().ciTools.is_parameter_contains_value(topic_map["IMAGE_BRANCH"]) &&
            topic_map["IMAGE_VERSION"] && NGCITools().ciTools.is_parameter_contains_value(topic_map["IMAGE_VERSION"])) {
        error "IMAGE_BRANCH and IMAGE_VERSION cannot be defined together. remove one or both of them from Gerrit topic to continue "
    }
  
    def sonic_branch = env.DEFAULT_SONIC_BRANCH ? env.DEFAULT_SONIC_BRANCH : "develop"
    if (topic_map["IMAGE_BRANCH"] && NGCITools().ciTools.is_parameter_contains_value(topic_map["IMAGE_BRANCH"])) {
        sonic_branch = topic_map["IMAGE_BRANCH"]
        print "SONiC image branch name is defined by topic: ${sonic_branch}"
    } else if (project == "sonic") {
        def branch_map = NGCITools().ciTools.read_json(NGCITools().ciTools.getFileContent("${env.SONIC_BRANCH_MAP}"))
        sonic_branch = env.GERRIT_BRANCH.replace("develop-", "")
        if (branch_map["${env.GERRIT_BRANCH}"] && NGCITools().ciTools.is_parameter_contains_value(branch_map["${env.GERRIT_BRANCH}"])) {
            sonic_branch = branch_map["${env.GERRIT_BRANCH}"]
        }
        print "SONiC image branch name is defined by mapping file or convention develop-<branch> name : ${sonic_branch}"
    }

    def sonic_version_name
    if (topic_map["IMAGE_VERSION"] && NGCITools().ciTools.is_parameter_contains_value(topic_map["IMAGE_VERSION"])) {
        sonic_version_name = topic_map["IMAGE_VERSION"]
        print "SONiC image version  is defined by topic \"IMAGE_VERSION\"."
    } else {
        def mgmt_tools = NGCITools().ciTools.load_project_lib("${env.SHARED_LIB_FILE}")
        sonic_version_name = mgmt_tools.get_sonic_lastrc_version(sonic_branch)
        print "SONiC image version is defined by lastrc link for branch: ${sonic_branch}"
    }

    if (sonic_version_name.contains("_Public")) {
        env.VERSION_DIRECTORY = env.VERSION_DIRECTORY + "/public"
    }

    def sonic_bin_path = "${env.VERSION_DIRECTORY}/${sonic_version_name}/Mellanox/sonic-mellanox.bin"
    env.README_PATH = "${env.VERSION_DIRECTORY}/${sonic_version_name}"
    if (! new File(sonic_bin_path).exists()) {
        error "ERROR:SONiC bin file not found: ${sonic_bin_path}"
    }
    env.SONIC_BIN = sonic_bin_path
}

def set_nvos_bin(topic_map, project){
    if (topic_map["IMAGE_NVOS_BRANCH"] && NGCITools().ciTools.is_parameter_contains_value(topic_map["IMAGE_NVOS_BRANCH"]) &&
            topic_map["IMAGE_NVOS_VERSION"] && NGCITools().ciTools.is_parameter_contains_value(topic_map["IMAGE_NVOS_VERSION"])) {
        error "IMAGE_NVOS_BRANCH and IMAGE_NVOS_VERSION cannot be defined together. remove one or both of them from Gerrit topic to continue "
    }

    def nvos_branch = env.DEFAULT_NVOS_BRANCH ? env.DEFAULT_NVOS_BRANCH : "master"
    if (topic_map["IMAGE_NVOS_BRANCH"] && NGCITools().ciTools.is_parameter_contains_value(topic_map["IMAGE_NVOS_BRANCH"])) {
        nvos_branch = topic_map["IMAGE_NVOS_BRANCH"]
        print "NVOS image branch name is defined by topic: ${nvos_branch}"
    } else if (project == "nvos") {
        if (env.GERRIT_BRANCH && NGCITools().ciTools.is_parameter_contains_value(env.GERRIT_BRANCH)) {
            nvos_branch = env.GERRIT_BRANCH.replace("_ver", "")
            print "NVOS image branch name branch name: ${nvos_branch}"
        }
    }

    def nvos_version_name
    if (topic_map["IMAGE_NVOS_VERSION"] && NGCITools().ciTools.is_parameter_contains_value(topic_map["IMAGE_NVOS_VERSION"])) {
        nvos_version_name = topic_map["IMAGE_NVOS_VERSION"]
        print "NVOS image version  is defined by topic \"IMAGE_VERSION\"."
    } else {
        def mgmt_tools = NGCITools().ciTools.load_project_lib("${env.SHARED_LIB_FILE}")
        nvos_version_name =  mgmt_tools.get_nvos_lastrc_version(nvos_branch)
        print "NVOS image version is defined by lastrc link for branch: ${nvos_branch}"
    }
    def nvos_bin_path = "${env.NVOS_VERSION_DIRECTORY}/${nvos_version_name}/amd64/nvos-amd64-${nvos_version_name}.bin"
    if (! new File(nvos_bin_path).exists()) {
        error "ERROR: NVOS bin file not found: ${nvos_bin_path}"
    }
    env.NVOS_BIN = nvos_bin_path
}

def run_step(name) {
    try {
        def topic = (GerritTools.get_topic(env.GERRIT_CHANGE_NUMBER)).replace("\"","")
        def topic_map = [:]
        for (_topic in topic.split(",")) {
            if (_topic.contains("=")) {
                topic_map[_topic.split("=")[0].trim()] = _topic.split("=", 2)[1].trim().replace("\"","")
            }
        }

        def project = "sonic"
        if (env.GERRIT_BRANCH.startsWith("dev-") || env.GERRIT_BRANCH.startsWith("dev_") ||env.GERRIT_BRANCH.startsWith("nvos")){
            project = "nvos"
        }

        if (topic_map["RUN_COMMUNITY_REGRESSION"] && topic_map["RUN_COMMUNITY_REGRESSION"].toBoolean() == true) {
            env.RUN_COMMUNITY_REGRESSION = true
        }

        set_sonic_bin(topic_map, project)
        set_nvos_bin(topic_map, project)


        //Copy files to external storage
        env.nfs_dir = "/auto/sw_system_project/devops/sw-r2d2-bot/${env.JOB_NAME}/${currentBuild.number}"

        //copy build moduls dir
        if (!fileExists(env.nfs_dir + "/build")) {
            NGCITools().ciTools.run_sh("mkdir -p ${env.nfs_dir}/build/ci")
            NGCITools().ciTools.run_sh("mkdir -p ${env.nfs_dir}/sonic-mgmt")
            NGCITools().ciTools.run_sh("chmod -R 777 ${env.nfs_dir}")
            NGCITools().ciTools.run_sh("mkdir -p ${env.nfs_dir}/LOGS")
            NGCITools().ciTools.run_sh("chmod 777 ${env.nfs_dir}/LOGS")
            print "copying mgmt repo files to " + env."nfs_dir"
            NGCITools().ciTools.run_sh("cp -rf ./. ${env.nfs_dir}/sonic-mgmt/")
            NGCITools().ciTools.run_sh("cp -r build/. ${env.nfs_dir}/build/")
            //Copy bat properties from sonic_devops shared location (used by bat.groovy)
            NGCITools().ciTools.run_sh("cp /auto/sw_system_release/ci/sonic_devops/build/ci/bat_properties_file.txt ${env.nfs_dir}/build/ci/")
            NGCITools().ciTools.run_sh("cp /auto/sw_system_release/ci/nos/nvos/build/common/bat_properties_file.txt ${env.nfs_dir}/build/common/")
        }

        //copy sonic_devops build
        NGCITools().ciTools.run_sh("mkdir -p ${env.nfs_dir}/sonic_devops/build")
        NGCITools().ciTools.run_sh("chmod 777 ${env.nfs_dir}/sonic_devops/build")


    } catch (Throwable ex) {
        NGCITools().ciTools.set_error_in_env(ex, "devops", name)
        return false
    }
    return true
}


def cleanup(name) {
    return true
}

def headline(name) {
    if ("${name}".contains(":")) {
        return "${name}".split(":")[0] + " " + env."${name}_status"
    } else {
        return "${name} " + env."${name}_status"
    }
}


def summary(name) {
    if (env."${name}_status" != "Success") {
        return env."${name}_status" + " - exception: " + env."${name}_error"
    } else {
        return env."${name}_status"
    }
}


return this
