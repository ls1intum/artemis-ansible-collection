"""Check the effective core and Valkey settings used by AI Worker ownership."""

import os
import json
import shutil
from pathlib import Path
import subprocess
import tempfile
import tarfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class AiWorkerConfigurationTest(unittest.TestCase):
    maxDiff = None

    def render(self, templates, values):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = [Path(tmp) / f'output-{index}' for index in range(len(templates))]
            tasks = [
                {'name': f'Render {source}', 'ansible.builtin.template': {
                    'src': str(ROOT / source), 'dest': str(target), 'mode': '0600'}}
                for source, target in zip(templates, outputs)
            ]
            play = [{'name': 'Render production settings', 'hosts': 'localhost',
                     'gather_facts': False, 'vars': values, 'tasks': tasks}]
            path = Path(tmp) / 'render.yml'
            path.write_text(yaml.safe_dump(play))
            result = subprocess.run(
                ['ansible-playbook', '-i', 'localhost,', '-c', 'local', str(path)],
                capture_output=True, text=True, timeout=60,
                env=dict(os.environ, ANSIBLE_NOCOLOR='1'), check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return [target.read_text() for target in outputs]

    def test_core_and_writer_render_distinct_generation_settings(self):
        templates = ['roles/artemis/templates/application-prod.yml.j2',
                     'roles/artemis/templates/artemis.env.j2']
        defaults = yaml.safe_load((ROOT / 'roles/artemis/defaults/main.yml').read_text())
        for core in (False, True):
            with self.subTest(core=core):
                values = dict(defaults, artemis_computed_is_core_node=core,
                              artemis_hyperion_enabled=core,
                              artemis_hyperion_exercise_generation_enabled=True,
                              artemis_aiworker_ids=['worker-1'] if core else [])
                rendered_yaml, rendered_env = self.render(templates, values)
                config = yaml.safe_load(rendered_yaml)['artemis']
                self.assertEqual(config['hyperion']['enabled'], core)
                self.assertTrue(config['hyperion']['exercise-generation']['enabled'])
                self.assertIn("ARTEMIS_HYPERION_EXERCISEGENERATION_ENABLED='true'", rendered_env)
                if core:
                    self.assertEqual(config['aiworker']['ids'], ['worker-1'])
                    self.assertIn("ARTEMIS_AIWORKER_IDS='worker-1'", rendered_env)
                else:
                    self.assertNotIn('aiworker', config)
                    self.assertNotIn('ARTEMIS_AIWORKER_IDS=', rendered_env)

    def test_valkey_renders_synchronous_non_eviction_storage(self):
        values = yaml.safe_load((ROOT / 'roles/valkey/defaults/main.yml').read_text())
        values.update({'valkey_wireguard_address': '10.0.0.1',
                       'valkey_appendonly': True, 'valkey_appendfsync': 'always',
                       'valkey': {'port': 6379, 'username': 'artemis',
                                  'password': 'test-app', 'admin_username': 'admin',
                                  'admin_password': 'test-admin'}})
        (config,) = self.render(['roles/valkey/templates/valkey.conf.j2'], values)
        for setting in ('appendonly yes', 'appendfsync always',
                        'no-appendfsync-on-rewrite no', 'maxmemory-policy noeviction'):
            self.assertIn(setting, config.splitlines())


    def validate(self, task_file, values):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'validate.yml'
            path.write_text(yaml.safe_dump([{
                'name': 'Validate deployment inputs', 'hosts': 'localhost',
                'gather_facts': False, 'vars': values,
                'tasks': [{'ansible.builtin.import_tasks': str(ROOT / task_file)}],
            }]))
            return subprocess.run(
                ['ansible-playbook', '-i', 'localhost,', '-c', 'local', str(path)],
                capture_output=True, text=True, timeout=60, check=False,
            )

    def test_writer_guard_does_not_enable_model_coordination(self):
        defaults = yaml.safe_load((ROOT / 'roles/artemis/defaults/main.yml').read_text())
        for core, enabled, ids, success in [(False, False, [], True), (True, False, [], True),
                                           (True, True, ['generation-1'], True), (True, True, [], False)]:
            with self.subTest(core=core, hyperion=enabled):
                values = dict(defaults, artemis_computed_is_core_node=core,
                              artemis_hyperion_enabled=enabled,
                              artemis_hyperion_exercise_generation_enabled=True,
                              artemis_aiworker_ids=ids,
                              continuous_integration={'localci': {}}, version_control={'localvc': {}})
                result = self.validate('roles/artemis/tasks/ai_worker_validation.yml', values)
                self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
                if not success:
                    self.assertIn('Configure distinct AI Worker IDs', result.stdout)

    def test_generation_settings_use_the_same_values_in_yaml_and_compose(self):
        defaults = yaml.safe_load((ROOT / 'roles/artemis/defaults/main.yml').read_text())
        agent = {'max-job-duration': 'PT20M', 'stale-job-timeout': 'PT25M',
                 'max-tokens-per-job': 700000, 'default-profile': 'review-profile',
                 'profiles': {'review-profile': {'model': 'provider/model-1.2',
                     'display-name': "Instructor's ${NOT_AN_ENV_VAR}", 'context-window-tokens': 128000}}}
        generation = {'max-concurrent-jobs-per-core-node': 3, 'shutdown-drain-timeout': 'PT11M'}
        values = dict(defaults, artemis_computed_is_core_node=True,
                      artemis_hyperion_agent=agent, artemis_hyperion_generation=generation)
        config, env = self.render(['roles/artemis/templates/application-prod.yml.j2',
                                  'roles/artemis/templates/artemis.env.j2'], values)
        hyperion = yaml.safe_load(config)['artemis']['hyperion']
        self.assertEqual(hyperion['agent'], agent)
        self.assertEqual(hyperion['generation'], generation)
        if shutil.which('docker') is None:
            self.skipTest('Docker Compose is needed for the env-file parser check')
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'core.env').write_text(env)
            compose = Path(tmp) / 'compose.yml'
            compose.write_text(yaml.safe_dump({'services': {'core': {
                'image': 'example.invalid/artemis:not-started', 'env_file': [str(Path(tmp) / 'core.env')],
            }}}))
            result = subprocess.run(['docker', 'compose', '--env-file', str(Path(tmp) / 'core.env'), '-f', str(compose), 'config', '--environment'],
                                    capture_output=True, text=True, check=False, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            # --environment exposes parsed values, without config's round-trip dollar escaping.
            application_json = next(line.split('=', 1)[1] for line in result.stdout.splitlines()
                                    if line.startswith('SPRING_APPLICATION_JSON='))
            actual = json.loads(application_json)
            self.assertEqual(actual['artemis']['hyperion'], {'agent': agent, 'generation': generation})

    def test_disabled_string_flags_and_defaults_do_not_emit_generation_overrides(self):
        defaults = yaml.safe_load((ROOT / 'roles/artemis/defaults/main.yml').read_text())
        values = dict(defaults, artemis_computed_is_core_node=True,
                      artemis_hyperion_enabled='false', artemis_hyperion_exercise_generation_enabled='false')
        config, env = self.render(['roles/artemis/templates/application-prod.yml.j2',
                                  'roles/artemis/templates/artemis.env.j2'], values)
        self.assertFalse(yaml.safe_load(config)['artemis']['hyperion']['enabled'])
        self.assertFalse(yaml.safe_load(config)['artemis']['hyperion']['exercise-generation']['enabled'])
        self.assertNotIn('SPRING_APPLICATION_JSON=', env)
        self.assertIn("ARTEMIS_HYPERION_ENABLED='false'", env)

    def test_worker_rejects_unsafe_or_unsupported_inputs(self):
        defaults = yaml.safe_load((ROOT / 'roles/ai_worker/defaults/main.yml').read_text())
        valid = dict(defaults, ai_worker_dedicated_host=True, ai_worker_id='worker-1',
                     ai_worker_image='example.invalid/worker@sha256:' + 'a' * 64,
                     ai_worker_sandbox_image='example.invalid/sandbox@sha256:' + 'b' * 64,
                     ai_worker_eureka_url='https://registry.example.invalid/eureka/',
                     ai_worker_model_base_url='https://model.example.invalid',
                     ai_worker_model='qualified-model', ai_worker_model_api_key='test-key')
        cases = [({'ai_worker_dedicated_host': False}, False),
                 ({'ai_worker_image': 'example.invalid/worker:latest'}, False),
                 ({'ai_worker_workload_version': 2}, False),
                 ({'ai_worker_profile': 'java-maven'}, False),
                 ({'ai_worker_model_api_key': ''}, False),
                 ({'ai_worker_model_options': {'model': 'hidden-override'}}, False),
                 ({'ai_worker_model_options': {'base-url': 'http://insecure.invalid'}}, False),
                 ({'ai_worker_model_options': {'max-retries': 3}}, False),
                 ({'ai_worker_slots': 17}, False),
                 ({'ai_worker_model_options': {'temperature': 0.5}}, True)]
        for override, success in cases:
            with self.subTest(override=override):
                result = self.validate('roles/ai_worker/tasks/validate.yml', dict(valid, **override))
                self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)

    def test_real_environment_inventories_render_separate_core_and_worker_settings(self):
        for environment, slots, enabled in [('test', 1, True), ('staging', 2, True), ('prod', 4, False)]:
            with self.subTest(environment=environment), tempfile.TemporaryDirectory() as tmp:
                inventory = ROOT / 'examples/ai_worker/inventories' / environment / 'hosts.yml'
                worker = {'name': 'Validate worker inventory', 'hosts': 'generation_workers', 'gather_facts': False,
                          'tasks': [
                    {'name': 'Load worker validation only', 'ansible.builtin.include_role': {
                        'name': str(ROOT / 'roles/ai_worker'), 'tasks_from': 'validate', 'public': True}},
                    {'name': 'Read the effective worker configuration', 'ansible.builtin.set_fact': {
                        'config': "{{ lookup('ansible.builtin.template', '" + str(ROOT / 'roles/ai_worker/templates/application.yml.j2') + "') | from_yaml }}"}},
                    {'name': 'Check environment isolation and runtime capability', 'ansible.builtin.assert': {'that': [
                        "config.spring.profiles.active == ['prod', 'aiworker']",
                        'config.artemis.aiworker.id in artemis_aiworker_ids',
                        f"config.artemis.aiworker.id == 'generation-{environment}-1'",
                        f"ai_worker_directory == '/opt/ai-worker-{environment}'",
                        "config.artemis.aiworker.workload == 'hyperion-generation'",
                        "config.artemis.aiworker.profile == 'java-gradle'",
                        "config.artemis.aiworker['workload-version'] == 1",
                        f"config.artemis.aiworker['max-concurrent-executions'] == {slots}",
                        f"config.spring.data.redis.host == 'valkey-{environment}.example.invalid'",
                        f"config.spring.ai.openai.chat.model == 'qualified-{environment}-model'",
                        f"config.spring.ai.openai['base-url'] == 'https://model-{environment}.example.invalid/v1'",
                        "config.spring.main['web-application-type'] == 'none'",
                        'config.eureka.client.enabled == false',
                    ]}}]}
                core = {'name': 'Validate core inventory', 'hosts': 'artemis_cores', 'gather_facts': False,
                        'tasks': [
                            {'name': 'Load core validation only', 'ansible.builtin.include_role': {
                                'name': str(ROOT / 'roles/artemis'), 'tasks_from': 'ai_worker_validation', 'public': True}},
                            {'name': 'Read the effective core YAML', 'ansible.builtin.set_fact': {
                                'core_config': "{{ lookup('ansible.builtin.template', '" + str(ROOT / 'roles/artemis/templates/application-prod.yml.j2') + "') | from_yaml }}"}},
                            {'name': 'Check coordinator settings', 'ansible.builtin.assert': {'that': [
                            f'artemis_hyperion_exercise_generation_enabled == {str(enabled).lower()}',
                            "artemis_hyperion_agent['profiles']['standard']['model'] == 'qualified-" + environment + "-model'",
                            f"artemis_hyperion_generation['max-concurrent-jobs-per-core-node'] == {slots}",
                            'artemis_hyperion_enabled == true',
                            f"core_config.spring.data.redis.host == 'valkey-{environment}.example.invalid'",
                            f"core_config.artemis.hyperion['exercise-generation'].enabled == {str(enabled).lower()}",
                            f"core_config.artemis.hyperion.agent.profiles.standard.model == 'qualified-{environment}-model'",
                        ]}}]}
                play = Path(tmp) / 'inventory.yml'
                play.write_text(yaml.safe_dump([worker, core]))
                fixtures = Path(tmp) / 'fixtures.yml'
                fixtures.write_text(yaml.safe_dump({
                    'ai_worker_release_image': 'example.invalid/worker@sha256:' + 'a' * 64,
                    'ai_worker_release_sandbox_image': 'example.invalid/sandbox@sha256:' + 'b' * 64,
                    'vault_valkey_password': 'provider-test-key', 'vault_ai_worker_model_api_key': 'model-test-key',
                }))
                result = subprocess.run(['ansible-playbook', '-i', str(inventory), '-c', 'local',
                                         str(play), '-e', '@' + str(fixtures)],
                                        capture_output=True, text=True, timeout=60, check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


    def test_packaged_role_validates_each_environment_without_deploying(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            existing = os.environ.get('ANSIBLE_COLLECTIONS_PATH',
                                      str(Path.home() / '.ansible/collections') + ':/usr/share/ansible/collections')
            env = dict(os.environ, ANSIBLE_COLLECTIONS_PATH=str(path / 'collections') + os.pathsep + existing)
            result = subprocess.run(['ansible-galaxy', 'collection', 'build', str(ROOT), '--output-path', tmp],
                                    capture_output=True, text=True, check=False, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            (archive,) = path.glob('*.tar.gz')
            with tarfile.open(archive) as collection:
                names = collection.getnames()
                self.assertIn('roles/ai_worker/tasks/main.yml', names)
                self.assertFalse(any(name.startswith(('.ai/', '.ansible/')) for name in names))
            result = subprocess.run(['ansible-galaxy', 'collection', 'install', str(archive),
                                     '-p', str(path / 'collections'), '--no-deps', '--force'],
                                    capture_output=True, text=True, env=env, check=False, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            fixtures = path / 'fixtures.yml'
            fixtures.write_text(yaml.safe_dump({
                'ai_worker_release_image': 'example.invalid/worker@sha256:' + 'a' * 64,
                'ai_worker_release_sandbox_image': 'example.invalid/sandbox@sha256:' + 'b' * 64,
                'vault_valkey_password': 'provider-test-key', 'vault_ai_worker_model_api_key': 'model-test-key',
            }))
            core_play = path / 'core.yml'
            core_play.write_text(yaml.safe_dump([{
                'name': 'Validate the core role without deployment', 'hosts': 'artemis_cores',
                'gather_facts': False, 'roles': ['ls1intum.artemis.artemis'],
            }]))
            for environment in ('test', 'staging', 'prod'):
                with self.subTest(environment=environment):
                    result = subprocess.run([
                        'ansible-playbook', '-i', str(ROOT / 'examples/ai_worker/inventories' / environment / 'hosts.yml'),
                        '-c', 'local', str(ROOT / 'examples/ai_worker/deploy.yml'),
                        '-e', '@' + str(fixtures), '--tags', 'validation',
                    ], capture_output=True, text=True, env=env, check=False, timeout=60)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertNotIn('Inspect an existing worker', result.stdout)
                    command = [
                        'ansible-playbook', '-i', str(ROOT / 'examples/ai_worker/inventories' / environment / 'hosts.yml'),
                        '-c', 'local', str(core_play), '-e', '@' + str(fixtures), '--tags', 'validation',
                    ]
                    result = subprocess.run(command, capture_output=True, text=True, env=env, check=False, timeout=60)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn('Validate inventory-owned generation settings', result.stdout)
                    if environment == 'test':
                        result = subprocess.run(command + ['-e', '{"artemis_hyperion_agent": []}'],
                                                capture_output=True, text=True, env=env, check=False, timeout=60)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('YAML mappings', result.stdout)


if __name__ == '__main__':
    unittest.main()
