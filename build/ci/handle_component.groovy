package com.mellanox.jenkins.generic_modules

def pre(name) {
    return true
}


def run_step(name) {
    try {
        print "Component match = ${env.CHANGED_COMPONENTS}"
        if (env.RUN_COMMUNITY_REGRESSION && env.RUN_COMMUNITY_REGRESSION.toBoolean() == true &&  env.CHANGED_COMPONENTS && env.CHANGED_COMPONENTS.contains("NoMatch")) {
            print "Topic \"RUN_COMMUNITY_REGRESSION=true\" and changed files triggered community regression tests"
        } else {
            env.SKIP_COMMUNITY_REGRESSION = "true"
            NGCITools().ciTools.insert_test_result_to_matrix(name, "ETH_COMMUNITY", "SPC", "Skipped=status")

        }

        if (env.CHANGED_COMPONENTS && (env.CHANGED_COMPONENTS.contains("SONIC_BAT_ONLY") && !env.CHANGED_COMPONENTS.contains("NVOS_BAT_ONLY")
                && !env.CHANGED_COMPONENTS.contains("COMMON_BAT_ONLY") && !env.CHANGED_COMPONENTS.contains("NoMatch"))){
            print "'NVOS' BAT are skipped"
            env.SKIP_NVOS_BAT = "true"
            NGCITools().ciTools.insert_test_result_to_matrix(name, "IB", "QTM2", "Skipped=status")
        }

        //If NVOS only, disable all sonic BAT
        if (env.CHANGED_COMPONENTS && (env.CHANGED_COMPONENTS.contains("NVOS_BAT_ONLY") && !env.CHANGED_COMPONENTS.contains("SONIC_BAT_ONLY")
                && !env.CHANGED_COMPONENTS.contains("COMMON_BAT_ONLY") && !env.CHANGED_COMPONENTS.contains("NoMatch"))){
            print "'SONIC' BAT are skipped"
            NGCITools().ciTools.insert_test_result_to_matrix(name, "ETH", "SPC", "Skipped=status")
            NGCITools().ciTools.insert_test_result_to_matrix(name, "ETH", "SPC2", "Skipped=status")
            NGCITools().ciTools.insert_test_result_to_matrix(name, "ETH", "SPC3", "Skipped=status")
            NGCITools().ciTools.insert_test_result_to_matrix(name, "SIMX", "SPC", "Skipped=status")
            NGCITools().ciTools.insert_test_result_to_matrix(name, "SIMX", "SPC2", "Skipped=status")
            NGCITools().ciTools.insert_test_result_to_matrix(name, "SIMX", "SPC3", "Skipped=status")
            NGCITools().ciTools.insert_test_result_to_matrix(name, "SIMX", "SPC4", "Skipped=status")
            NGCITools().ciTools.insert_test_result_to_matrix(name, "DPU", "BF3", "Skipped=status")
            env.SKIP_DPU_BAT = "true"
            env.SKIP_BAT = "true"
            env.SKIP_SIMX = "true"
        }

        return true
    }
    catch (Throwable exc) {
        NGCITools().ciTools.set_error_in_env(exc, "user", name)
        return false

    }
}


def post(name) {
    return true
}


def cleanup(name) {
    return true
}

def headline(name) {
    return "${name} " + env."${name}_status"
}


def summary(name) {
    if (env."${name}_status" != "Success") {
        return env."${name}_status" + " - exception: " + env."${name}_error"
    } else {
        return env."${name}_status"
    }
}


return this
