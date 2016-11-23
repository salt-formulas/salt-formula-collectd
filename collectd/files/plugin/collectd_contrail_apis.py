#!/usr/bin/python
#
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
#

import collectd
import requests
import xml.dom.minidom
import xml

import collectd_base as base


NAME = 'contrail'
# Default sampling interval
INTERVAL = 60


def check_state(item, state):
    return item.getElementsByTagName(
        "state")[0].childNodes[0].toxml() == state


class ContrailApiPlugin(base.Base):

    def __init__(self, *args, **kwargs):
        super(ContrailApiPlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME
        self.session = requests.Session()
        self.session.mount(
            'http://',
            requests.adapters.HTTPAdapter(max_retries=self.max_retries)
        )
        self.session.mount(
            'https://',
            requests.adapters.HTTPAdapter(max_retries=self.max_retries)
        )
        self.urls = {}
        self.xml_element = {}
        self.result_type = {}
        self.state = {}

    def config_callback(self, config):
        super(ContrailApiPlugin, self).config_callback(config)
        for node in config.children:
            self.logger.debug("Got config request for '{}': {} {}".format(
                node.key.lower(), node.values[0], node.values[1])
            )
            if node.key.lower() == "url":
                self.urls[node.values[0]] = node.values[1]
            elif node.key.lower() == 'xml_element':
                self.xml_element[node.values[0]] = node.values[1]
            elif node.key.lower() == 'result_type':
                self.result_type[node.values[0]] = node.values[1]
            elif node.key.lower() == 'state':
                self.state[node.values[0]] = node.values[1]

    def itermetrics(self):
        for name, url in self.urls.items():
            self.logger.debug("Requesting {} URL {}".format(
                name, url)
            )
            try:
                r = self.session.get(url, timeout=self.timeout)
            except Exception as e:
                msg = "Got exception for '{}': {}".format(name, e)
                raise base.CheckException(msg)
            else:
                if r.status_code != 200:
                    self.logger.error(
                        ("{} ({}) responded with code {} "
                         "").format(name, url,
                                    r.status_code))
                    yield {'type_instance': name, 'values': self.FAIL}
                else:
                    try:
                        self.logger.debug(
                            "Got response from {}: '{}'"
                            "".format(url, r.text))
                        px = xml.dom.minidom.parseString(r.text)
                        itemlist = px.getElementsByTagName(
                            self.xml_element[name]
                        )
                        if name not in self.result_type:
                            count = 0
                            state = self.state.get('name')
                            for i in itemlist:
                                if state is None or check_state(i, state):
                                    count = count + 1
                            self.logger.debug(
                                "Got count for {}: '{}'".format(name, count))
                            yield {'type_instance': name, 'values': count}
                        else:
                            rval = itemlist[0].getElementsByTagName(
                                self.result_type[name]
                            )[0].childNodes[0].toxml()
                        self.logger.debug(
                            "Got val for {}: '{}'".format(name, rval))
                        yield {'type_instance': name, 'values': rval}
                    except Exception as e:
                        msg = ("Got exception while parsing "
                               "response for '{}': {}").format(name, e)
                        raise base.CheckException(msg)


plugin = ContrailApiPlugin(collectd)


def config_callback(conf):
    plugin.config_callback(conf)


def notification_callback(notification):
    plugin.notification_callback(notification)


def read_callback():
    plugin.conditional_read_callback()

collectd.register_config(config_callback)
collectd.register_notification(notification_callback)
collectd.register_read(read_callback, INTERVAL)
