"""The anonymous release must not fetch an unpublished source dependency."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("review_source", ROOT / "envs/source.py")
source_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source_tool)


class ReviewSourceTests(unittest.TestCase):
    def test_local_dependency_remains_usable_without_git_history_or_network(self):
        row = source_tool.model_spec("failsafe")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            for name in row["source"]:
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# synthetic interface fixture\n")
            with patch.object(source_tool.subprocess, "run", side_effect=AssertionError("no network or Git")):
                self.assertEqual(source_tool.resolve_source("failsafe", row, source), source.resolve())

    def test_implicit_source_resolution_stops_before_any_git_operation(self):
        row = source_tool.model_spec("failsafe")
        with patch.object(source_tool.subprocess, "run", side_effect=AssertionError("no network or Git")):
            with self.assertRaisesRegex(ValueError, "--source IMPORT_ROOT"):
                source_tool.resolve_source("failsafe", row, None)
            with self.assertRaisesRegex(ValueError, "--source IMPORT_ROOT"):
                source_tool.fetch_source("failsafe", row, ROOT)

    def test_other_baselines_keep_their_pinned_public_sources(self):
        row = source_tool.model_spec("liv")
        spec = source_tool.download_spec("liv", row)
        self.assertEqual(spec["repository"], "https://github.com/penn-pal-lab/LIV.git")
        self.assertEqual(spec["revision"], "a12991f53aab01f3cecc1315a81068ba12e2bd6b")
