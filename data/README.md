# Updating the source data

To update the source data, follow these steps:

1. **Update the Goodreads Export**:
   - Export the latest reading data from Goodreads for one or more club members.
   - Place new or unchanged exports in `data/goodreads/clean/`. If the export needs cleaning, place it in `data/goodreads/messy/` and run `notebooks/cleaning.ipynb` to move the cleaned file to `data/goodreads/clean/`.
   - Register the export file name (without path) in `src/scifi/members.py` by adding it to the member's `file_name` in the registry.
   - Thomas's exports come without the `Average Rating` column (a Goodreads bug since October 2026). Do not replace his committed file with a raw export: add only the new rows, with the average looked up on goodreads.com. The tests fail when a book read so far has no Goodreads average.

2. **Update the Book Club Source**:
    - Update the `data/bookclub/bookclub.csv` file with the latest book club meeting records.

3. **Update the Manual Ratings**:
   - Update the `data/bookclub/manual_ratings.csv` file with any manual ratings or corrections.

4. **Update the Authors**:
   - When the club reads a new author, add one row to `data/bookclub/authors.csv`. The `author` must match the `Auteur` in `bookclub.csv` exactly. The tests fail if an author is missing or a cell is empty.
   - Reuse a value that is already in the file, so the dashboard groups stay the same:

     | column | rule |
     |---|---|
     | `gender` | `gemengd` for co-authors of different genders |
     | `country` | one country, in Dutch: the country they are known for as a writer |
     | `religion` | a known religious background counts; `seculier` only for known atheists/agnostics; otherwise `onbekend` |
     | `lgbtq` | `ja` only if public (out, or a known same-sex marriage); otherwise `onbekend`, never `nee` |
     | `ethnicity` | the club's judgement from public biographies |

5. **Data Processing**:
   - The app runs the data processing pipeline live when it starts. The `data/processed_data.csv` file is only an export and is not required to run the dashboard.
