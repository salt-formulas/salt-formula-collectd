========
Collectd
========

Collectd is a daemon which collects system performance statistics periodically and provides mechanisms to store the values in a variety of ways, for example in RRD files. 

Sample pillars
==============

Send data over TCP to Graphite Carbon (old way plugins)

.. code-block:: yaml

    collectd:
      client:
        enabled: true
        read_interval: 60
        plugins:
        - name: cpu
        - name: df
        - name: disk
        - name: entropy
        - name: interface
        - name: load
        - name: memory
        - name: processes
        - name: swap
        - name: uptime
        - name: users
        - name: write_graphite
          host: carbon1.comain.com
          port: 2003

Gather libvirt data from local KVM

.. code-block:: yaml

    collectd:
      client:
        enabled: true
        read_interval: 60
        plugins:
        - name: cpu
        - name: libvirt
          connection: 'qemu:///system'

Send data over AMQP

.. code-block:: yaml

    collectd:
      client:
        enabled: true
        read_interval: 60
        plugins:
        - name: cpu
        - name: users
        - name: amqp
          host: broker1.comain.com
          port: 5672
          user: monitor
          password: amqp-pwd
          virtual_host: '/monitor'

Send data over carbon

.. code-block:: yaml

    collectd:
      client:
        enabled: true
        backend:
          carbon:
            engine: carbon
            host: metrics.domain.com
            port: 2003

Read more
=========

* http://collectd.org/documentation.shtml
* http://www.canopsis.org/2013/02/collectd-graphite/
* http://collectd.org/documentation/manpages/collectd.conf.5.shtml#plugin_libvirt
* http://libvirt.org/uri.html#URI_qemu
