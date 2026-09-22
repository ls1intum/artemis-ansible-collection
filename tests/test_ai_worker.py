"""Render/validate the real role with Ansible; no Docker, credentials or remote host needed."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class AiWorkerTest(unittest.TestCase):
    def run_role(self, overrides=None, render=False):
        values = {
            'ai_worker_dedicated_host': True,
            'ai_worker_workload': 'hyperion-generation',
            'ai_worker_profile': 'java-gradle',
            'ai_worker_id': 'staging-worker-1',
            'ai_worker_image': 'registry.example/worker@sha256:' + 'a' * 64,
            'ai_worker_sandbox_image': 'registry.example/sandbox@sha256:' + 'b' * 64,
            'ai_worker_broker_url': 'tcp://broker.example:61617?sslEnabled=true&verifyHost=true',
            'ai_worker_broker_user': 'worker-user',
            'ai_worker_broker_password': 'unit-test-placeholder',
            'ai_worker_model_base_url': 'https://model.example',
            'ai_worker_model': 'qualified-model',
            'ai_worker_model_api_key': 'unit-test-placeholder',
        }
        values.update(overrides or {})
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'application.yml'
            tasks = [{'name': 'Validate the real role', 'ansible.builtin.include_role': {
                'name': 'ai_worker', 'tasks_from': 'validate', 'public': True}}]
            if render:
                tasks.append({'name': 'Render worker configuration', 'ansible.builtin.template': {
                    'src': str(ROOT / 'roles/ai_worker/templates/application.yml.j2'),
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
        result, config = self.run_role({'ai_worker_model_api_key': secret, 'ai_worker_slots': 4}, render=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(config['spring']['ai']['openai']['api-key'], secret)
        self.assertEqual(config['spring']['ai']['openai']['chat']['options']['model'], 'qualified-model')
        self.assertEqual(config['spring']['ai']['openai']['max-retries'], 0)
        self.assertEqual(config['artemis']['aiworker']['max-concurrent-executions'], 4)
        self.assertFalse(config['artemis']['telemetry']['gen-ai']['capture-content'])
        self.assertNotIn('datasource', config['spring'])

    def test_other_workload_does_not_require_model_credentials(self):
        result, config = self.run_role({'ai_worker_workload': 'document-check', 'ai_worker_profile': 'text',
                                        'ai_worker_model_api_key': '', 'ai_worker_model': '', 'ai_worker_model_base_url': ''}, render=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(config['spring']['ai']['model']['chat'], 'none')
        self.assertEqual(config['artemis']['aiworker']['workload'], 'document-check')

    def test_colocated_installation_requires_an_explicit_separate_daemon(self):
        result, _ = self.run_role({'ai_worker_dedicated_host': False, 'ai_worker_isolated_daemon': True})
        self.assertNotEqual(result.returncode, 0)
        result, _ = self.run_role({'ai_worker_dedicated_host': False, 'ai_worker_isolated_daemon': True,
                                   'ai_worker_docker_socket': '/run/isolated-worker/docker.sock'})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        tasks = yaml.safe_load((ROOT / 'roles/ai_worker/tasks/main.yml').read_text())
        for task in tasks:
            for module, arguments in task.items():
                if module.startswith('community.docker.'):
                    self.assertEqual(arguments['docker_host'], 'unix://{{ ai_worker_docker_socket }}')

    def test_rejects_unsafe_configuration(self):
        for override in [
            {'ai_worker_dedicated_host': False},
            {'ai_worker_image': 'registry.example/worker:latest'},
            {'ai_worker_sandbox_image': 'registry.example/sandbox:latest'},
            {'ai_worker_id': '../worker'},
            {'ai_worker_profile': '../toolchain'},
            {'ai_worker_slots': 0},
            {'ai_worker_slots': 17},
            {'ai_worker_slots': 1.5},
            {'ai_worker_broker_url': 'tcp://broker.example:61616'},
            {'ai_worker_broker_url': 'tcp://broker.example:61617?sslEnabled=true&trustAll=true'},
            {'ai_worker_broker_url': 'tcp://broker.example:61617?sslEnabled=true&verifyHost=false'},
            {'ai_worker_broker_url': 'tcp://broker.example:61617?sslEnabled=true&trustAll=TrUe'},
            {'ai_worker_broker_url': 'tcp://broker.example:61617?sslEnabled=true&verifyHost=FaLsE'},
            {'ai_worker_model_base_url': 'http://model.example'},
            {'ai_worker_model_api_key': ''},
        ]:
            with self.subTest(override=list(override)):
                result, _ = self.run_role(override)
                self.assertNotEqual(result.returncode, 0)

    def test_core_admission_configuration_fails_closed(self):
        valid = {
            'artemis_aiworker_enabled': False,
            'artemis_hyperion_enabled': True,
            'artemis_hyperion_exercise_generation_enabled': True,
            'artemis_computed_is_core_node': True,
            'version_control': {'localvc': {}},
            'continuous_integration': {'localci': {}},
            'artemis_aiworker': {
                'broker_url': 'tcp://broker.example:61617?sslEnabled=true&verifyHost=true',
                'user': 'core-only', 'password': 'unit-test-only', 'ids': ['worker-1']},
        }
        cases = [({}, True), ({'artemis_hyperion_enabled': False}, True),
                 ({'artemis_hyperion_enabled': False, 'artemis_aiworker_enabled': False,
                   'artemis_computed_is_core_node': False, 'artemis_aiworker': {}}, True),
                 ({'artemis_hyperion_enabled': False, 'artemis_aiworker_enabled': False,
                   'valkey': {'host': 'valkey.example'}}, False),
                 ({'artemis_computed_is_core_node': False}, False),
                 ({'valkey': {'host': 'valkey.example'}}, False),
                 ({'valkey': {'host': 'valkey.example'}, 'valkey_appendonly': True, 'valkey_appendfsync': 'always'}, True),
                 ({'valkey': {'host': 'valkey.example'}, 'valkey_appendonly': True, 'valkey_appendfsync': 'everysec'}, False),
                 ({'valkey': {'host': 'valkey.example'}, 'valkey_appendonly': False, 'valkey_appendfsync': 'always'}, False),
                 ({'valkey': {'host': 'valkey.example'}, 'valkey_appendonly': True, 'valkey_appendfsync': 'always',
                   'valkey_maxmemory_policy': 'allkeys-lru'}, False),
                 ({'artemis_aiworker': {}}, False),
                 ({'artemis_aiworker': dict(valid['artemis_aiworker'], ids='abc')}, False),
                 ({'artemis_aiworker': dict(valid['artemis_aiworker'], ids=['worker', 'worker'])}, False),
                 ({'artemis_aiworker_enabled': False, 'artemis_hyperion_exercise_generation_enabled': False,
                   'artemis_aiworker': {}, 'valkey': {'host': 'valkey.example'}}, True)]
        cases.extend([({'artemis_aiworker_enabled': True, 'artemis_hyperion_enabled': False,
                        'artemis_hyperion_exercise_generation_enabled': False}, True),
                      ({'artemis_aiworker_enabled': True, 'artemis_hyperion_enabled': False,
                        'artemis_hyperion_exercise_generation_enabled': False, 'artemis_aiworker': {}}, False)])
        for option in ['trustAll=TRUE', 'verifyHost=FALSE', 'trustAll=TrUe', 'verifyHost=FaLsE']:
            cases.append(({'artemis_aiworker': dict(valid['artemis_aiworker'],
                          broker_url='tcp://broker.example:61617?sslEnabled=true&' + option)}, False))
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

    def render_writer_configuration(self, core_node, generation_core=False):
        values = yaml.safe_load((ROOT / 'roles/artemis/defaults/main.yml').read_text())
        values.update({'artemis_aiworker_enabled': 'false', 'artemis_aiworker': {},
                       'artemis_computed_is_core_node': core_node,
                       'artemis_hyperion_enabled': generation_core, 'artemis_hyperion_exercise_generation_enabled': True})
        if generation_core:
            values['artemis_aiworker'] = {'broker_url': 'tcp://broker.example:61617?sslEnabled=true&verifyHost=true',
                                          'user': 'core-only', 'password': 'unit-test-only', 'ids': ['worker-1']}
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'application.yml'
            play = [{'name': 'Render production configuration with string false', 'hosts': 'localhost',
                     'gather_facts': False, 'vars': values, 'tasks': [{
                         'name': 'Render actual application template', 'ansible.builtin.template': {
                             'src': str(ROOT / 'roles/artemis/templates/application-prod.yml.j2'),
                             'dest': str(output), 'mode': '0600'}}]}]
            path = Path(tmp) / 'render.yml'
            path.write_text(yaml.safe_dump(play))
            result = subprocess.run(['ansible-playbook', '-i', 'localhost,', '-c', 'local', str(path)],
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            config = yaml.safe_load(output.read_text())['artemis']
            if generation_core:
                self.assertTrue(config['aiworker']['enabled'])
                self.assertEqual(config['aiworker']['ids'], ['worker-1'])
            else:
                self.assertNotIn('aiworker', config)
            self.assertEqual(config['hyperion']['enabled'], generation_core)
            self.assertTrue(config['hyperion']['exercise-generation']['enabled'])

    def test_string_false_omits_worker_configuration(self):
        self.render_writer_configuration(True)

    def test_writer_only_node_renders_generation_guard_without_model_or_broker(self):
        self.render_writer_configuration(False)

    def test_generation_core_renders_worker_without_standalone_flag(self):
        self.render_writer_configuration(True, generation_core=True)

    def test_container_has_no_network_listener_or_privileged_mode(self):
        tasks = yaml.safe_load((ROOT / 'roles/ai_worker/tasks/main.yml').read_text())
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
