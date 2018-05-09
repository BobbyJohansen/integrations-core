# (C) Datadog, Inc. 2010-2017
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

# stdlib
from nose.plugins.attrib import attr
from time import sleep
from unittest import TestCase
from mock import patch
import re
import copy

# 3p

# project
from tests.checks.common import AgentCheckTest, load_class
from datadog_checks.openstack import OpenStackCheck

from checks import AgentCheck


OS_CHECK_NAME = 'openstack'
OS_CHECK_MODULE = 'openstack.openstack'

OpenStackProjectScope = load_class(OS_CHECK_MODULE, "OpenStackProjectScope")
OpenStackUnscoped = load_class(OS_CHECK_MODULE, "OpenStackUnscoped")
KeystoneCatalog = load_class(OS_CHECK_MODULE, "KeystoneCatalog")
IncompleteConfig = load_class(OS_CHECK_MODULE, "IncompleteConfig")
IncompleteAuthScope = load_class(OS_CHECK_MODULE, "IncompleteAuthScope")
IncompleteIdentity = load_class(OS_CHECK_MODULE, "IncompleteIdentity")


class MockHTTPResponse(object):
    def __init__(self, response_dict, headers):
        self.response_dict = response_dict
        self.headers = headers

    def json(self):
        return self.response_dict


EXAMPLE_AUTH_RESPONSE = {
    u'token': {
        u'methods': [
            u'password'
        ],
        u'roles': [
            {
                u'id': u'f20c215f5a4d47b7a6e510bc65485ced',
                u'name': u'datadog_monitoring'
            },
            {
                u'id': u'9fe2ff9ee4384b1894a90878d3e92bab',
                u'name': u'_member_'
            }
        ],
        u'expires_at': u'2015-11-02T15: 57: 43.911674Z',
        u'project': {
            u'domain': {
                u'id': u'default',
                u'name': u'Default'
            },
            u'id': u'0850707581fe4d738221a72db0182876',
            u'name': u'admin'
        },
        u'catalog': [
            {
                u'endpoints': [
                    {
                        u'url': u'http://10.0.2.15:8773/',
                        u'interface': u'public',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'541baeb9ab7542609d7ae307a7a9d5f0'
                    },
                    {
                        u'url': u'http: //10.0.2.15:8773/',
                        u'interface': u'admin',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'5c648acaea9941659a5dc04fb3b18e49'
                    },
                    {
                        u'url': u'http: //10.0.2.15:8773/',
                        u'interface': u'internal',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'cb70e610620542a1804522d365226981'
                    }
                ],
                u'type': u'compute',
                u'id': u'1398dc02f9b7474eb165106485033b48',
                u'name': u'nova'
            },
            {
                u'endpoints': [
                    {
                        u'url': u'http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876',
                        u'interface': u'internal',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'354e35ed19774e398f80dc2a90d07f4b'
                    },
                    {
                        u'url': u'http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876',
                        u'interface': u'public',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'36e8e2bf24384105b9d56a65b0900172'
                    },
                    {
                        u'url': u'http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876',
                        u'interface': u'admin',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'de93edcbf7f9446286687ec68423c36f'
                    }
                ],
                u'type': u'computev21',
                u'id': u'2023bd4f451849ba8abeaaf283cdde4f',
                u'name': u'novav21'
            },
            {
                u'endpoints': [
                    {
                        u'url': u'http://10.0.2.15:9292',
                        u'interface': u'internal',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'7c1e318d8f7f42029fcb591598df2ef5'
                    },
                    {
                        u'url': u'http://10.0.2.15:9292',
                        u'interface': u'public',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'afcc88b1572f48a38bb393305dc2b584'
                    },
                    {
                        u'url': u'http://10.0.2.15:9292',
                        u'interface': u'admin',
                        u'region': u'RegionOne',
                        u'region_id': u'RegionOne',
                        u'id': u'd9730dbdc07844d785913219da64a197'
                    }
                ],
                u'type': u'network',
                u'id': u'21ad241f26194bccb7d2e49ee033d5a2',
                u'name': u'neutron'
            },

        ],
        u'extras': {

        },
        u'user': {
            u'domain': {
                u'id': u'default',
                u'name': u'Default'
            },
            u'id': u'5f10e63fbd6b411186e561dc62a9a675',
            u'name': u'datadog'
        },
        u'audit_ids': [
            u'OMQQg9g3QmmxRHwKrfWxyQ'
        ],
        u'issued_at': u'2015-11-02T14: 57: 43.911697Z'
    }
}
MOCK_HTTP_RESPONSE = MockHTTPResponse(response_dict=EXAMPLE_AUTH_RESPONSE, headers={"X-Subject-Token": "fake_token"})

