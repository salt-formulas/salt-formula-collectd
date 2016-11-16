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

import collectd
import re

import collectd_base as base

NAME = 'glusterfs'
GLUSTER_BINARY = '/usr/sbin/gluster'

peer_re = re.compile(r'^Hostname: (?P<peer>.+)$', re.MULTILINE)
state_re = re.compile(r'^State: (?P<state>.+)$', re.MULTILINE)


class GlusterfsPlugin(base.Base):

    def __init__(self, *args, **kwargs):
        super(GlusterfsPlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME

    def itermetrics(self):
        # Collect peers' status
        out, err = self.execute([GLUSTER_BINARY, 'peer', 'status'],
                                shell=False)
        if not out:
            raise base.CheckException("Failed to execute gluster")

        total = 0
        total_by_state = {
            'up': 0,
            'down': 0
        }

        for line in out.split('\n\n'):
            peer_m = peer_re.search(line)
            state_m = state_re.search(line)
            if peer_m and state_m:
                total += 1
                if state_m.group('state') == 'Peer in Cluster (Connected)':
                    v = 1
                    total_by_state['up'] += 1
                else:
                    v = 0
                    total_by_state['down'] += 1
                yield {
                    'type_instance': 'peer',
                    'values': v,
                    'meta': {
                        'peer': peer_m.group('peer')
                    }
                }

        for state, count in total_by_state.items():
            yield {
                'type_instance': 'peers_count',
                'values': count,
                'meta': {
                    'state': state
                }
            }
            yield {
                'type_instance': 'peers_percent',
                'values': 100.0 * count / total,
                'meta': {
                    'state': state
                }
            }


plugin = GlusterfsPlugin(collectd)


def init_callback():
    plugin.restore_sigchld()


def config_callback(conf):
    plugin.config_callback(conf)


def read_callback():
    plugin.read_callback()

collectd.register_init(init_callback)
collectd.register_config(config_callback)
collectd.register_read(read_callback)
