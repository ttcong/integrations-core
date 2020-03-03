# (C) Datadog, Inc. 2019-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import csv
import io
import re

GAUGE = 'gauge'
RATE = 'rate'
COUNT = 'count'


BROKER_METRICS = r'''
bean	type	unit_name	description	check_metric
kafka.server:type=ReplicaManager,name=UnderMinIsrPartitionCount	YAMMER_GAUGE	partition	Number of partitions whose in-sync replicas count is less than minIsr.	TRUE
kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions	YAMMER_GAUGE	partition	Number of under-replicated partitions (| ISR | < | all replicas |). Alert if value is greater than 0.	TRUE
kafka.cluster:type=Partition,topic={topic},name=UnderMinIsr,partition={partition}	YAMMER_GAUGE	partition	Number of partitions whose in-sync replicas count is less than minIsr. These partitions will be unavailable to producers who use acks=all.	TRUE
kafka.controller:type=KafkaController,name=OfflinePartitionsCount	YAMMER_GAUGE	partition	Number of partitions that don’t have an active leader and are hence not writable or readable. Alert if value is greater than 0.	TRUE
kafka.controller:type=KafkaController,name=ActiveControllerCount	YAMMER_GAUGE		Number of active controllers in the cluster. Alert if the aggregated sum across all brokers in the cluster is anything other than 1 because there should be exactly one controller per cluster.	TRUE
kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec	YAMMER_METER	byte	Aggregate incoming byte rate.	TRUE
kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec	YAMMER_METER	byte	Aggregate outgoing byte rate.	TRUE
kafka.network:type=RequestMetrics,name=RequestsPerSec,request={Produce|FetchConsumer|FetchFollower}	YAMMER_METER	request	Request rate.	TRUE
kafka.server:type=BrokerTopicMetrics,name=TotalProduceRequestsPerSec	YAMMER_METER	request	Produce request rate.	TRUE
kafka.server:type=BrokerTopicMetrics,name=TotalFetchRequestsPerSec	YAMMER_METER	request	Fetch request rate.	TRUE
kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec	YAMMER_METER	request	Produce request rate for requests that failed.	TRUE
kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec	YAMMER_METER	request	Fetch request rate for requests that failed.	TRUE
kafka.controller:type=ControllerStats,name=LeaderElectionRateAndTimeMs	YAMMER_TIMER		Leader election rate and latency.	FALSE
kafka.controller:type=ControllerStats,name=UncleanLeaderElectionsPerSec	YAMMER_METER		Unclean leader election rate.	TRUE
kafka.server:type=ReplicaManager,name=PartitionCount	YAMMER_GAUGE	partition	Number of partitions on this broker. This should be mostly even across all brokers.	TRUE
kafka.server:type=ReplicaManager,name=LeaderCount	YAMMER_GAUGE		Number of leaders on this broker. This should be mostly even across all brokers. If not, set auto.leader.rebalance.enable to true on all brokers in the cluster.	TRUE
kafka.server:type=ReplicaFetcherManager,name=MaxLag,clientId=Replica	YAMMER_GAUGE	message	Maximum lag in messages between the follower and leader replicas. This is controlled by the replica.lag.max.messages config.	TRUE
kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent	YAMMER_METER	fraction	Average fraction of time the request handler threads are idle. Values are between 0 (all resources are used) and 1 (all resources are available)	TRUE
kafka.network:type=SocketServer,name=NetworkProcessorAvgIdlePercent	YAMMER_GAUGE	fraction	Average fraction of time the network processor threads are idle. Values are between 0 (all resources are used) and 1 (all resources are available)	TRUE
kafka.network:type=RequestChannel,name=RequestQueueSize	YAMMER_GAUGE	request	Size of the request queue. A congested request queue will not be able to process incoming or outgoing requests	TRUE
kafka.network:type=RequestMetrics,name=TotalTimeMs,request={Produce|FetchConsumer|FetchFollower}	YAMMER_HISTOGRAM	millisecond	Total time in ms to serve the specified request	TRUE
kafka.network:type=RequestMetrics,name=RequestQueueTimeMs,request={Produce|FetchConsumer|FetchFollower}	YAMMER_HISTOGRAM	millisecond	Time the request waits in the request queue	TRUE
kafka.network:type=RequestMetrics,name=LocalTimeMs,request={Produce|FetchConsumer|FetchFollower}	YAMMER_HISTOGRAM	millisecond	Time the request is processed at the leader	TRUE
kafka.network:type=RequestMetrics,name=RemoteTimeMs,request={Produce|FetchConsumer|FetchFollower}	YAMMER_HISTOGRAM	millisecond	Time the request waits for the follower. This is non-zero for produce requests when acks=all	TRUE
kafka.network:type=RequestMetrics,name=ResponseQueueTimeMs,request={Produce|FetchConsumer|FetchFollower}	YAMMER_HISTOGRAM	millisecond	Time the request waits in the response queue	TRUE
kafka.network:type=RequestMetrics,name=ResponseSendTimeMs,request={Produce|FetchConsumer|FetchFollower}	YAMMER_HISTOGRAM	millisecond	Time to send the response	TRUE
kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec	YAMMER_METER	message	Aggregate incoming message rate.	TRUE
kafka.log:type=LogFlushStats,name=LogFlushRateAndTimeMs	YAMMER_TIMER	flush	Log flush rate and time.	FALSE
kafka.server:type=ReplicaManager,name=IsrShrinksPerSec	YAMMER_METER		If a broker goes down, ISR for some of the partitions will shrink. When that broker is up again, ISR will be expanded once the replicas are fully caught up. Other than that, the expected value for both ISR shrink rate and expansion rate is 0.	TRUE
kafka.server:type=ReplicaManager,name=IsrExpandsPerSec	YAMMER_METER		When a broker is brought up after a failure, it starts catching up by reading from the leader. Once it is caught up, it gets added back to the ISR.	TRUE
kafka.server:type=FetcherLagMetrics,name=ConsumerLag,clientId=([-.\w]+),topic=([-.\w]+),partition=([0-9]+)	YAMMER_GAUGE	message	Lag in number of messages per follower replica. This is useful to know if the replica is slow or has stopped replicating from the leader.	FALSE
kafka.server:type=DelayedOperationPurgatory,delayedOperation=Produce,name=PurgatorySize	YAMMER_GAUGE	request	Number of requests waiting in the producer purgatory. This should be non-zero when acks=all is used on the producer.	TRUE
kafka.server:type=DelayedOperationPurgatory,delayedOperation=Fetch,name=PurgatorySize	YAMMER_GAUGE	request	Number of requests waiting in the fetch purgatory. This is high if consumers use a large value for fetch.wait.max.ms .	TRUE
'''.strip()

