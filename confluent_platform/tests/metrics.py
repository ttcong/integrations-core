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
            MBean('kafka.server:type=ReplicaManager,name=UnderMinIsrPartitionCount', TYPE_GAUGE,
                  desc='Number of partitions whose in-sync replicas count is less than minIsr.'),
            MBean('kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions', TYPE_GAUGE,
                  desc='Number of under-replicated partitions (| ISR | < | all replicas |). Alert if value is greater than 0.'),
        ]
    }
]


def build_row(metric_name, bean, current_metrics):
    current_metric = current_metrics.get(metric_name)
    new_row = {
        'metric_name': metric_name,
        'metric_type': 'gauge',
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
            if metrics:
                for metric in metrics:
                    metric_name = "{}.{}".format(mbean.get_metric_name(alias), metric.suffix)
                    writer.writerow(build_row(metric_name, mbean, current_metrics))
            else:
                writer.writerow(build_row(mbean.get_metric_name(alias), mbean, current_metrics))

    content = out.getvalue()
    out.close()
    return content


def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
