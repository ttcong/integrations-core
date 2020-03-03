# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import os

import pytest

from datadog_checks.dev import docker_run
from datadog_checks.dev.utils import load_jmx_config

from .common import COMMUNICATION_PORTS, HERE


@pytest.fixture(scope='session')
def dd_environment():
    with docker_run(
        os.path.join(HERE, 'docker', 'docker-compose.yaml'),
        log_patterns=[':{} is STARTED'.format(port) for port in COMMUNICATION_PORTS],
    ):
        yield load_jmx_config(), {'use_jmx': True}
