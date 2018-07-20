# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

# stdlib
# import copy

# project
import conftest
from datadog_checks.sqlserver import SQLServer

"""
Runs against AppVeyor's SQLServer setups with their default configurations
"""


def test_check_sql2008(aggregator, spin_up_sqlserver, get_config, get_sql2008_instance):
    sqlserver_check = SQLServer(conftest.CHECK_NAME, get_config, {})
    sqlserver_check.check(get_sql2008_instance)
    aggregator.assert_metric('sqlserver.clr.executioon', count=1)
    aggregator.assert_metric('sqlserver.exec.in_progress', count=1)
    for m in aggregator._metrics:
        print m


'''
@attr('windows')
@attr(requires='sqlserver')
class TestSqlserver(AgentCheckTest):
    """Basic Test for sqlserver integration."""
    CHECK_NAME = 'sqlserver'

    def _test_check(self, config):
        self.run_check_twice(config, force_reload=True)

        # Check our custom metrics
        self.assertMetric('sqlserver.clr.execution')
        self.assertMetric('sqlserver.exec.in_progress')
        # Make sure the ALL custom metric is tagged by db
        self.assertMetricTagPrefix('sqlserver.db.commit_table_entries', tag_prefix='db')

        instance_tags = config['instances'][0].get('tags', [])
        expected_tags = instance_tags + ['host:{}'.format(config['instances'][0]['host']), 'db:master']
        for metric in EXPECTED_METRICS:
            self.assertMetric(metric, count=1)

        self.assertServiceCheckOK('sqlserver.can_connect', tags=expected_tags)

        self.coverage_report()

    @attr('fixme')
    def test_check_2008(self):
        config = copy.deepcopy(CONFIG)
        config['instances'] = [SQL2008_INSTANCE]
        self._test_check(config)

    def test_check_2012(self):
        config = copy.deepcopy(CONFIG)
        config['instances'] = [SQL2012_INSTANCE]
        self._test_check(config)

    @attr('fixme')
    def test_check_2014(self):
        config = copy.deepcopy(CONFIG)
        config['instances'] = [SQL2014_INSTANCE]
        self._test_check(config)

    def test_check_no_connection(self):
        config = copy.deepcopy(CONFIG)
        config['instances'] = [{
            'host': '(local)\SQL2012SP1',
            'username': 'sa',
            'password': 'InvalidPassword',
            'timeout': 1,
            'tags': ['optional:tag1'],
        }]

        with self.assertRaisesRegexp(Exception, 'Unable to connect to SQL Server'):
            self.run_check(config, force_reload=True)

        self.assertServiceCheckCritical('sqlserver.can_connect',
                                        tags=['host:(local)\SQL2012SP1', 'db:master', 'optional:tag1'])

@attr('unix')
@attr('fixme')
@attr(requires='sqlserver')
class TestSqlserverLinux(AgentCheckTest):
    """Basic Test for sqlserver integration."""

    def test_check(self):
        config = copy.deepcopy(CONFIG)
        config['instances'] = [LINUX_INSTANCE]

        self.run_check_twice(config, force_reload=True)

        # FIXME: assert something, someday

'''
