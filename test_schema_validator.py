import csv
import json

import pytest

from generate_lecture_series import export

from schema_validator import audio_word_bounds, validate_csv


@pytest.mark.parametrize(
    ("orientation", "expected"),
    [
        ("vertical", (120, 145)),
        ("horizontal", (350, 410)),
        ("unknown", (120, 145)),
    ],
)
def test_audio_word_targets_follow_video_runtime(orientation, expected):
    assert audio_word_bounds(orientation) == expected


def test_paired_series_exports_are_render_schema_valid(tmp_path, capsys):
    outputs = export(tmp_path)

    for orientation, path in outputs.items():
        assert validate_csv(str(path))
        output = capsys.readouterr().out
        assert "[WARN]" not in output
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == 10
        assert all(row["orientation"] == orientation for row in rows)
        assert all(row["lesson_id"] in row["video_id"] for row in rows)
        lower, upper = audio_word_bounds(orientation)
        assert all(lower <= len(row["audio_script"].split()) <= upper for row in rows)

        projectile = next(row for row in rows if row["lesson_id"] == "mix02")
        visuals = json.loads(projectile["visual_data_json"])
        motion = next(item for item in visuals if item["type"] == "projectile_motion")
        assert (motion["v0"], motion["angle"], motion["g"]) == (20.0, 30, 10.0)
