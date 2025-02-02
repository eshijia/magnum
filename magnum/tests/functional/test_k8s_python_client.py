# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from magnum.common.pythonk8sclient.swagger_client import api_client
from magnum.common.pythonk8sclient.swagger_client.apis import apiv_api
from magnum.tests.functional.python_client_base import BaseMagnumClient
from magnum.tests.functional.python_client_base import BayTest
from magnumclient.openstack.common.apiclient import exceptions


class TestBayModelResource(BayTest):
    coe = 'kubernetes'

    def test_baymodel_create_and_delete(self):
        self._test_baymodel_create_and_delete()


class TestBayResource(BayTest):
    coe = 'kubernetes'

    def test_bay_create_and_delete(self):
        self._test_bay_create_and_delete()


class TestKubernetesAPIs(BaseMagnumClient):
    @classmethod
    def setUpClass(cls):
        super(TestKubernetesAPIs, cls).setUpClass()
        cls.baymodel = cls._create_baymodel('testk8sAPI')
        cls.bay = cls._create_bay('testk8sAPI', cls.baymodel.uuid)
        kube_api_address = cls.cs.bays.get(cls.bay.uuid).api_address
        kube_api_url = 'http://%s' % kube_api_address
        k8s_client = api_client.ApiClient(kube_api_url)
        cls.k8s_api = apiv_api.ApivApi(k8s_client)

    @classmethod
    def tearDownClass(cls):
        cls._delete_bay(cls.bay.uuid)
        try:
            cls._wait_on_status(cls.bay,
                                ["CREATE_COMPLETE",
                                 "DELETE_IN_PROGRESS", "CREATE_FAILED"],
                                ["DELETE_FAILED", "DELETE_COMPLETE"])
        except exceptions.NotFound:
            pass
        cls._delete_baymodel(cls.baymodel.uuid)

    def test_pod_apis(self):
        pod_manifest = {'apiVersion': 'v1',
                        'kind': 'Pod',
                        'metadata': {'color': 'blue', 'name': 'test'},
                        'spec': {'containers': [{'image': 'dockerfile/redis',
                                 'name': 'redis'}]}}

        resp = self.k8s_api.create_namespaced_pod(body=pod_manifest,
                                                  namespace='default')
        self.assertEqual(resp.metadata.name, 'test')
        self.assertTrue(resp.status.phase)

        resp = self.k8s_api.read_namespaced_pod(name='test',
                                                namespace='default')
        self.assertEqual(resp.metadata.name, 'test')
        self.assertTrue(resp.status.phase)

        resp = self.k8s_api.delete_namespaced_pod(name='test', body={},
                                                  namespace='default')

    def test_service_apis(self):
        service_manifest = {'apiVersion': 'v1',
                            'kind': 'Service',
                            'metadata': {'labels': {'name': 'frontend'},
                                         'name': 'frontend',
                                         'resourceversion': 'v1'},
                            'spec': {'ports': [{'port': 80,
                                                'protocol': 'TCP',
                                                'targetPort': 80}],
                                     'selector': {'name': 'frontend'}}}

        resp = self.k8s_api.create_namespaced_service(body=service_manifest,
                                                      namespace='default')
        self.assertEqual(resp.metadata.name, 'frontend')
        self.assertTrue(resp.status)

        resp = self.k8s_api.read_namespaced_service(name='frontend',
                                                    namespace='default')
        self.assertEqual(resp.metadata.name, 'frontend')
        self.assertTrue(resp.status)

        resp = self.k8s_api.delete_namespaced_service(name='frontend',
                                                      namespace='default')

    def test_replication_controller_apis(self):
        rc_manifest = {
            'apiVersion': 'v1',
            'kind': 'ReplicationController',
            'metadata': {'labels': {'name': 'frontend'},
                         'name': 'frontend'},
            'spec': {'replicas': 2,
                     'selector': {'name': 'frontend'},
                     'template': {'metadata': {
                         'labels': {'name': 'frontend'}},
                         'spec': {'containers': [{
                             'image': 'nginx',
                             'name': 'nginx',
                             'ports': [{'containerPort': 80,
                                        'protocol': 'TCP'}]}]}}}}

        resp = self.k8s_api.create_namespaced_replication_controller(
            body=rc_manifest, namespace='default')
        self.assertEqual(resp.metadata.name, 'frontend')
        self.assertEqual(resp.spec.replicas, 2)

        resp = self.k8s_api.read_namespaced_replication_controller(
            name='frontend', namespace='default')
        self.assertEqual(resp.metadata.name, 'frontend')
        self.assertEqual(resp.spec.replicas, 2)

        resp = self.k8s_api.delete_namespaced_replication_controller(
            name='frontend', body={}, namespace='default')
