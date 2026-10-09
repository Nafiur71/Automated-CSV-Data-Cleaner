# CleanCSV - Automated CSV & Excel Data Cleaner & Data Onboarding Platform

An enterprise-ready, intelligent data cleaning platform for tabular datasets. Inspired by modern data onboarding tools (such as Flatfile), CleanCSV transforms messy, duplicate-filled, and incomplete datasets into pristine, production-ready CSV, Excel, and JSON spreadsheets in seconds.

---

## Complete Feature Matrix

### Phase 1: Core Engine & Flatfile-Lite Foundation
- **Multi-Format Support**: Upload and clean both **CSV** and **Excel (`.xlsx`, `.xls`)** files.
- **Smart Column Mapping (Flatfile-Lite)**: Interactive visual interface to rename messy headers and prune unwanted columns before processing.
- **Automated Date Standardization**: Detects inconsistent date formats (`12/05/2024`, `2024/05/12`, `May 12, 2024`) and normalizes them into ISO standard `YYYY-MM-DD`.
- **Outlier Detection & Capping (IQR Rule)**: Identifies extreme numeric outliers using the Interquartile Range rule and safely caps them.
- **Automated Whitespace Trimming**: Removes extra whitespace from column names and string cells.
- **Duplicate Removal**: Automatically drops redundant rows and logs precise audit metrics.
- **Dynamic Missing Value Imputation**:
  - **Numeric columns**: Fill missing values using `median` (default, robust against skew), `mean`, or `zero`.
  - **Text columns**: Fill missing text with `unknown` (default: `"Unknown"`), `mode`, or `empty`.
- **Integer Type Preservation**: Prevents awkward `.0` floating-point conversions for integer columns (e.g. `Age`, `Salary`) using nullable integer formatting (`Int64`).

### Phase 2: Interactive Grid, Validation & Audit Profiling
- **In-Browser Editable Spreadsheet Grid**: Click or double-click directly into any cell in the Cleaned Data table to edit values in real time before downloading.
- **Cell-Level Error Highlighting & Validation**: Automatic regex checks for invalid email formats, malformed URLs, and negative numbers with tooltips and warning borders.
- **"Issues Only" Filter**: 1-click filter button (`⚠️ Issues Only`) to quickly isolate rows requiring manual review.
- **Multi-Format Export Suite**: Export clean datasets in **CSV**, **Excel (.xlsx)**, **JSON**, or copy directly to clipboard with 1 click.
- **Comprehensive Data Quality & Audit Report Modal**:
  - Overall Data Health Score (0-100%).
  - Memory consumption reduction stats & percentage saved.
  - Column-by-column breakdown: Inferred Data Types, Missing %, Unique counts, and Min/Max ranges.

### Phase 3: AI-Powered Smart Cleaners
- **🤖 AI/Fuzzy Category Clustering**: Automatically unifies misspelled or slightly varied categories (e.g., `["Dhk", "dhaka", "Dhaka City"]` $\rightarrow$ `"Dhaka"`) using intelligent sequence matching.
- **👤 AI Full Name Dissector**: Automatically parses full names, strips honorifics (`Dr.`, `Mr.`, `Mrs.`), and splits them into clean `First_Name` and `Last_Name` columns.

### Phase 4: SaaS, Programmatic SEO & B2B Embeddable Widget
- **🚀 Programmatic SEO (pSEO) Landing Pages**: Targeted keyword entry points designed for high Google search intent:
  - `/excel-cleaner` (Excel .xlsx/.xls spreadsheet cleaner online free)
  - `/csv-cleaner` (Free browser-based CSV validator & normalizer)
  - `/clean-shopify-csv` (Clean Shopify products, inventory & customer lists)
  - `/remove-csv-duplicates-online` (Instant duplicate row purge tool)
  - `/convert-excel-to-clean-csv` (Excel to clean CSV converter)
  - `/fix-csv-date-format-online` (Standardize mixed date formats to ISO YYYY-MM-DD)
- **⚡ B2B Embeddable Widget (`/embed.js` & `/embed-demo`)**:
  - 3-line embed snippet enabling any third-party web application to launch CleanCSV in an in-app modal.
- **📦 Multi-File Batch Processing**:
  - Upload multiple files at once and download all cleaned spreadsheets bundled in a single `cleancsv_batch_results.zip` file.
- **🔍 Search Engine Infrastructure**:
  - Google-compliant JSON-LD structured data (`SoftwareApplication`, `FAQPage`).
  - `/sitemap.xml` and `/robots.txt` dynamic crawler endpoints.

---

## Market Comparison: Why CleanCSV Beats Competitors

| Feature | CleanCSV (Us) | CleanMyExcel.io | DataSort.app | ChatGPT / Macros |
|---|---|---|---|---|
| **Pricing** | **100% Free Forever** | Paid Tiers | Paid ($2.99 - $39.99/mo) | $20/mo Plus |
| **Max File Size** | **64 MB Free** | 1 MB Limit | 500 Rows (Free) | ~500 rows limit |
| **Instant Download** | **Yes (Direct 1-Click)** | No (Requires Email) | Yes | Copy/paste required |
| **Live In-Browser Grid** | **Yes (Click & Edit)** | No | Basic Grid | No |
| **"Issues Only" Filter** | **Yes (1-Click Toggle)** | No | No | No |
| **Smart Schema Mapping** | **Yes (Flatfile-Lite)** | No | Multi-step | Manual Prompts |
| **Batch ZIP Cleaning** | **Yes (Multi-file)** | No | Paid Plans Only | No |
| **Data Privacy** | **100% In-Memory Safe** | Cloud Storage | Cloud / IndexedDB | Data may be logged |

---

## Installation

Ensure you have Python 3.9+ installed.

1. Clone or download the repository.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

### 1. Interactive Web Application (Recommended)

Run the local web dashboard:
```bash
python app.py
```
Then open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser:
- Drag and drop any single CSV/Excel file or drop multiple files for batch processing.
- Customize column names in the **Column Mapping** panel.
- Enable AI Category Clustering or Name Dissection.
- Click any cell in the **Cleaned Data** table to edit live on screen.
- Open the **Audit Report** modal to inspect memory savings and column health.
- Export as **CSV**, **Excel (.xlsx)**, **JSON**, or copy to clipboard.

Explore the landing pages:
- [http://127.0.0.1:5000/excel-cleaner](http://127.0.0.1:5000/excel-cleaner) — Excel Cleaner
- [http://127.0.0.1:5000/csv-cleaner](http://127.0.0.1:5000/csv-cleaner) — CSV Cleaner
- [http://127.0.0.1:5000/embed-demo](http://127.0.0.1:5000/embed-demo) — B2B Embed Widget Demo
- [http://127.0.0.1:5000/clean-shopify-csv](http://127.0.0.1:5000/clean-shopify-csv) — Shopify Tool
- [http://127.0.0.1:5000/remove-csv-duplicates-online](http://127.0.0.1:5000/remove-csv-duplicates-online) — Duplicate Purge Tool

---

### 2. Command Line Interface (CLI)

```bash
# Standard clean
python cleaner.py -i my_dataset.xlsx -o my_dataset_cleaned.xlsx

# With outlier capping
python cleaner.py -i dirty_data.csv --handle-outliers
```

---

## Running Automated Tests

Run the full test suite (19 automated tests):
```bash
python test_cleaner.py
python test_app.py
```

---

## License

MIT License. Free to use, modify, and distribute.