EXAMPLE_PROJECTS_RESPONSE = {
    "projects": [
        {
            "domain_id": "1789d1",
            "enabled": True,
            "id": "263fd9",
            "links": {
                "self": "https://example.com/identity/v3/projects/263fd9"
            },
            "name": "Test Group"
        },
    ],
    "links": {
        "self": "https://example.com/identity/v3/auth/projects",
        "previous": None,
        "next": None,
    }
} 
MOCK_HTTP_PROJECTS_RESPONSE = MockHTTPResponse(response_dict=EXAMPLE_PROJECTS_RESPONSE, headers={})

@attr(requires='openstack')
class OSProjectScopeTest(TestCase):
    BAD_AUTH_SCOPES = [
        {'auth_scope': {'project': {}}},
        {'auth_scope': {'project': {'id': ''}}},
        {'auth_scope': {'project': {'name': 'test'}}},
        {'auth_scope': {'project': {'name': 'test', 'domain': {}}}},
        {'auth_scope': {'project': {'name': 'test', 'domain': {'id': ''}}}},
    ]

    GOOD_UNSCOPED_AUTH_SCOPES = [
        {'auth_scope': {}},  # unscoped project
    ]

    GOOD_AUTH_SCOPES = [
        {'auth_scope': {'project': {'id': 'test_project_id'}}},
        {'auth_scope': {'project': {'name': 'test', 'domain': {'id': 'test_id'}}}},
    ]

    BAD_USERS = [
        {'user': {}},
        {'user': {'name': ''}},
        {'user': {'name': 'test_name', 'password': ''}},
        {'user': {'name': 'test_name', 'password': 'test_pass', 'domain': {}}},
        {'user': {'name': 'test_name', 'password': 'test_pass', 'domain': {'id': ''}}},
    ]

    GOOD_USERS = [
        {'user': {'name': 'test_name', 'password': 'test_pass', 'domain': {'id': 'test_id'}}},
    ]

    def _test_bad_auth_scope(self, scope):
        self.assertRaises(IncompleteAuthScope, OpenStackProjectScope.get_auth_scope, scope)

    def test_get_auth_scope(self):
        for scope in self.BAD_AUTH_SCOPES:
            self._test_bad_auth_scope(scope)

        for scope in self.GOOD_UNSCOPED_AUTH_SCOPES:
            auth_scope = OpenStackProjectScope.get_auth_scope(scope)
            self.assertEqual(auth_scope, None)
            auth_scope = OpenStackUnscoped.get_auth_scope(scope)

            self.assertEqual(auth_scope, None)

        for scope in self.GOOD_AUTH_SCOPES:
            auth_scope = OpenStackProjectScope.get_auth_scope(scope)

            # Should pass through unchanged
            self.assertEqual(auth_scope, scope.get('auth_scope'))

    def _test_bad_user(self, user):
        self.assertRaises(IncompleteIdentity, OpenStackProjectScope.get_user_identity, user)


    def test_get_user_identity(self):
        for user in self.BAD_USERS:
            self._test_bad_user(user)

        for user in self.GOOD_USERS:
            parsed_user = OpenStackProjectScope.get_user_identity(user)
            self.assertEqual(parsed_user, {'methods': ['password'], 'password': user})

    def test_from_config(self):
        init_config = {'keystone_server_url': 'http://10.0.2.15:5000', 'nova_api_version': 'v2'}
        bad_instance_config = {}

        good_instance_config = {'user': self.GOOD_USERS[0]['user'], 'auth_scope': self.GOOD_AUTH_SCOPES[0]['auth_scope']}

        self.assertRaises(IncompleteConfig, OpenStackProjectScope.from_config, init_config, bad_instance_config)

        with patch('datadog_checks.openstack.openstack.OpenStackProjectScope.request_auth_token', return_value=MOCK_HTTP_RESPONSE):
            append_config = good_instance_config.copy()
            append_config['append_tenant_id'] = True
            scope = OpenStackProjectScope.from_config(init_config, append_config)
            self.assertTrue(isinstance(scope, OpenStackProjectScope))

            self.assertEqual(scope.auth_token, 'fake_token')
            self.assertEqual(scope.tenant_id, 'test_project_id')

            # Test that append flag worked
            self.assertEqual(scope.service_catalog.nova_endpoint, 'http://10.0.2.15:8773/test_project_id')

    def test_unscoped_from_config(self):
        init_config = {'keystone_server_url': 'http://10.0.2.15:5000', 'nova_api_version': 'v2'}

        good_instance_config = {'user': self.GOOD_USERS[0]['user'], 'auth_scope': self.GOOD_UNSCOPED_AUTH_SCOPES[0]['auth_scope']}

        mock_http_response = copy.deepcopy(EXAMPLE_AUTH_RESPONSE)
        mock_http_response['token'].pop('catalog')
        mock_http_response['token'].pop('project')
        mock_response = MockHTTPResponse(response_dict=mock_http_response, headers={'X-Subject-Token': 'fake_token'})
        with patch('datadog_checks.openstack.openstack.OpenStackUnscoped.request_auth_token', return_value=mock_response):
            with patch('datadog_checks.openstack.openstack.OpenStackUnscoped.request_project_list', return_value=MOCK_HTTP_PROJECTS_RESPONSE):
                with patch('datadog_checks.openstack.openstack.OpenStackUnscoped.get_token_for_project', return_value=MOCK_HTTP_RESPONSE):
                    append_config = good_instance_config.copy()
                    append_config['append_tenant_id'] = True
                    scope = OpenStackUnscoped.from_config(init_config, append_config)
                    self.assertTrue(isinstance(scope, OpenStackUnscoped))

                    self.assertEqual(scope.auth_token, 'fake_token')
                    self.assertEqual(len(scope.project_scope_map), 1)
                    for _, scope in scope.project_scope_map.iteritems():
                        self.assertTrue(isinstance(scope, OpenStackProjectScope))
                        self.assertEqual(scope.auth_token, 'fake_token')
                        self.assertEqual(scope.tenant_id, '263fd9')


