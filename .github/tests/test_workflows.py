import unittest
from pathlib import Path
import yaml

class WorkflowContract(unittest.TestCase):
    def setUp(self):
        self.source = Path(".github/workflows/render.yml").read_text()
        # BaseLoader deliberately preserves the YAML 1.2 `on` key.
        self.workflow = yaml.load(self.source, Loader=yaml.BaseLoader)

    def test_render_never_runs_automatically_on_code_push(self):
        self.assertNotIn("push", self.workflow["on"])
        self.assertEqual(self.workflow["on"]["repository_dispatch"]["types"], ["render-metaverse"])

    def test_render_controls_are_validated_before_network_or_claims(self):
        steps = self.workflow["jobs"]["render"]["steps"]
        self.assertEqual(steps[0]["name"], "Validate render controls")
        self.assertIn("MV_NARRATION_STYLE", steps[0]["run"])
        self.assertEqual(self.workflow["on"]["workflow_dispatch"]["inputs"]["render_profile"]["options"], ["balanced", "cinematic", "expressive", "reduced_motion"])

    def test_sparse_checkout_has_every_shared_renderer_dependency(self):
        checkout = next(s for s in self.workflow["jobs"]["render"]["steps"] if s.get("uses", "").startswith("actions/checkout@"))
        for module in ["render_short.py", "render_profiles.py", "story_renderer.py", "kids_music.py", "sfx.py"]:
            self.assertIn("scripts/" + module, checkout["with"]["sparse-checkout"])
        self.assertEqual(checkout["with"]["ref"], "main")
        self.assertEqual(checkout["with"]["persist-credentials"], "false")

    def test_dispatch_values_are_env_not_interpolated_shell(self):
        self.assertIn("github.event.client_payload.render_profile", self.workflow["env"]["MV_RENDER_PROFILE"])
        for step in self.workflow["jobs"]["render"]["steps"]:
            self.assertNotIn("github.event.client_payload", step.get("run", ""))

if __name__ == "__main__":
    unittest.main()
