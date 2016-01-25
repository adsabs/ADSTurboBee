[![Build Status](https://travis-ci.org/adsabs/ADSWorker.svg)](https://travis-ci.org/adsabs/ADSWorker)
[![Coverage Status](https://coveralls.io/repos/adsabs/ADSWorker/badge.svg)](https://coveralls.io/r/adsabs/ADSWorker)

# ADSWorker

A generic template for building ADS pipeline applicaitons.

To build your own worker, first clone this repository and rename stuff.

1. git clone git@github.com:adsabs/ADSWorker.git
2. `init.sh ADSMyNewName`

Then commit the results into a new repository. (and remove this section from the README)       
       

dev setup - vagrant (docker)
============================

1. vim ADSWorker/local_config.py #edit, edit
1. `vagrant up db rabbitmq app --provider=docker`
1. `vagrant ssh app`
1. `cd /vagrant`

This will start the pipeline inside the `app` container - make sure you have configured endpoints and
access tokens correctly.

We are using 'docker' provider (ie. instead of virtualbox VM, you run the processes in docker).
On some systems, it is necessary to do: `export VAGRANT_DEFAULT_PROVIDER=docker` or always 
specify `--provider docker' when you run vagrant.
 
The  directory is synced to /vagrant/ on the guest.


dev setup - local editing
=========================

If you (also) hate when stuff is unnecessarily complicated, then you can run/develop locally
(using whatever editor/IDE/debugger you like)

1. virtualenv python
1. source python/bin/activate
1. pip install -r requirements.txt
1. pip install -r dev-requirements.txt
1. vagrant `up db rabbitmq --provider=docker`

This will setup python `virtualenv` and the database + rabbitmq. You can run the pipeline and 
tests locally. 


RabbitMQ
========

`vagrant up rabbitmq`

The RabbitMQ will be on localhost:6672. The administrative interface on localhost:25672.


Database
========

`vagrant up db`

PostgreSQL on localhost:6432



production setup
================

`vagrant up prod`

It will automatically download/install the latest release from the github (no, not
your local changes - only from github).

If you /ADSWorker/prod_config.py is available, it will copy and use it in place of
`local_config.py`

No ports are exposed, no SSH access is possible. New releases will deployed automatically.

Typical installation:

1. `vim ADSWorker/prod_config.py` # edit, edit...
1. `vagrant up prod`


production setup - docker way
=============================

1. cd manifests/production/app
2. docker build --name ADSWorker -t ADSWorker .
3. cd ../../.. 
4. vim prod_config.py # edit, edit...
4. dockerun -d -v .:/vagrant/ --name ADSWorker ADSWorker /sbin/my_init


Here are some useful commands:

- restart service

	`docker exec ADSWorker sv restart app`

- tail log from one of the workers

	`docker exec ADSWorker tail -f /app/logs/ClaimsImporter.log`
