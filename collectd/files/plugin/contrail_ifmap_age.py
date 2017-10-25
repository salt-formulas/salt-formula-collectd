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

import contextlib
import time
import urllib2
from xml.etree import ElementTree
if __name__ == '__main__':
    import collectd_fake as collectd
else:
    import collectd
import collectd_base as base


NAME = 'contrail_ifmap_age'


class ContrailIfmapTraceBufPlugin(base.Base):
    """
    This plugin checks age of last entry in IF-MAP trace buffer.
    The idea is to collect the ages of last entry in IF-MAP trace buffer over
    multiple nodes and check statistical properties of the set to
    determine incorrectly functioning irond IF-MAP server.
    """
    def __init__(self, *args, **kwargs):
        super(ContrailIfmapTraceBufPlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME
        self.port = 8083
        self.host = 'localhost'
        self.protocol = 'http'

    def config_callback(self, conf):
        super(ContrailIfmapTraceBufPlugin, self).config_callback(conf)

        for node in conf.children:
            if node.key == 'port':
                self.port = node.values[0]
            elif node.key == 'host':
                self.host = node.values[0]
            elif node.key == 'protocol':
                self.protocol = node.values[0]

    def itermetrics(self):
        url = "{}://{}:{}/Snh_SandeshTraceRequest?x=IFMapTraceBuf".format(
            self.protocol, self.host, self.port)
        try:
            with contextlib.closing(urllib2.urlopen(url, None, 5)) as response:
                rcode = response.getcode()
                if rcode == 200:
                    tree = ElementTree.fromstring(response.read())
                    items = [(int(exc.text.split()[0]), exc.text)
                             for exc in tree.iter('element')]
                    if len(items) > 0:
                        last_entry = sorted(items, reverse=True)[0][0]
                        now = time.time()
                        age = now - last_entry / 1000000.0
                        msg = "The last entry is {} seconds old."
                        self.logger.info(msg.format(age))
                        yield {'values': age, 'type': 'gauge'}
                    else:
                        msg = "No entry in IF-MAP trace buffer!"
                        raise base.CheckException(msg)
                else:
                    msg = "Unexpected code {} while contacting {}"
                    raise base.CheckException(msg.format(rcode, url))
        except urllib2.URLError as exc:
            msg = "Cannot retrieve last entry from IF-MAP trace buffer: {}!"
            raise base.CheckException(msg.format(str(exc)))


plugin = ContrailIfmapTraceBufPlugin(collectd)


def config_callback(conf):
    """
        Collectd callback for configuration
    """
    plugin.config_callback(conf)


def read_callback():
    """
        Collectd callback for reading metrics
    """
    plugin.read_callback()


if __name__ == '__main__':
    collectd.load_configuration(plugin)
    plugin.read_callback()
else:
    collectd.register_config(config_callback)
    collectd.register_read(read_callback)
