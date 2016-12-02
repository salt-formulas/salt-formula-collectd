{%- if client.enabled %}

{{ client.service }}_client_conf_dir:
  file.directory:
  - name: {{ client.config_dir }}
  - user: root
  - mode: 750
  - makedirs: true

{{ client.service }}_client_conf_dir_clean:
  file.directory:
  - name: {{ client.config_dir }}
  - clean: true

{%- for plugin_name, plugin in plugins.iteritems() %}

{%- if plugin.get('plugin', 'native') not in ['python'] %}

{{ client.config_dir }}/{{ plugin_name }}.conf:
  file.managed:
  {%- if plugin.template is defined %}
  - source: salt://{{ plugin.template }}
  - template: jinja
  - defaults:
    plugin: {{ plugin|yaml }}
  {%- else %}
  - contents: "<LoadPlugin {{ plugin.plugin }}>\n  Globals false\n</LoadPlugin>\n"
  {%- endif %}
  - user: root
  - mode: 660
  - require:
    - file: {{ client.service }}_client_conf_dir
  - require_in:
    - file: {{ client.service }}_client_conf_dir_clean

{%- endif %}

{%- endfor %}

{%- if client.file_logging %}

{{ client.config_dir }}/00_collectd_logfile.conf:
  file.managed:
  - source: salt://collectd/files/collectd_logfile.conf
  - template: jinja
  - defaults:
    service_name: {{ client.service }}
  - user: root
  - group: root
  - mode: 660
  - require:
    - file: {{ client.service }}_client_conf_dir
  - require_in:
    - file: {{ client.service }}_client_conf_dir_clean

{%- endif %}

{{ client.config_dir }}/collectd_python.conf:
  file.managed:
  - source: salt://collectd/files/collectd_python.conf
  - template: jinja
  - user: root
  - group: root
  - mode: 660
  - defaults:
      plugin: {{ plugins|yaml }}
  - require:
    - file: {{ client.service }}_client_conf_dir
  - require_in:
    - file: {{ client.service }}_client_conf_dir_clean

{{ client.config_file }}:
  file.managed:
  - source: salt://collectd/files/collectd.conf
  - template: jinja
  - user: root
  - group: root
  - mode: 640
  - defaults:
    plugin: {{ plugins|yaml }}
    client: {{ client|yaml }}
  - require:
    - file: {{ client.service }}_client_conf_dir
  - require_in:
    - file: {{ client.service }}_client_conf_dir_clean

{%- set network_backend = {} %}
{%- for backend_name, backend in client.backend.iteritems() %}

{%- if backend.engine not in ['network'] %}

{{ client.config_dir }}/collectd_writer_{{ backend_name }}.conf:
  file.managed:
  - source: salt://collectd/files/backend/{{ backend.engine }}.conf
  - template: jinja
  - user: root
  - group: root
  - mode: 660
  - defaults:
    backend: {{ backend|yaml }}
  - require:
    - file: {{ client.service }}_client_conf_dir
  - require_in:
    - file: {{ client.service }}_client_conf_dir_clean

{%- else %}

{%- set network_backend = salt['grains.filter_by']({'default': network_backend}, merge={backend_name: backend}) %}

{%- endif %}

{%- endfor %}

{%- if network_backend|length > 0 %}

{{ client.config_dir }}/collectd_writer_network.conf:
  file.managed:
  - source: salt://collectd/files/backend/network.conf
  - template: jinja
  - user: root
  - group: root
  - mode: 660
  - defaults:
    backend: {{ backend|yaml }}
  - require:
    - file: {{ client.service }}_client_conf_dir
  - require_in:
    - file: {{ client.service }}_client_conf_dir_clean

{%- endif %}

{{ client.defaults_file }}:
  file.managed:
  - source: salt://collectd/files/default_collectd
  - template: jinja
  - user: root
  - group: root
  - mode: 644

{{ client.service }}_service:
{%- if client.automatic_starting %}
  service.running:
  - enable: true
  - watch:
    - file: {{ client.config_file }}
    - file: {{ client.config_dir }}/*
    - file: {{ client.defaults_file }}
{%- else %}
  service.disabled:
{%- endif %}
  - name: {{ client.service }}

{%- endif %}
