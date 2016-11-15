{%- if pillar.collectd is defined %}
include:
{%- if pillar.collectd.client is defined %}
- collectd.client
{%- endif %}
{%- if pillar.collectd.remote_client is defined %}
- collectd.remote_client
{%- endif %}
{%- endif %}
