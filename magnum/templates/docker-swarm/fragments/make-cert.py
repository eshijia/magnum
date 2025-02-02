#!/usr/bin/python

# Copyright 2015 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import subprocess

import requests

HEAT_PARAMS_PATH = '/etc/sysconfig/heat-params'
PUBLIC_IP_URL = 'http://169.254.169.254/latest/meta-data/public-ipv4'
CERT_DIR = '/etc/docker'
CERT_CONF_DIR = '%s/conf' % CERT_DIR
CA_CERT_PATH = '%s/ca.crt' % CERT_DIR
SERVER_CONF_PATH = '%s/server.conf' % CERT_CONF_DIR
SERVER_KEY_PATH = '%s/server.key' % CERT_DIR
SERVER_CSR_PATH = '%s/server.csr' % CERT_DIR
SERVER_CERT_PATH = '%s/server.crt' % CERT_DIR

CSR_CONFIG_TEMPLATE = """
[req]
distinguished_name = req_distinguished_name
req_extensions     = req_ext
x509_extensions    = req_ext
prompt = no
copy_extensions = copyall
[req_distinguished_name]
CN = swarm.invalid
[req_ext]
subjectAltName = %(subject_alt_names)s
extendedKeyUsage = clientAuth,serverAuth
"""


def _parse_config_value(value):
    parsed_value = value
    if parsed_value[-1] == '\n':
        parsed_value = parsed_value[:-1]
    return parsed_value[1:-1]


def load_config():
    config = dict()
    with open(HEAT_PARAMS_PATH, 'r') as fp:
        for line in fp.readlines():
            key, value = line.split('=', 1)
            config[key] = _parse_config_value(value)
    return config


def create_dirs():
    os.makedirs(CERT_CONF_DIR)


def _get_public_ip():
    return requests.get(PUBLIC_IP_URL).text


def _build_subject_alt_names(config):
    subject_alt_names = [
        'IP:%s' % _get_public_ip(),
        'IP:%s' % config['SWARM_NODE_IP'],
        'IP:127.0.0.1'
    ]
    return ','.join(subject_alt_names)


def write_ca_cert(config):
    bay_cert_url = '%s/certificates/%s' % (config['MAGNUM_URL'],
                                           config['BAY_UUID'])
    headers = {'X-Auth-Token': config['USER_TOKEN']}
    ca_cert_resp = requests.get(bay_cert_url,
                                headers=headers)

    with open(CA_CERT_PATH, 'w') as fp:
        fp.write(ca_cert_resp.json()['pem'])


def write_server_key():
    subprocess.call(['openssl', 'genrsa',
                     '-out', SERVER_KEY_PATH,
                     '4096'])


def _write_csr_config(config):
    with open(SERVER_CONF_PATH, 'w') as fp:
        params = {
            'subject_alt_names': _build_subject_alt_names(config)
        }
        fp.write(CSR_CONFIG_TEMPLATE % params)


def create_server_csr(config):
    _write_csr_config(config)
    subprocess.call(['openssl', 'req', '-new',
                     '-days', '1000',
                     '-key', SERVER_KEY_PATH,
                     '-out', SERVER_CSR_PATH,
                     '-reqexts', 'req_ext',
                     '-extensions', 'req_ext',
                     '-config', SERVER_CONF_PATH])

    with open(SERVER_CSR_PATH, 'r') as fp:
        return {'bay_uuid': config['BAY_UUID'], 'csr': fp.read()}


def write_server_cert(config, csr_req):
    cert_url = '%s/certificates' % config['MAGNUM_URL']
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': config['USER_TOKEN']
    }
    csr_resp = requests.post(cert_url,
                             data=json.dumps(csr_req),
                             headers=headers)

    with open(SERVER_CERT_PATH, 'w') as fp:
        fp.write(csr_resp.json()['pem'])


def main():
    config = load_config()
    if config['INSECURE'] == 'False':
        create_dirs()
        write_ca_cert(config)
        write_server_key()
        csr_req = create_server_csr(config)
        write_server_cert(config, csr_req)


if __name__ == '__main__':
    main()
