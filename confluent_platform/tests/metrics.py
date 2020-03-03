# (C) Datadog, Inc. 2019-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import csv
import io
import re

GAUGE = 'gauge'
RATE = 'rate'

class Attribute:
    def __init__(self, name, check_metric=True):
        self.name = name
        self.check_metric = check_metric


class Metric:
    def __init__(self, suffix, metric_type, unit_name='', orientation=0):
        self.suffix = suffix
        self.metric_type = metric_type
        self.unit_name = unit_name
        self.orientation = orientation


class MBean:
    def __init__(self, bean_name, desc='', attrs=None, check_metric=True):
        self.bean_name = bean_name
        self.desc = desc
        self.attrs = attrs
        self.check_metric = check_metric
        self.domain, self.props = self._parse_name(bean_name)

    @staticmethod
    def _parse_name(name):
        domain, raw_props = name.split(':', 1)

        props = {}
        for raw_prop in raw_props.split(','):
            k, v = raw_prop.split('=', 1)
            props[k] = v

        return domain, props

    def get_metric_name(self, alias):
        alias = alias.replace('$domain', camel_to_snake(self.domain))
        alias = alias.replace('$type', camel_to_snake(self.props['type']))
        alias = alias.replace('$name', camel_to_snake(self.props['name']))
        return alias


