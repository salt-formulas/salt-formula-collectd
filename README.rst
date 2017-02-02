========
Collectd
========

Collectd is a daemon which collects system performance statistics periodically and provides mechanisms to store the values in a variety of ways, for example in RRD files.

Sample pillars
==============

Data writers
------------

Send data over TCP to Graphite Carbon

.. code-block:: yaml

    collectd:
      client:
        enabled: true
        read_interval: 60
        backend:
          carbon_service:
            engine: carbon
            host: carbon1.comain.com
            port: 2003

Send data over AMQP

.. code-block:: yaml

    collectd:
      client:
        enabled: true
        read_interval: 60
        backend:
          amqp_broker:
            engine: amqp
            host: broker1.comain.com
            port: 5672
            user: monitor
            password: amqp-pwd
            virtual_host: '/monitor'

Send data over HTTP

.. code-block:: yaml

    collectd:
      client:
        enabled: true
        read_interval: 60
        backend:
          http_service:
            engine: http
            host: service.comain.com
            port: 8123


Data collectors
---------------


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

Collecting the SNMP metrics

.. code-block:: yaml

    collectd:
      client:
        data:
          connected_devices:
            type: devices
            values:
            - IF-MIB::ifNumber.0
        host:
          ubiquity:
            address: 10.0.0.1
            community: public
            version: 2
            data:
            - connected_devices


Collecting the cURL response times and codes

.. code-block:: yaml

    collectd:
      client:
        check:
          curl:
            service1:
              url: "https://service.domain.com:443/"
            service2:
              url: "https://service.domain.com:443/"


Collecting the ping response times

.. code-block:: yaml

    collectd:
      client:
        check:
          ping:
            host_label1:
              host: "172.10.31.14"
            host_label2:
              host: "172.10.31.12"

Read more
=========

* http://collectd.org/documentation.shtml
* http://www.canopsis.org/2013/02/collectd-graphite/
* http://collectd.org/documentation/manpages/collectd.conf.5.shtml#plugin_libvirt
* http://libvirt.org/uri.html#URI_qemu

Documentation and Bugs
======================

To learn how to install and update salt-formulas, consult the documentation
available online at:

    http://salt-formulas.readthedocs.io/

In the unfortunate event that bugs are discovered, they should be reported to
the appropriate issue tracker. Use Github issue tracker for specific salt
formula:

    https://github.com/salt-formulas/salt-formula-collectd/issues

For feature requests, bug reports or blueprints affecting entire ecosystem,
use Launchpad salt-formulas project:

    https://launchpad.net/salt-formulas

You can also join salt-formulas-users team and subscribe to mailing list:

    https://launchpad.net/~salt-formulas-users

Developers wishing to work on the salt-formulas projects should always base
their work on master branch and submit pull request against specific formula.

    https://github.com/salt-formulas/salt-formula-collectd

Any questions or feedback is always welcome so feel free to join our IRC
channel:

    #salt-formulas @ irc.freenode.net
