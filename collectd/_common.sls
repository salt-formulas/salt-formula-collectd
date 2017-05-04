{%- from "collectd/map.jinja" import client with context %}

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


/usr/lib/collectd-python:
  file.recurse:
  - source: salt://collectd/files/plugin
