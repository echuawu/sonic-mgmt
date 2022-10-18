package com.mellanox.jenkins

def pre(name) {
    return true
}


def run_step(name) {
    try {
        //last sha1 from local
        def last_local_commit = NGCITools().ciTools.run_sh_return_output("git rev-parse ${env.MGMT_GERRIT_BRANCH}").trim()

        //copy commit msg
        if (!fileExists(".git/hooks/commit-msg")) {
            NGCITools().ciTools.run_sh('''scp -p -P 29418 l-sw-gerrit-01.mtl.labs.mlnx:hooks/commit-msg ".git/hooks/"''')
        }
        NGCITools().ciTools.run_sh("git remote add upstream ${env.GITHUB_REPOSITORY} && git fetch upstream")
        try {
            NGCITools().ciTools.run_sh("git merge upstream/${env.GITHUB_BRANCH} --no-ff")
        } catch (Throwable ex) {
            print "Merge conflicts were found. Verifying if all conflicts are in 'permitted to override' list."
            def conflict_files = NGCITools().ciTools.run_sh_return_output("git diff --name-only --diff-filter=U")
            def merge_our_files = NGCITools().ciTools.run_sh_return_output("cat build/merge/merge_overwrite_conflicts")
            merge_our_files = merge_our_files.split("\n")
            conflict_files = conflict_files.split("\n")
            def found_in_file
            for (conflict in conflict_files) {
                found_in_file = false
                for (file in merge_our_files) {
                    if (conflict.contains(file)){
                        found_in_file = true
                        print "File ${conflict} will be taken from 'our' git"
                        NGCITools().ciTools.run_sh("git checkout HEAD -- ${conflict}")
                        break
                    }
                }
                if (!found_in_file){
                    print "File ${conflict} will be taken from 'thiers' git"
                    NGCITools().ciTools.run_sh("git checkout upstream/${env.GITHUB_BRANCH} -- ${conflict}")
                }
                NGCITools().ciTools.run_sh("git add ${conflict}")
            }
            print "All permitted automatic fixes for conflicts were done.\nTrying to commit the conflicts solutions.\n" +
                    "Will fail if there are still more conflicts!"
            NGCITools().ciTools.run_sh("git commit -m 'Merge remote-tracking branch 'upstream/${env.GITHUB_BRANCH}' into ${env.MGMT_GERRIT_BRANCH}'")
        }
        //Check if there are new changes

        def new_commit = NGCITools().ciTools.run_sh_return_output("git rev-parse ${env.MGMT_GERRIT_BRANCH}").trim()
        if (new_commit == last_local_commit) {
            env.MAIL_SUBJECT = "There are no new changes available."
            currentBuild.description = env.MAIL_SUBJECT
            print "There are no new changes."
            return true
        }

        //Add changeID
        NGCITools().ciTools.run_sh("git commit -C HEAD --amend")

        env.NEW_CHANGES = true

        print "New changes found!"

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
