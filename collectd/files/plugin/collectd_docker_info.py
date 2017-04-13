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

import collectd_base as base

NAME = 'docker'
DOCKER_BINARY = '/usr/bin/docker'
INTERVAL = 60


class DockerInfoPlugin(base.Base):

    def __init__(self, *args, **kwargs):
        super(DockerInfoPlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME
        self.timeout = 3

    def itermetrics(self):
        cmd = [DOCKER_BINARY, 'info', '-f', "{{ json .}}"]
        (retcode, out, err) = self.execute(cmd, shell=False, log_error=True)
        if retcode != 0:
            raise base.CheckException("{} : {}".format(DOCKER_BINARY, err))
        try:
            infos = json.loads(out)
        except ValueError as e:
            raise base.CheckException("{}: document: '{}'".format(e, out))
        else:
            yield {'values': infos.get('Containers', 0),
                   'plugin_instance': 'containers_total',
                   }
            yield {'values': infos.get('ContainersPaused', 0),
                   'plugin_instance': 'containers',
                   'meta': {'status': 'paused'},
                   }
            yield {'values': infos.get('ContainersRunning', 0),
                   'plugin_instance': 'containers',
                   'meta': {'status': 'running'},
                   }
            yield {'values': infos.get('ContainersStopped', 0),
                   'plugin_instance': 'containers',
                   'meta': {'status': 'stopped'},
                   }
            yield {'values': infos.get('Images', 0),
                   'plugin_instance': 'images',
                   }

plugin = DockerInfoPlugin(collectd)


def init_callback():
    plugin.restore_sigchld()


def config_callback(conf):
    plugin.config_callback(conf)


def read_callback():
    plugin.read_callback()

if __name__ == '__main__':
    collectd.load_configuration(plugin)
    plugin.read_callback()
    plugin.shutdown_callback()
else:
    collectd.register_init(init_callback)
    collectd.register_config(config_callback)
    collectd.register_read(read_callback, INTERVAL)
