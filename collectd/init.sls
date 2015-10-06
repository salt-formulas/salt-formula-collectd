
include:
{% if pillar.collectd.client is defined %}
- collectd.client
{% endif %}
