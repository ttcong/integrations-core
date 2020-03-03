# (C) Datadog, Inc. 2019-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import csv
import io
import re
import sys


TYPE_GAUGE = 'com.yammer.metrics.reporting.JmxReporter$Gauge'
TYPE_KAFKA_MBEAN = 'com.yammer.metrics.reporting.JmxReporter$Gauge'


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
        'suffixes': ['avg', 'count'],
        'beans': [
            MBean('kafka.server:type=ReplicaManager,name=UnderMinIsrPartitionCount', TYPE_GAUGE),
            MBean('kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions', TYPE_GAUGE),
        ]
    }
    # MBean('kafka.cluster:type=Partition,topic={topic},name=UnderMinIsr,partition={partition}', attrs=[
    #     Attribute('hello')
    # ], clazz=TYPE_KAFKA_MBEAN),
]


def build_metadata_csv():
    headers = 'metric_name,metric_type,interval,unit_name,per_unit_name,description,orientation,integration,short_name'.split(',')
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=headers)
    writer.writeheader()

    def write_metric(metric_name, bean):
        writer.writerow({
            'metric_name': metric_name,
            'metric_type': 'gauge',
        })

    for group in MBEANS:
        alias = group['alias']
        suffixes = group['suffixes']
        for bean in group['beans']:
            if suffixes:
                for suffix in suffixes:
                    write_metric("{}.{}".format(bean.get_metric_name(alias), suffix), bean)
            else:
                write_metric(bean.get_metric_name(alias), bean)
    content = out.getvalue()
    out.close()
    return content


def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
