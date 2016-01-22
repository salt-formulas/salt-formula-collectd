{%- from "collectd/map.jinja" import client with context %}
{%- if client.enabled %}

{%- if grains.os == 'Ubuntu' and (grains.osrelease in ['10.04', '12.04']) %}

collectd_repo:
  pkgrepo.managed:
  - human_name: Collectd
  - ppa: nikicat/collectd
  - file: /etc/apt/sources.list.d/collectd.list
  - require_in:
    - pkg: collectd_client_packages

collectd_amqp_packages:
  pkg.installed:
  - names: 
    - librabbitmq0

{%- elif grains.os == 'Ubuntu' and (grains.osrelease in ['14.04', '16.04']) %}

collectd_amqp_packages:
  pkg.installed:
  - names: 
    - librabbitmq1

{%- endif %}

collectd_client_packages:
  pkg.installed:
  - names: {{ client.pkgs }}

/etc/collectd:
  file.directory:
  - user: root
  - mode: 750
  - makedirs: true
  - require:
    - pkg: collectd_client_packages

{{ client.config_dir }}:
  file.directory:
  - user: root
  - mode: 750
  - makedirs: true
  - clean: true
  - require:
    - pkg: collectd_client_packages

collectd_client_grains_dir:
  file.directory:
  - name: /etc/salt/grains.d
  - mode: 700
  - makedirs: true
  - user: root

{%- set service_grains = {'collectd': {'plugin': {}}} %}
{%- for service_name, service in pillar.items() %}
{%- if service.get('_support', {}).get('collectd', {}).get('enabled', False) %}
{%- set grains_fragment_file = service_name+'/meta/collectd.yml' %}
{%- macro load_grains_file() %}{% include grains_fragment_file %}{% endmacro %}
{%- set grains_yaml = load_grains_file()|load_yaml %}
{%- set _dummy = service_grains.collectd.plugin.update(grains_yaml.plugin) %}
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

{%- for plugin_name, plugin in service_grains.collectd.plugin.iteritems() %}

{{ client.config_dir }}/{{ plugin_name }}.conf:
  file.managed:
  {%- if plugin.template is defined %}
  - source: salt://{{ plugin.template }}
  - template: jinja
  - defaults:
    plugin: {{ plugin|yaml }}
  {%- else %}
  - contents: "LoadPlugin {{ plugin.plugin }}\n"
  {%- endif %}
  - user: root
  - mode: 660
  - require:
    - file: {{ client.config_dir }}
  - watch_in:
    - service: collectd_service

{%- endfor %}

/etc/collectd/filters.conf:
  file.managed:
  - source: salt://collectd/files/filters.conf
  - template: jinja
  - user: root
  - group: root
  - mode: 660
  - watch_in:
    - service: collectd_service
  - require:
    - file: {{ client.config_dir }}

/etc/collectd/thresholds.conf:
  file.managed:
  - source: salt://collectd/files/thresholds.conf
  - template: jinja
  - user: root
  - group: root
  - mode: 660
  - watch_in:
    - service: collectd_service
  - require:
    - file: {{ client.config_dir }}

{{ client.config_file }}:
  file.managed:
  - source: salt://collectd/files/collectd.conf
  - template: jinja
  - user: root
  - group: root
  - mode: 640
  - defaults:
    service_grains: {{ service_grains|yaml }}
  - require:
    - file: {{ client.config_dir }}
  - watch_in:
    - service: collectd_service

{%- for backend_name, backend in client.backend.iteritems() %}

{{ client.config_dir }}/collectd_writer_{{ backend_name }}.conf:
  file.managed:
  - source: salt://collectd/files/backend/{{ backend.engine }}.conf
  - template: jinja
  - user: root
  - group: root
  - mode: 660
  - defaults:
    backend_name: "{{ backend_name }}"
  - require:
    - file: {{ client.config_dir }}
  - watch_in:
    - service: collectd_service

{%- endfor %}

collectd_service:
  service.running:
  - name: collectd
  - enable: true
  - require:
    - pkg: collectd_client_packages

{%- endif %}
