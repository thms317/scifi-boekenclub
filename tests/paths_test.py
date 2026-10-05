"""Tests for paths module."""

import os
import time
from pathlib import Path

import pytest

from scifi.members import BookClubMembers
from scifi.paths import GOODREADS_DIR, input_files, source_fingerprint


class TestInputFiles:
    """Test class for the input_files function."""

    @pytest.fixture(scope="class")
    def temp_data_dir(self, tmp_path_factory: pytest.TempPathFactory) -> Path:
        """Fixture for creating a temporary data directory structure."""
        data_dir = tmp_path_factory.mktemp("data")
        # Goodreads exports, one of them named like Thirsa's and Peter's exports
        goodreads_dir = data_dir / "goodreads" / "clean"
        goodreads_dir.mkdir(parents=True)
        (goodreads_dir / "member1.csv").touch()
        (goodreads_dir / "goodreads_library_export-member2.csv").touch()
        # Bookclub input files
        (data_dir / "bookclub").mkdir()
        for name in ("bookclub.csv", "manual_ratings.csv", "authors.csv"):
            (data_dir / "bookclub" / name).touch()
        # Generated outputs, where save_processed_data writes them
        (data_dir / "processed_data.csv").touch()
        (data_dir / "goodreads" / "goodreads_combined.csv").touch()
        (data_dir / "goodreads" / "goodreads_unmatched.csv").touch()
        return data_dir

    def test_input_files_returns_goodreads_exports(self, temp_data_dir: Path) -> None:
        """Test that input_files returns every Goodreads export, whatever its name."""
        files = input_files(temp_data_dir)
        assert {f.name for f in files if f.parent.name == "clean"} == {
            "member1.csv",
            "goodreads_library_export-member2.csv",
        }

    def test_input_files_returns_bookclub_csvs(self, temp_data_dir: Path) -> None:
        """Test that input_files returns bookclub CSV files."""
        files = input_files(temp_data_dir)
        assert {f.name for f in files if f.parent.name == "bookclub"} == {
            "bookclub.csv",
            "manual_ratings.csv",
            "authors.csv",
        }

    def test_input_files_excludes_generated_outputs(self, temp_data_dir: Path) -> None:
        """Test that input_files excludes generated outputs."""
        file_names = {f.name for f in input_files(temp_data_dir)}
        assert not file_names & {
            "processed_data.csv",
            "goodreads_combined.csv",
            "goodreads_unmatched.csv",
        }

    def test_input_files_includes_every_member_export(self) -> None:
        """Test that every member's real Goodreads export keys the dashboard cache."""
        member_exports = {GOODREADS_DIR / name for name in BookClubMembers.get_reviewer_mapping()}
        assert member_exports <= set(input_files())


class TestSourceFingerprint:
    """Test class for the source_fingerprint function."""

    def test_fingerprint_changes_when_file_added(self, tmp_path: Path) -> None:
        """Test that fingerprint changes when a file is added."""
        file1, file2 = tmp_path / "file1.csv", tmp_path / "file2.csv"
        file1.touch()
        fp1 = source_fingerprint([file1, file2])
        file2.touch()
        assert source_fingerprint([file1, file2]) != fp1

    def test_fingerprint_changes_when_file_edited(self, tmp_path: Path) -> None:
        """Test that fingerprint changes when a file is edited."""
        file1 = tmp_path / "file1.csv"
        file1.write_text("data")
        fp1 = source_fingerprint([file1])
        file1.write_text("new data")
        assert source_fingerprint([file1]) != fp1

    def test_fingerprint_changes_when_file_edited_by_mtime(self, tmp_path: Path) -> None:
        """Test that fingerprint changes when a file's mtime is changed."""
        file1 = tmp_path / "file1.csv"
        file1.write_text("data")
        fp1 = source_fingerprint([file1])
        # Change mtime without changing content
        time.sleep(0.01)
        os.utime(file1, None)
        assert source_fingerprint([file1]) != fp1

    def test_fingerprint_changes_when_file_removed(self, tmp_path: Path) -> None:
        """Test that fingerprint changes when a file is removed."""
        file1, file2 = tmp_path / "file1.csv", tmp_path / "file2.csv"
        file1.touch()
        file2.touch()
        fp1 = source_fingerprint([file1, file2])
        file2.unlink()
        assert source_fingerprint([file1, file2]) != fp1

    def test_fingerprint_ignores_nonexistent_files(self, tmp_path: Path) -> None:
        """Test that fingerprint ignores nonexistent files."""
        file1 = tmp_path / "file1.csv"
        file1.touch()
        fp = source_fingerprint([file1, tmp_path / "file2.csv"])
        assert [item[0] for item in fp] == [str(file1)]

    def test_fingerprint_is_sorted(self, tmp_path: Path) -> None:
        """Test that fingerprint is returned in sorted order."""
        files = [tmp_path / name for name in ("c.csv", "a.csv", "b.csv")]
        for file in files:
            file.touch()
        paths = [item[0] for item in source_fingerprint(files)]
        assert paths == sorted(paths)
