# Updating the source data

To update the source data, follow these steps:

1. **Update the Goodreads Export**:
   - Export the latest reading data from Goodreads for one or more club members. This extracts relevant metadata from Goodreads.
   - Save the export files in the `data/goodreads` directory.
   - Add the new members to the `get_reviewer_mapping` function in the `src/scifi/utils.py` module.

2. **Update the Book Club Source**:
    - Update the `data/bookclub/bookclub.csv` file with the latest book club meeting records.

3. **Update the Manual Ratings**:
   - A fresh Goodreads is not always necessary, instead update the `data/bookclub/manual_ratings.csv` file accordingly.

4. **Merge the Data**:
   - Run the data processing script to merge the Goodreads export data with the book club meeting records. This will create a new dataset that combines both sources of information. As of now, this is done manually by running the `notebooks/aggregating.ipynb` notebook.
