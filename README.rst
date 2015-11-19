========
Collectd
========

Collectd is a daemon which collects system performance statistics periodically and provides mechanisms to store the values in a variety of ways, for example in RRD files. 

Sample pillars
==============

Send data over TCP to Graphite Carbon

.. code-block:: yaml

    collectd:
      client:
        enabled: true
        read_interval: 60
        backend:
          carbon:
            host: carbon1.comain.com
            port: 2003

Send data over AMQP

.. code-block:: yaml

    collectd:
      client:
        enabled: true
        read_interval: 60
        backend:
          amqp:
            host: broker1.comain.com
            port: 5672
            user: monitor
            password: amqp-pwd
           virtual_host: '/monitor'

Monitor network devices, defined in 'external' dictionary

.. code-block:: yaml

    external:
      network_device:
        MX80-01:
          community: test
          model: Juniper_MX80
          management: 
            address: 10.0.0.254
            port: fxp01
            engine: snmp/ssh
          interface:
            xe-0/0/0:
              description: MEMBER-OF-LACP-TO-QFX
              type: 802.3ad
              subinterface:
                xe-0/0/0.0:
                  description: MEMBER-OF-LACP-TO-QFX
    collectd:
      client:
        enabled: true
        ...

Read more
=========

* http://collectd.org/documentation.shtml
* http://www.canopsis.org/2013/02/collectd-graphite/
* http://collectd.org/documentation/manpages/collectd.conf.5.shtml#plugin_libvirt
* http://libvirt.org/uri.html#URI_qemu
