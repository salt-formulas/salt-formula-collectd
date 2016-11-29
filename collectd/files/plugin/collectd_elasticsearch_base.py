#!/usr/bin/python
# Copyright 2016 Mirantis, Inc.
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

import requests

import collectd_base as base


class ElasticsearchBase(base.Base):
    def __init__(self, *args, **kwargs):
        super(ElasticsearchBase, self).__init__(*args, **kwargs)
        self.protocol = 'http'
        self.address = '127.0.0.1'
        self.port = 9200
        self.url = None
        self.session = requests.Session()
        self.session.mount(
            'http://',
            requests.adapters.HTTPAdapter(max_retries=self.max_retries)
        )
        self.session.mount(
            'https://',
            requests.adapters.HTTPAdapter(max_retries=self.max_retries)
        )

    def config_callback(self, conf):
        super(ElasticsearchBase, self).config_callback(conf)

        for node in conf.children:
            if node.key == 'Address':
                self.address = node.values[0]
            if node.key == 'Port':
                self.port = node.values[0]
            if node.key == 'Protocol':
                self.protocol = node.values[0]

        self.url = "{protocol}://{address}:{port}/".format(
            **{
                'protocol': self.protocol,
                'address': self.address,
                'port': int(self.port),
            })

    def query_api(self, resource):
        url = "{}{}".format(self.url, resource)
        try:
            r = self.session.get(url, timeout=self.timeout)
        except Exception as e:
            msg = "Got exception for '{}': {}".format(url, e)
            raise base.CheckException(msg)

        if r.status_code != 200:
            msg = "{} responded with code {}".format(url, r.status_code)
            raise base.CheckException(msg)

        return r.json()
