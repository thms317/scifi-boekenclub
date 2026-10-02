"""Tests for paths module."""

import os
import time
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scifi.paths import input_files, source_fingerprint


class TestInputFiles:
    """Test class for the input_files function."""

    @pytest.fixture(scope="class")
    def temp_data_dir(self) -> Generator[Path, None, None]:
        """Fixture for creating a temporary data directory structure."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create goodreads/clean directory with sample CSVs
            goodreads_dir = tmpdir_path / "goodreads" / "clean"
            goodreads_dir.mkdir(parents=True)
            (goodreads_dir / "member1.csv").touch()
            (goodreads_dir / "member2.csv").touch()

            # Create bookclub directory with input files
            bookclub_dir = tmpdir_path / "bookclub"
            bookclub_dir.mkdir(parents=True)
            (bookclub_dir / "bookclub.csv").touch()
            (bookclub_dir / "manual_ratings.csv").touch()
            (bookclub_dir / "authors.csv").touch()

            # Create generated outputs that should be excluded
            (tmpdir_path / "processed_data.csv").touch()
            (goodreads_dir / "goodreads_combined.csv").touch()
            (goodreads_dir / "goodreads_unmatched.csv").touch()

            yield tmpdir_path

    def test_input_files_returns_goodreads_exports(self, temp_data_dir: Path) -> None:
        """Test that input_files returns Goodreads exports."""
        files = input_files(temp_data_dir)
        goodreads_files = [f for f in files if f.parent.name == "clean"]
        assert len(goodreads_files) == 2

    def test_input_files_returns_bookclub_csvs(self, temp_data_dir: Path) -> None:
        """Test that input_files returns bookclub CSV files."""
        files = input_files(temp_data_dir)
        bookclub_files = [f for f in files if f.parent.name == "bookclub"]
        assert len(bookclub_files) == 3
        assert any(f.name == "bookclub.csv" for f in bookclub_files)
        assert any(f.name == "manual_ratings.csv" for f in bookclub_files)
        assert any(f.name == "authors.csv" for f in bookclub_files)

    def test_input_files_excludes_generated_outputs(self, temp_data_dir: Path) -> None:
        """Test that input_files excludes generated outputs."""
        files = input_files(temp_data_dir)
        file_names = [f.name for f in files]
        assert "processed_data.csv" not in file_names
        assert "goodreads_combined.csv" not in file_names
        assert "goodreads_unmatched.csv" not in file_names


class TestSourceFingerprint:
    """Test class for the source_fingerprint function."""

    def test_fingerprint_changes_when_file_added(self) -> None:
        """Test that fingerprint changes when a file is added."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.csv"
            file1.touch()

            fp1 = source_fingerprint([file1])

            # Add a new file
            file2 = tmpdir_path / "file2.csv"
            file2.touch()

            fp2 = source_fingerprint([file1, file2])

            assert fp1 != fp2

    def test_fingerprint_changes_when_file_edited(self) -> None:
        """Test that fingerprint changes when a file is edited."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.csv"
            file1.write_text("data")

            fp1 = source_fingerprint([file1])

            # Modify the file
            file1.write_text("new data")

            fp2 = source_fingerprint([file1])

            assert fp1 != fp2

    def test_fingerprint_changes_when_file_edited_by_mtime(self) -> None:
        """Test that fingerprint changes when a file's mtime is changed."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.csv"
            file1.write_text("data")

            fp1 = source_fingerprint([file1])

            # Change mtime without changing content
            time.sleep(0.01)  # Ensure time passes
            os.utime(file1, None)

            fp2 = source_fingerprint([file1])

            assert fp1 != fp2

    def test_fingerprint_changes_when_file_removed(self) -> None:
        """Test that fingerprint changes when a file is removed."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.csv"
            file2 = tmpdir_path / "file2.csv"
            file1.touch()
            file2.touch()

            fp1 = source_fingerprint([file1, file2])

            # Remove a file (it will not be included in the fingerprint)
            file2.unlink()

            fp2 = source_fingerprint([file1, file2])

            assert fp1 != fp2

    def test_fingerprint_ignores_nonexistent_files(self) -> None:
        """Test that fingerprint ignores nonexistent files."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.csv"
            file2 = tmpdir_path / "file2.csv"
            file1.touch()

            # file2 doesn't exist
            fp = source_fingerprint([file1, file2])

            # Should only include file1
            assert len(fp) == 1
            assert str(file1) in fp[0][0]

    def test_fingerprint_is_sorted(self) -> None:
        """Test that fingerprint is returned in sorted order."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_c = tmpdir_path / "c.csv"
            file_a = tmpdir_path / "a.csv"
            file_b = tmpdir_path / "b.csv"
            file_c.touch()
            file_a.touch()
            file_b.touch()

            # Pass files in non-sorted order
            fp = source_fingerprint([file_c, file_a, file_b])

            # Should be sorted by path
            paths = [item[0] for item in fp]
            assert paths == sorted(paths)
