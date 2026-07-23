"""Opt-in real Huasheng acceptance using only the public SDK.

This test creates a paid/external project, so it is never enabled by default.
It replaces the previous fixed-path script that reimplemented the SDK and only
checked for a CDN URL.  A successful run now requires a complete MP4 plus
ffprobe stream/duration evidence and a SHA-256 digest.
"""

import hashlib
import json
import os
import shutil
import subprocess

import pytest

from huasheng import HuashengClient

pytestmark = pytest.mark.real_external


def _sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as media:
        for chunk in iter(lambda: media.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_environment(name):
    value = os.environ.get(name, "").strip()
    if not value:
        pytest.fail("{} is required when HUASHENG_REAL_E2E=1".format(name))
    return value


def _probe_media(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        pytest.fail("ffprobe is required for real media acceptance")
    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration,format_name:stream=index,codec_type,codec_name",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


@pytest.mark.skipif(
    os.environ.get("HUASHENG_REAL_E2E") != "1",
    reason="set HUASHENG_REAL_E2E=1 to allow a real paid/external project",
)
def test_real_project_download_is_complete_media(tmp_path, record_property):
    sessdata = _required_environment("HUASHENG_SESSDATA")
    bili_jct = _required_environment("HUASHENG_BILI_JCT")
    script = _required_environment("HUASHENG_REAL_SCRIPT")

    client = HuashengClient(
        cookies={"SESSDATA": sessdata, "bili_jct": bili_jct},
        poll_interval=float(os.environ.get("HUASHENG_POLL_INTERVAL", "5")),
        poll_timeout=float(os.environ.get("HUASHENG_POLL_TIMEOUT", "1800")),
    )
    project = client.create_project(script=script)
    completed_project = client.wait_for_completion(project.pid)

    output = tmp_path / "huasheng-real-output.mp4"
    client.export_and_download(
        completed_project.id,
        str(output),
        completed_project.project_hash,
    )

    assert output.is_file()
    assert output.stat().st_size > 1024
    evidence = client.last_download_evidence
    assert evidence is not None
    assert evidence["content_type"].startswith("video/")
    assert evidence["bytes_downloaded"] == output.stat().st_size
    if evidence["content_length"] is not None:
        assert evidence["content_length"] == output.stat().st_size
    assert evidence["sha256"] == _sha256_file(output)

    probe = _probe_media(output)
    assert float(probe["format"]["duration"]) > 0
    assert "mp4" in probe["format"]["format_name"]
    stream_types = {stream["codec_type"] for stream in probe["streams"]}
    assert {"video", "audio"}.issubset(stream_types)
    assert all(stream.get("codec_name") for stream in probe["streams"])

    record_property("download_evidence", json.dumps(evidence, sort_keys=True))
    record_property(
        "media_probe",
        json.dumps(
            {
                "duration": probe["format"]["duration"],
                "format_name": probe["format"]["format_name"],
                "streams": probe["streams"],
            },
            sort_keys=True,
        ),
    )
