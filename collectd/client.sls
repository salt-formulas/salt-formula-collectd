{%- from "collectd/map.jinja" import client with context %}
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

{%- set service_grains = {'collectd': {'remote_plugin': {}, 'local_plugin': {}}} %}

{%- for service_name in pillar.keys()|sort %}
  {%- set service = salt['pillar.items'](service_name)[service_name] %}
  {%- if service.get('_support', {}).get('collectd', {}).get('enabled', False) %}
    {%- set grains_fragment_file = service_name+'/meta/collectd.yml' %}
    {%- macro load_grains_file() %}{% include grains_fragment_file ignore missing %}{% endmacro %}
    {%- set grains_yaml = load_grains_file()|load_yaml %}

    {%- if grains_yaml is mapping %}
      {%- set service_grains = salt['grains.filter_by']({'default': service_grains}, merge={'collectd': grains_yaml}) %}
    {%- endif %}
  {%- endif %}
{%- endfor %}

{%- set plugins = service_grains.collectd.get('local_plugin', {}) %}
{%- include "collectd/_service.sls" %}

{%- endif %}
