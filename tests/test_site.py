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
    assert '12GEMSDOE_multiphysics_submission_06ca61e5.tif' in home
    assert 'Download .TIF' in home
    
    # Check that released GeoTIFF deliverables exist
    tif_path = root / 'docs/downloads/12GEMSDOE_multiphysics_submission_06ca61e5.tif'
    zip_path = root / 'docs/downloads/12GEMSDOE_multiphysics_submission_06ca61e5.zip'
    assert tif_path.is_file(), f"Submission TIF must exist at {tif_path}"
    assert zip_path.is_file(), f"Submission ZIP must exist at {zip_path}"

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
    assert r['release_allowed'] is True
    assert r['means']['multiphysics25'] > r['means']['raw19'], "Multi-Physics must beat baseline"
    # Assert win on all 4 folds
    for delta in r['paired_deltas_multiphysics25_vs_raw19']:
        assert delta > 0, "Multi-Physics 25 must win every fold"
