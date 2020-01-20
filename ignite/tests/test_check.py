# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

import pytest


@pytest.mark.e2e
def test_e2e(dd_agent_check):
    instance = {}
    aggregator = dd_agent_check(instance)
    metrics = [
    ]
    for metric in metrics:
        aggregator.assert_metric(metric)
