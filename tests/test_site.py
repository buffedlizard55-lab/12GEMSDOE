import sys
from pathlib import Path
from html.parser import HTMLParser
import json, hashlib, rasterio, numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from core import validate


def _needs_data(*paths):
    for p in paths:
        if not Path(p).is_file():
            pytest.skip(f"requires git-ignored data file: {p} "
                        "(run scripts/download_competition_data.sh)")

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ('href', 'src') and v:
                self.links.append(v)

def test_static_links_and_submission_deliverable():
    root = Path(__file__).resolve().parents[1]
    html_files = [root / 'index.html', *root.glob('docs/*.html')]
    assert len(html_files) >= 2, "Must have index.html and executive-summary.html"
    
    for p in html_files:
        parser = Links()
        parser.feed(p.read_text())
        for link in parser.links:
            if not link.startswith(('http', 'https', 'mailto', '#')):
                target = (p.parent / link.split('#')[0]).resolve()
                assert target.exists(), f"Broken link in {p}: {link} -> {target}"

    home = (root / 'docs/index.html').read_text()
    guide = (root / 'docs/executive-summary.html').read_text()
    assert 'Download .TIF' in home and 'Download .TIF' in guide

    # Round-7 primary deliverable must be the one the site hands out (supersedes R6/R5).
    primary = '12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.tif'
    assert primary in home, 'index.html must link the Round-7 primary artifact'
    assert primary in guide, 'executive-summary.html must link the Round-7 primary artifact'
    for name in (primary,
                 primary.replace('.tif', '.zip'),
                 primary.replace('.tif', '_allfinite.tif')):
        assert (root / 'docs/downloads' / name).is_file(), f'missing deliverable: {name}'
    # The primary button must come before any archive button (deliverable obvious at the top).
    assert home.index(primary) < home.index('12GEMSDOE_r6-nms3-h28-texture_8721329b55c7.tif')
    # The step-by-step guide must name the current file, not a stale one.
    assert 'select <code>' + primary in guide, 'guide step 4 must reference the current primary'
    assert '12GEMSDOE-v1 | MultiPhysics25 archive' not in guide, 'stale Round-1 note in guide'

    # Previous Round-6 and Round-5 archives stay downloadable.
    for arch in ('12GEMSDOE_r6-nms3-h28-texture_8721329b55c7.tif', '12GEMSDOE_r5-nms3-trace_055e9aac96b8.tif'):
        assert (root / 'docs/downloads' / arch).is_file(), f'{arch} archive must remain'

    # Live leaderboard feed must be wired and the committed feed parseable.
    assert 'leaderboard.json' in home and (root / 'docs/leaderboard.json').is_file()

    # The superseded round-1..4 archive stays downloadable and referenced.
    archived = '12GEMSDOE_multiphysics_submission_06ca61e5.tif'
    assert (root / 'docs/downloads' / archived).is_file()

    # The copy-to-clipboard note must match the manifest of the shipped artifact.
    manifest = json.loads(
        (root / 'docs/downloads' / primary.replace('.tif', '.json')).read_text())
    note = manifest['suggested_note']
    assert note in home and note in guide, 'site note must match the manifest note'

def test_submission_artifact_strict_conformance():
    root = Path(__file__).resolve().parents[1]
    tif_path = root / 'docs/downloads/12GEMSDOE_multiphysics_submission_06ca61e5.tif'
    template_path = root / 'data/sample_submission.tif'
    _needs_data(tif_path, template_path)

    # Run core.validate() on the actual artifact against template
    report = validate(tif_path, template_path)
    assert report['valid_pixels'] == 5167373
    assert report['min'] >= 0.0
    assert report['max'] <= 1.0
    assert report['sha256'] == '06ca61e5c6a3e55eaf40228d97054a35af1187be9c98e0ef95d996f9919efc6b'
    
    with rasterio.open(tif_path) as s:
        assert s.crs.to_string() == 'EPSG:32611'
        assert s.shape == (3730, 3292)
        assert s.dtypes == ('float32',)
        arr = s.read(1)
        mask = s.read_masks(1) > 0
        assert np.isfinite(arr[mask]).all(), "All valid pixels must be finite (no NaNs inside mask)"
        assert np.isnan(arr[~mask]).all(), "All pixels outside mask must be strict NaN"

def test_archived_result_and_holdout_gain():
    root = Path(__file__).resolve().parents[1]
    evidence_screen = root / 'evidence/screening.json'
    docs_screen = root / 'docs/screening.json'
    assert evidence_screen.is_file()
    assert docs_screen.is_file()
    
    r = json.loads(evidence_screen.read_text())
    assert len(r['folds']) == 4
    # This is deliberately retained as a historical *unmasked* diagnostic.
    # It cannot authorize a new-fault submission because random06 wins.
    assert r['release_allowed'] is False
    assert r['status'] == 'legacy_unmasked_known_fault_diagnostic_not_submission_eligible'
    assert r['means']['multiphysics25'] > r['means']['raw19'], "Historical comparison changed unexpectedly"
    assert r['means']['random06'] > r['means']['multiphysics25']
    assert r['archived_format_artifact']['format_validated_only'] is True
    assert r['archived_format_artifact']['release_authorized'] is False
