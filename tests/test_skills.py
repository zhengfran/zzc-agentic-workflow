"""Offline integration tests for catalog selection, updates, and ownership."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('common', ROOT / 'scripts/skills_common.py')
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)


class SkillsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='skills-test-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / 'catalog'
        self.repo.mkdir()
        shutil.copytree(ROOT / 'scripts', self.repo / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
        self.remote = self.base / 'upstream'
        self.remote.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.data = {'version': 2, 'repositories': {'test': {'url': str(self.remote)}}, 'skills': {}}
        for name in ('one', 'two'):
            self.add_skill(name, 'upstream')
        self.add_skill('custom', 'custom')
        self.commit()
        self.save()
        self.target = self.base / 'project'
        self.target.mkdir()
        self.dst = self.target / '.agents/skills'

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.remote), *args], check=True, capture_output=True, text=True)

    def add_skill(self, name, policy):
        src = self.remote / 'skills' / name
        src.mkdir(parents=True)
        (src / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Test\n---\noriginal\n')
        shutil.copytree(src, self.repo / name)
        self.data['skills'][name] = {'pack': 'coding', 'update': policy}
        if policy == 'upstream':
            self.data['skills'][name].update(repository='test', path=f'skills/{name}', hash=common.folder_hash(src))

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')

    def save(self):
        (self.repo / 'skills.json').write_text(json.dumps(self.data))

    def run_tool(self, tool, *args, success=True):
        result = subprocess.run([str(self.repo / 'scripts' / tool), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def install(self, *args, success=True):
        return self.run_tool('skills-install', 'coding', self.target, '--agents', 'agents', *args, success=success)

    def change_remote(self):
        for name in ('one', 'two'):
            (self.remote / 'skills' / name / 'SKILL.md').write_text(f'upstream changed {name}\n')
        self.commit()

    def test_check_does_not_modify_and_apply_only_updates_selected(self):
        self.change_remote()
        before = (self.repo / 'skills.json').read_bytes()
        result = self.run_tool('skills-update')
        self.assertIn('update available', result.stdout)
        self.assertEqual(before, (self.repo / 'skills.json').read_bytes())
        self.assertIn('original', (self.repo / 'one/SKILL.md').read_text())
        self.run_tool('skills-update', 'one', '--apply')
        self.assertIn('upstream changed', (self.repo / 'one/SKILL.md').read_text())
        self.assertIn('original', (self.repo / 'two/SKILL.md').read_text())
        data = json.loads((self.repo / 'skills.json').read_text())
        self.assertEqual(data['skills']['one']['commit'], self.git('rev-parse', 'HEAD').stdout.strip())
        self.assertNotIn('commit', data['skills']['two'])
        self.assertFalse((self.repo / 'skills').exists())

    def test_diff_shows_changes_and_missing_skill_can_be_restored(self):
        self.change_remote()
        result = self.run_tool('skills-update', 'one', '--diff')
        self.assertIn('+upstream changed one', result.stdout)
        shutil.rmtree(self.repo / 'one')
        result = self.run_tool('skills-update', 'one', '--diff')
        self.assertIn('restore available', result.stdout)
        self.assertFalse((self.repo / 'one').exists())
        self.run_tool('skills-update', 'one', '--apply')
        self.assertIn('upstream changed one', (self.repo / 'one/SKILL.md').read_text())

    def test_update_preserves_symlinks_and_executable_modes(self):
        source = self.remote / 'skills/one'
        script = source / 'run'
        script.write_text('#!/bin/sh\necho ok\n')
        script.chmod(0o755)
        (source / 'linked').symlink_to('run')
        self.commit()
        self.run_tool('skills-update', 'one', '--apply')
        local = self.repo / 'one'
        self.assertTrue((local / 'linked').is_symlink())
        self.assertTrue((local / 'run').stat().st_mode & 0o111)
        self.assertEqual(common.folder_hash(local), common.folder_hash(source))

    def test_custom_and_unselected_apply_rejected_before_fetch(self):
        self.run_tool('skills-update', 'custom', '--apply', success=False)
        self.run_tool('skills-update', '--apply', success=False)
        self.assertFalse((self.repo / '.cache').exists())

    def test_local_edits_survive_upstream_update(self):
        self.change_remote()
        local = self.repo / 'one/SKILL.md'
        local.write_text('my changes\n')
        result = self.run_tool('skills-update', 'one', '--apply', success=False)
        self.assertIn('CONFLICT', result.stdout)
        self.assertEqual(local.read_text(), 'my changes\n')

    def test_apply_all_excludes_custom(self):
        self.change_remote()
        self.run_tool('skills-update', '--all', '--apply')
        self.assertIn('upstream changed', (self.repo / 'two/SKILL.md').read_text())
        self.assertIn('original', (self.repo / 'custom/SKILL.md').read_text())

    def test_missing_upstream_path_fails_without_replacing_local(self):
        self.data['skills']['one']['path'] = 'no-such-path'
        self.save()
        self.run_tool('skills-update', 'one', '--apply', success=False)
        self.assertIn('original', (self.repo / 'one/SKILL.md').read_text())

    def test_install_dry_run_additive_selection_and_owned_pruning(self):
        self.install('--dry-run')
        self.assertFalse(self.dst.exists())
        self.install('--skills', 'one')
        self.assertTrue((self.dst / 'one').is_symlink())
        self.assertFalse((self.dst / 'two').exists())
        self.install('--skills', 'two', '--copy')
        self.assertTrue((self.dst / 'one').is_symlink())
        self.assertFalse((self.dst / 'two').is_symlink())
        (self.dst / 'unrelated').mkdir()
        del self.data['skills']['one']
        self.save()
        self.install()
        self.assertFalse((self.dst / 'one').exists())
        self.assertTrue((self.dst / 'unrelated').is_dir())
        self.assertTrue((self.dst / 'custom').is_symlink())

    def test_unmanaged_collision_preflights_all_destinations(self):
        self.dst.mkdir(parents=True)
        (self.dst / 'one').mkdir()
        (self.dst / 'one/keep').write_text('unmanaged')
        self.run_tool('skills-install', 'coding', self.target, '--agents', 'claude,agents', success=False)
        self.assertFalse((self.target / '.claude').exists())
        self.assertEqual((self.dst / 'one/keep').read_text(), 'unmanaged')

    def test_missing_catalog_skill_and_bad_state_fail_closed(self):
        shutil.rmtree(self.repo / 'one')
        self.install(success=False)
        self.assertFalse(self.dst.exists())
        shutil.copytree(self.remote / 'skills/one', self.repo / 'one')
        self.dst.mkdir(parents=True)
        (self.dst / '.zzc-skills-managed').write_text('zzc-skills\tcoding\t../../outside\n')
        self.install(success=False)
        self.assertFalse((self.dst / 'two').exists())

    def test_unsafe_source_path_rejected_before_fetch(self):
        self.data['skills']['one']['path'] = '../outside'
        self.save()
        self.run_tool('skills-update', success=False)
        self.assertFalse((self.repo / '.cache').exists())

    def test_atomic_replace_rolls_back(self):
        source, local = self.remote / 'skills/one', self.repo / 'one'
        (source / 'SKILL.md').write_text('new')
        real_replace = common.os.replace
        def replace(src, dst):
            if '.new.' in str(src):
                raise OSError('simulated swap failure')
            return real_replace(src, dst)
        with patch.object(common.os, 'replace', side_effect=replace):
            with self.assertRaises(OSError):
                common.atomic_replace_dir(local, source)
        self.assertIn('original', (local / 'SKILL.md').read_text())


if __name__ == '__main__':
    unittest.main()