YAMMER_METRICS = BROKER_METRICS


class Attribute:
    def __init__(self, name, check_metric=True):
        self.name = name
        self.check_metric = check_metric


class Metric:
    def __init__(self, metric_type, suffix=None, per_unit_name='', orientation=0, check_metric=True):
        self.suffix = suffix
        self.metric_type = metric_type
        self.per_unit_name = per_unit_name
        self.orientation = orientation
        self.check_metric = check_metric


class MBean:
    def __init__(self, bean_name, yammer_type, desc='', unit_name='', attrs=None, check_metric=True):
        self.bean_name = bean_name
        self.desc = desc
        self.unit_name = unit_name
        self.attrs = attrs
        self.check_metric = check_metric
        self.domain, self.props = self._parse_name(bean_name)
        self.yammer_type = yammer_type

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


# flatten structure
reader = csv.DictReader(io.StringIO(YAMMER_METRICS), delimiter='\t')
ALL_MBEANS = [MBean(row['bean'], yammer_type=row['type'], unit_name=row['unit_name'], desc=row['description'],
                    check_metric=row['check_metric'] == 'TRUE') for row in reader if row]


MBEANS_CONFIG = [
    {
        # Yammer Gauge
        # https://metrics.dropwizard.io/2.2.0/apidocs/com/yammer/metrics/core/Gauge.html
        'alias': '$domain.$type.$name',
        'metrics': [
            Metric(GAUGE),
        ],
        'beans': [b for b in ALL_MBEANS if b.yammer_type == 'YAMMER_GAUGE']
    },
    {
        # Yammer Meter
        # https://metrics.dropwizard.io/2.2.0/apidocs/com/yammer/metrics/core/Meter.html
        # Note:
        # - `count` is monotonically increasing
        'alias': '$domain.$type.$name',
        'metrics': [
            Metric(COUNT, 'count', check_metric=False),  # Seems `agent check` doesn't return jmx count metrics
            Metric(GAUGE, 'fifteen_minute_rate', per_unit_name='second'),
            Metric(GAUGE, 'five_minute_rate', per_unit_name='second'),
            Metric(GAUGE, 'one_minute_rate', per_unit_name='second'),
            Metric(GAUGE, 'mean_rate', per_unit_name='second'),
        ],
        'beans': [b for b in ALL_MBEANS if b.yammer_type == 'YAMMER_METER']
    },
    {
        # Yammer Timer
        # https://metrics.dropwizard.io/2.2.0/apidocs/com/yammer/metrics/core/Timer.html
        # Note:
        # - `count` is monotonically increasing
        'alias': '$domain.$type.$name',
        'metrics': [
            Metric(COUNT, 'count', check_metric=False),  # Seems `agent check` doesn't return jmx count metrics
            Metric(GAUGE, '50percentile', per_unit_name='second'),
            Metric(GAUGE, '75percentile', per_unit_name='second'),
            Metric(GAUGE, '95percentile', per_unit_name='second'),
            Metric(GAUGE, '98percentile', per_unit_name='second'),
            Metric(GAUGE, '99percentile', per_unit_name='second'),
            Metric(GAUGE, '999percentile', per_unit_name='second'),
            Metric(GAUGE, 'fifteen_minute_rate', per_unit_name='second'),
            Metric(GAUGE, 'five_minute_rate', per_unit_name='second'),
            Metric(GAUGE, 'one_minute_rate', per_unit_name='second'),
            Metric(GAUGE, 'max', per_unit_name='second'),
            Metric(GAUGE, 'mean', per_unit_name='second'),
            Metric(GAUGE, 'mean_rate', per_unit_name='second'),
            Metric(GAUGE, 'min', per_unit_name='second'),
            Metric(GAUGE, 'std_dev', per_unit_name='second'),
        ],
        'beans': [b for b in ALL_MBEANS if b.yammer_type == 'YAMMER_TIMER']
    },
]


def build_one_metric(metric, alias, bean, current_metrics):
    current_metrics = current_metrics or {}
    metric_name = bean.get_metric_name(alias)
    desc = bean.desc.rstrip('.')

    if metric.suffix:
        metric_name = "{}.{}".format(bean.get_metric_name(alias), metric.suffix)
        desc = "{} ({})".format(desc, metric.suffix)

    current_metric = current_metrics.get(metric_name)
    new_row = {
        'metric_name': metric_name,
        'metric_type': metric.metric_type,
        'description': desc,
        'unit_name': bean.unit_name,
        'integration': 'confluent_platform',
    }
    if current_metric:
        for field in ['orientation']:
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

    rows = build_metrics(current_metrics)

    writer.writerows(rows)
    content = out.getvalue()
    out.close()
    return content


def build_metrics(current_metrics=None, checked_only=False):
    rows = []
    for group in MBEANS_CONFIG:
        alias = group['alias']
        metrics = group['metrics']
        for mbean in group['beans']:  # type: MBean
            if checked_only and not mbean.check_metric:
                continue
            for metric in metrics:
                if checked_only and not metric.check_metric:
                    continue
                rows.append(build_one_metric(metric, alias, mbean, current_metrics))
    return rows


def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
