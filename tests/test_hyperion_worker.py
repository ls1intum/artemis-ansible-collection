"""Render/validate the real role with Ansible; no Docker, credentials or remote host needed."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class HyperionWorkerTest(unittest.TestCase):
    def run_role(self, overrides=None, render=False):
        values = {
            'hyperion_worker_dedicated_host': True,
            'hyperion_worker_id': 'staging-worker-1',
            'hyperion_worker_image': 'registry.example/worker@sha256:' + 'a' * 64,
            'hyperion_worker_sandbox_image': 'registry.example/sandbox@sha256:' + 'b' * 64,
            'hyperion_worker_broker_url': 'tcp://broker.example:61617?sslEnabled=true&verifyHost=true',
            'hyperion_worker_broker_user': 'worker-user',
            'hyperion_worker_broker_password': 'unit-test-placeholder',
            'hyperion_worker_model_base_url': 'https://model.example',
            'hyperion_worker_model': 'qualified-model',
            'hyperion_worker_model_api_key': 'unit-test-placeholder',
        }
        values.update(overrides or {})
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'application.yml'
            tasks = [{'name': 'Validate the real role', 'ansible.builtin.include_role': {
                'name': 'hyperion_worker', 'tasks_from': 'validate', 'public': True}}]
            if render:
                tasks.append({'name': 'Render worker configuration', 'ansible.builtin.template': {
                    'src': str(ROOT / 'roles/hyperion_worker/templates/application.yml.j2'),
                    'dest': str(output), 'mode': '0600'}, 'no_log': True})
            play = [{'name': 'Verify worker configuration locally', 'hosts': 'localhost',
                     'gather_facts': False, 'vars': values, 'tasks': tasks}]
            path = Path(tmp) / 'test.yml'
            path.write_text(yaml.safe_dump(play))
            env = dict(os.environ, ANSIBLE_ROLES_PATH=str(ROOT / 'roles'), ANSIBLE_NOCOLOR='1')
            result = subprocess.run(['ansible-playbook', '-i', 'localhost,', '-c', 'local', str(path)],
                                    capture_output=True, text=True, env=env, timeout=60)
            config = yaml.safe_load(output.read_text()) if output.exists() else None
            return result, config

    def test_valid_configuration_and_quoted_secrets(self):
        secret = 'test-only: "quoted"\\path\nsecond-line'
        result, config = self.run_role({'hyperion_worker_model_api_key': secret, 'hyperion_worker_slots': 4}, render=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(config['spring']['ai']['openai']['api-key'], secret)
        self.assertEqual(config['spring']['ai']['openai']['chat']['options']['model'], 'qualified-model')
        self.assertEqual(config['spring']['ai']['openai']['max-retries'], 0)
        self.assertEqual(config['artemis']['hyperion']['worker']['max-concurrent-generations'], 4)
        self.assertFalse(config['artemis']['telemetry']['gen-ai']['capture-content'])
        self.assertNotIn('datasource', config['spring'])

    def test_rejects_unsafe_configuration(self):
        for override in [
            {'hyperion_worker_dedicated_host': False},
            {'hyperion_worker_image': 'registry.example/worker:latest'},
            {'hyperion_worker_sandbox_image': 'registry.example/sandbox:latest'},
            {'hyperion_worker_id': '../worker'},
            {'hyperion_worker_toolchain': '../toolchain'},
            {'hyperion_worker_slots': 0},
            {'hyperion_worker_slots': 17},
            {'hyperion_worker_slots': 1.5},
            {'hyperion_worker_broker_url': 'tcp://broker.example:61616'},
            {'hyperion_worker_broker_url': 'tcp://broker.example:61617?sslEnabled=true&trustAll=true'},
            {'hyperion_worker_broker_url': 'tcp://broker.example:61617?sslEnabled=true&verifyHost=false'},
            {'hyperion_worker_model_base_url': 'http://model.example'},
            {'hyperion_worker_model_api_key': ''},
        ]:
            with self.subTest(override=list(override)):
                result, _ = self.run_role(override)
                self.assertNotEqual(result.returncode, 0)

    def test_core_admission_configuration_fails_closed(self):
        valid = {
            'artemis_hyperion_enabled': True,
            'artemis_hyperion_exercise_generation_enabled': True,
            'artemis_computed_is_core_node': True,
            'version_control': {'localvc': {}},
            'continuous_integration': {'localci': {}},
            'artemis_hyperion_workers': {
                'broker_url': 'tcp://broker.example:61617?sslEnabled=true&verifyHost=true',
                'user': 'core-only', 'password': 'unit-test-only', 'ids': ['worker-1']},
        }
        cases = [({}, True), ({'artemis_hyperion_enabled': False}, False),
                 ({'artemis_computed_is_core_node': False}, False),
                 ({'valkey': {'host': 'valkey.example'}}, False),
                 ({'valkey': {'host': 'valkey.example'}, 'valkey_appendonly': True, 'valkey_appendfsync': 'always'}, True),
                 ({'valkey': {'host': 'valkey.example'}, 'valkey_appendonly': True, 'valkey_appendfsync': 'everysec'}, False),
                 ({'valkey': {'host': 'valkey.example'}, 'valkey_appendonly': False, 'valkey_appendfsync': 'always'}, False),
                 ({'valkey': {'host': 'valkey.example'}, 'valkey_appendonly': True, 'valkey_appendfsync': 'always',
                   'valkey_maxmemory_policy': 'allkeys-lru'}, False),
                 ({'artemis_hyperion_workers': {}}, False),
                 ({'artemis_hyperion_workers': dict(valid['artemis_hyperion_workers'], ids='abc')}, False),
                 ({'artemis_hyperion_workers': dict(valid['artemis_hyperion_workers'], ids=['worker', 'worker'])}, False),
                 ({'artemis_hyperion_exercise_generation_enabled': False,
                   'artemis_hyperion_workers': {}, 'valkey': {'host': 'valkey.example'}}, True)]
        for overrides, expected in cases:
            with self.subTest(overrides=list(overrides)), tempfile.TemporaryDirectory() as tmp:
                play = [{'name': 'Validate core authoring opt-in', 'hosts': 'localhost', 'gather_facts': False,
                         'vars': dict(valid, **overrides), 'tasks': [{
                             'name': 'Validate the production core configuration', 'ansible.builtin.import_tasks':
                             str(ROOT / 'roles/artemis/tasks/hyperion_validation.yml')}]}]
                path = Path(tmp) / 'core.yml'
                path.write_text(yaml.safe_dump(play))
                result = subprocess.run(['ansible-playbook', '-i', 'localhost,', '-c', 'local', str(path)],
                                        capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode == 0, expected, result.stdout + result.stderr)

    def test_valkey_renders_synchronous_appendonly_persistence(self):
        values = yaml.safe_load((ROOT / 'roles/valkey/defaults/main.yml').read_text())
        values.update({'valkey_wireguard_address': '10.0.0.1', 'valkey_appendonly': True,
                       'valkey_appendfsync': 'always',
                       'valkey': {'port': 6379, 'username': 'artemis', 'password': 'test-only-app',
                                  'admin_username': 'admin', 'admin_password': 'test-only-admin'}})
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'valkey.conf'
            play = [{'name': 'Render the real Valkey configuration', 'hosts': 'localhost',
                     'gather_facts': False, 'vars': values, 'tasks': [{
                         'name': 'Render synchronous coordination storage', 'ansible.builtin.template': {
                             'src': str(ROOT / 'roles/valkey/templates/valkey.conf.j2'),
                             'dest': str(output), 'mode': '0600'}, 'no_log': True}]}]
            path = Path(tmp) / 'test.yml'
            path.write_text(yaml.safe_dump(play))
            result = subprocess.run(['ansible-playbook', '-i', 'localhost,', '-c', 'local', str(path)],
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            config = output.read_text().splitlines()
            for setting in ['appendonly yes', 'appendfsync always', 'no-appendfsync-on-rewrite no',
                            'maxmemory-policy noeviction']:
                self.assertIn(setting, config)

    def test_container_has_no_network_listener_or_privileged_mode(self):
        tasks = yaml.safe_load((ROOT / 'roles/hyperion_worker/tasks/main.yml').read_text())
        container = next(task['community.docker.docker_container'] for task in tasks if 'community.docker.docker_container' in task)
        self.assertNotIn('published_ports', container)
        self.assertNotIn('privileged', container)
        self.assertTrue(container['read_only'])
        self.assertEqual(container['cap_drop'], ['ALL'])
        self.assertIn('no-new-privileges:true', container['security_opts'])
        self.assertEqual(container['stop_timeout'], 150)
        self.assertEqual(len(container['volumes']), 2)


if __name__ == '__main__':
    unittest.main()
