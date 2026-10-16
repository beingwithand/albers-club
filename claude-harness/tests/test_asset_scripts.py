"""palette.py and psd_layers.py. The pure-Python parts run everywhere; image/PSD IO is skipped
when Pillow or psd-tools is missing."""
import contextlib
import importlib.util
import io
import pathlib
import random
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


palette = load("palette")
psd_layers = load("psd_layers")
HAVE_PIL = importlib.util.find_spec("PIL") is not None
HAVE_PSD = importlib.util.find_spec("psd_tools") is not None


def synthetic(seed=1):
    rng = random.Random(seed)
    jitter = lambda c: tuple(max(0, min(255, v + rng.randint(-6, 6))) for v in c)  # noqa: E731
    return ([jitter((245, 240, 230)) for _ in range(600)] +   # cream background
            [jitter((20, 24, 40)) for _ in range(250)] +      # navy text
            [jitter((230, 40, 60)) for _ in range(100)] +     # red accent
            [jitter((120, 150, 170)) for _ in range(50)])     # grey-blue support


class TestClustering(unittest.TestCase):
    def assertNear(self, a, b, tol=12):
        self.assertTrue(all(abs(x - y) <= tol for x, y in zip(a, b)), f"{a} not near {b}")

    def test_kmeans_finds_clusters(self):
        clusters = palette.kmeans(synthetic(), k=4, seed=0)
        self.assertEqual(len(clusters), 4)
        self.assertEqual([n for _, n in clusters], [600, 250, 100, 50])
        self.assertNear(clusters[0][0], (245, 240, 230))
        self.assertNear(clusters[2][0], (230, 40, 60))

    def test_kmeans_deterministic(self):
        self.assertEqual(palette.kmeans(synthetic(), 4, seed=3), palette.kmeans(synthetic(), 4, seed=3))

    def test_kmeans_fewer_colours_than_k(self):
        out = palette.kmeans([(0, 0, 0)] * 5 + [(255, 255, 255)] * 3, k=6)
        self.assertEqual([n for _, n in out], [5, 3])
        self.assertEqual(palette.kmeans([], 3), [])

    def test_median_cut(self):
        clusters = palette.median_cut(synthetic(), k=4)
        self.assertEqual(len(clusters), 4)
        self.assertEqual(sum(n for _, n in clusters), 1000)
        self.assertNear(clusters[0][0], (245, 240, 230))

    def test_roles(self):
        cols = palette.assign_roles(palette.kmeans(synthetic(), k=4, seed=0))
        roles = {c["role"]: c["hex"] for c in cols}
        self.assertEqual(set(roles), {"background", "text", "accent", "primary"})
        self.assertEqual(cols[0]["role"], "background")
        self.assertAlmostEqual(sum(c["share"] for c in cols), 1.0, places=3)
        text = next(c for c in cols if c["role"] == "text")
        self.assertGreater(text["contrast_vs_background"], 10)
        accent = next(c for c in cols if c["role"] == "accent")
        self.assertGreater(accent["rgb"][0], 200)

    def test_colour_maths(self):
        self.assertEqual(palette.hex_of((255, 0, 16.4)), "#ff0010")
        self.assertAlmostEqual(palette.contrast((0, 0, 0), (255, 255, 255)), 21.0, places=2)
        self.assertAlmostEqual(palette.contrast((10, 10, 10), (10, 10, 10)), 1.0)

    def test_missing_pillow_message(self):
        orig = palette._import_pil
        palette._import_pil = lambda: (None, None)
        self.addCleanup(setattr, palette, "_import_pil", orig)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(palette.main(["whatever.png"]), 2)
        self.assertIn("pip install Pillow", err.getvalue())

    @unittest.skipUnless(HAVE_PIL, "Pillow not installed")
    def test_image_end_to_end(self):
        from PIL import Image
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        im = Image.new("RGBA", (40, 40), (250, 250, 250, 255))
        for x in range(10):
            for y in range(40):
                im.putpixel((x, y), (10, 10, 60, 255))
        for x in range(30, 40):
            for y in range(40):
                im.putpixel((x, y), (0, 0, 0, 0))       # transparent: ignored
        im.save(d / "img.png")
        manifest = d / "assets" / "assets.yaml"
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(palette.main([str(d / "img.png"), "-k", "3", "--manifest", str(manifest)]), 0)
        self.assertIn("#fafafa  background", out.getvalue())
        text = manifest.read_text(encoding="utf-8")
        self.assertIn("type: palette", text)
        self.assertRegex(text, r"id: A-[0-9a-f]{8}-1")
        self.assertEqual(len(list((d / "assets" / "palette").glob("*.json"))), 1)


