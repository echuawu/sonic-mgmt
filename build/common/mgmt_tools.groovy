package com.mellanox.jenkins

def get_sonic_lastrc_version(target_branch) {
    //Check for lastrc
    try {
        print "Getting lastrc SONiC version"
        def version_path = env.VERSION_DIRECTORY
        def lastrc = NGCITools().ciTools.run_sh_return_output("readlink ${version_path}/${target_branch}-lastrc-internal-sonic-mellanox.bin")
        if (lastrc.contains("_Public")) {
            version_path = version_path  + "/public"
        }
        def lastrc_version = lastrc.replace("${version_path}", "").replace("/dev/","/").replace("/Mellanox/sonic-mellanox.bin", "").replace("/", "")
        print "CI will use branch:${target_branch} lastrc version: ${lastrc_version} for running BAT"
        return lastrc_version
    } catch (Throwable lastrc_ex) {
        //Handle non exist links
        error "No lastrc soft link is available for branch ${target_branch}. please contact DevOps for more help"
    }
}

def get_nvos_lastrc_version(target_branch) {
    //Check for lastrc
    try {
        print "Getting lastrc NVOS version"
        def version_path = env.NVOS_VERSION_DIRECTORY
        def lastrc = NGCITools().ciTools.run_sh_return_output("readlink ${version_path}/lastrc_${target_branch}")
        def lastrc_version = lastrc.replace("${version_path}", "").replace("/dev/","/").replace("/amd64/", "").replace("/", "")
        print "CI will use branch:${target_branch} lastrc version: ${lastrc_version} for running BAT"
        return lastrc_version
    } catch (Throwable lastrc_ex) {
        //Handle non exist links
        error "No lastrc soft link is available for branch ${target_branch}. please contact DevOps for more help"
    }
}

def get_dpu_lastrc_version(target_branch) {
    //Check for lastrc
    try {
        print "Getting lastrc DPU version"
        def version_path = env.DPU_VERSION_DIRECTORY
        def lastrc = NGCITools().ciTools.run_sh_return_output("readlink ${version_path}/${target_branch}-latest-internal-sonic-nvidia-bluefield.bfb")
        def lastrc_version = lastrc.replace("${version_path}", "").replace("/dev/","/").replace("/Nvidia-bluefield/sonic-nvidia-bluefield.bfb", "").replace("/", "")
        print "CI will use branch:${target_branch} lastrc version: ${lastrc_version} for running BAT"
        return lastrc_version
    } catch (Throwable lastrc_ex) {
        //Handle non exist links
        error "No lastrc soft link is available for branch ${target_branch}. please contact DevOps for more help"
    }
}

return this