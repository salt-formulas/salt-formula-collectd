#!/usr/bin/python
#
# Copyright 2017 Mirantis, Inc.
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

if __name__ == '__main__':
    import collectd_fake as collectd
else:
    import collectd
import re
import requests

import collectd_base as base


NAME = 'calico_felix'
# Default sampling interval
INTERVAL = 60


class CalicoFelixPlugin(base.Base):

    def __init__(self, *args, **kwargs):
        super(CalicoFelixPlugin, self).__init__(*args, **kwargs)
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
        self.url = None

    def config_callback(self, config):
        super(CalicoFelixPlugin, self).config_callback(config)
        for node in config.children:
            self.logger.debug("Got config request for '{}': {}".format(
                node.key.lower(), node.values[0])
            )
            if node.key.lower() == "url":
                self.url = node.values[0]

    def itermetrics(self):
        if self.url:
            self.logger.debug("Requesting URL {}".format(
                self.url)
            )
            try:
                r = self.session.get(self.url, timeout=self.timeout)
            except Exception as e:
                msg = "Got exception for '{}': {}".format(self.url, e)
                raise base.CheckException(msg)

            if r.status_code != 200:
                self.logger.error(
                    ("{} responded with code {} "
                     "").format(self.url,
                                r.status_code))
                raise base.CheckException(
                    "Failed to gather Calico Felix metrics ({})".format(
                        r.status_code
                    )
                )
            self.logger.debug(
                "Got response from {}: '{}'"
                "".format(self.url, r.text))
            # Example payload:
            # # HELP felix_active_local_endpoints Number
            # # of active endpoints on this host.
            # # TYPE felix_active_local_endpoints gauge
            # felix_active_local_endpoints 1
            # # HELP felix_iptables_chains Number of active iptables chains.
            # # TYPE felix_iptables_chains gauge
            # felix_iptables_chains{ip_version="4",table="filter"} 14
            # felix_iptables_chains{ip_version="4",table="nat"} 6
            # felix_iptables_chains{ip_version="4",table="raw"} 6
            # felix_iptables_chains{ip_version="6",table="filter"} 14
            # felix_iptables_chains{ip_version="6",table="nat"} 6
            # felix_iptables_chains{ip_version="6",table="raw"} 6
            # # HELP go_goroutines Number of goroutines that currently exist.
            # # TYPE go_goroutineqs gauge
            # go_goroutines 39
            for l in r.text.split('\n'):
                # Line is empty or is a comment
                if not l or l.startswith('#'):
                    continue

                (name, rval) = l.split()
                self.logger.debug(
                    "Got val for {}: '{}'".format(name, rval))
                # For some metrics, remove the existing felix prefix
                # to ensure homogeneity
                if name.startswith('felix_'):
                    name = name.replace('felix_', '', 1)
                # Initialization of returned metric
                ret_metric = {
                    'values': rval
                }
                # Metric can have implicit dimensions. For example:
                # felix_iptables_rules{ip_version="4",table="filter"}
                m = re.search(
                    '^(?P<name>[^{]+)(?:{(?P<dimensions>.[^}]+)})?$',
                    name)
                if not m:
                    self.logger.error(
                        "Error parsing metric name {}".format(
                            name))
                    continue

                if m.group('dimensions'):
                    name = m.group('name')
                    meta = {}
                    for d in m.group('dimensions').split(','):
                        (k, v) = d.split('=')
                        meta[k] = v.strip('"')
                    if len(meta) > 0:
                        ret_metric['meta'] = meta
                ret_metric['type_instance'] = m.group('name')
                yield ret_metric


plugin = CalicoFelixPlugin(collectd)


def config_callback(conf):
    plugin.config_callback(conf)


def notification_callback(notification):
    plugin.notification_callback(notification)


def read_callback():
    plugin.conditional_read_callback()

if __name__ == '__main__':
    collectd.load_configuration(plugin)
    plugin.read_callback()
else:
    collectd.register_config(config_callback)
    collectd.register_notification(notification_callback)
    collectd.register_read(read_callback, INTERVAL)
