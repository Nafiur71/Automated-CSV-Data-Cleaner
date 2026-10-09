"""Flask Web Application for Automated CSV & Excel Data Cleaner.

Provides a clean REST API and serves the interactive web interface.
Supports CSV & Excel (.xlsx, .xls) uploads, Flatfile-Lite column mapping,
date standardization, outlier detection, and multi-format exports.
"""

from __future__ import annotations

import base64
import io
import json
import os
from typing import Any
import zipfile
from flask import Flask, jsonify, render_template, request, Response, send_file
import pandas as pd
from cleaner import clean_dataframe, load_data, validate_dataframe, generate_profiling_report

app = Flask(__name__)
# Set maximum upload size to 64 MB
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024


@app.route("/")
def index() -> str:
    """Renders the main dashboard."""
    return render_template(
        "index.html",
        seo_title="CleanCSV - Automated Data Cleaner & Onboarding Platform",
        seo_heading="Clean messy CSV & Excel data in seconds",
        seo_subtext="Upload CSV or Excel files. Standardize dates, remove duplicates, cap outliers, map columns, and edit cells live on-screen before exporting.",
        seo_tag="Smart Data Platform",
    )


@app.route("/clean-shopify-csv")
def shopify_cleaner() -> str:
    """Programmatic SEO landing page for Shopify store CSVs."""
    return render_template(
        "index.html",
        seo_title="Shopify Product & Inventory CSV Cleaner Online",
        seo_heading="Clean & Fix Shopify CSV Files Instantly",
        seo_subtext="Format customer names, clean inventory tags, remove duplicate SKUs, and fix prices for flawless Shopify import.",
        seo_tag="E-Commerce & Shopify Tool",
    )


@app.route("/remove-csv-duplicates-online")
def duplicate_cleaner() -> str:
    """Programmatic SEO landing page for duplicate removal."""
    return render_template(
        "index.html",
        seo_title="Remove Duplicate Rows from CSV Online - Free & Secure",
        seo_heading="Remove Duplicate Rows from CSV in 1 Click",
        seo_subtext="Instantly detect and purge identical rows from your CSV and Excel files. 100% private in-memory processing.",
        seo_tag="Duplicate Purge Utility",
    )


@app.route("/convert-excel-to-clean-csv")
def excel_to_csv() -> str:
    """Programmatic SEO landing page for Excel to CSV conversion."""
    return render_template(
        "index.html",
        seo_title="Convert Excel (.xlsx) to Clean CSV Online",
        seo_heading="Convert Excel to Clean, Normalized CSV",
        seo_subtext="Upload messy Excel sheets and export standardized, whitespace-free, date-normalized CSV or Excel files.",
        seo_tag="Excel to CSV Converter",
    )


@app.route("/fix-csv-date-format-online")
def date_formatter() -> str:
    """Programmatic SEO landing page for date standardization."""
    return render_template(
        "index.html",
        seo_title="Fix & Standardize CSV Date Formats Online (ISO YYYY-MM-DD)",
        seo_heading="Standardize CSV Dates to YYYY-MM-DD Online",
        seo_subtext="Auto-detect mixed date formats (DD/MM/YYYY, MM-DD-YYYY, Mon DD, YYYY) and convert to ISO 8601 standard.",
        seo_tag="Date Normalizer",
        canonical_url="https://cleancsv.app/fix-csv-date-format-online",
    )


@app.route("/excel-cleaner")
def excel_cleaner() -> str:
    """Programmatic SEO landing page targeting Excel cleaner queries."""
    return render_template(
        "index.html",
        seo_title="Free AI Excel Cleaner & Formatter Online - CleanCSV",
        seo_heading="Clean & Normalize Excel (.xlsx / .xls) Files Online",
        seo_subtext="Free Excel spreadsheet cleaner. Deduplicate rows, repair broken headers, standardize dates, and edit tables live in your browser up to 64MB with zero signup.",
        seo_tag="Excel Cleaner Tool",
        canonical_url="https://cleancsv.app/excel-cleaner",
    )


@app.route("/csv-cleaner")
def csv_cleaner() -> str:
    """Programmatic SEO landing page targeting CSV cleaner queries."""
    return render_template(
        "index.html",
        seo_title="Free CSV Cleaner Online - Fast, Private & Unlimited",
        seo_heading="Free CSV Data Cleaner & Validator Online",
        seo_subtext="Clean, deduplicate, and validate messy CSV files. Instant browser-based processing, interactive grid editing, and zero email required.",
        seo_tag="CSV Cleaner Tool",
        canonical_url="https://cleancsv.app/csv-cleaner",
    )


