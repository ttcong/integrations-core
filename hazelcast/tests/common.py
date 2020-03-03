# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from datadog_checks.dev import get_docker_hostname, get_here

CHECK_NAME = 'hazelcast'

HERE = get_here()
HOST = get_docker_hostname()

COMMUNICATION_PORTS = [5701, 5702]
