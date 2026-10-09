"""Automated CSV & Excel Data Cleaner.

A production-grade, modular cleaning engine for tabular data.
Features:
- Excel (.xlsx, .xls) and CSV loading & exporting
- Smart Column Mapping & Column Pruning (Flatfile-Lite)
- Automatic Date & Time Standardization (ISO YYYY-MM-DD)
- Outlier Detection & Capping (IQR Rule)
- Whitespace Trimming & Deduplication
- Dynamic Missing Value Imputation
- Integer Data Type Preservation
"""

from __future__ import annotations

import argparse
import difflib
import io
import os
import re
import sys
from typing import Any, Optional, Union
import pandas as pd


def standardize_dates(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Detects and standardizes inconsistent date strings into 'YYYY-MM-DD'."""
    standardized_cols = []
    date_separators = re.compile(r"[-/.]|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", re.IGNORECASE)

    for col in df.select_dtypes(include=["object", "string"]).columns:
        series = df[col].dropna().astype(str).str.strip()
        if len(series) == 0:
            continue

        # Check if sample contains date-like patterns
        sample_contains_date = series.head(10).apply(lambda s: bool(date_separators.search(s))).mean()
        if sample_contains_date < 0.6:
            continue

        # Try parsing dates with mixed format support
        try:
            parsed = pd.to_datetime(series, errors="coerce", format="mixed")
            valid_ratio = parsed.notna().mean()
            # If at least 70% of non-empty values are valid dates, standardize
            if valid_ratio >= 0.7:
                df[col] = parsed.dt.strftime("%Y-%m-%d")
                standardized_cols.append(col)
        except Exception:
            continue

    return df, standardized_cols


def handle_outliers(
    df: pd.DataFrame,
    factor: float = 1.5,
    clip: bool = True,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Detects and optionally caps numeric outliers using the Interquartile Range (IQR) rule."""
    outlier_report: dict[str, int] = {}
    numeric_cols = df.select_dtypes(include=["number"]).columns

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        if iqr <= 0:
            continue

        lower_bound = q1 - (factor * iqr)
        upper_bound = q3 + (factor * iqr)

        outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
        count = int(outlier_mask.sum())

        if count > 0:
            outlier_report[col] = count
            if clip:
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)

    return df, outlier_report


def normalize_fuzzy_categories(
    df: pd.DataFrame,
    similarity_threshold: float = 0.80,
) -> tuple[pd.DataFrame, dict[str, dict[str, str]]]:
    """Clusters and normalizes misspelled categorical values using sequence matching."""
    cluster_report: dict[str, dict[str, str]] = {}
    for col in df.select_dtypes(include=["object", "string"]).columns:
        series = df[col].dropna().astype(str).str.strip()
        if len(series) < 3:
            continue

        unique_vals = list(series.unique())
        if len(unique_vals) > 50 or len(unique_vals) <= 1:
            continue

        counts = series.value_counts().to_dict()
        sorted_candidates = sorted(unique_vals, key=lambda v: counts.get(v, 0), reverse=True)

        mapping: dict[str, str] = {}
        canonical_set: set[str] = set()

        for val in sorted_candidates:
            matched = False
            for canon in canonical_set:
                ratio = difflib.SequenceMatcher(None, val.lower(), canon.lower()).ratio()
                if ratio >= similarity_threshold or (len(val) <= 4 and canon.lower().startswith(val.lower())):
                    mapping[val] = canon
                    matched = True
                    break
            if not matched:
                canonical_set.add(val)

        if mapping:
            df[col] = df[col].replace(mapping)
            cluster_report[col] = mapping

    return df, cluster_report


