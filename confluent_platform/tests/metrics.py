# (C) Datadog, Inc. 2019-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import csv
import io
import os
import re

from .common import HERE

GAUGE = 'gauge'
RATE = 'rate'
COUNT = 'count'


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
        metric_name = alias.replace('$domain', camel_to_snake(self.domain))
        metric_name = metric_name.replace('$type', camel_to_snake(self.props['type']))
        metric_name = metric_name.replace('$name', camel_to_snake(self.props['name']))
        return metric_name


def get_beans_config():
    all_beans = []
    for component in ['broker']:
        with open(os.path.join(HERE, 'metrics', '{}.csv'.format(component)), 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                check_metric = row['check_metric'] == 'TRUE'
                bean = MBean(row['bean'],
                             yammer_type=row['type'],
                             unit_name=row['unit_name'],
                             desc=row['description'],
                             check_metric=check_metric)
                all_beans.append(bean)

    return [
        {
            # Yammer Gauge
            # https://metrics.dropwizard.io/2.2.0/apidocs/com/yammer/metrics/core/Gauge.html
            'alias': '$domain.$type.$name',
            'metrics': [
                Metric(GAUGE),
            ],
            'beans': [b for b in all_beans if b.yammer_type == 'YAMMER_GAUGE']
        },
        {
            # Yammer Meter
            # https://metrics.dropwizard.io/2.2.0/apidocs/com/yammer/metrics/core/Meter.html
            # Note:
            # - `count` is monotonically increasing
            'alias': '$domain.$type.$name',
            'metrics': [
                Metric(COUNT, 'count', check_metric=False),  # `agent check` doesn't return jmx count metrics yet
                Metric(GAUGE, 'fifteen_minute_rate', per_unit_name='second'),
                Metric(GAUGE, 'five_minute_rate', per_unit_name='second'),
                Metric(GAUGE, 'one_minute_rate', per_unit_name='second'),
                Metric(GAUGE, 'mean_rate', per_unit_name='second'),
            ],
            'beans': [b for b in all_beans if b.yammer_type == 'YAMMER_METER']
        },
        {
            # Yammer Timer
            # https://metrics.dropwizard.io/2.2.0/apidocs/com/yammer/metrics/core/Timer.html
            # Note:
            # - `count` is monotonically increasing
            'alias': '$domain.$type.$name',
            'metrics': [
                Metric(COUNT, 'count', check_metric=False),  # `agent check` doesn't return jmx count metrics yet
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
            'beans': [b for b in all_beans if b.yammer_type == 'YAMMER_TIMER']
        },
        {
            # Yammer Histogram
            # https://metrics.dropwizard.io/2.2.0/apidocs/com/yammer/metrics/core/Histogram.html
            # Note:
            # - `count` is monotonically increasing
            'alias': '$domain.$type.$name',
            'metrics': [
                Metric(COUNT, 'count', check_metric=False),  # `agent check` doesn't return jmx count metrics yet
                Metric(GAUGE, '50percentile', per_unit_name='second'),
                Metric(GAUGE, '75percentile', per_unit_name='second'),
                Metric(GAUGE, '95percentile', per_unit_name='second'),
                Metric(GAUGE, '98percentile', per_unit_name='second'),
                Metric(GAUGE, '99percentile', per_unit_name='second'),
                Metric(GAUGE, '999percentile', per_unit_name='second'),
                Metric(GAUGE, 'max', per_unit_name='second'),
                Metric(GAUGE, 'mean', per_unit_name='second'),
                Metric(GAUGE, 'min', per_unit_name='second'),
                Metric(GAUGE, 'std_dev', per_unit_name='second'),
            ],
            'beans': [b for b in all_beans if b.yammer_type == 'YAMMER_HISTOGRAM']
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
    for group in get_beans_config():
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
