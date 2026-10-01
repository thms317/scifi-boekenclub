# Updating the source data

To update the source data, follow these steps:

1. **Update the Goodreads Export**:
   - Export the latest reading data from Goodreads for one or more club members. This extracts relevant metadata from Goodreads.
   - Save the export files in the `data/goodreads` directory.
   - Add the new members to the `BookClubMembers` dataclass in the `src/scifi/members.py` module.

2. **Update the Book Club Source**:
    - Update the `data/bookclub/bookclub.csv` file with the latest book club meeting records.

3. **Update the Manual Ratings**:
   - A fresh Goodreads is not always necessary, instead update the `data/bookclub/manual_ratings.csv` file accordingly.

4. **Update the Authors**:
   - When the club reads a new author, add one row to `data/bookclub/authors.csv`. The `author` must match the `Auteur` in `bookclub.csv` exactly. The tests fail if an author is missing or a value is not allowed.
   - Use only these values (see `AUTHOR_CATEGORIES` in `src/scifi/utils.py`):

     | column | values | rule |
     |---|---|---|
     | `gender` | `man`, `vrouw`, `non-binair`, `gemengd` | `gemengd` for co-authors of different genders |
     | `country` | one country, in Dutch | the country they are known for as a writer |
     | `religion` | `christelijk`, `joods`, `boeddhistisch`, `spiritueel`, `seculier`, `onbekend` | a known religious background counts; `seculier` only for known atheists/agnostics |
     | `lgbtq` | `ja`, `onbekend` | `ja` only if public (out, or a known same-sex marriage), with a `source`. Never `nee` |
     | `ethnicity` | `europees`, `afrikaans`, `aziatisch`, `latijns-amerikaans`, `onbekend` | the club's judgement from public biographies |

   - `source`: one link per author, usually Wikipedia.

5. **Merge the Data (optional)**:
   - Run the data processing script to merge the Goodreads export data with the book club meeting records. This will create a new dataset that combines both sources of information. This will happen automatically while running the Streamlit app, but can be done manually by running the `notebooks/aggregating.ipynb` notebook.
