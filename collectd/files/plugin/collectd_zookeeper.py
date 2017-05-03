#!/usr/bin/env python

#  Licensed to the Apache Software Foundation (ASF) under one or more
#  contributor license agreements.  See the NOTICE file distributed with this
#  work for additional information regarding copyright ownership.  The ASF
#  licenses this file to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""Check Zookeeper Cluster.
"""

if __name__ == '__main__':
    import collectd_fake as collectd
else:
    import collectd
import collectd_base as base
import socket

NAME = 'zookeeper'
# Default sampling interval
INTERVAL = 50

ZK_HOST = "localhost"
ZK_PORT = 2181
COUNTERS = set(["zk_packets_received", "zk_packets_sent"])
# 4-letter cmds and any expected response
RUOK_CMD = "ruok"
IMOK_RESP = "imok"
MNTR_CMD = "mntr"


class ZookeeperServer(object):

    def __init__(self, logger, host='localhost', port='2181', timeout=1):
        self._logger = logger
        self._address = (host, int(port))
        self._timeout = timeout

    def get_stats(self):
        """Get ZooKeeper server stats as a map."""
        stats = {}
        # methods for each four-letter cmd
        stats.update(self._get_health_stat())
        stats.update(self._get_mntr_stats())
        return stats

    def _create_socket(self):
        return socket.socket()

    def _send_cmd(self, cmd):
        """Send a 4letter word command to the server."""
        response = ""
        s = self._create_socket()
        try:
            s.settimeout(self._timeout)
            s.connect(self._address)
            s.send(cmd)
            response = s.recv(2048)
            s.close()
        except socket.timeout:
            self._logger.error(('Service not healthy: '
                                'timed out calling "%s"') % cmd)
        except socket.error, e:
            self._logger.error(('Service not healthy: '
                                'error calling "%s": %s') % (cmd, e))
        return response

    def _get_health_stat(self):
        """Send the 'ruok' 4letter word command and parse the output."""
        response = self._send_cmd(RUOK_CMD)
        return {
            'zk_service_health':
            base.Base.OK if response == IMOK_RESP else base.Base.FAIL
        }

    def _get_mntr_stats(self):
        """Send 'mntr' 4letter word command and parse the output."""
        response = self._send_cmd(MNTR_CMD)
        result = {}
        for line in response.splitlines():
            try:
                key, value = self._parse_line(line)
                if key == 'zk_server_state':
                    result['zk_is_leader'] = int(value != 'follower')
                elif key == 'zk_version':
                    continue
                else:
                    result[key] = value
            except ValueError:
                # Ignore broken lines.
                pass
        return result

    def _parse_line(self, line):
        try:
            key, value = map(str.strip, line.split('\t'))
        except ValueError:
            raise ValueError('Found invalid line: %s' % line)
        if not key:
            raise ValueError('The key is mandatory and should not be empty')
        try:
            value = int(value)
        except (TypeError, ValueError):
            pass
        return key, value


class ZookeeperServerPlugin(base.Base):

    def __init__(self, *args, **kwargs):
        super(ZookeeperServerPlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME
        self._config = {}

    def itermetrics(self):
        """Get stats for local Zookeeper server."""
        host = self._config.get('host', False)
        port = self._config.get('port', False)
        if host and port:
            zk = ZookeeperServer(self.logger, host, port)
            stats = zk.get_stats()
            for k, v in stats.items():
                try:
                    yield {
                        'type': 'counter' if k in COUNTERS else 'gauge',
                        'type_instance': k.replace('zk_', ''),
                        'values': v,
                    }
                except (TypeError, ValueError):
                    self.logger.error(('error dispatching stat; host=%s, '
                                       'key=%s, val=%s') % (host, k, v))
                    pass
        else:
            self.logger.error('Missing host or port')

    def config_callback(self, config):
        """Received configuration information"""
        super(ZookeeperServerPlugin, self).config_callback(config)
        zk_host = ZK_HOST
        zk_port = ZK_PORT
        for node in config.children:
            if node.key == 'Hosts':
                if len(node.values[0]) > 0:
                    zk_host = node.values[0].strip()
                else:
                    self.logger.error(('ERROR: Invalid Hosts string. '
                                       'Using default of %s') % zk_host)
            elif node.key == 'Port':
                if isinstance(node.values[0], float) and node.values[0] > 0:
                    try:
                        zk_port = int(node.values[0])
                    except:
                        self.logger.error(('ERROR: Converting Port number. '
                                           'Using default of %s') % zk_port)
                else:
                    self.logger.error(('ERROR: Invalid Port number. '
                                       'Using default of %s') % zk_port)
            else:
                collectd.warning('zookeeper plugin: Unknown config key: %s.'
                                 % node.key)
                continue
        self._config = {
            'host': zk_host,
            'port': zk_port,
        }
        self.logger.info('Configured with %s.' % self._config)


plugin = ZookeeperServerPlugin(collectd)


def config_callback(conf):
    plugin.config_callback(conf)


def read_callback():
    plugin.read_callback()

if __name__ == '__main__':
    collectd.load_configuration(plugin)
    plugin.read_callback()
else:
    collectd.register_config(config_callback)
    collectd.register_read(read_callback, INTERVAL)
