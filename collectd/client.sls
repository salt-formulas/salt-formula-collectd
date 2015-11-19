{%- from "collectd/map.jinja" import client with context %}
{%- if client.enabled %}

{% if grains.os == 'Ubuntu' and (grains.osrelease in ['10.04', '12.04']) %}

collectd_repo:
  pkgrepo.managed:
  - human_name: Collectd
  - ppa: nikicat/collectd
  - file: /etc/apt/sources.list.d/collectd.list
  - require_in:
    - pkg: collectd_packages

collectd_amqp_packages:
  pkg.installed:
  - names: 
    - librabbitmq0

{% endif %}

collectd_packages:
  pkg.installed:
  - names: {{ client.pkgs }}

/etc/collectd:
  file.directory:
  - user: root
  - mode: 750
  - makedirs: true
  - require:
    - pkg: collectd_packages

{{ client.config_dir }}:
  file.directory:
  - user: root
  - mode: 750
  - makedirs: true
  - require:
    - pkg: collectd_packages

{%- for service in client.supported_services %}
{%- if service in grains.roles %}

{%- for service_group in service.split('.') %}
{%- if loop.first %}
{{ client.config_dir }}/{{ service|replace('.', '_') }}.conf:
  file.managed:
  - source: salt://{{ service_group }}/files/collectd.conf
  - template: jinja
  - user: root
  - mode: 660
  - require:
    - file: {{ client.config_dir }}
  - watch_in:
    - service: collectd_service
{%- endif %}
{%- endfor %}

{%- endif %}
{%- endfor %}

{%- if pillar.get('external', {}).network_device is defined %}
{{ client.config_dir }}/network_snmp.conf:
  file.managed:
  - source: salt://collectd/files/conf.d/network_snmp.conf
  - template: jinja
  - user: root
  - mode: 660
  - require:
    - file: {{ client.config_dir }}
  - watch_in:
    - service: collectd_service
{%- endif %}

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

{{ client.config_dir }}/{{ backend_name }}.conf:
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
    - pkg: collectd_packages

{%- endif %}
