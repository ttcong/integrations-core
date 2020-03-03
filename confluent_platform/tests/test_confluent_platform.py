# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from datadog_checks.confluent_platform import ConfluentPlatformCheck
from .metrics import build_metadata_csv


def test_check(aggregator):
    instance = {}
    check = ConfluentPlatformCheck('confluent_platform', {}, {})
    check.check(instance)

    aggregator.assert_all_metrics_covered()

    build_metadata_csv()
    1/0