def split_full_names(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Splits full name strings into 'First_Name' and 'Last_Name'."""
    split_cols: list[str] = []
    name_cols = [target_column] if target_column and target_column in df.columns else []

    if not name_cols:
        for c in df.select_dtypes(include=["object", "string"]).columns:
            if re.search(r"\b(full_?name|customer_?name|name|client_?name)\b", str(c), re.IGNORECASE):
                name_cols.append(c)
                break

    for col in name_cols:
        series = df[col].dropna().astype(str).str.strip()
        if len(series) == 0:
            continue

        titles = r"^(?:Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.|Doctor|Engr\.)\s+"
        first_names = []
        last_names = []

        for val in df[col]:
            if pd.isna(val) or val is None or not str(val).strip():
                first_names.append(None)
                last_names.append(None)
                continue
            cleaned = re.sub(titles, "", str(val).strip())
            parts = cleaned.split(maxsplit=1)
            first_names.append(parts[0] if parts else "")
            last_names.append(parts[1] if len(parts) > 1 else "")

        fn_col = f"{col}_First" if f"{col}_First" not in df.columns else f"{col}_First_Name"
        ln_col = f"{col}_Last" if f"{col}_Last" not in df.columns else f"{col}_Last_Name"

        df[fn_col] = first_names
        df[ln_col] = last_names
        split_cols.extend([fn_col, ln_col])

    return df, split_cols


def clean_dataframe(
    df: pd.DataFrame,
    numeric_strategy: str = "median",
    string_strategy: str = "unknown",
    drop_duplicates: bool = True,
    trim_strings: bool = True,
    standardize_date_columns: bool = True,
    handle_outliers_flag: bool = False,
    fuzzy_clustering: bool = False,
    split_names: bool = False,
    column_mapping: Optional[dict[str, str]] = None,
    drop_columns: Optional[list[str]] = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Cleans a pandas DataFrame and returns the cleaned DataFrame with a summary report."""
    initial_rows = len(df)
    report: dict[str, Any] = {
        "initial_rows": initial_rows,
        "initial_columns": len(df.columns),
        "duplicates_removed": 0,
        "dropped_columns": [],
        "renamed_columns": {},
        "standardized_dates": [],
        "outliers_handled": {},
        "fuzzy_clusters": {},
        "name_columns_split": [],
        "imputed_columns": {},
        "final_rows": 0,
    }

    # 1. Clean and normalize column headers
    df.columns = df.columns.astype(str).str.strip()

    # 2. Prune requested drop columns
    if drop_columns:
        valid_drops = [c for c in drop_columns if c in df.columns]
        if valid_drops:
            df = df.drop(columns=valid_drops)
            report["dropped_columns"] = valid_drops

    # 3. Apply Column Mapping (Flatfile-Lite)
    if column_mapping:
        valid_renames = {k: v.strip() for k, v in column_mapping.items() if k in df.columns and v.strip()}
        if valid_renames:
            df = df.rename(columns=valid_renames)
            report["renamed_columns"] = valid_renames

    # 4. Strip string values
    if trim_strings:
        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

    # 5. Remove duplicate rows
    if drop_duplicates:
        df = df.drop_duplicates()
        report["duplicates_removed"] = initial_rows - len(df)

    # 6. Standardize Dates
    if standardize_date_columns:
        df, date_cols = standardize_dates(df)
        report["standardized_dates"] = date_cols

    # 7. Handle Outliers (IQR)
    if handle_outliers_flag:
        df, outlier_info = handle_outliers(df, factor=1.5, clip=True)
        report["outliers_handled"] = outlier_info

    # 8. AI/NLP Fuzzy Category Clustering (Phase 3)
    if fuzzy_clustering:
        df, clusters = normalize_fuzzy_categories(df)
        report["fuzzy_clusters"] = clusters

    # 9. AI/NLP Name Dissector (Phase 3)
    if split_names:
        df, split_cols = split_full_names(df)
        report["name_columns_split"] = split_cols

    # 8. Impute missing numeric values
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        missing_count = int(df[col].isna().sum())
        if missing_count > 0:
            if numeric_strategy == "median":
                fill_val = df[col].median()
            elif numeric_strategy == "mean":
                fill_val = df[col].mean()
            elif numeric_strategy == "zero":
                fill_val = 0
            else:
                fill_val = df[col].median()

            df[col] = df[col].fillna(fill_val)
            report["imputed_columns"][col] = {
                "missing_count": missing_count,
                "filled_with": fill_val,
                "strategy": numeric_strategy,
            }

    # 9. Impute missing string/object values
    object_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in object_cols:
        missing_count = int(df[col].isna().sum())
        if missing_count > 0:
            if string_strategy == "mode" and not df[col].mode().empty:
                fill_val = df[col].mode().iloc[0]
            elif string_strategy == "unknown":
                fill_val = "Unknown"
            else:
                fill_val = ""

            df[col] = df[col].fillna(fill_val)
            report["imputed_columns"][col] = {
                "missing_count": missing_count,
                "filled_with": fill_val,
                "strategy": string_strategy,
            }

    # 10. Preserve integer data types where appropriate
    for col in numeric_cols:
        if (df[col].dropna() % 1 == 0).all():
            df[col] = df[col].round().astype("Int64")

    report["final_rows"] = len(df)
    return df, report


def validate_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Inspects DataFrame cells against standard validation rules (emails, URLs, negative values)."""
    email_regex = re.compile(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$")
    url_regex = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

    cell_errors: dict[str, str] = {}
    col_issues: dict[str, int] = {}
    non_negative_keywords = {"age", "salary", "price", "cost", "revenue", "quantity", "qty", "count"}

    for col in df.columns:
        col_lower = str(col).lower()
        is_email_col = "email" in col_lower or "mail" in col_lower
        is_url_col = "url" in col_lower or "link" in col_lower or "website" in col_lower
        is_positive_col = any(k in col_lower for k in non_negative_keywords)

        for row_idx, val in enumerate(df[col]):
            if pd.isna(val) or val is None or val == "":
                continue

            str_val = str(val).strip()

            if is_email_col and not email_regex.match(str_val):
                cell_errors[f"{row_idx}_{col}"] = "Invalid email address format"
                col_issues[col] = col_issues.get(col, 0) + 1
            elif is_url_col and not url_regex.match(str_val):
                cell_errors[f"{row_idx}_{col}"] = "Invalid URL format"
                col_issues[col] = col_issues.get(col, 0) + 1
            elif is_positive_col:
                try:
                    num_val = float(str_val)
                    if num_val < 0:
                        cell_errors[f"{row_idx}_{col}"] = "Negative number not allowed"
                        col_issues[col] = col_issues.get(col, 0) + 1
                except (ValueError, TypeError):
                    pass

    return {
        "total_errors": len(cell_errors),
        "cell_errors": cell_errors,
        "column_issues": col_issues,
    }


def generate_profiling_report(df_before: pd.DataFrame, df_after: pd.DataFrame) -> dict[str, Any]:
    """Generates data profiling statistics and health audit metrics."""
    mem_before = int(df_before.memory_usage(deep=True).sum())
    mem_after = int(df_after.memory_usage(deep=True).sum())
    reduction_pct = round(((mem_before - mem_after) / mem_before * 100), 1) if mem_before > 0 else 0.0

    columns_profile = []
    total_cells = df_after.shape[0] * df_after.shape[1] if df_after.shape[0] > 0 else 1
    total_missing_after = int(df_after.isna().sum().sum())

    for col in df_after.columns:
        series = df_after[col]
        missing_count = int(series.isna().sum())
        unique_count = int(series.nunique())
        dtype_str = str(series.dtype)

        if "int" in dtype_str.lower():
            friendly_type = "Integer"
        elif "float" in dtype_str.lower():
            friendly_type = "Decimal"
        elif "datetime" in dtype_str.lower():
            friendly_type = "Date/Time"
        else:
            friendly_type = "Text"

        val_min = None
        val_max = None
        if pd.api.types.is_numeric_dtype(series) and not series.dropna().empty:
            val_min = round(float(series.min()), 2)
            val_max = round(float(series.max()), 2)

        columns_profile.append({
            "name": col,
            "type": friendly_type,
            "missing_count": missing_count,
            "missing_pct": round((missing_count / len(series) * 100), 1) if len(series) > 0 else 0,
            "unique_count": unique_count,
            "min": val_min,
            "max": val_max,
        })

    missing_ratio = total_missing_after / total_cells
    health_score = max(50, min(100, int(100 - (missing_ratio * 100))))

    return {
        "health_score": health_score,
        "memory_before_bytes": mem_before,
        "memory_after_bytes": mem_after,
        "memory_reduction_pct": reduction_pct,
        "initial_rows": int(len(df_before)),
        "final_rows": int(len(df_after)),
        "initial_cols": int(len(df_before.columns)),
        "final_cols": int(len(df_after.columns)),
        "columns_profile": columns_profile,
    }


def load_data(file_source: Union[str, io.BytesIO], filename: str = "") -> pd.DataFrame:
    """Loads CSV or Excel data from a file path or in-memory byte buffer."""
    name = filename.lower() if filename else (file_source if isinstance(file_source, str) else "").lower()

    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(file_source)
    else:
        # Default to CSV
        if isinstance(file_source, io.BytesIO):
            try:
                return pd.read_csv(file_source, encoding="utf-8")
            except UnicodeDecodeError:
                file_source.seek(0)
                return pd.read_csv(file_source, encoding="latin1")
        else:
            try:
                return pd.read_csv(file_source, encoding="utf-8")
            except UnicodeDecodeError:
                return pd.read_csv(file_source, encoding="latin1")


def clean_csv(
    file_path: str,
    output_path: Optional[str] = None,
    numeric_strategy: str = "median",
    string_strategy: str = "unknown",
    standardize_dates_flag: bool = True,
    handle_outliers_flag: bool = False,
) -> pd.DataFrame:
    """Reads a CSV or Excel file, cleans its contents, prints a summary, and saves the result."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    print(f"[INFO] Loading file: {file_path}")
    df = load_data(file_path, filename=file_path)

    print("\n--- Original Data Preview ---")
    print(df.to_string(index=False))

    cleaned_df, report = clean_dataframe(
        df,
        numeric_strategy=numeric_strategy,
        string_strategy=string_strategy,
        standardize_date_columns=standardize_dates_flag,
        handle_outliers_flag=handle_outliers_flag,
    )

    print("\n--- Data Cleaning Summary ---")
    print(f"- Total rows loaded: {report['initial_rows']}")
    print(f"- Duplicate rows removed: {report['duplicates_removed']}")
    if report["standardized_dates"]:
        print(f"- Standardized Date columns: {', '.join(report['standardized_dates'])}")
    if report["outliers_handled"]:
        print("- Outliers clipped (IQR):")
        for col, count in report["outliers_handled"].items():
            print(f"  * {col}: {count} outliers adjusted")
    if report["imputed_columns"]:
        print("- Missing values imputed:")
        for col, info in report["imputed_columns"].items():
            print(f"  * {col}: {info['missing_count']} missing filled with {info['filled_with']} ({info['strategy']})")
    else:
        print("- No missing values found.")
    print(f"- Final row count: {report['final_rows']}")

    print("\n--- Cleaned Data Preview ---")
    print(cleaned_df.to_string(index=False))

    # Determine output file path
    if not output_path:
        base, ext = os.path.splitext(file_path)
        output_path = f"{base}_cleaned{ext}" if base != "cleaned_data" else "cleaned_data.csv"

    if output_path.lower().endswith((".xlsx", ".xls")):
        cleaned_df.to_excel(output_path, index=False)
    else:
        cleaned_df.to_csv(output_path, index=False)

    print(f"\n[SUCCESS] Cleaned data saved successfully: {output_path}")
    return cleaned_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automated CSV & Excel Data Cleaner: cleans duplicates, dates, outliers, and missing values."
    )
    parser.add_argument(
        "-i",
        "--input",
        default="dirty_data.csv",
        help="Path to the input CSV/Excel file (default: dirty_data.csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="cleaned_data.csv",
        help="Path to the output CSV/Excel file (default: cleaned_data.csv)",
    )
    parser.add_argument(
        "--numeric-strategy",
        choices=["median", "mean", "zero"],
        default="median",
        help="Strategy to fill missing numeric values (default: median)",
    )
    parser.add_argument(
        "--string-strategy",
        choices=["unknown", "mode", "empty"],
        default="unknown",
        help="Strategy to fill missing string/text values (default: unknown)",
    )
    parser.add_argument(
        "--handle-outliers",
        action="store_true",
        help="Detect and clip numeric outliers using the IQR rule",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        clean_csv(
            file_path=args.input,
            output_path=args.output,
            numeric_strategy=args.numeric_strategy,
            string_strategy=args.string_strategy,
            handle_outliers_flag=args.handle_outliers,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
