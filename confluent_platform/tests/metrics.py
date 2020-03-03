# (C) Datadog, Inc. 2019-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import csv
import io
import re

TYPE_GAUGE = 'com.yammer.metrics.reporting.JmxReporter$Gauge'
TYPE_KAFKA_MBEAN = 'com.yammer.metrics.reporting.JmxReporter$Gauge'


class Attribute:
    def __init__(self, name, check_metric=True):
        self.name = name
        self.check_metric = check_metric


class Metric:
    def __init__(self, suffix, unit_name='', orientation=0):
        self.suffix = suffix
        self.unit_name = unit_name
        self.orientation = orientation


class MBean:
    def __init__(self, bean_name, clazz, desc='', attrs=None, check_metric=True):
        self.bean_name = bean_name
        self.clazz = clazz
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
        'alias': '$domain.$type.$name',
        'metrics': [
            Metric('avg'),
            Metric('count'),
        ],
        'beans': [
            MBean('kafka.server:type=ReplicaManager,name=UnderMinIsrPartitionCount', TYPE_GAUGE, desc='Number of partitions whose in-sync replicas count is less than minIsr.'),
            MBean('kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions', TYPE_GAUGE, desc='Number of under-replicated partitions (| ISR | < | all replicas |). Alert if value is greater than 0.'),
        ]
    }
    # MBean('kafka.cluster:type=Partition,topic={topic},name=UnderMinIsr,partition={partition}', attrs=[
    #     Attribute('hello')
    # ], clazz=TYPE_KAFKA_MBEAN),
]


def build_metadata_csv():
    headers = 'metric_name,metric_type,interval,unit_name,per_unit_name,description,orientation,integration,short_name'.split(',')
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=headers, lineterminator='\n')
    writer.writeheader()

    def write_metric(metric_name, bean):
        writer.writerow({
            'metric_name': metric_name,
            'metric_type': 'gauge',
            'description': bean.desc,
        })

    for group in MBEANS:
        alias = group['alias']
        metrics = group['metrics']
        for mbean in group['beans']:  # type: MBean
            if metrics:
                for metric in metrics:
                    write_metric("{}.{}".format(mbean.get_metric_name(alias), metric.suffix), mbean)
            else:
                write_metric(mbean.get_metric_name(alias), mbean)
    content = out.getvalue()
    out.close()
    return content


def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
