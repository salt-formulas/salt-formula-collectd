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
import json
import time

import collectd_base as base

NAME = 'k8s'
KUBECTL_BINARY = '/usr/bin/kubectl'
INTERVAL = 30


class K8sPlugin(base.Base):

    def __init__(self, *args, **kwargs):
        super(K8sPlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME
        self._threads = {}
        self.polling_interval = INTERVAL
        self.resources = []
        self._get_nodes = False

    def shutdown_callback(self):
        for tid, t in self._threads.items():
            if t.is_alive():
                self.logger.info('Waiting for {} thread to finish'.format(tid))
                t.stop()
                t.join()

    def config_callback(self, config):
        super(K8sPlugin, self).config_callback(config)
        for node in config.children:
            if node.key == 'PollingInterval':
                self.polling_interval = int(node.values[0])
            elif node.key == 'GetNodes':
                if node.values[0].lower() == 'true':
                    self._get_nodes = True

    def kubectl_get(self, resource):

        def kubectl_poller():
            cmd = [KUBECTL_BINARY, 'get', '-o', 'json', resource]
            data = self.execute_to_json(cmd, shell=False, log_error=True)
            return data.get('items', [])

        if resource not in self._threads:
            t = base.AsyncPoller(self.collectd,
                                 kubectl_poller,
                                 self.polling_interval,
                                 resource)
            t.start()
            self._threads[resource] = t

        t = self._threads[resource]
        if not t.is_alive():
            self.logger.warning("Unexpected end of the thread {}".format(
                t.name))
            del self._threads[resource]
            return []

        return t.results

    @staticmethod
    def _check_conditions(conditions, _type):
        return all(
            [cnd.get('status') == 'True' for cnd in conditions
             if cnd.get('type') == _type]
        )

    def _iter_node_metrics(self, nodes):
        if nodes:
            total, total_ready = (0, 0)
            for node in nodes:
                self.logger.debug(node.get('metadata', {}).get('name'))
                conditions = node.get(
                    'status', {}).get('conditions', [])
                if self._check_conditions(conditions, _type='Ready'):
                    total_ready += 1
                total += 1
            yield {'values': total_ready,
                   'plugin_instance': 'nodes',
                   'meta': {'status': 'ready'},
                   }
            yield {'values': total - total_ready,
                   'plugin_instance': 'nodes',
                   'meta': {'status': 'not_ready'},
                   }
            yield {'values': total,
                   'plugin_instance': 'nodes_total'
                   }

    def itermetrics(self):
        if self._get_nodes:
            items = self.kubectl_get('nodes')
            return self._iter_node_metrics(items)


plugin = K8sPlugin(collectd, disable_check_metric=True)


def init_callback():
    plugin.restore_sigchld()


def config_callback(conf):
    plugin.config_callback(conf)


def read_callback():
    plugin.read_callback()

if __name__ == '__main__':
    collectd.load_configuration(plugin)
    plugin._get_nodes = True
    plugin.read_callback()
    collectd.info('Sleeping for {}s'.format(INTERVAL))
    time.sleep(INTERVAL)
    plugin.read_callback()
    plugin.shutdown_callback()
else:
    collectd.register_init(init_callback)
    collectd.register_config(config_callback)
    collectd.register_read(read_callback, INTERVAL)



