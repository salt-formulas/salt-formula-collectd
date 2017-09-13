#!/usr/bin/python
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

if __name__ == '__main__':
    import collectd_fake as collectd
else:
    import collectd
import os
import requests

import collectd_base as base

NAME = 'bond_status'


class BondStatusPlugin(base.Base):
    def __init__(self, *args, **kwargs):
        super(BondStatusPlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME
        self.bonds = []
        self.bond_dir = '/proc/net/bonding/'

    def config_callback(self, conf):
        super(BondStatusPlugin, self).config_callback(conf)

        for node in conf.children:
            if node.key == 'Bond':
                self.bonds.append(node.values[0])

    def itermetrics(self):
        if "all" in self.bonds or len(self.bonds) == 0:
            try:
                self.bonds = os.listdir(self.bond_dir)
            except OSError as e:
                msg = "Error listing all bonds in {}".format(self.bond_dir)
                raise base.CheckException(msg)

        for bond in self.bonds:
            try:
                with open(self.bond_dir + bond, 'r') as fp:
                    bond_info = fp.readlines()
            except IOError as e:
                msg = "Error reading bond info for {}".format(bond)
                self.logger.error(msg)
                continue

            links_total = 0
            links_down = 0
            skip_first_mii_status = True
            for line in bond_info:
                if line.startswith("MII Status:"):
                    # First occurance of "MII Status" is for the bond as a
                    # whole, but we only want individual links.
                    if skip_first_mii_status:
                        skip_first_mii_status = False
                        continue

                    status = line[12:]
                    if status == "down":
                        links_down += 1
                    links_total += 1

            yield {
                'type': 'links',
                'type_instance': 'total',
                'values': [links_total],
                'meta': {'interface': bond}
            }
            yield {
                'type': 'links',
                'type_instance': 'down',
                'values': [links_down],
                'meta': {'interface': bond}
            }


plugin = BondStatusPlugin(collectd)


def config_callback(conf):
    plugin.config_callback(conf)


def read_callback():
    plugin.read_callback()


if __name__ == '__main__':
    collectd.load_configuration(plugin)
    plugin.bonds = ["bond0"]
    plugin.read_callback()
else:
    collectd.register_config(config_callback)
    collectd.register_read(read_callback)
