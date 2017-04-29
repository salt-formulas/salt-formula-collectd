{%- from "collectd/map.jinja" import client, service_grains with context %}
{%- if client.enabled %}

include:
- collectd._common

/etc/collectd:
  file.directory:
  - user: root
  - mode: 750
  - makedirs: true
  - require:
    - pkg: collectd_client_packages

{%- set plugins = service_grains.collectd.local_plugin %}
{%- include "collectd/_service.sls" %}

{%- endif %}
