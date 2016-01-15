{%- if pillar.collectd is defined %}
include:
{%- if pillar.collectd.client is defined %}
- collectd.client
{%- endif %}
{%- endif %}