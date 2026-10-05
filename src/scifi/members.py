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
    file_name : str | None
        File name of the member's Goodreads export, if available.
    active : bool
        Whether the member is currently active in the book club.
    """

    index: int
    name: str
    file_name: str | None
    active: bool


class BookClubMembers:
    """Container for all book club member data and query methods."""

    _members: ClassVar[list[BookClubMember]] = [
        BookClubMember(0, "Thirsa", "goodreads_library_export-thirsa.csv", active=True),
        BookClubMember(1, "Koen_v_W", "koen_goodreads_library_export.csv", active=True),
        BookClubMember(2, "Dion", "dion_goodreads_library_export.csv", active=True),
        BookClubMember(3, "Laurynas", "laurynas_goodreads_library_export.csv", active=True),
        BookClubMember(4, "Marloes", None, active=True),
        BookClubMember(5, "Robert", "Thomas is een worstje_clean.csv", active=True),
        BookClubMember(6, "Peter", "goodreads_library_export-PHT_clean.csv", active=True),
        BookClubMember(7, "Thomas", "thomas_goodreads_library_export.csv", active=True),
        BookClubMember(8, "Koen_M", "koen_m_goodreads_library_export.csv", active=True),
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
        """Return the mapping from file names to reviewer names.

        Returns
        -------
        dict[str, str]
            A dictionary mapping file names to reviewer names.
        """
        return {
            member.file_name: member.name for member in cls._members if member.file_name is not None
        }
