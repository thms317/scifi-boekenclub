"""Data structures for book club members."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass
class BookClubMember:
    """Represents a book club member with their associated data file and status.

    Attributes
    ----------
    index : int
        The member's index position in the club.
    name : str
        The member's name as used in the book club.
    file_path : str | None
        Path to the member's Goodreads export file, if available.
    active : bool
        Whether the member is currently active in the book club.
    """

    index: int
    name: str
    file_path: str | None
    active: bool


class BookClubMembers:
    """Container for all book club member data and query methods."""

    _members: ClassVar[list[BookClubMember]] = [
        BookClubMember(
            index=0,
            name="Thirsa",
            file_path="data/goodreads/clean/goodreads_library_export-thirsa.csv",
            active=True,
        ),
        BookClubMember(
            index=1,
            name="Koen_v_W",
            file_path="data/goodreads/clean/koen_goodreads_library_export.csv",
            active=True,
        ),
        BookClubMember(
            index=2,
            name="Dion",
            file_path="data/goodreads/clean/dion_goodreads_library_export.csv",
            active=True,
        ),
        BookClubMember(
            index=3,
            name="Laurynas",
            file_path=None,
            active=True,
        ),
        BookClubMember(
            index=4,
            name="Marloes",
            file_path=None,
            active=True,
        ),
        BookClubMember(
            index=5,
            name="Robert",
            file_path="data/goodreads/clean/Thomas is een worstje_clean.csv",
            active=True,
        ),
        BookClubMember(
            index=6,
            name="Peter",
            file_path="data/goodreads/clean/goodreads_library_export-PHT_clean.csv",
            active=True,
        ),
        BookClubMember(
            index=7,
            name="Thomas",
            file_path="data/goodreads/clean/thomas_goodreads_library_export.csv",
            active=True,
        ),
        BookClubMember(
            index=8,
            name="Koen_M",
            file_path="data/goodreads/clean/koen_m_goodreads_library_export.csv",
            active=True,
        ),
    ]

    @classmethod
    def get_all_members(cls) -> list[BookClubMember]:
        """Return all book club members.

        Returns
        -------
        list[BookClubMember]
            A list of all book club members.
        """
        return cls._members.copy()

    @classmethod
    def get_member_names(cls) -> list[str]:
        """Return a list of all member names.

        Returns
        -------
        list[str]
            A list of all member names.
        """
        return [member.name for member in cls._members]

    @classmethod
    def get_active_members(cls) -> list[BookClubMember]:
        """Return only the active book club members.

        Returns
        -------
        list[BookClubMember]
            A list of active book club members.
        """
        return [member for member in cls._members if member.active]

    @classmethod
    def get_reviewer_mapping(cls) -> dict[str, str]:
        """Return the mapping from file paths to reviewer names.

        Returns
        -------
        dict[str, str]
            A dictionary mapping file paths to reviewer names.
        """
        return {
            member.file_path: member.name for member in cls._members if member.file_path is not None
        }
