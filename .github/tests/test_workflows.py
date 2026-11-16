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

    def test_runtime_preflight_precedes_any_render_claim(self):
        steps = self.workflow["jobs"]["render"]["steps"]
        preflight = next(s for s in steps if s["name"] == "Preflight sparse renderer imports")
        render = next(s for s in steps if s["name"] == "Render and upload queued videos")
        self.assertLess(steps.index(preflight), steps.index(render))
        self.assertEqual(preflight["if"], render["if"])
        self.assertEqual(preflight["working-directory"], "renderer-source")
        self.assertEqual(preflight["env"]["PYTHONPATH"], "scripts")
        self.assertIn("importlib.import_module(module)", preflight["run"])
        self.assertNotIn("main()", preflight["run"].split("python3 - <<'PY'")[1])

    def test_preflight_catches_missing_transitive_sparse_import(self):
        import os
        import subprocess
        import sys
        import tempfile

        step = next(s for s in self.workflow["jobs"]["render"]["steps"]
                    if s["name"] == "Preflight sparse renderer imports")
        code = step["run"].split("python3 - <<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            # Synthetic modules only: no private source or runtime requests.
            for module in ("render_profiles", "kids_music", "sfx", "story_renderer", "html_video"):
                (root / (module + ".py")).write_text("")
            (root / "render_short.py").write_text("import missing_sparse_helper\n")
            environment = dict(os.environ, PYTHONPATH=str(root))
            result = subprocess.run([sys.executable, "-c", code], cwd=root, env=environment,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing_sparse_helper", result.stderr)
            (root / "missing_sparse_helper.py").write_text("")
            # Preflight checks executable availability, without executing either.
            for binary in ("ffmpeg", "ffprobe"):
                path = root / binary
                path.write_text("#!/bin/sh\nexit 99\n")
                path.chmod(0o755)
            environment["PATH"] = str(root)
            result = subprocess.run([sys.executable, "-c", code], cwd=root, env=environment,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Renderer import OK: render_short", result.stdout)
            (root / "ffprobe").unlink()
            result = subprocess.run([sys.executable, "-c", code], cwd=root, env=environment,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing required renderer executable: ffprobe", result.stderr)

    def test_diagnostics_identify_source_revision_and_stream_logs(self):
        self.assertEqual(self.workflow["env"]["PYTHONUNBUFFERED"], "1")
        steps = self.workflow["jobs"]["render"]["steps"]
        checkout = next(s for s in steps if s.get("id") == "source")
        self.assertEqual(checkout["with"]["ref"], "main")
        summary = next(s for s in steps if s["name"] == "Report render outcome")
        self.assertEqual(summary["env"]["SOURCE_REVISION"], "${{ steps.source.outputs.commit }}")
        self.assertIn("SOURCE_REVISION", summary["run"])



    def test_optional_smoke_controls_reach_env_without_numeric_zero_fallback(self):
        for name in ("content_id", "max_videos"):
            setting = self.workflow["on"]["workflow_dispatch"]["inputs"][name]
            self.assertEqual(setting["default"], "")
            self.assertEqual(setting["type"], "string")
            expression = self.workflow["env"]["MV_" + name.upper()]
            self.assertIn("inputs." + name, expression)
            # format converts JSON 0 / false to nonempty strings for validation,
            # rather than `value || ''` silently dropping the requested cap.
            self.assertIn("format('{0}', github.event.client_payload." + name + ")", expression)

    def test_smoke_controls_validate_before_any_network_call(self):
        import os
        import subprocess
        import sys

        code = self.workflow["jobs"]["render"]["steps"][0]["run"]
        code = code.split("python3 - <<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
        defaults = dict(os.environ, MV_RENDER_PROFILE="balanced", MV_NARRATION_STYLE="per_video",
                        MV_BATCH="3", MV_BUDGET_MIN="45", MV_CONTENT_ID="", MV_MAX_VIDEOS="")
        cases = [
            ("", "", True),
            ("", "1", True),
            ("0a150cb1-4ae4-426b-bb5c-a37a43cb3ac0", "1", True),
            ("0A150CB1-4AE4-426B-BB5C-A37A43CB3AC0", "100", True),
            ("not-a-uuid", "1", False),
            ("0a150cb14ae4426bbb5ca37a43cb3ac0", "1", False),
            ("../../somewhere", "1", False),
            ("", "0", False),
            ("", "-1", False),
            ("", "101", False),
            ("", "1.0", False),
            ("", "false", False),
            ("", "1; echo injected", False),
        ]
        for content_id, max_videos, valid in cases:
            with self.subTest(content_id=content_id, max_videos=max_videos):
                environment = dict(defaults, MV_CONTENT_ID=content_id, MV_MAX_VIDEOS=max_videos)
                result = subprocess.run([sys.executable, "-c", code], env=environment,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode == 0, valid, result.stderr)


if __name__ == "__main__":
    unittest.main()
