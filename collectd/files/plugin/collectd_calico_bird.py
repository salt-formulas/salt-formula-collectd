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
import re
import time

import collectd_base as base

NAME = 'calico_bird'
# Default sampling interval
INTERVAL = 60
BIRDCL_BINARY = '/usr/bin/birdcl'

re_memory = re.compile(r"(?P<attribute>.*):\s+"
                       r"(?P<quantity>\d+)\s"
                       r"(?P<multiplier>[kMG ])B\s*")

re_protocol = re.compile(r"(?P<name>\S+)\s+"
                         r"(?P<protocol>\S+)\s+"
                         r"(?P<table>\S+)\s+"
                         r"(?P<state>\S+)\s+"
                         r"(?P<since>\d{2}:\d{2}:\d{2})"
                         r"(?P<info>.*)")


def protocol_metric(line):
    re_match = re_protocol.match(line)
    if re_match:
        if re_match.group("protocol") == "BGP":
            return gen_metric(
                'bgp_up', re_match.group('state') == 'up',
                {
                    'bird_protocol_instance': re_match.group('name'),
                }
            )


def memory_metric(line):
    re_match = re_memory.match(line)
    if re_match:
        quantity = int(re_match.group("quantity"))
        for m in " kMG":
            if re_match.group("multiplier") == m:
                break
            quantity *= 1024
        mname = 'memory_' + re_match.group(
            'attribute').lower().replace(' ', '_')
        return gen_metric(
            mname, quantity
        )


def gen_metric(name, val, meta={}):
    ret_metric = {
        'type_instance': name,
        'values': val,
    }
    if meta:
        ret_metric['meta'] = meta
    return ret_metric


class CalicoBirdPlugin(base.Base):

    _checks = {
        'memory': {
            'cmd_args': ['show', 'memory'],
            'func': memory_metric,
        },
        'protocol': {
            'cmd_args': ['show', 'protocols'],
            'func': protocol_metric,
        },
    }

    def __init__(self, *args, **kwargs):
        super(CalicoBirdPlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME
        self._socketfiles = {}

    def config_callback(self, config):
        super(CalicoBirdPlugin, self).config_callback(config)
        for node in config.children:
            m = re.search('^ipv(?P<ip_version>[46])_socket$', node.key.lower())
            if m:
                self._socketfiles[m.group('ip_version')] = node.values[0]

    def _run_birdcl_command(self, sockf, args):
        cmd = [
            BIRDCL_BINARY,
            '-s',
            sockf
        ] + args
        retcode, out, err = self.execute(cmd, shell=False)
        if retcode == 0:
            return out
        msg = "Failed to execute {} '{}'".format(cmd, err)
        raise base.CheckException(msg)

    def itermetrics(self):
        for ipv, sockf in self._socketfiles.items():
            for lcname, lcheck in self._checks.items():
                out = self._run_birdcl_command(sockf, lcheck['cmd_args'])
                for metric in filter(
                        None,
                        [lcheck['func'](line) for line in out.split('\n')]
                ):
                    if not metric.get('meta', False):
                        metric['meta'] = {}
                    metric['meta'].update({'ip_version': ipv})
                    yield metric


plugin = CalicoBirdPlugin(collectd)


def init_callback():
    plugin.restore_sigchld()


def config_callback(conf):
    plugin.config_callback(conf)


def read_callback():
    plugin.read_callback()

if __name__ == '__main__':
    collectd.load_configuration(plugin)
    plugin.read_callback()
    collectd.info('Sleeping for {}s'.format(INTERVAL))
    time.sleep(INTERVAL)
    plugin.read_callback()
else:
    collectd.register_init(init_callback)
    collectd.register_config(config_callback)
    collectd.register_read(read_callback, INTERVAL)
