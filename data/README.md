# Updating the source data

To update the source data, follow these steps:

1. **Update the Goodreads Export**:

   - Export the latest reading data from Goodreads for one or more club members. This extracts relevant metadata from Goodreads.
   - Save the export files in the `data/goodreads` directory.

2. **Update the Book Club Source**:
    - Update the `bookclub_source.csv` file with the latest book club meeting records.

3. **Merge the Data**:
   - Run the data processing script to merge the Goodreads export data with the book club meeting records. This will create a new dataset that combines both sources of information. As of now, this is done manually by running the `notebooks/aggregating.ipynb` notebook.
