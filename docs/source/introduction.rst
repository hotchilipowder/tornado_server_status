=======================
Introduction
=======================

Motivation
************************************

Monitoring server resources is a very important service. The mature system-level solutions include: `Grafana+Prometheus <https://grafana.com/docs/grafana/latest/getting-started/getting-started-prometheus/>`_. It is an open-source monitoring system with a dimensional data model, flexible query language, efficient time series database and modern alerting approach. But it is too heavy for simple VPS monitoring, we just want to know how the server is going on. So we start this project just for fun and simplity.

Similar projects include `ServerStatus(Python) <https://github.com/cppla/ServerStatus>`_ , `ServerStatus(PHP) <https://github.com/mojeda/ServerStatus>`_ and `nezha (Go) <https://github.com/naiba/nezha>`_

These projects have been successful, but most of them rely on installing a script on the server side to query server resources. Of course, this is very good for collecting information, but it is too complicated and not good for a simple monitoring server.

Why choose tornado as the server?
===================================

Answer
    Because the configuration of tornado is relatively simple compared to flask and django. It is fit for simple projects. For this project, we used `asyncssh <https://asyncssh.readthedocs.io/>`_ as the client, and for a given VPS, we obtain the server status information by querying the script through ssh.

