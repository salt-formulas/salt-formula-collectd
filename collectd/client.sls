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

{%- for service_name, service in pillar.items() %}
{%- if service.get('_support', {}).get('collectd', {}).get('enabled', False) %}

{%- set grains_fragment_file = service_name+'/meta/collectd.yml' %}
{%- macro load_grains_file() %}{% include grains_fragment_file ignore missing %}{% endmacro %}
{%- set grains_yaml = load_grains_file()|load_yaml %}

{%- if grains_yaml is mapping %}
{%- set service_grains = salt['grains.filter_by']({'default': service_grains}, merge={'collectd': grains_yaml}) %}
{%- endif %}

{%- endif %}
{%- endfor %}

collectd_client_grain:
  file.managed:
  - name: /etc/salt/grains.d/collectd
  - source: salt://collectd/files/collectd.grain
  - template: jinja
  - user: root
  - mode: 600
  - defaults:
    service_grains: {{ service_grains|yaml }}
  - require:
    - pkg: collectd_client_packages
    - file: collectd_client_grains_dir

collectd_client_grain_validity_check:
  cmd.wait:
  - name: python -c "import yaml; stream = file('/etc/salt/grains.d/collectd', 'r'); yaml.load(stream); stream.close()"
  - require:
    - pkg: collectd_client_packages
  - watch:
    - file: collectd_client_grain

{%- set plugins = service_grains.collectd.local_plugin %}
{%- include "collectd/_service.sls" %}

{%- endif %}
