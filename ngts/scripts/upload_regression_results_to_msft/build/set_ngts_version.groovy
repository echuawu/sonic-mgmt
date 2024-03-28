def pre(name) {
    echo "PRE:: Setting ngts version"
    return true
}

def run_step(name) {
    try {
        echo "Setting ngts version"
        echo "params ${params}"
        dir("ngts/scripts/upload_regression_results_to_msft"){
            ngts_version = NGCITools().ciTools.run_sh_return_output("sh ./get_ngts_version.sh")
        }
        echo "ngts version is $ngts_version"
        env.NGTS_VERSION = ngts_version
        return true
    }
    catch (Throwable exc) {
        NGCITools().ciTools.set_error_in_env(exc, "user", name)
        return false
    }
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

