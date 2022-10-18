package com.mellanox.jenkins

def client_side_validation(client_validation_groovy) {
    //Load client side validation error map
    def errors_map = [:]
    errors_map = client_validation_groovy.mgmt_merge_flow()

    def errors_html = ""


    if (errors_map.size() > 0) {

        errors_map.each { param, param_error ->
            errors_html += "</br><B>${param}:</B>&nbsp${env."${param}"}</B>"
            if (NGCITools().ciTools.is_parameter_contains_value(errors_map["${param}"])) {
                errors_html += "  ${errors_map["${param}"]}"
            }
        }
        error "&nbsp</br>${errors_html}"
    }
    return true
}

def pre(name) {
    return true
}


def run_step(name) {
    try {
        env.MGMT_GERRIT_BRANCH = env.MGMT_GERRIT_BRANCH.replaceAll("origin\\/", "").replaceAll("origin1\\/", "").replaceAll("origin2\\/", "").trim()
        env.GITHUB_BRANCH = env.MGMT_GITHUB_BRANCH.replaceAll("origin\\/", "").replaceAll("origin1\\/", "").replaceAll("origin2\\/", "").trim()
        env.IMAGE_BRANCH = env.IMAGE_GITHUB_BRANCH.replaceAll("origin\\/", "").replaceAll("origin1\\/", "").replaceAll("origin2\\/", "").trim()
        env.OVERRIDE_BRANCH_NAME = env.MGMT_GERRIT_BRANCH

        //Run client validation
        env.RELEASE_ERRORS_MAP="true"
        env.MERGE_HTML_VALIDATION="false"
        def client_validation_groovy = load("build/common/client_validation.groovy")
        client_side_validation(client_validation_groovy)


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
