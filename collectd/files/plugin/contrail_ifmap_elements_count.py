#!/usr/bin/python
#
#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import time
import signal
import string
import subprocess
import sys

plugin_name = "contrail"
plugin_instance = "ifmap-elements-count"
plugin_interval = 90
plugin_type = 'gauge'

command = "/usr/bin/ifmap-view visual visual 2>&1 | wc -l"


def restore_sigchld():
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)


def log_verbose(msg):
    collectd.info('%s plugin [verbose]: %s' % (plugin_name, msg))


def payload():
    ifmap_view_number_of_elements = subprocess.check_output(
        command, shell=True)
    return ifmap_view_number_of_elements


def configure_callback(conf):
    for node in conf.children:
        val = str(node.values[0])


def payload_callback():
    value = payload()
    # log_verbose(
    #     'Sending value: %s.%s=%s' % (
    #         plugin_name, '-'.join([val.plugin, val.type]), value))
    val = collectd.Values(
        plugin=plugin_name,  # metric source
        plugin_instance=plugin_instance,
        type=plugin_type,
        type_instance=plugin_name,
        interval=plugin_interval,
        meta={'0': True},
        values=[value]
    )

    val.dispatch()


if __name__ == '__main__':
    print "Plugin: " + plugin_name
    payload = payload()
    print("%s" % (payload))
    sys.exit(0)
else:
    import collectd

    collectd.register_init(restore_sigchld)
    collectd.register_config(configure_callback)
    collectd.register_read(payload_callback, plugin_interval)
