import io
import json
import unittest
import zipfile
from app import app


class TestWebApp(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CleanCSV", response.data)

    def test_seo_landing_pages(self):
        routes = [
            "/clean-shopify-csv",
            "/remove-csv-duplicates-online",
            "/convert-excel-to-clean-csv",
            "/fix-csv-date-format-online",
            "/excel-cleaner",
            "/csv-cleaner",
        ]
        for route in routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"CleanCSV", res.data)

    def test_crawler_endpoints(self):
        robots_res = self.client.get("/robots.txt")
        self.assertEqual(robots_res.status_code, 200)
        self.assertIn(b"User-agent", robots_res.data)

        sitemap_res = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap_res.status_code, 200)
        self.assertEqual(sitemap_res.mimetype, "application/xml")
        self.assertIn(b"<urlset", sitemap_res.data)

    def test_embed_pages(self):
        embed_res = self.client.get("/embed-demo")
        self.assertEqual(embed_res.status_code, 200)
        self.assertIn(b"Apex CRM", embed_res.data)

        script_res = self.client.get("/embed.js")
        self.assertEqual(script_res.status_code, 200)
        self.assertIn(b"CleanCSV", script_res.data)

    def test_sample_api(self):
        response = self.client.get("/api/sample")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertIn("Name,Age,Salary", json_data["csv"])
        self.assertEqual(json_data["columns"], ["Name", "Age", "Salary"])

    def test_inspect_api(self):
        csv_bytes = b"Cust_Name,JoinDate,Salary\nRahim,2024-01-01,30000\n"
        data = {
            "file": (io.BytesIO(csv_bytes), "customers.csv"),
        }
        response = self.client.post("/api/inspect", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["columns"], ["Cust_Name", "JoinDate", "Salary"])

    def test_clean_api_with_ai_and_validation(self):
        csv_bytes = (
            b"Customer_Name,City,Email,Salary,Date\n"
            b"Dr. John Watson,Dhaka,test@example.com,50000,2024/01/01\n"
            b"Sherlock Holmes,dhaka,bad_email,-200,2024/01/01\n"
        )
        data = {
            "file": (io.BytesIO(csv_bytes), "sample.csv"),
            "numeric_strategy": "median",
            "string_strategy": "unknown",
            "drop_duplicates": "true",
            "trim_strings": "true",
            "standardize_dates": "true",
            "handle_outliers": "false",
            "fuzzy_clustering": "true",
            "split_names": "true",
        }
        response = self.client.post("/api/clean", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertIn("validation", json_data)
        self.assertIn("profiling", json_data)
        self.assertIn("Customer_Name_First", json_data["cleaned"]["columns"])

    def test_batch_clean_api(self):
        f1 = (io.BytesIO(b"Name,Age\nA,10\nA,10\n"), "file1.csv")
        f2 = (io.BytesIO(b"City,Temp\nDhaka,30\n"), "file2.csv")

        data = {
            "files": [f1, f2],
        }
        response = self.client.post("/api/clean-batch", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/zip")

        # Verify ZIP contains the 2 cleaned files
        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            names = zf.namelist()
            self.assertIn("file1_cleaned.csv", names)
            self.assertIn("file2_cleaned.csv", names)


if __name__ == "__main__":
    unittest.main()
