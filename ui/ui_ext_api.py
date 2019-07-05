import requests
import time
import base64
import sys
import os
import json
import argparse
import urllib3
import configparser
import logging
from pprint import pprint

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


class UiPlugin:
    def __init__(self, vcduri, username, password, org="System"):
        self._token = None
        self.vcduri = vcduri
        self.current_ui_extension = {}
        self.getToken(username, org, password)

    def __request(self, method, path=None, data=None, uri=None, auth=None, content_type="application/json", accept="application/json"):
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
        else :
            logger.error("Request code error -> %s" %r.status_code)
            sys.exit(0)

    def getToken(self, username, org, password):
        r = self.__request('POST',
                           '/api/sessions',
                           auth=(('%s@%s' % (username, org)), password),
                           accept='application/*+xml;version=31.0')
        self._token = r.headers['x-vcloud-authorization']

    def getUiExtensions(self):
        return self.__request('GET', '/cloudapi/extensions/ui/')

    def getUiExtension(self, eid):
        return self.__request('GET', '/cloudapi/extensions/ui/%s' % eid)

    def postUiExtension(self, data):
        return self.__request('POST', '/cloudapi/extensions/ui/', json.dumps(data))

    def putUiExtension(self, eid, data):
        return self.__request('PUT', '/cloudapi/extensions/ui/%s' % eid, json.dumps(data))

    def deleteUiExtension(self, eid):
        return self.__request('DELETE', '/cloudapi/extensions/ui/%s' % eid)

    def postUiExtensionPlugin(self, eid, data):
        return self.__request('POST', '/cloudapi/extensions/ui/%s/plugin' % eid, json.dumps(data))

    def putUiExtensionPlugin(self, uri, data):
        return self.__request('PUT', uri=uri, content_type="application/zip", accept=None, data=data)

    def deleteUiExtensionPlugin(self, eid):
        return self.__request('DELETE', '/cloudapi/extensions/ui/%s/plugin' % eid)

    def getUiExtensionTenants(self, eid):
        return self.__request('GET', '/cloudapi/extensions/ui/%s/tenants' % eid)

    def postUiExtensionTenantsPublishAll(self, eid):
        return self.__request('POST', '/cloudapi/extensions/ui/%s/tenants/publishAll' % eid)

    def postUiExtensionTenantsPublish(self, eid, data):
        return self.__request('POST', '/cloudapi/extensions/ui/%s/tenants/publish' % eid, data)

    def postUiExtensionTenantsUnPublishAll(self, eid):
        return self.__request('POST', '/cloudapi/extensions/ui/%s/tenants/unpublishAll' % eid)

    def postUiExtensionTenantsUnPublish(self, eid, data):
        return self.__request('POST', '/cloudapi/extensions/ui/%s/tenants/unpublish' % eid, data)

###

    def postUiExtensionPluginFromFile(self, eid, fn):
        data = {
            "fileName": fn.split('/')[-1],
            "size": os.stat(fn).st_size
        }
        return self.postUiExtensionPlugin(eid, data)

    def putUiExtensionPluginFromFile(self, eid, fn):
        data = open(fn, 'rb').read()
        return self.putUiExtensionPlugin(eid, data)

    def deleteUiExtensionPluginSafe(self, eid):
        if self.current_ui_extension.get('plugin_status', None) == 'ready':
            return self.deleteUiExtensionPlugin(eid)
        else:
            print('Unable to delete plugin for %s' % eid)
            return None

    def walkUiExtensions(self):
        for ext in self.getUiExtensions().json():
            self.current_ui_extension = ext
            yield ext

###

    def parseManifest(self, fn, enabled=True):
        data = json.load(open(fn, 'rb'))
        return {
            "pluginName": data['name'],
            "vendor": data['vendor'],
            "description": data['description'],
            "version": data['version'],
            "license": data['license'],
            "link": data['link'],
            "tenant_scoped": "tenant" in data['scope'],
            "provider_scoped": "service-provider" in data['scope'],
            "enabled": enabled
        }

    def addExtension(self, data, fn, publishAll=False):
        r = self.postUiExtension(data).json()
        eid = r['id']
        self.addPlugin(eid, fn, publishAll=publishAll)

    def addPlugin(self, eid, fn, publishAll=False):
        r = self.postUiExtensionPluginFromFile(eid, fn)
        link = r.headers["Link"].split('>')[0][1:]

        self.putUiExtensionPluginFromFile(link, fn)

        if publishAll:
            self.postUiExtensionTenantsPublishAll(eid)

    def removeAllUiExtensions(self):
        for ext in self.walkUiExtensions():
            self.removeExtension(ext['id'])

    def removeExtension(self, eid):
        self.removePlugin(eid)
        self.deleteUiExtension(eid)

    def removePlugin(self, eid):
        self.deleteUiExtensionPluginSafe(eid)

    def replacePlugin(self, eid, fn, publishAll=False):
        self.removePlugin(eid)
        self.addPlugin(eid, fn, publishAll=publishAll)

    ###

    def deploy(self, basedir):
        manifest = self.parseManifest(
            '%s/manifest.json' % basedir, enabled=True)

        eid = None
        for ext in self.walkUiExtensions():
            if manifest['pluginName'] == ext['pluginName'] and manifest['version'] == ext['version']:
                eid = ext['id']
                break

        if not eid:
            self.addExtension(manifest, '%s/plugin.zip' %
                              basedir, publishAll=True)
        else:
            self.replacePlugin(eid, '%s/plugin.zip' %
                               basedir, publishAll=True)
        logger.info("Extension UI deploy")

    def remove(self, basedir):
        manifest = self.parseManifest(
            '%s/manifest.json' % basedir, enabled=True)

        eid = None
        for ext in self.walkUiExtensions():
            if manifest['pluginName'] == ext['pluginName'] and manifest['version'] == ext['version']:
                return self.removeExtension(ext['id'])

        logger.error("Extension UI not found")
        sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('UI Extension Helper')
    parser.add_argument(
        'command', help='Valid Commands: deploy, remove, removeAllUiExtensions, listUiExtensions')
    parser.add_argument("--server", "-s", help="Hostame server", required=True)
    parser.add_argument("--user", "-u", help="Username to connect", required=True)
    parser.add_argument("--password", "-p", help="Password to connect", required=True)
    parser.add_argument("--folder", "-f", help="Folder where is plugin.zip and manifest.json", required=True)
    args = parser.parse_args()

    vcduri = "https://" + args.server
    user = args.user
    password = args.password
    folder = args.folder

    ui = UiPlugin(vcduri, user, password)

    if args.command == 'deploy':
        ui.deploy(folder)
    elif args.command == 'remove':
        ui.remove(folder)
    elif args.command == 'removeAllUiExtensions':
        ui.removeAllUiExtensions()
    elif args.command == 'listUiExtensions':
        pprint(ui.getUiExtensions().json())
    else:
        raise ValueError('Command (%s) not found' % args.command)
    sys.exit(0)
