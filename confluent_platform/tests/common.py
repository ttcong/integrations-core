# (C) Datadog, Inc. 2019-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from datadog_checks.dev import get_docker_hostname, get_here

CHECK_NAME = 'activemq'

HERE = get_here()
HOST = get_docker_hostname()

TEST_QUEUES = ('FOO_QUEUE', 'TEST_QUEUE')
TEST_TOPICS = ('FOO_TOPIC', 'TEST_TOPIC')
TEST_MESSAGE = {'body': 'test_message'}
TEST_AUTH = ('admin', 'admin')

TEST_PORT = 8161
BASE_URL = 'http://{}:{}/api/message'.format(HOST, TEST_PORT)

# not all metrics will be available in our E2E environment, specifically:
# "activemq.queue.dequeue_count",
# "activemq.queue.dispatch_count",
# "activemq.queue.enqueue_count",
# "activemq.queue.expired_count",
# "activemq.queue.in_flight_count",

ACTIVEMQ_E2E_METRICS = [
    "activemq.queue.avg_enqueue_time",
    "activemq.queue.consumer_count",
    "activemq.queue.producer_count",
    "activemq.queue.max_enqueue_time",
    "activemq.queue.min_enqueue_time",
    "activemq.queue.memory_pct",
    "activemq.queue.size",
    "activemq.broker.store_pct",
    "activemq.broker.temp_pct",
    "activemq.broker.memory_pct",
]


TYPE_GAUGE = 'com.yammer.metrics.reporting.JmxReporter$Gauge'


class Attribute(object):
    def __init__(self, name, check_metric=True):
        self.name = name
        self.check_metric = check_metric


class MBean(object):
    def __init__(self, bean_name, clazz, attrs=None, check_metric=True):
        self.bean_name = bean_name
        self.clazz = clazz
        self.attrs = attrs
        self.check_metric = check_metric
        self.domain = None

    @staticmethod
    def _parse_name(name):




MBEANS = [
    MBean('kafka.server:type=ReplicaManager,name=UnderMinIsrPartitionCount', TYPE_GAUGE),
    MBean('kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions', TYPE_GAUGE),
    # MBean('kafka.cluster:type=Partition,topic={topic},name=UnderMinIsr,partition={partition}', attrs=[
    #     Attribute('hello')
    # ]),
]
