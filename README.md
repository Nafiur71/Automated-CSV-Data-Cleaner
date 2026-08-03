# Data Cleaning & Preprocessing Script with Pandas 

A Python-based automation script designed to clean and preprocess raw or "dirty" dataset files. Using the powerful `pandas` library, this script automates tasks like removing duplicate records and handling missing values (NaN) with smart default metrics.

##  Features
- **Data Loading:** Reads messy `.csv` data directly into Pandas DataFrames.
- **Duplicate Removal:** Automatically detects and drops exact duplicate rows (`drop_duplicates()`) to maintain unique logs.
- **Missing Value Handling (Imputation):** 
  - Fills empty **Age** fields with a default fallback of `25`.
  - Fills empty **Salary** fields with a default fallback of `35,000`.
- **Live Diagnostics:** Prints the comparison between raw data and cleaned data in the console.
- **Auto-Export:** Exports the finalized, polished dataset into a brand new file called `cleaned_data.csv`.

## Tech Stack & Libraries
- Python 3
- Pandas

##  How to Run the Script

1. **Install Dependencies:**
   Make sure you have Pandas installed on your machine:
   ```bash
   pip install pandas
   ```

2. **Prepare the Data:**
   Place your messy dataset named `dirty_data.csv` in the same directory as the script.

3. **Execute the Cleaner:**
   Run the python script using your terminal:
   ```bash
   python scraper.py
   ```

## Logic Implementation Details
- `df.drop_duplicates()`: Removes rows with repeated information.
- `df['Age'].fillna(25)`: Replaces missing ages (`NaN`) to prevent mathematical calculation errors.
- `df['Salary'].fillna(35000)`: Sets standard default salary entries for unrecorded items.
