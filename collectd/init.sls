{%- if pillar.collectd is defined %}
include:
- collectd.client
{%- endif %}