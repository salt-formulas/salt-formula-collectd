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

NAME = 'elasticsearch'


class ElasticsearchNodePlugin(base.ElasticsearchBase):
    def __init__(self, *args, **kwargs):
        super(ElasticsearchNodePlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME
        self._previous = {}

    @staticmethod
    def _metric(name, values, meta=None):
        return {'type_instance': name, 'values': values, 'meta': meta or {}}

    def _get_latency(self, name, count, time):
        cname = '{}_count'.format(name)
        tname = '{}_time'.format(name)
        prev_count = self._previous.get(cname)
        prev_time = self._previous.get(tname)
        self._previous[cname] = count
        self._previous[tname] = time
        if prev_count and prev_time:
            diff_count = count - prev_count
            diff_time = time - prev_time
            return diff_time / diff_count if diff_count > 0 else 0

    def itermetrics(self):
        stats = self.query_api('_nodes/_local/stats').get(
            'nodes', {}).values()[0]
        indices = stats['indices']
        yield self._metric('documents', indices['docs']['count'])
        yield self._metric('documents_deleted', indices['docs']['deleted'])
        yield self._metric(
            'indexing_current', indices['indexing']['index_current'])
        yield self._metric(
            'indexing_failed', indices['indexing']['index_failed'])
        indexing_latency = self._get_latency(
            'indexing', indices['indexing']['index_total'],
            indices['indexing']['index_time_in_millis'])
        if indexing_latency:
            yield self._metric('indexing_latency', indexing_latency)
        yield self._metric('store_size', indices['store']['size_in_bytes'])
        fd_open = 0
        if stats['process']['max_file_descriptors'] > 0:
            fd_open = 100.0 * stats['process']['open_file_descriptors'] \
                / stats['process']['max_file_descriptors']
        yield self._metric('fd_open_percent', fd_open)

        thread_pools = stats['thread_pool']
        for pool in ('bulk', 'flush', 'search', 'index', 'get'):
            yield self._metric('thread_pool_queue',
                               thread_pools[pool]['queue'], {'pool': pool})
            yield self._metric('thread_pool_rejected',
                               thread_pools[pool]['rejected'], {'pool': pool})
            yield self._metric('thread_pool_completed',
                               thread_pools[pool]['completed'], {'pool': pool})
        mem = stats['jvm']['mem']
        yield self._metric('jvm_heap_max', mem['heap_max_in_bytes'])
        yield self._metric('jvm_heap_used_percent', mem['heap_used_percent'])
        yield self._metric('jvm_heap_used', mem['heap_used_in_bytes'])
        for pool, stat in mem['pools'].items():
            yield self._metric(
                'jvm_heap_pool', stat['used_in_bytes'], {'pool': pool})
        gc = stats['jvm']['gc']
        for pool, stat in gc['collectors'].items():
            yield self._metric('jvm_gc_count', stat['collection_count'],
                               {'pool': pool})
            yield self._metric('jvm_gc_time',
                               stat['collection_time_in_millis'],
                               {'pool': pool})

        search = indices['search']
        for phase in ('query', 'fetch'):
            yield self._metric('{}_current'.format(phase),
                               search['{}_current'.format(phase)])
            latency = self._get_latency(
                phase,
                search['{}_total'.format(phase)],
                search['{}_time_in_millis'.format(phase)])
            if latency is not None:
                yield self._metric('{}_latency'.format(phase), latency)
        yield self._metric('query_count', search['query_total'])

        query = indices['query_cache']
        yield self._metric('query_cache_size', query['memory_size_in_bytes'])
        yield self._metric('query_cache_evictions', query['evictions'])

        fielddata = indices['fielddata']
        yield self._metric('fielddata_size', fielddata['memory_size_in_bytes'])
        yield self._metric('fielddata_evictions', fielddata['evictions'])

        for operation in ('merges', 'flush', 'refresh'):
            yield self._metric(operation, indices[operation]['total'])
            latency = self._get_latency(
                operation,
                indices[operation]['total'],
                indices[operation]['total_time_in_millis'])
            if latency is not None:
                yield self._metric('{}_latency'.format(operation), latency)


plugin = ElasticsearchNodePlugin(collectd)


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
