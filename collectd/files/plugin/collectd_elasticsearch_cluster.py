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

import collectd_elasticsearch_base as base

NAME = 'elasticsearch_cluster'
HEALTH_MAP = {
    'green': 1,
    'yellow': 2,
    'red': 3,
}
METRICS = ['number_of_nodes', 'active_primary_shards', 'active_primary_shards',
           'active_shards', 'relocating_shards', 'unassigned_shards',
           'number_of_pending_tasks', 'initializing_shards']


class ElasticsearchClusterHealthPlugin(base.ElasticsearchBase):
    def __init__(self, *args, **kwargs):
        super(ElasticsearchClusterHealthPlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME

    def itermetrics(self):
        data = self.query_api('_cluster/health')
        self.logger.debug("Got response from Elasticsearch: '%s'" % data)

        yield {
            'type_instance': 'health',
            'values': HEALTH_MAP[data['status']],
            'meta': {'discard_hostname': True}
        }

        for metric in METRICS:
            value = data.get(metric)
            if value is None:
                # Depending on the Elasticsearch version, not all metrics are
                # available
                self.logger.info("Couldn't find {} metric".format(metric))
                continue
            yield {
                'type_instance': metric,
                'values': value,
                'meta': {'discard_hostname': True}
            }

plugin = ElasticsearchClusterHealthPlugin(collectd, local_check=False)


def config_callback(conf):
    plugin.config_callback(conf)


def read_callback():
    plugin.read_callback()

if __name__ == '__main__':
    collectd.load_configuration(plugin)
    plugin.read_callback()
else:
    collectd.register_config(config_callback)
    collectd.register_read(read_callback)
