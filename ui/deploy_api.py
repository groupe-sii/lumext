import requests
import time
import base64
import sys
import os
import json
import argparse
import urllib3
import configparser
import xmltodict
import logging
from pprint import pprint

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.add_stderr_logger()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s')
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
console_formatter = logging.Formatter("%(levelname)s\t | %(message)s")
console_logger = logging.StreamHandler()
console_logger.setFormatter(console_formatter)
console_logger.setLevel(logging.DEBUG)
logger.addHandler(console_logger)

############### TO DELETE ################



########################################


class APIExtension:
    def __init__(self, vcduri, username, password, org="System"):
        self._token = None
        self.vcduri = vcduri
        self.getToken(username, org, password)

    def __request(self, method, path=None, data=None, uri=None, auth=None, content_type="application/vnd.vmware.admin.service+xml", accept="application/*+xml;version=31.0"):
        headers = {}
        if self._token:
            headers['x-vcloud-authorization'] = self._token
        if content_type:
            headers['Content-Type'] = content_type
        if accept:
            headers['Accept'] = accept
        if path:
            uri = self.vcduri+path
        r = requests.request(method, uri, headers=headers, auth=auth,
                             data=data, verify=False)
        if 200 <= r.status_code <= 299:
            return r
        raise Exception(
            print(r))

    def getToken(self, username, org, password):
        r = self.__request('POST',
                           '/api/sessions',
                           auth=(('%s@%s' % (username, org)), password),
                           accept='application/*+xml;version=31.0')
        self._token = r.headers['x-vcloud-authorization']

    def get_extension_link(self, extension_name):
        r = self.__request("GET", "/api/admin/extension/service/query")
        data = xmltodict.parse(r.text)
        logger.info("Got extension link")
        if not("AdminServiceRecord" in data["QueryResultRecords"]):
            logger.error('No extension to delete')
            sys.exit(-1)
        elif isinstance(data["QueryResultRecords"]["AdminServiceRecord"], list):
            for item in data["QueryResultRecords"]["AdminServiceRecord"]:
                if item['@namespace'] == extension_name:
                    return "/api" + item['@href'].split("/api", 1)[-1]
        elif isinstance(data["QueryResultRecords"]["AdminServiceRecord"], dict):
            return "/api" + data["QueryResultRecords"]["AdminServiceRecord"]['@href'].split("/api", 1)[1]

    def get_extension_data(self, ext_uri):
        r = self.__request("GET", ext_uri)
        logger.info("Got extension data")
        return r.content.decode()

    def disable_extension(self, extension_name):
        ext_uri = self.get_extension_link(extension_name)
        payload = self.get_extension_data(ext_uri)
        payload = payload.replace(
            "vmext:Enabled>true<", "vmext:Enabled>false<")
        self.__request("PUT", ext_uri, data=payload)
        logger.info("Extension is now disabled")
        return

    def enable_extension(self, extension_name):
        ext_uri = self.get_extension_link(extension_name)
        payload = self.get_extension_data(ext_uri)
        payload = payload.replace(
            "vmext:Enabled>false<", "vmext:Enabled>true<")
        self.__request("PUT", ext_uri, data=payload)
        logger.info("Extension is now enabled")
        return

    def delete_extension(self, extension_name):
        ext_uri = self.get_extension_link(extension_name)
        self.__request("DELETE", ext_uri)
        return

    def create_extension(self, extension_file):
        with open(extension_file, 'r') as f:
            payload = f.read()
        self.__request("POST", "/api/admin/extension/service", data=payload)
        logger.info("Extension is deployed")
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser('API Extension Helper')
    parser.add_argument(
        'command', help='Valid Commands: deploy, redeploy, remove')
    parser.add_argument("--server", "-s", help="Hostame server", required=True)
    parser.add_argument("--user", "-u", help="Username to connect", required=True)
    parser.add_argument("--password", "-p", help="Password to connect", required=True)
    parser.add_argument("--extension_file", "-e", help="Folder and name of the file in xml which describe extension", required=True)
    parser.add_argument("--extension_name", "-n", help="Extension name", required=True)
    args = parser.parse_args()

    vcduri = "https://" + args.server
    user = args.user
    password = args.password
    extension_file = args.extension_file
    extension_name = args.extension_name

    api = APIExtension(vcduri, user, password)

    if args.command == 'deploy':
        api.create_extension(extension_file)
    elif args.command == 'redeploy':
        api.disable_extension(extension_name)
        api.delete_extension(extension_name)
        api.create_extension(extension_file)
    elif args.command == 'remove':
        api.disable_extension(extension_name)
        api.delete_extension(extension_name)
    else:
        raise ValueError('Command (%s) not found' % args.command)
        sys.exit(0)
