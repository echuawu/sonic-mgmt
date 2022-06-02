import os
import argparse

SUCCESS = 0
sw_password = 'YourPaSsWoRd'


class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def colorful_print(color, str):
    print(color+"\n{}\n".format(str)+colors.ENDC)


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Positional mandatory arguments
    parser.add_argument("--debian", "-deb", help="The debian path to build and deploy.", type=str, required=True)
    parser.add_argument("--switch", "-sw", help="The switch name to deploy on.", type=str, required=True)
    parser.add_argument("--dockers", "-d", help="A list of the dockers names' to deploy.", nargs="+", type=str, required=True)

    # Optional arguments
    parser.add_argument("--debug", "-dbg", help="debug")
    parser.add_argument("--source", "-src", help="source code to debug")
    parser.add_argument("--skip", "-s", help="Skip deb build, deploy deb only.", action="store_true", default=False)

    # Parse arguments
    args = parser.parse_args()

    return args


def remove_deb_file(deb_path):
    cmd = "rm -rf {}".format(deb_path)
    colorful_print(colors.OKBLUE, ">> {}".format(cmd))
    if os.system(cmd) != SUCCESS:
       colorful_print(colors.FAIL, "failed in: {}".format(cmd))
       exit(1)


def make(deb_path, debug_flag):
    deb_path_arr = deb_path.split('/')
    if len(deb_path_arr) <= 2:
        colorful_print(colors.FAIL, "failed: invalid deb path {}".format(deb_path))
        exit(1)
    build_system = deb_path_arr[2]
    if debug_flag:
        cmd = 'make BLDENV={} SONIC_BUILD_JOBS=10 INSTALL_DEBUG_TOOLS=y {}'.format(build_system, deb_path)
    else:
        cmd = 'make BLDENV={} SONIC_BUILD_JOBS=10 {}'.format(build_system, deb_path)
    colorful_print(colors.OKBLUE, ">> {}".format(cmd))
    if os.system(cmd) != SUCCESS:
        colorful_print(colors.FAIL, "failed in: {}".format(cmd))
        exit(1)


def scp(password, src, dst):
    cmd = 'sshpass -p {} scp -r {} {}'.format(password, src, dst)
    colorful_print(colors.OKBLUE, '>> scp -r {} {}'.format(src, dst))
    if os.system(cmd) != SUCCESS:
        colorful_print(colors.FAIL, 'failed in:scp -r {} {}'.format(src, dst))
        exit(1)


def switch_command(switch, command):
    colorful_print(colors.OKBLUE, ">> {}".format(command))
    if os.system("sshpass -p '{}' ssh admin@{} {}".format(sw_password, switch, command)) != SUCCESS:
        colorful_print(colors.FAIL, "failed in : {}".format(command))
        exit(1)


def docker_cp(switch, file_path, docker):
    switch_command(switch, "docker cp {} {}:/".format(file_path, docker))


def dpkg(switch, docker, deb):
    switch_command(switch, "docker exec -t {} dpkg -i {}".format(docker, deb))


def docker_restart(switch, docker):
    switch_command(switch, "sudo systemctl restart {}.service".format(docker))


def deploy(deb, switch, dockers, skip_build):

    if not skip_build:
        # removes old deb files
        remove_deb_file(deb)

        # build the new debs
        make(deb, False)

    # copy the new deb to the switch
    scp(sw_password, deb, 'admin@{}:/tmp'.format(switch))

    path_in_switch = deb.split('/')[-1]

    for docker in dockers:
        # copy the deb from the switch to the docker
        docker_cp(switch, "/tmp/{}".format(path_in_switch), docker)

        # depackage the debs
        dpkg(switch, docker, path_in_switch)

        # restart the docker
        docker_restart(switch, docker)


def deploy_dbg(deb, deb_dbg, src_code_path, switch, dockers, skip_build):

    if not skip_build:
        # removes old deb files
        remove_deb_file(deb)
        remove_deb_file(deb_dbg)

        # build the new debs
        make(deb, deb_dbg)

    # copy the sorce code to the switch
    src_code_folder = src_code_path.split('/')[-2]
    scp(sw_password, src_code_path, 'admin@{}:/tmp'.format(switch))

    # copy the new debs to the switch
    scp(sw_password, deb, 'admin@{}:/tmp'.format(switch))
    scp(sw_password, deb_dbg, 'admin@{}:/tmp'.format(switch))

    deb_path_in_switch = deb.split('/')[-1]
    deb_dbg_path_in_switch = deb_dbg.split('/')[-1]

    for docker in dockers:
        # copy the debs and source code from the switch to the docker
        docker_cp(switch, "/tmp/{}".format(deb_path_in_switch), docker)
        docker_cp(switch, "/tmp/{}".format(deb_dbg_path_in_switch), docker)
        docker_cp(switch, "/tmp/{}".format(src_code_folder), docker)

        # depackage the debs
        dpkg(switch, docker, deb_path_in_switch)
        dpkg(switch, docker, deb_dbg_path_in_switch)

        # restart the docker
        docker_restart(switch, docker)


if __name__ == '__main__':
    args = parse_arguments()
    deb = args.debian
    switch = args.switch
    dockers = args.dockers
    skip_build = args.skip

    colorful_print(colors.OKBLUE, "Running SONiC dev tool helper...")

    if args.debug:
        deb_dbg = args.debug
        src = args.source
        deploy_dbg(deb, deb_dbg, src, switch, dockers, skip_build)
    else:
        deploy(deb, switch, dockers, skip_build)
    colorful_print(colors.OKGREEN, "Finished! Happy coding!")









