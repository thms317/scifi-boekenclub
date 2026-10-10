"""Data structures for book club members."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass
class BookClubMember:
    """Represents a book club member with their associated data file and status.

    Attributes
    ----------
    name : str
        The member's name as used in the book club.
    file_name : str | None
        File name of the member's Goodreads export, if available.
    active : bool
        Whether the member is currently active in the book club.
    """

    name: str
    file_name: str | None = None
    active: bool = True


class BookClubMembers:
    """Container for all book club member data and query methods.

    The members are listed in column order.
    """

    _members: ClassVar[list[BookClubMember]] = [
        BookClubMember("Thirsa", "goodreads_library_export-thirsa.csv"),
        BookClubMember("Koen_v_W", "koen_goodreads_library_export.csv"),
        BookClubMember("Dion", "dion_goodreads_library_export.csv"),
        BookClubMember("Laurynas"),
        BookClubMember("Marloes"),
        BookClubMember("Robert", "Thomas is een worstje_clean.csv"),
        BookClubMember("Peter", "goodreads_library_export-PHT_clean.csv"),
        BookClubMember("Thomas", "thomas_goodreads_library_export.csv"),
        BookClubMember("Koen_M", "koen_m_goodreads_library_export.csv"),
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
