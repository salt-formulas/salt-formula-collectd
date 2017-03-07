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

import collectd_base as base
import requests

NAME = 'http_check'


class HTTPCheckPlugin(base.Base):

    def __init__(self, *args, **kwargs):
        super(HTTPCheckPlugin, self).__init__(*args, **kwargs)
        self.plugin = NAME
        self.urls = {}
        self.expected_codes = {}
        self.expected_contents = {}

        self.timeout = 3
        self.max_retries = 2

        self.interval = base.INTERVAL
        self.polling_interval = base.INTERVAL

        self.sessions = {}
        self._threads = {}

    def shutdown_callback(self):
        for tid, t in self._threads.items():
            if t.is_alive():
                self.logger.info('Waiting for {} thread to finish'.format(tid))
                t.stop()
                t.join()

    def config_callback(self, config):
        super(HTTPCheckPlugin, self).config_callback(config)
        for node in config.children:
            if node.key == "Url":
                self.urls[node.values[0]] = node.values[1]
            elif node.key == 'ExpectedCode':
                self.expected_codes[node.values[0]] = int(node.values[1])
            elif node.key == 'ExpectedContent':
                self.expected_contents[node.values[0]] = node.values[1]

        for name, url in self.urls.items():
            session = requests.Session()
            session.mount(
                'http://',
                requests.adapters.HTTPAdapter(max_retries=self.max_retries)
            )
            if url.startswith('https'):
                session.mount(
                    'https://',
                    requests.adapters.HTTPAdapter(max_retries=self.max_retries)
                )
            self.sessions[name] = session

    def check_url(self, name, url):

        def get():
            try:
                r = self.sessions[name].get(url, timeout=self.timeout)
            except Exception as e:
                self.logger.warning("Got exception for '{}': {}".format(
                    url, e)
                )
                status = self.FAIL
            else:

                expected_code = self.expected_codes.get(name, 200)
                if r.status_code != expected_code:
                    self.logger.warning(
                        ("{} ({}) responded with code {} "
                         "while {} is expected").format(name, url,
                                                        r.status_code,
                                                        expected_code))
                    status = self.FAIL
                else:
                    self.logger.debug(
                        "Got response from {}: '{}'".format(url, r.content))
                    status = self.OK
                    expected_content = self.expected_contents.get(name)
                    if expected_content:
                        if r.content != expected_content:
                            status = self.FAIL
                            self.logger.warning(
                                'Content "{}" does not match "{}"'.format(
                                    r.content[0:30], expected_content
                                ))
            return [status]

        if url not in self._threads:
            t = base.AsyncPoller(self.collectd,
                                 get,
                                 self.polling_interval,
                                 url)
            t.start()
            self._threads[url] = t

        t = self._threads[url]
        if not t.is_alive():
            self.logger.warning("Unexpected end of the thread {}".format(
                t.name))
            del self._threads[url]
            return []

        return t.results

    def itermetrics(self):
        for name, url in self.urls.items():
            r = self.check_url(name, url)
            if r:
                yield {'type_instance': name, 'values': r}


plugin = HTTPCheckPlugin(collectd, disable_check_metric=True)


def config_callback(conf):
    plugin.config_callback(conf)


def notification_callback(notification):
    plugin.notification_callback(notification)


def read_callback():
    plugin.conditional_read_callback()


if __name__ == '__main__':
    plugin.urls['google_ok'] = 'https://www.google.com'
    plugin.urls['google_fail'] = 'https://www.google.com/not_found'
    plugin.urls['no_network'] = 'https://127.0.0.2:999'
    plugin.expected_codes['google_ok'] = 200
    plugin.expected_codes['google_fail'] = 200
    collectd.load_configuration(plugin)
    plugin.read_callback()
    import time
    time.sleep(base.INTERVAL)
    plugin.read_callback()
    plugin.shutdown_callback()
else:
    collectd.register_config(config_callback)
    collectd.register_notification(notification_callback)
    collectd.register_read(read_callback, base.INTERVAL)
