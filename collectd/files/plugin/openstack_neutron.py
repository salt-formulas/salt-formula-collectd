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
# Collectd plugin for getting resource statistics from Neutron
if __name__ == '__main__':
    import collectd_fake as collectd
else:
    import collectd

import collectd_openstack as openstack

PLUGIN_NAME = 'openstack_neutron'
INTERVAL = openstack.INTERVAL


class NeutronStatsPlugin(openstack.CollectdPlugin):
    """ Class to report the statistics on Neutron objects.

        number of networks broken down by status
        number of subnets
        number of ports broken down by owner and status
        number of routers broken down by status
        number of floating IP addresses broken down by free/associated
    """

    def __init__(self, *args, **kwargs):
        super(NeutronStatsPlugin, self).__init__(*args, **kwargs)
        self.plugin = PLUGIN_NAME
        self.interval = INTERVAL
        self.pagination_limit = 100

    def itermetrics(self):

        def groupby_status(x):
            return x.get('status', 'unknown').lower()

        def groupby_port(x):
            owner = x.get('device_owner', 'none')
            if owner.startswith('network:'):
                owner = owner.replace('network:', '')
            elif owner.startswith('compute:'):
                # The part after 'compute:' is the name of the Nova AZ
                owner = 'compute'
            else:
                owner = 'none'
            status = x.get('status', 'unknown').lower()
            return "%s.%s" % (owner, status)

        def groupby_floating(x):
            return 'associated' if x.get('port_id', None) else None

        # Networks
        networks = self.get_objects('neutron', 'networks', api_version='v2.0',
                                    params={'fields': ['id', 'status']})
        status = self.count_objects_group_by(networks,
                                             group_by_func=groupby_status)
        for s, nb in status.iteritems():
            yield {
                'plugin_instance': 'networks',
                'values': nb,
                'meta': {'state': s, 'discard_hostname': True}
            }
        yield {
            'plugin_instance': 'networks',
            'type_instance': 'total',
            'values': len(networks),
            'meta': {'discard_hostname': True},
        }

        # Subnets
        subnets = self.get_objects('neutron', 'subnets', api_version='v2.0',
                                   params={'fields': ['id']})
        yield {'plugin_instance': 'subnets', 'values': len(subnets),
               'meta': {'discard_hostname': True}}

        # Ports
        ports = self.get_objects('neutron', 'ports', api_version='v2.0',
                                 params={'fields': ['id', 'status',
                                                    'device_owner']})
        status = self.count_objects_group_by(ports,
                                             group_by_func=groupby_port)
        for s, nb in status.iteritems():
            (owner, state) = s.split('.')
            yield {
                'plugin_instance': 'ports',
                'values': nb,
                'meta': {'state': state, 'owner': owner,
                         'discard_hostname': True}
            }
        yield {
            'plugin_instance': 'ports',
            'type_instance': 'total',
            'values': len(ports),
            'meta': {'discard_hostname': True},
        }

        # Routers
        routers = self.get_objects('neutron', 'routers', api_version='v2.0',
                                   params={'fields': ['id', 'status']})
        status = self.count_objects_group_by(routers,
                                             group_by_func=groupby_status)
        for s, nb in status.iteritems():
            yield {
                'plugin_instance': 'routers',
                'values': nb,
                'meta': {'state': s, 'discard_hostname': True}
            }
        yield {
            'plugin_instance': 'routers',
            'type_instance': 'total',
            'values': len(routers),
            'meta': {'discard_hostname': True},
        }

        # Floating IP addresses
        floatingips = self.get_objects('neutron', 'floatingips',
                                       api_version='v2.0',
                                       params={'fields': ['id', 'status',
                                                          'port_id']})
        status = self.count_objects_group_by(floatingips,
                                             group_by_func=groupby_floating)
        for s, nb in status.iteritems():
            yield {
                'plugin_instance': 'floatingips',
                'values': nb,
                'meta': {'state': s, 'discard_hostname': True}
            }
        yield {
            'plugin_instance': 'floatingips',
            'type_instance': 'total',
            'values': len(floatingips),
            'meta': {'discard_hostname': True},
        }


plugin = NeutronStatsPlugin(collectd, PLUGIN_NAME, disable_check_metric=True)


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
