# test_invoices_by_vendor.py
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from db import Base, init_db, get_db
from queries import save_invoice_extraction
import app

# ----------------------------
# Test database (file-based SQLite for testing)
# ----------------------------
import os
TEST_DATABASE_URL = "sqlite:///./test_byvendor.db"
engine = init_db(TEST_DATABASE_URL)
Base.metadata.create_all(bind=engine)

# Override FastAPI dependency with module get_db
app.app.dependency_overrides[get_db] = get_db

class TestInvoicesByVendor(unittest.TestCase):

    def setUp(self):
        # Clean and recreate DB before each test
        import db as db_module
        Base.metadata.drop_all(bind=db_module.engine)
        Base.metadata.create_all(bind=db_module.engine)
        self.client = TestClient(app.app)
        self.setup_test_data()

    def setup_test_data(self):
        """Insert test invoice data for multiple vendors"""
        invoices = [
            {
                "InvoiceId": "36259",
                "VendorName": "SuperStore",
                "InvoiceDate": "2012-03-06T00:00:00+00:00",
                "BillingAddressRecipient": "Aaron Bergman",
                "ShippingAddress": "98103, Seattle, Washington, United States",
                "SubTotal": 53.82,
                "ShippingCost": 4.29,
                "InvoiceTotal": 58.11,
                "Items": [
                    {"Description": "Newell 330 Art, Office Supplies, OFF-AR-5309",
                     "Name": "Newell 330 Art, Office Supplies, OFF-AR-5309",
                     "Quantity": 3, "UnitPrice": 17.94, "Amount": 53.82}
                ]
            },
            {
                "InvoiceId": "36258",
                "VendorName": "SuperStore",
                "InvoiceDate": "2012-03-05T00:00:00+00:00",
                "BillingAddressRecipient": "John Doe",
                "ShippingAddress": "123 Main St",
                "SubTotal": 100.0,
                "ShippingCost": 10.0,
                "InvoiceTotal": 110.0,
                "Items": [{"Description": "Test Item", "Name": "Test Product", "Quantity": 1, "UnitPrice": 100.0, "Amount": 100.0}]
            },
            {
                "InvoiceId": "50000",
                "VendorName": "OtherVendor",
                "InvoiceDate": "2012-04-01T00:00:00+00:00",
                "BillingAddressRecipient": "Jane Smith",
                "ShippingAddress": "456 Oak Ave",
                "SubTotal": 200.0,
                "ShippingCost": 20.0,
                "InvoiceTotal": 220.0,
                "Items": []
            }
        ]

        from db import SessionLocal
        db = SessionLocal()
        try:
            for inv in invoices:
                save_invoice_extraction(db, {"confidence": 1, "data": inv, "dataConfidence": {}, "predictionTime": 1.0})
        finally:
            db.close()

    def test_get_invoices_by_vendor_success(self):
        response = self.client.get("/invoices/vendor/SuperStore")
        self.assertEqual(response.status_code, 200)
        result = response.json()

        self.assertEqual(result["VendorName"], "SuperStore")
        self.assertEqual(result["TotalInvoices"], 2)
        self.assertEqual(len(result["invoices"]), 2)
        self.assertEqual(result["invoices"][0]["InvoiceId"], "36258")  # ordered by date
        self.assertEqual(result["invoices"][1]["InvoiceId"], "36259")

    def test_get_invoices_by_vendor_not_found(self):
        response = self.client.get("/invoices/vendor/NonExistentVendor")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["VendorName"], "NonExistentVendor")
        self.assertEqual(result["TotalInvoices"], 0)
        self.assertEqual(result["invoices"], [])

    def test_get_invoices_by_vendor_case_sensitive(self):
        response = self.client.get("/invoices/vendor/superstore")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["VendorName"], "superstore")
        self.assertEqual(result["TotalInvoices"], 0)

    def test_get_invoices_by_vendor_single_invoice(self):
        response = self.client.get("/invoices/vendor/OtherVendor")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["VendorName"], "OtherVendor")
        self.assertEqual(result["TotalInvoices"], 1)
        self.assertEqual(result["invoices"][0]["InvoiceId"], "50000")

    def test_get_invoices_by_vendor_includes_all_fields(self):
        response = self.client.get("/invoices/vendor/SuperStore")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        invoice = result["invoices"][0]
        required_fields = [
            "InvoiceId", "VendorName", "InvoiceDate",
            "BillingAddressRecipient", "ShippingAddress",
            "SubTotal", "ShippingCost", "InvoiceTotal", "Items"
        ]
        for field in required_fields:
            self.assertIn(field, invoice)

    def test_get_invoices_by_vendor_empty_string(self):
        response = self.client.get("/invoices/vendor/")
        if response.status_code == 200:
            result = response.json()
            self.assertEqual(result["TotalInvoices"], 0)


if __name__ == '__main__':
    unittest.main()
