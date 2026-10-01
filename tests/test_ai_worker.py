"""Check the effective core and Valkey settings used by AI Worker ownership."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class AiWorkerConfigurationTest(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
