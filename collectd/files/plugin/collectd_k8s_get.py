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

if __name__ == '__main__':
    import collectd_fake as collectd
else:
    import collectd

import collectd_base as base
import requests

NAME = 'k8s'
INTERVAL = 30


class K8sGetPlugin(base.Base):
    def __init__(self, *args, **kwargs):
        super(K8sGetPlugin, self).__init__(*args, **kwargs)
        self._threads = {}
        self.session = None
        self.plugin = NAME
        self.endpoint = None
        self.verify = False
        self.client_key = None
        self.client_certs = None

        self.interval = INTERVAL
        self.polling_interval = INTERVAL

        self.timeout = 3
        self.max_retries = 2

    def shutdown_callback(self):
        for tid, t in self._threads.items():
            if t.is_alive():
                self.logger.info('Waiting for {} thread to finish'.format(tid))
                t.stop()
                t.join()

    def config_callback(self, config):
        super(K8sGetPlugin, self).config_callback(config)
        for node in config.children:
            if node.key == "Endpoint":
                self.endpoint = node.values[0]
            elif node.key == 'Verify':
                if node.values[0].lower() == 'false':
                    self.verify = False
            elif node.key == 'ClientCert':
                self.client_cert = node.values[0]
            elif node.key == 'ClientKey':
                self.client_key = node.values[0]

        session = requests.Session()
        if self.endpoint.startswith('https'):
            session.mount(
                'https://',
                requests.adapters.HTTPAdapter(max_retries=self.max_retries)
            )
        else:
            session.mount(
                'http://',
                requests.adapters.HTTPAdapter(max_retries=self.max_retries)
            )

        session.verify = self.verify
        if self.client_cert and self.client_key:
            session.cert = (self.client_cert, self.client_key)
        elif self.client_cert:
            session.cert = self.client_cert

        self.session = session

    def get(self, url):

        def get():
            try:
                r = self.session.get(url, timeout=self.timeout)
                data = r.json()
            except Exception as e:
                self.logger.warning("Got exception for '{}': {}".format(
                    url, e)
                )
                raise base.CheckException('Fail to get {}'.self(url))

            else:

                if r.status_code != 200:
                    msg = ("{} responded with code {} "
                           "while 200 is expected").format(url, r.status_code)
                    self.logger.warning(msg)
                    raise base.CheckException(msg)
            return data.get('items', [])

        if url not in self._threads:
            t = base.AsyncPoller(self.collectd,
                                 get,
                                 self.polling_interval,
                                 url)
            t.start()
            self._threads[url] = t

        t = self._threads[url]
        if not t.is_alive():
            self.logger.warning("Unexpected end of the thread {}".format(
                t.name))
            del self._threads[url]
            return []

        return t.results

    @staticmethod
    def _check_conditions(conditions, _type):
        return all(
            [cnd.get('status') == 'True' for cnd in conditions
             if cnd.get('type') == _type]
        )

    def itermetrics(self):
        nodes = self.get('{}/api/v1/nodes'.format(self.endpoint))
        total, total_ready = (0, 0)
        for node in nodes:
            self.logger.debug(node.get('metadata', {}).get('name'))
            conditions = node.get(
                'status', {}).get('conditions', [])
            if self._check_conditions(conditions, _type='Ready'):
                total_ready += 1
            total += 1
        if total > 0:
            yield {'values': (100.0 * (total - total_ready)) / total,
                   'plugin_instance': 'nodes_percent',
                   'meta': {'status': 'not_ready',
                            'discard_hostname': True},
                   }

        yield {'values': total_ready,
               'plugin_instance': 'nodes',
               'meta': {'status': 'ready', 'discard_hostname': True},
               }
        yield {'values': total - total_ready,
               'plugin_instance': 'nodes',
               'meta': {'status': 'not_ready', 'discard_hostname': True},
               }
        yield {'values': total,
               'plugin_instance': 'nodes_total',
               'meta': {'discard_hostname': True}
               }


plugin = K8sGetPlugin(collectd, disable_check_metric=True)


def config_callback(conf):
    plugin.config_callback(conf)


def notification_callback(notification):
    plugin.notification_callback(notification)


def read_callback():
    plugin.conditional_read_callback()


if __name__ == '__main__':
    plugin.endpoint = 'https://172.16.10.253:443'
    plugin.verify = False
    plugin.client_key = '/etc/kubernetes/ssl/kubelet-client.key'
    plugin.client_cert = '/etc/kubernetes/ssl/kubelet-client.crt'

    collectd.load_configuration(plugin)
    plugin.read_callback()
    import time
    time.sleep(base.INTERVAL)
    plugin.read_callback()
    plugin.shutdown_callback()
else:
    collectd.register_config(config_callback)
    collectd.register_notification(notification_callback)
    collectd.register_read(read_callback, base.INTERVAL)

