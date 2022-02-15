import logging
import os
import time
import re
from multiprocessing.pool import ThreadPool
from http.server import HTTPServer
import json
from ngts.scripts.sonic_deploy.image_http_request_handler import ImageHTTPRequestHandler
from ngts.constants.constants import MarsConstants

logger = logging.getLogger()


def prepare_images(base_version, target_version, serve_file):
    """
    Method which starts HTTP server if need and share image via HTTP
    """
    image_urls = {"base_version": "", "target_version": ""}

    if serve_file:
        serve_files_over_http(base_version, target_version, image_urls)
    else:
        set_image_path(base_version, "base_version", image_urls)
        if target_version:
            set_image_path(target_version, "target_version", image_urls)

    for image_role in image_urls:
        logger.info('Image {image_role} URL is:{image}'.format(image_role=image_role, image=image_urls[image_role]))
    return image_urls


def set_image_path(image_path, image_key, image_dict):
    if is_url(image_path):
        path = image_path
    else:
        verify_file_exists(image_path)
        logger.info("Image {} path is:{}".format(image_key, os.path.realpath(image_path)))
        path = get_installer_url_from_nfs_path(image_path)
    image_dict[image_key] = path


def get_installer_url_from_nfs_path(image_path):
    verify_image_stored_in_nfs(image_path)
    image_path = get_image_path_in_new_nfs_dir(image_path)
    return "{http_base}{image_path}".format(http_base=MarsConstants.HTTTP_SERVER_FIT69, image_path=image_path)


def verify_image_stored_in_nfs(image_path):
    nfs_base_path = r'\/auto\/|\/\.autodirect\/'
    is_located_in_nfs = re.match(r"^({nfs_base_path}).+".format(nfs_base_path=nfs_base_path), image_path)
    assert is_located_in_nfs, "The Image must be located under {nfs_base_path}".\
        format(nfs_base_path=nfs_base_path)


def get_image_path_in_new_nfs_dir(image_path):
    return re.sub(r"^\/\.autodirect\/", "/auto/", image_path)


def is_url(image_path):
    return re.match('https?://', image_path)


def serve_files_over_http(base_version, target_version, image_urls):
    served_files = {}
    verify_file_exists(base_version)
    served_files["/base_version"] = base_version
    if target_version:
        verify_file_exists(target_version)
        served_files["/target_version"] = target_version

    httpd = start_http_server(served_files)
    http_base_url = "http://{}:{}".format(httpd.server_name, httpd.server_port)
    for served_file_path in served_files:
        image_urls[served_file_path.lstrip("/")] = http_base_url + served_file_path


def verify_file_exists(image_path):
    is_file = os.path.isfile(image_path)
    assert is_file, "Cannot access Image {}: no such file.".format(image_path)


def start_http_server(served_files):
    """
    @summary: Use ThreadPool to start a HTTP server
    @param served_files: Dictionary of the files to be served. Dictionary format:
        {"/base_version": "/.autodirect/sw_system_release/sonic/201811-latest-sonic-mellanox.bin",
         "/target_version": "/.autodirect/sw_system_release/sonic/master-latest-sonic-mellanox.bin"}
    """
    logger.info("Try to serve files over HTTP:\n%s" % json.dumps(served_files, indent=4))
    ImageHTTPRequestHandler.served_files = served_files
    httpd = HTTPServer(("", 0), ImageHTTPRequestHandler)

    def run_httpd():
        httpd.serve_forever()

    pool = ThreadPool()
    pool.apply_async(run_httpd)
    time.sleep(5)  # The http server needs couple of seconds to startup
    logger.info("Started HTTP server on STM to serve files %s over http://%s:%s" %
                (str(served_files), httpd.server_name, httpd.server_port))
    return httpd


def get_sonic_branch(image_path):
    """
    Get image branch from path: /auto/sw_system_release/sonic/master.234-27a6641fb_Internal/Mellanox/sonic-mellanox.bin
    :param image_path: example: /auto/sw_system_release/sonic/master.234-27a6641fb_Internal/Mellanox/sonic-mellanox.bin
    :return: branch, example: master
    """
    branch_part_index = 1
    branch_index = 0
    real_path = os.path.realpath(image_path)
    branch = real_path.split('/auto/sw_system_release/sonic/')[branch_part_index].split('.')[branch_index]
    return branch
