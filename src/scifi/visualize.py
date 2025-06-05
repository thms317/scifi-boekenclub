"""Visualization functions for the scifi project."""

import numpy as np


def rating_to_color(rating: float, alpha: float = 0.3) -> str:
    """Convert a rating to an RGBA color string.

    Parameters
    ----------
    rating : float
        The rating to convert, expected to be in the range 1-5.
    alpha : float, optional
        The alpha value for the color, by default 0.3

    Returns
    -------
    str
        The RGBA color string.
    """
    # Normalize rating from 1-5 to 0-1
    normalized = (rating - 1) / 4
    normalized = np.clip(normalized, 0, 1)

    # Interpolate between red and green
    red = int(255 * (1 - normalized))
    green = int(255 * normalized)
    blue = 0

    return f"rgba({red}, {green}, {blue}, {alpha})"


def create_voting_text(bookclub_members_list: list[str], row: dict[str, float]) -> str:
    """Create a summary of voting members and their ratings.

    Parameters
    ----------
    bookclub_members_list : list[str]
        List of member names who voted.
    row : dict[str, float]
        A dictionary containing member ratings.

    Returns
    -------
    str
        A formatted string listing the voting members and their ratings.
    """
    voters = []
    for member in bookclub_members_list:
        value = row.get(member)
        if value is not None and value != 0:
            voters.append(f"{member}: {value:.1f}")
    return "<br>".join(voters)