class FakeLayer(list):
    def __init__(self, name, kind="pixel", children=None, visible=True, text=None, opacity=255,
                 blend="normal", bbox=(0, 0, 10, 10)):
        super().__init__(children or [])
        self.name, self.kind, self.visible, self.text = name, kind, visible, text
        self.opacity, self.blend_mode, self.bbox = opacity, blend, bbox

    def is_group(self):
        return self.kind == "group"


class TestPsdLayers(unittest.TestCase):
    def tree(self):
        return [FakeLayer("Background"),
                FakeLayer("Title", "group", [FakeLayer("Headline", "type", text="가을 전시"),
                                             FakeLayer("Logo", "smartobject", visible=False)]),
                FakeLayer("Shape 1", "shape", opacity=128, blend="multiply")]

    def test_walk_paths_and_kinds(self):
        recs = list(psd_layers.walk(self.tree()))
        self.assertEqual([r["path"] for r in recs],
                         ["Background", "Title", "Title/Headline", "Title/Logo", "Shape 1"])
        self.assertEqual(recs[2]["text"], "가을 전시")
        self.assertFalse(recs[3]["visible"])

    def test_entries_and_yaml(self):
        recs = list(psd_layers.walk(self.tree()))
        sha = "ab12cd34" + "0" * 56
        entries = psd_layers.to_entries(recs, sha, "poster.psd", 4, "psd-tools@1.9", "2026-10-16")
        self.assertEqual(entries[0]["id"], "A-ab12cd34-4")
        self.assertEqual([e["type"] for e in entries], ["layer", "layer", "text", "image", "vector"])
        self.assertIn("hidden", entries[3]["tags"])
        self.assertIn("blend:multiply", entries[4]["tags"])
        self.assertIn("opacity:128", entries[4]["tags"])
        y = psd_layers.entry_yaml(entries[2])
        self.assertIn('source: "knowledge/raw/ab12cd34_poster.psd#Title/Headline"', y)
        self.assertIn("path: null", y)
        self.assertIn('rights: {owner: "unknown", license: "unknown"', y)

    def test_append_continues_ids(self):
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        m = d / "assets" / "assets.yaml"
        sha = "ab12cd34" + "0" * 56
        recs = list(psd_layers.walk(self.tree()))
        psd_layers.append_entries(m, psd_layers.to_entries(recs[:2], sha, "p.psd", 1, "t", "d"))
        text = m.read_text(encoding="utf-8")
        self.assertEqual(psd_layers.existing_indices(text, "ab12cd34"), [1, 2])
        self.assertEqual(psd_layers.next_index(text, "ab12cd34"), 3)
        self.assertEqual(psd_layers.next_index(text, "ffffffff"), 1)
        psd_layers.append_entries(m, psd_layers.to_entries(recs[2:], sha, "p.psd", 3, "t", "d"))
        self.assertEqual(psd_layers.existing_indices(m.read_text(encoding="utf-8"), "ab12cd34"), [1, 2, 3, 4, 5])

    def test_export_text_layer(self):
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        recs = [r for r in psd_layers.walk(self.tree()) if r["kind"] == "type"]
        entries = psd_layers.to_entries(recs, "ab12cd34" + "0" * 56, "p.psd", 1, "t", "d")
        problems = psd_layers.export(entries, d / "assets" / "assets.yaml")
        self.assertEqual(problems, [])
        self.assertEqual(entries[0]["path"], "assets/text/A-ab12cd34-1.txt")
        self.assertEqual((d / "assets" / "text" / "A-ab12cd34-1.txt").read_text(encoding="utf-8"), "가을 전시")

    @unittest.skipIf(HAVE_PSD, "psd-tools installed; missing-dependency path not reachable")
    def test_missing_psd_tools_message(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(psd_layers.main(["x.psd"]), 2)
        self.assertIn("pip install psd-tools", err.getvalue())


if __name__ == "__main__":
    unittest.main()