@app.route("/robots.txt")
def robots() -> Response:
    """Robots.txt for search engines."""
    content = "User-agent: *\nAllow: /\nSitemap: https://cleancsv.app/sitemap.xml\n"
    return Response(content, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap() -> Response:
    """Dynamic sitemap for Google and Bing web crawlers."""
    pages = [
        {"loc": "https://cleancsv.app/", "priority": "1.0", "changefreq": "daily"},
        {"loc": "https://cleancsv.app/excel-cleaner", "priority": "0.9", "changefreq": "weekly"},
        {"loc": "https://cleancsv.app/csv-cleaner", "priority": "0.9", "changefreq": "weekly"},
        {"loc": "https://cleancsv.app/remove-csv-duplicates-online", "priority": "0.8", "changefreq": "weekly"},
        {"loc": "https://cleancsv.app/convert-excel-to-clean-csv", "priority": "0.8", "changefreq": "weekly"},
        {"loc": "https://cleancsv.app/fix-csv-date-format-online", "priority": "0.8", "changefreq": "weekly"},
        {"loc": "https://cleancsv.app/clean-shopify-csv", "priority": "0.8", "changefreq": "weekly"},
        {"loc": "https://cleancsv.app/embed-demo", "priority": "0.7", "changefreq": "monthly"},
    ]
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page in pages:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{page['loc']}</loc>")
        xml_lines.append(f"    <changefreq>{page['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{page['priority']}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>")
    return Response("\n".join(xml_lines), mimetype="application/xml")


@app.route("/embed-demo")
def embed_demo() -> str:
    """Renders the B2B Embed Widget demo page."""
    return render_template("embed_demo.html")


@app.route("/embed.js")
def embed_script() -> Response:
    """Serves the standalone B2B embeddable CleanCSV widget script."""
    js_content = """
    window.CleanCSV = {
        open: function(options) {
            options = options || {};
            var modal = document.createElement("div");
            modal.style.position = "fixed";
            modal.style.top = "0";
            modal.style.left = "0";
            modal.style.width = "100%";
            modal.style.height = "100%";
            modal.style.backgroundColor = "rgba(15, 23, 42, 0.75)";
            modal.style.zIndex = "999999";
            modal.style.display = "flex";
            modal.style.alignItems = "center";
            modal.style.justifyContent = "center";

            var frame = document.createElement("iframe");
            frame.src = window.location.origin + "/";
            frame.style.width = "90%";
            frame.style.maxWidth = "1100px";
            frame.style.height = "85%";
            frame.style.border = "none";
            frame.style.borderRadius = "20px";
            frame.style.boxShadow = "0 25px 50px -12px rgba(0, 0, 0, 0.25)";

            modal.appendChild(frame);
            modal.onclick = function(e) { if(e.target === modal) document.body.removeChild(modal); };
            document.body.appendChild(modal);
        }
    };
    """
    return Response(js_content, mimetype="application/javascript")


@app.route("/api/clean-batch", methods=["POST"])
def clean_batch_files() -> Any:
    """Cleans multiple uploaded CSV/Excel files and returns a downloadable ZIP bundle."""
    files = request.files.getlist("files")
    if not files or len(files) == 0:
        return jsonify({"success": False, "error": "No files provided for batch processing."}), 400

    zip_buffer = io.BytesIO()
    processed_count = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            if not file.filename:
                continue
            try:
                buffer = io.BytesIO(file.read())
                df = load_data(buffer, filename=file.filename)
                cleaned_df, _ = clean_dataframe(df)

                out_buf = io.StringIO()
                cleaned_df.to_csv(out_buf, index=False)
                base, _ = os.path.splitext(file.filename)
                zip_file.writestr(f"{base}_cleaned.csv", out_buf.getvalue())
                processed_count += 1
            except Exception:
                continue

    if processed_count == 0:
        return jsonify({"success": False, "error": "Failed to process batch files."}), 400

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="cleancsv_batch_results.zip",
    )