@attr(requires='openstack')
class KeyStoneCatalogTest(TestCase):

    def test_get_nova_endpoint(self):
        self.assertEqual(KeystoneCatalog.get_nova_endpoint(EXAMPLE_AUTH_RESPONSE), u'http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876')
        self.assertEqual(KeystoneCatalog.get_nova_endpoint(EXAMPLE_AUTH_RESPONSE, nova_api_version='v2'), u'http://10.0.2.15:8773/')

    def test_get_neutron_endpoint(self):
        self.assertEqual(KeystoneCatalog.get_neutron_endpoint(EXAMPLE_AUTH_RESPONSE), u'http://10.0.2.15:9292')

    def test_from_auth_response(self):
        catalog = KeystoneCatalog.from_auth_response(EXAMPLE_AUTH_RESPONSE, 'v2.1')
        self.assertTrue(isinstance(catalog, KeystoneCatalog))
        self.assertEqual(catalog.neutron_endpoint, u'http://10.0.2.15:9292')
        self.assertEqual(catalog.nova_endpoint, u'http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876')


@attr(requires='openstack')
class TestOpenstack(AgentCheckTest):
    '''Test for openstack integration.'''
    CHECK_NAME = OS_CHECK_NAME

    # Samples
    # .. server/network
    ALL_SERVER_DETAILS = {
        "server-1":{"id":"server-1", "name":"server-name-1", "status":"ACTIVE"},
        "server-2":{"id":"server-2", "name":"server-name-2", "status":"ACTIVE"},
        "other-1":{"id":"other-1", "name":"server-name-other-1", "status":"ACTIVE"},
        "other-2":{"id":"other-2", "name":"server-name-other-2", "status":"ACTIVE"}
    }
    ALL_IDS = ['server-1', 'server-2', 'other-1', 'other-2']
    EXCLUDED_NETWORK_IDS = ['server-1', 'other-.*']
    EXCLUDED_SERVER_IDS = ['server-2', 'other-.*']
    FILTERED_NETWORK_ID = 'server-2'
    FILTERED_SERVER_ID = 'server-1'


    # Example response from - https://developer.openstack.org/api-ref/compute/#list-servers-detailed
    # ID and server-name values have been changed for test readability
    MOCK_NOVA_SERVERS = {
        "servers": [
            {
                "OS-DCF:diskConfig": "AUTO",
                "OS-EXT-AZ:availability_zone": "nova",
                "OS-EXT-SRV-ATTR:host": "compute",
                "OS-EXT-SRV-ATTR:hostname": "server-1",
                "OS-EXT-SRV-ATTR:hypervisor_hostname": "fake-mini",
                "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
                "OS-EXT-SRV-ATTR:kernel_id": "",
                "OS-EXT-SRV-ATTR:launch_index": 0,
                "OS-EXT-SRV-ATTR:ramdisk_id": "",
                "OS-EXT-SRV-ATTR:reservation_id": "r-iffothgx",
                "OS-EXT-SRV-ATTR:root_device_name": "/dev/sda",
                "OS-EXT-SRV-ATTR:user_data": "IyEvYmluL2Jhc2gKL2Jpbi9zdQplY2hvICJJIGFtIGluIHlvdSEiCg==",
                "OS-EXT-STS:power_state": 1,
                "OS-EXT-STS:task_state": 'null',
                "OS-EXT-STS:vm_state": "active",
                "OS-SRV-USG:launched_at": "2017-02-14T19:24:43.891568",
                "OS-SRV-USG:terminated_at": 'null',
                "accessIPv4": "1.2.3.4",
                "accessIPv6": "80fe::",
                "hostId": "2091634baaccdc4c5a1d57069c833e402921df696b7f970791b12ec6",
                "host_status": "UP",
                "id": "server-1",
                "metadata": {
                    "My Server Name": "Apache1"
                },
                "name": "new-server-test",
                "status": "DELETED",
                "tags": [],
                "tenant_id": "6f70656e737461636b20342065766572",
                "updated": "2017-02-14T19:24:43Z",
                "user_id": "fake"
            },
            {
                "OS-DCF:diskConfig": "AUTO",
                "OS-EXT-AZ:availability_zone": "nova",
                "OS-EXT-SRV-ATTR:host": "compute",
                "OS-EXT-SRV-ATTR:hostname": "server-2",
                "OS-EXT-SRV-ATTR:hypervisor_hostname": "fake-mini",
                "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
                "OS-EXT-SRV-ATTR:kernel_id": "",
                "OS-EXT-SRV-ATTR:launch_index": 0,
                "OS-EXT-SRV-ATTR:ramdisk_id": "",
                "OS-EXT-SRV-ATTR:reservation_id": "r-iffothgx",
                "OS-EXT-SRV-ATTR:root_device_name": "/dev/sda",
                "OS-EXT-SRV-ATTR:user_data": "IyEvYmluL2Jhc2gKL2Jpbi9zdQplY2hvICJJIGFtIGluIHlvdSEiCg==",
                "OS-EXT-STS:power_state": 1,
                "OS-EXT-STS:task_state": 'null',
                "OS-EXT-STS:vm_state": "active",
                "OS-SRV-USG:launched_at": "2017-02-14T19:24:43.891568",
                "OS-SRV-USG:terminated_at": 'null',
                "accessIPv4": "1.2.3.4",
                "accessIPv6": "80fe::",
                "hostId": "2091634baaccdc4c5a1d57069c833e402921df696b7f970791b12ec6",
                "host_status": "UP",
                "id": "server_newly_added",
                "metadata": {
                    "My Server Name": "Apache1"
                },
                "name": "newly_added_server",
                "status": "ACTIVE",
                "tags": [],
                "tenant_id": "6f70656e737461636b20342065766572",
                "updated": "2017-02-14T19:24:43Z",
                "user_id": "fake"
            }
        ]
    }

    # .. config
    MOCK_CONFIG = {
        'init_config': {
            'keystone_server_url': 'http://10.0.2.15:5000',
            'ssl_verify': False,
            'exclude_network_ids': EXCLUDED_NETWORK_IDS,
        },
        'instances': [
            {
                'name': 'test_name', 'user': {'name': 'test_name', 'password': 'test_pass', 'domain': {'id': 'test_id'}},
                'auth_scope': {'project': {'id': 'test_project_id'}},
            }
        ]
    }

    def setUp(self):
        self.load_check(self.MOCK_CONFIG, self.DEFAULT_AGENT_CONFIG)

    def test_ensure_auth_scope(self):
        instance = self.MOCK_CONFIG["instances"][0]
        instance['tags'] = ['optional:tag1']

        self.assertRaises(KeyError, self.check.get_scope_for_instance, instance)

        with patch('datadog_checks.openstack.openstack.OpenStackProjectScope.request_auth_token', return_value=MOCK_HTTP_RESPONSE):
            scope = self.check.ensure_auth_scope(instance)

            self.assertEqual(self.check.get_scope_for_instance(instance), scope)
            self.check._send_api_service_checks(scope, ['optional:tag1'])

            self.service_checks = self.check.get_service_checks()
            # Sort the tags list
            for sc in self.service_checks:
                sc["tags"].sort()
                tags = ['keystone_server:http://10.0.2.15:5000', 'optional:tag1']
                tags.sort()

                # Can only use assertServiceCheck if we ran the whole check with run_check
                # We mock this API response, so return OK
                if sc.get('check') == self.check.IDENTITY_API_SC:
                    self.assertEqual(sc.get('status'), AgentCheck.OK)
                # URLs are nonexistant, so return CRITICAL
                elif sc.get('check') == self.check.COMPUTE_API_SC:
                    self.assertEqual(sc.get('status'), AgentCheck.CRITICAL)
                elif sc.get('check') == self.check.NETWORK_API_SC:
                    self.assertEqual(sc.get('status'), AgentCheck.CRITICAL)

            self.check._current_scope = scope

        self.check.delete_current_scope()
        self.assertRaises(KeyError, self.check.get_scope_for_instance, instance)

    def test_parse_uptime_string(self):
        uptime_parsed = self.check._parse_uptime_string(u' 16:53:48 up 1 day, 21:34,  3 users,  load average: 0.04, 0.14, 0.19\n')
        self.assertEqual(uptime_parsed.get('loads'), [0.04, 0.14, 0.19])

    def test_cache_utils(self):
        self.check.CACHE_TTL['aggregates'] = 1
        expected_aggregates = {'hyp_1': ['aggregate:staging', 'availability_zone:test']}

        with patch('datadog_checks.openstack.OpenStackCheck.get_all_aggregate_hypervisors', return_value=expected_aggregates):
            self.assertEqual(self.check._get_and_set_aggregate_list(), expected_aggregates)
            sleep(1.5)
            self.assertTrue(self.check._is_expired('aggregates'))

    @patch('datadog_checks.openstack.OpenStackCheck.get_all_servers', return_value=ALL_SERVER_DETAILS)
    def test_server_exclusion(self, *args):
        """
        Exclude servers using regular expressions.
        """
        openstackCheck = OpenStackCheck("test", {
            'keystone_server_url': 'http://10.0.2.15:5000',
            'ssl_verify': False,
            'exclude_server_ids': self.EXCLUDED_SERVER_IDS
        }, {}, instances=self.MOCK_CONFIG)

        # Retrieve servers
        openstackCheck.server_details_by_id = copy.deepcopy(self.ALL_SERVER_DETAILS)
        i_key = "test_instance"
        server_ids = openstackCheck.get_servers_managed_by_hypervisor(i_key, False, False)
    
        # Assert
        # .. 1 out of 4 server ids filtered
        self.assertEqual(len(server_ids), 1)

        # Ensure the server IDs filtered are the ones expected
        for server_id in server_ids:
            assert server_id in self.FILTERED_SERVER_ID


    @patch('datadog_checks.openstack.OpenStackCheck.get_all_network_ids', return_value=ALL_IDS)
    def test_network_exclusion(self, *args):
        """
        Exclude networks using regular expressions.
        """
        with patch('datadog_checks.openstack.OpenStackCheck.get_stats_for_single_network') \
                as mock_get_stats_single_network:

            self.check.exclude_network_id_rules = set([re.compile(rule) for rule in self.EXCLUDED_NETWORK_IDS])

            # Retrieve network stats
            self.check.get_network_stats([])

            # Assert
            # .. 1 out of 4 network filtered in
            self.assertEqual(mock_get_stats_single_network.call_count, 1)
            self.assertEqual(
                mock_get_stats_single_network.call_args[0][0], self.FILTERED_NETWORK_ID
            )

            # cleanup
            self.check.exclude_network_id_rules = set([])

    @patch('datadog_checks.openstack.OpenStackCheck._make_request_with_auth_fallback', return_value=MOCK_NOVA_SERVERS)
    @patch('datadog_checks.openstack.OpenStackCheck.get_nova_endpoint', return_value="http://10.0.2.15:8774/v2.1/0850707581fe4d738221a72db0182876")
    @patch('datadog_checks.openstack.OpenStackCheck.get_auth_token', return_value="test_auth_token")
    @patch('datadog_checks.openstack.OpenStackCheck.get_project_name_from_id', return_value="tenant-1")
    def test_cache_between_runs(self, *args):
        """
        Ensure the cache contains the expected VMs between check runs.
        """

        openstackCheck = OpenStackCheck("test", {
            'keystone_server_url': 'http://10.0.2.15:5000',
            'ssl_verify': False,
            'exclude_server_ids': self.EXCLUDED_SERVER_IDS
        }, {}, instances=self.MOCK_CONFIG)

        # Start off with a list of servers 
        openstackCheck.server_details_by_id = copy.deepcopy(self.ALL_SERVER_DETAILS)
        i_key = "test_instance"

        # Update the cached list of servers based on what the endpoint returns
        cached_servers = openstackCheck.get_all_servers(i_key, False)

        assert 'server-1' not in cached_servers
        assert 'server_newly_added' in cached_servers
