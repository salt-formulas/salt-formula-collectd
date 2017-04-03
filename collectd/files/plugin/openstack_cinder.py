#!/usr/bin/python
# Copyright 2015 Mirantis, Inc.
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
# Collectd plugin for getting statistics from Cinder
if __name__ == '__main__':
    import collectd_fake as collectd
else:
    import collectd

import collectd_openstack as openstack

PLUGIN_NAME = 'openstack_cinder'
INTERVAL = openstack.INTERVAL
volumes_statuses = ('creating', 'available', 'attaching',
                    'in-use', 'deleting', 'error',
                    'error-deleting', 'backing-up',
                    'restoring-backup', 'error_restoring',
                    'error_extending')
snapshots_statuses = ('creating', 'available', 'deleting',
                      'error', 'error_deleting')


class CinderStatsPlugin(openstack.CollectdPlugin):
    """ Class to report the statistics on Cinder objects.

        number of volumes broken down by state
        total size of volumes usable and in error state
    """

    def __init__(self, *args, **kwargs):
        super(CinderStatsPlugin, self).__init__(*args, **kwargs)
        self.plugin = PLUGIN_NAME
        self.interval = INTERVAL
        self.pagination_limit = 500

    @staticmethod
    def gen_metric(name, nb, state):
        return {
            'plugin_instance': name,
            'values': nb,
            'meta': {
                'state': state,
                'discard_hostname': True,
            }
        }

    def itermetrics(self):

        def groupby(d):
            return d.get('status', 'unknown').lower()

        def count_size_bytes(d):
            return d.get('size', 0) * 10 ** 9

        vols_details = self.get_objects('cinderv2', 'volumes',
                                        params={'all_tenants': 1},
                                        detail=True)
        vols_status = self.count_objects_group_by(vols_details,
                                                  group_by_func=groupby)
        for status in volumes_statuses:
            nb = vols_status.get(status, 0)
            yield CinderStatsPlugin.gen_metric('volumes',
                                               nb,
                                               status)

        vols_sizes = self.count_objects_group_by(vols_details,
                                                 group_by_func=groupby,
                                                 count_func=count_size_bytes)
        for status in volumes_statuses:
            nb = vols_sizes.get(status, 0)
            yield CinderStatsPlugin.gen_metric('volumes_size',
                                               nb,
                                               status)

        snaps_details = self.get_objects('cinderv2', 'snapshots',
                                         params={'all_tenants': 1})
        snaps_status = self.count_objects_group_by(snaps_details,
                                                   group_by_func=groupby)
        for status in snapshots_statuses:
            nb = snaps_status.get(status, 0)
            yield CinderStatsPlugin.gen_metric('snapshots',
                                               nb,
                                               status)

        snaps_sizes = self.count_objects_group_by(snaps_details,
                                                  group_by_func=groupby,
                                                  count_func=count_size_bytes)
        for status in snapshots_statuses:
            nb = snaps_sizes.get(status, 0)
            yield CinderStatsPlugin.gen_metric('snapshots_size',
                                               nb,
                                               status)


plugin = CinderStatsPlugin(collectd, PLUGIN_NAME, disable_check_metric=True)


def config_callback(conf):
    plugin.config_callback(conf)


def notification_callback(notification):
    plugin.notification_callback(notification)


def read_callback():
    plugin.conditional_read_callback()


if __name__ == '__main__':
    import time
    collectd.load_configuration(plugin)
    plugin.read_callback()
    collectd.info('Sleeping for {}s'.format(INTERVAL))
    time.sleep(INTERVAL)
    plugin.read_callback()
    plugin.shutdown_callback()
else:
    collectd.register_config(config_callback)
    collectd.register_notification(notification_callback)
    collectd.register_read(read_callback, INTERVAL)
