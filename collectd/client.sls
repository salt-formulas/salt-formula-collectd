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

collectd_client_plugins_grain:
  file.managed:
  - name: /etc/salt/grains.d/collectd_plugins
  - source: salt://collectd/files/plugins.grain
  - template: jinja
  - user: root
  - mode: 600
  - require:
    - pkg: collectd_client_packages

{%- set collectd_plugin_yaml = salt['cmd.run']('[ -e /etc/salt/grains.d/collectd_plugins ] && cat /etc/salt/grains.d/collectd_plugins || echo "collectd_plugin: {}"') %}
{%- load_yaml as collectd_plugin %}
{{ collectd_plugin_yaml }}
{%- endload %}

{%- for plugin_name, plugin in collectd_plugin.collectd_plugin.iteritems() %}

{{ client.config_dir }}/{{ plugin_name }}.conf:
  file.managed:
  {%- if plugin.template is defined %}
  - source: salt://{{ plugin.template }}
  - template: jinja
  - defaults:
    plugin: {{ plugin|yaml }}
  {%- else %}
  - contents: "LoadPlugin {{ plugin.plugin }}"
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
  - mode: 660
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