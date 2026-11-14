import ast
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class PluginStructureTests(unittest.TestCase):
    def test_manifests_are_valid_json(self):
        plugin = json.loads((REPO_ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "agentic-framework")
        self.assertIn("version", plugin)
        self.assertIn("description", plugin)

        hooks = json.loads((REPO_ROOT / "hooks.json").read_text(encoding="utf-8"))
        self.assertIn("adf-safety-gate", hooks)

    def test_agents_have_frontmatter(self):
        agents = sorted((REPO_ROOT / "agents").glob("*.md"))
        self.assertEqual(len(agents), 6)
        for agent_file in agents:
            text = agent_file.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), f"{agent_file} missing YAML frontmatter")

    def test_skills_have_no_hardcoded_home_paths(self):
        skills = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 5)
        for skill_file in skills:
            text = skill_file.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), f"{skill_file} missing YAML frontmatter")
            self.assertNotIn("/home/", text, f"{skill_file} contains hardcoded /home/ path")

    def test_workflow_scripts_compile_with_top_level_await(self):
        scripts = sorted((REPO_ROOT / "skills").glob("*/scripts/*.py"))
        self.assertEqual(len(scripts), 5)
        for script in scripts:
            with self.subTest(script=script.name):
                source = script.read_text(encoding="utf-8")
                compile(source, str(script), "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)


if __name__ == "__main__":
    unittest.main()