@app.route("/api/sample", methods=["GET"])
def get_sample() -> Any:
    """Returns sample dirty CSV content for instant demonstration."""
    sample_path = os.path.join(os.path.dirname(__file__), "dirty_data.csv")
    if os.path.exists(sample_path):
        with open(sample_path, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({
            "success": True,
            "csv": content,
            "filename": "sample_dirty_data.csv",
            "columns": ["Name", "Age", "Salary"],
        })
    return jsonify({"success": False, "error": "Sample file not found"}), 404


@app.route("/api/inspect", methods=["POST"])
def inspect_file() -> Any:
    """Inspects an uploaded file and returns column names and row count for column mapping."""
    filename = "data.csv"
    file_bytes = None

    if "file" in request.files and request.files["file"].filename:
        uploaded_file = request.files["file"]
        filename = uploaded_file.filename or "data.csv"
        file_bytes = uploaded_file.read()
    elif "raw_csv" in request.form and request.form["raw_csv"].strip():
        file_bytes = request.form["raw_csv"].encode("utf-8")
        filename = request.form.get("filename", "sample.csv")
    else:
        return jsonify({"success": False, "error": "No file or data provided."}), 400

    try:
        buffer = io.BytesIO(file_bytes)
        df = load_data(buffer, filename=filename)
        columns = [str(c).strip() for c in df.columns]
        preview_rows = df.head(5).where(pd.notnull(df.head(5)), None).to_dict(orient="records")
        return jsonify({
            "success": True,
            "filename": filename,
            "columns": columns,
            "total_rows": int(len(df)),
            "preview": preview_rows,
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to inspect file: {str(e)}"}), 400


@app.route("/api/clean", methods=["POST"])
def clean_file() -> Any:
    """Receives uploaded CSV/Excel file, cleans it with configured rules, and returns preview and export payloads."""
    numeric_strategy = request.form.get("numeric_strategy", "median")
    string_strategy = request.form.get("string_strategy", "unknown")
    drop_duplicates = request.form.get("drop_duplicates", "true").lower() in ("true", "1", "yes")
    trim_strings = request.form.get("trim_strings", "true").lower() in ("true", "1", "yes")
    standardize_dates = request.form.get("standardize_dates", "true").lower() in ("true", "1", "yes")
    handle_outliers = request.form.get("handle_outliers", "false").lower() in ("true", "1", "yes")
    fuzzy_clustering = request.form.get("fuzzy_clustering", "false").lower() in ("true", "1", "yes")
    split_names = request.form.get("split_names", "false").lower() in ("true", "1", "yes")

    # Column mapping & dropping (Flatfile-Lite)
    column_mapping = {}
    if request.form.get("column_mapping"):
        try:
            column_mapping = json.loads(request.form.get("column_mapping", "{}"))
        except Exception:
            column_mapping = {}

    drop_columns = []
    if request.form.get("drop_columns"):
        try:
            drop_columns = json.loads(request.form.get("drop_columns", "[]"))
        except Exception:
            drop_columns = []

    filename = "cleaned_data.csv"
    file_bytes = None

    if "file" in request.files and request.files["file"].filename:
        uploaded_file = request.files["file"]
        filename = uploaded_file.filename or "data.csv"
        file_bytes = uploaded_file.read()
    elif "raw_csv" in request.form and request.form["raw_csv"].strip():
        file_bytes = request.form["raw_csv"].encode("utf-8")
        filename = request.form.get("filename", "custom_data.csv")
    else:
        return jsonify({"success": False, "error": "No file or data provided."}), 400

    try:
        buffer = io.BytesIO(file_bytes)
        df_original = load_data(buffer, filename=filename)
    except Exception as e:
        return jsonify({"success": False, "error": f"Could not parse file: {str(e)}"}), 400

    if df_original.empty:
        return jsonify({"success": False, "error": "The uploaded dataset is empty."}), 400

    original_cols = [str(c).strip() for c in df_original.columns]
    original_rows = df_original.head(25).where(pd.notnull(df_original.head(25)), None).to_dict(orient="records")

    try:
        df_cleaned, report = clean_dataframe(
            df_original.copy(),
            numeric_strategy=numeric_strategy,
            string_strategy=string_strategy,
            drop_duplicates=drop_duplicates,
            trim_strings=trim_strings,
            standardize_date_columns=standardize_dates,
            handle_outliers_flag=handle_outliers,
            fuzzy_clustering=fuzzy_clustering,
            split_names=split_names,
            column_mapping=column_mapping,
            drop_columns=drop_columns,
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Data cleaning failed: {str(e)}"}), 500

    cleaned_cols = [str(c).strip() for c in df_cleaned.columns]
    cleaned_rows = df_cleaned.head(25).where(pd.notnull(df_cleaned.head(25)), None).to_dict(orient="records")

    # Phase 2: Run Validation & Profiling
    validation_info = validate_dataframe(df_cleaned)
    profiling_info = generate_profiling_report(df_original, df_cleaned)

    # Generate CSV payload
    csv_buffer = io.StringIO()
    df_cleaned.to_csv(csv_buffer, index=False)
    cleaned_csv_str = csv_buffer.getvalue()

    # Generate Excel payload (Base64)
    excel_buffer = io.BytesIO()
    df_cleaned.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_b64 = base64.b64encode(excel_buffer.getvalue()).decode("utf-8")

    # Generate JSON payload
    json_str = df_cleaned.to_json(orient="records", indent=2)

    base_name, _ = os.path.splitext(filename)

    return jsonify({
        "success": True,
        "filename": filename,
        "download_csv_filename": f"{base_name}_cleaned.csv",
        "download_excel_filename": f"{base_name}_cleaned.xlsx",
        "download_json_filename": f"{base_name}_cleaned.json",
        "report": report,
        "validation": validation_info,
        "profiling": profiling_info,
        "original": {
            "columns": original_cols,
            "rows": original_rows,
            "total_rows": int(len(df_original)),
            "total_cols": int(len(df_original.columns)),
        },
        "cleaned": {
            "columns": cleaned_cols,
            "rows": cleaned_rows,
            "total_rows": int(len(df_cleaned)),
            "total_cols": int(len(df_cleaned.columns)),
        },
        "csv_content": cleaned_csv_str,
        "excel_b64": excel_b64,
        "json_content": json_str,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n[SERVER] Automated CSV & Excel Cleaner running at http://127.0.0.1:{port}/\n")
    app.run(host="127.0.0.1", port=port, debug=True)
