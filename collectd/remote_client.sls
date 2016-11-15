{%- from "collectd/map.jinja" import remote_client with context %}
{%- if remote_client.enabled %}

include:
- collectd._common

{# Collect all remote plugins from Salt mine #}
{%- set plugins = {} %}
{%- for node_name, node_grains in salt['mine.get']('*', 'grains.items').iteritems() %}
{%- if node_grains.collectd is defined %}
{%- set plugins = salt['grains.filter_by']({'default': plugins}, merge=node_grains.collectd.get('remote_plugin', {})) %}
{%- endif %}
{%- endfor %}

{%- set client = remote_client %}
{%- include "collectd/_service.sls" %}

{{ remote_client.service }}_service_file:
  file.managed:
{%- if grains.get('init', None) == 'systemd' %}
  - name: /etc/systemd/system/{{ remote_client.service }}.service
  - source: salt://collectd/files/collectd_systemd.service
{%- else %}
  - name: /etc/init/{{ remote_client.service }}
  - source: salt://collectd/files/collectd_upstart.service
{%- endif %}
  - user: root
  - mode: 644
  - defaults:
    service_name: {{ remote_client.service }}
    config_file: {{ remote_client.config_file }}
  - template: jinja
  - require_in:
    - service: {{ remote_client.service }}_service

{%- endif %}