MBEANS = [
    {
        # Yammer Gauge
        'alias': '$domain.$type.$name',
        'metrics': [
            Metric('avg', GAUGE),
            Metric('count', GAUGE),
        ],
        'beans': [
            MBean("kafka.server:type=ReplicaManager,name=UnderMinIsrPartitionCount", desc="Number of partitions whose in-sync replicas count is less than minIsr."),
            MBean("kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions", desc="Number of under-replicated partitions (| ISR | < | all replicas |). Alert if value is greater than 0."),
            MBean("kafka.cluster:type=Partition,topic={topic},name=UnderMinIsr,partition={partition}", desc="Number of partitions whose in-sync replicas count is less than minIsr. These partitions will be unavailable to producers who use acks=all."),
            MBean("kafka.controller:type=KafkaController,name=OfflinePartitionsCount", desc="Number of partitions that don’t have an active leader and are hence not writable or readable. Alert if value is greater than 0."),
            MBean("kafka.controller:type=KafkaController,name=ActiveControllerCount", desc="Number of active controllers in the cluster. Alert if the aggregated sum across all brokers in the cluster is anything other than 1 because there should be exactly one controller per cluster."),
            MBean("kafka.server:type=ReplicaManager,name=PartitionCount", desc="Number of partitions on this broker. This should be mostly even across all brokers."),
            MBean("kafka.server:type=ReplicaManager,name=LeaderCount",
                  desc="Number of leaders on this broker. This should be mostly even across all brokers. If not, set auto.leader.rebalance.enable to true on all brokers in the cluster."),
            MBean("kafka.server:type=ReplicaFetcherManager,name=MaxLag,clientId=Replica", desc="Maximum lag in messages between the follower and leader replicas. This is controlled by the replica.lag.max.messages config."),




            MBean("kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent", desc="Average fraction of time the network processor threads are idle. Values are between 0 (all resources are used) and 1 (all resources are available)"),
            MBean("kafka.network:type=RequestChannel,name=RequestQueueSize", desc="Size of the request queue. A congested request queue will not be able to process incoming or outgoing requests"),
            MBean("kafka.network:type=RequestMetrics,name=TotalTimeMs,request={Produce|FetchConsumer|FetchFollower}", desc="Total time in ms to serve the specified request"),
            MBean("kafka.network:type=RequestMetrics,name=RequestQueueTimeMs,request={Produce|FetchConsumer|FetchFollower}", desc="Time the request waits in the request queue"),
            MBean("kafka.network:type=RequestMetrics,name=LocalTimeMs,request={Produce|FetchConsumer|FetchFollower}", desc="Time the request is processed at the leader"),
            MBean("kafka.network:type=RequestMetrics,name=RemoteTimeMs,request={Produce|FetchConsumer|FetchFollower}", desc="Time the request waits for the follower. This is non-zero for produce requests when acks=all"),
            MBean("kafka.network:type=RequestMetrics,name=ResponseQueueTimeMs,request={Produce|FetchConsumer|FetchFollower}", desc="Time the request waits in the response queue"),
            MBean("kafka.network:type=RequestMetrics,name=ResponseSendTimeMs,request={Produce|FetchConsumer|FetchFollower}", desc="Time to send the response"),
            MBean("kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec", desc="Aggregate incoming message rate."),
            MBean("kafka.log:type=LogFlushStats,name=LogFlushRateAndTimeMs", desc="Log flush rate and time."),
            MBean("kafka.server:type=ReplicaManager,name=IsrShrinksPerSec", desc="If a broker goes down, ISR for some of the partitions will shrink. When that broker is up again, ISR will be expanded once the replicas are fully caught up. Other than that, the expected value for both ISR shrink rate and expansion rate is 0."),
            MBean("kafka.server:type=ReplicaManager,name=IsrExpandsPerSec", desc="When a broker is brought up after a failure, it starts catching up by reading from the leader. Once it is caught up, it gets added back to the ISR."),
            MBean("kafka.server:type=FetcherLagMetrics,name=ConsumerLag,clientId=([-.\w]+),topic=([-.\w]+),partition=([0-9]+)", desc="Lag in number of messages per follower replica. This is useful to know if the replica is slow or has stopped replicating from the leader."),
            MBean("kafka.server:type=DelayedOperationPurgatory,delayedOperation=Produce,name=PurgatorySize", desc="Number of requests waiting in the producer purgatory. This should be non-zero when acks=all is used on the producer."),
            MBean("kafka.server:type=DelayedOperationPurgatory,delayedOperation=Fetch,name=PurgatorySize", desc="Number of requests waiting in the fetch purgatory. This is high if consumers use a large value for fetch.wait.max.ms ."),
        ]
    },
    {
        # Yammer Meter
        'alias': '$domain.$type.$name',
        'metrics': [
            Metric('avg', GAUGE),
            Metric('count', GAUGE),
        ],
        'beans': [
            MBean("kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec", desc="Aggregate incoming byte rate."),
            MBean("kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec", desc="Aggregate outgoing byte rate."),
            MBean("kafka.network:type=RequestMetrics,name=RequestsPerSec,request={Produce|FetchConsumer|FetchFollower}",
                  desc="Request rate."),
            MBean("kafka.server:type=BrokerTopicMetrics,name=TotalProduceRequestsPerSec", desc="Produce request rate."),
            MBean("kafka.server:type=BrokerTopicMetrics,name=TotalFetchRequestsPerSec", desc="Fetch request rate."),
            MBean("kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec",
                  desc="Produce request rate for requests that failed."),
            MBean("kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec",
                  desc="Fetch request rate for requests that failed."),
            MBean("kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec",
                  desc="Unclean leader election rate."),
            MBean("kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent",
                  desc="Average fraction of time the request handler threads are idle. Values are between 0 (all resources are used) and 1 (all resources are available)"),

        ]
    },

    {
        # Yammer Timer
        'alias': '$domain.$type.$name',
        'metrics': [
            Metric('avg', GAUGE),
            Metric('count', GAUGE),
        ],
        'beans': [
            MBean("kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs",
                  desc="Leader election rate and latency."),

        ]
    },
]


def build_row(metric_name, metric, bean, current_metrics):
    current_metric = current_metrics.get(metric_name)
    new_row = {
        'metric_name': metric_name,
        'metric_type': metric.metric_type,
        'description': bean.desc,
    }
    if current_metric:
        for field in ['unit_name', 'orientation']:
            new_row[field] = current_metric[field]
    return new_row


def build_metadata_csv(orig_metadata):
    reader = csv.DictReader(io.StringIO(orig_metadata))
    current_metrics = {}
    for row in reader:
        current_metrics[row['metric_name']] = row

    headers = reader.fieldnames
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=headers, lineterminator='\n')
    writer.writeheader()

    for group in MBEANS:
        alias = group['alias']
        metrics = group['metrics']
        for mbean in group['beans']:  # type: MBean
            for metric in metrics:
                metric_name = "{}.{}".format(mbean.get_metric_name(alias), metric.suffix)
                writer.writerow(build_row(metric_name, metric, mbean, current_metrics))

    content = out.getvalue()
    out.close()
    return content


def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
