# (C) Datadog, Inc. 2019-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import pytest
from six import iteritems

from datadog_checks.base.stubs.aggregator import AggregatorStub
from .common import ACTIVEMQ_E2E_METRICS

# https://docs.confluent.io/current/kafka/monitoring.html#broker-metrics

BROKER_METRICS = [
    'kafka.server.replica_manager.under_min_isr_partition_count',
]

ALL_METRICS = BROKER_METRICS


@pytest.mark.e2e
def test_e2e(dd_agent_check):
    instance = {}
    aggregator = dd_agent_check(instance)  # type: AggregatorStub

    for metric in ALL_METRICS:
        aggregator.assert_metric(metric)

    for metric_name, metrics in iteritems(aggregator._metrics):
        # print("{} => {}".format(metric_name, metrics))
        print(metric_name)
    1/0
    # # for metric in ACTIVEMQ_E2E_METRICS:
    #     aggregator.assert_metric(metric)
