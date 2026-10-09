import os
import tempfile
import unittest
import pandas as pd
from cleaner import (
    clean_dataframe,
    clean_csv,
    standardize_dates,
    handle_outliers,
    validate_dataframe,
    generate_profiling_report,
    normalize_fuzzy_categories,
    split_full_names,
)


class TestDataCleaner(unittest.TestCase):
    def test_deduplication(self):
        data = {
            "Name": ["Alice", "Bob", "Alice"],
            "Age": [20, 30, 20],
        }
        df = pd.DataFrame(data)
        cleaned_df, report = clean_dataframe(df)
        self.assertEqual(len(cleaned_df), 2)
        self.assertEqual(report["duplicates_removed"], 1)

    def test_whitespace_trimming(self):
        data = {
            "  Name  ": [" Alice  ", " Bob "],
            "City": [" Dhaka ", "Sylhet "],
        }
        df = pd.DataFrame(data)
        cleaned_df, _ = clean_dataframe(df)
        self.assertIn("Name", cleaned_df.columns)
        self.assertEqual(cleaned_df["Name"].tolist(), ["Alice", "Bob"])
        self.assertEqual(cleaned_df["City"].tolist(), ["Dhaka", "Sylhet"])

    def test_numeric_imputation_median(self):
        data = {
            "Salary": [1000.0, None, 3000.0],
        }
        df = pd.DataFrame(data)
        cleaned_df, report = clean_dataframe(df, numeric_strategy="median")
        self.assertEqual(cleaned_df["Salary"].tolist(), [1000, 2000, 3000])
        self.assertIn("Salary", report["imputed_columns"])

    def test_date_standardization(self):
        data = {
            "JoinDate": ["2024/05/12", "12-05-2024", "2024-05-12"],
            "User": ["A", "B", "C"],
        }
        df = pd.DataFrame(data)
        cleaned_df, report = clean_dataframe(df, standardize_date_columns=True)
        self.assertIn("JoinDate", report["standardized_dates"])
        self.assertTrue(all("-" in d for d in cleaned_df["JoinDate"]))

    def test_outlier_handling_iqr(self):
        data = {
            "Values": [100.0, 105.0, 110.0, 115.0, 10000.0],
        }
        df = pd.DataFrame(data)
        cleaned_df, report = clean_dataframe(df, handle_outliers_flag=True)
        self.assertIn("Values", report["outliers_handled"])
        self.assertLess(cleaned_df["Values"].max(), 1000.0)

    def test_column_mapping_and_dropping(self):
        data = {
            "Cust_Name": ["John", "Jane"],
            "Temp_ID": [999, 888],
        }
        df = pd.DataFrame(data)
        cleaned_df, report = clean_dataframe(
            df,
            column_mapping={"Cust_Name": "full_name"},
            drop_columns=["Temp_ID"],
        )
        self.assertIn("full_name", cleaned_df.columns)
        self.assertNotIn("Temp_ID", cleaned_df.columns)
        self.assertIn("Temp_ID", report["dropped_columns"])

    def test_validation_dataframe(self):
        data = {
            "Email": ["valid@test.com", "broken_email.com"],
            "Salary": [50000, -100],
        }
        df = pd.DataFrame(data)
        validation = validate_dataframe(df)
        self.assertGreaterEqual(validation["total_errors"], 2)
        self.assertIn("1_Email", validation["cell_errors"])
        self.assertIn("1_Salary", validation["cell_errors"])

    def test_profiling_report(self):
        df_before = pd.DataFrame({
            "Name": ["A", "B", "A"],
            "Age": [20, None, 20],
        })
        df_after, _ = clean_dataframe(df_before)
        profile = generate_profiling_report(df_before, df_after)
        self.assertIn("health_score", profile)
        self.assertIn("memory_reduction_pct", profile)
        self.assertEqual(len(profile["columns_profile"]), 2)

    def test_excel_file_io(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, "test.xlsx")
            output_file = os.path.join(tmpdir, "test_cleaned.xlsx")

            pd.DataFrame({
                "Name": ["Sam", "Sam"],
                "Age": [40, 40],
            }).to_excel(input_file, index=False)

            result_df = clean_csv(input_file, output_path=output_file)
            self.assertTrue(os.path.exists(output_file))
            self.assertEqual(len(result_df), 1)

    def test_fuzzy_clustering(self):
        data = {
            "City": ["Dhaka", "dhaka", "Dacca", "Sylhet", "sylhet"],
        }
        df = pd.DataFrame(data)
        cleaned_df, report = clean_dataframe(df, fuzzy_clustering=True)
        # Should normalize dhaka -> Dhaka and sylhet -> Sylhet
        self.assertIn("City", report["fuzzy_clusters"])

    def test_name_splitting(self):
        data = {
            "Customer_Name": ["Dr. John Watson", "Sherlock Holmes", "Irene Adler"],
        }
        df = pd.DataFrame(data)
        cleaned_df, report = clean_dataframe(df, split_names=True)
        self.assertIn("Customer_Name_First", cleaned_df.columns)
        self.assertIn("Customer_Name_Last", cleaned_df.columns)
        self.assertEqual(cleaned_df["Customer_Name_First"].tolist(), ["John", "Sherlock", "Irene"])
        self.assertEqual(cleaned_df["Customer_Name_Last"].tolist(), ["Watson", "Holmes", "Adler"])


if __name__ == "__main__":
    unittest.main()
