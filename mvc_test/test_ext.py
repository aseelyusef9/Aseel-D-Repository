# test_app.py
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from db import Base, init_db, get_db
import app
from models import Invoice, Item, Confidence

# ----------------------------
# Test database setup (SQLite file-based for testing)
# ----------------------------
import os
TEST_DATABASE_URL = "sqlite:///./test_mvc.db"

engine = init_db(TEST_DATABASE_URL)
Base.metadata.create_all(bind=engine)

# Use the module's get_db as the override (it will use the initialized SessionLocal)
app.app.dependency_overrides[get_db] = get_db


class TestInvoiceExtractionMVC(unittest.TestCase):

    def setUp(self):
        # Ensure a fresh DB for each test
        import db as db_module
        Base.metadata.drop_all(bind=db_module.engine)
        Base.metadata.create_all(bind=db_module.engine)

    # ----------------------------
    # Test /extract endpoint
    # ----------------------------
    def test_extract_endpoint_success(self):
        mock_parsed_data = {
            "confidence": 1,
            "data": {
                "InvoiceId": "36259",
                "VendorName": "SuperStore",
                "InvoiceDate": "2012-03-06T00:00:00+00:00",
                "BillingAddressRecipient": "Aaron Bergman",
                "ShippingAddress": "98103, Seattle, Washington, United States",
                "SubTotal": 53.82,
                "ShippingCost": 4.29,
                "InvoiceTotal": 58.11,
                "Items": [
                    {
                        "Description": "Newell 330 Art, Office Supplies, OFF-AR-5309",
                        "Name": "Newell 330 Art, Office Supplies, OFF-AR-5309",
                        "Quantity": 3,
                        "UnitPrice": 17.94,
                        "Amount": 53.82
                    }
                ]
            },
            "dataConfidence": {
                "VendorName": 0.9491271,
                "InvoiceDate": 0.9999474,
                "BillingAddressRecipient": 0.9970944,
                "ShippingAddress": 0.9818857,
                "SubTotal": 0.90709054,
                "ShippingCost": 0.98618066,
                "InvoiceTotal": 0.9974165
            },
            "predictionTime": 1.5
        }
        
        with patch('app.parse_invoice_from_pdf', return_value=mock_parsed_data):
            client = TestClient(app.app)
            response = client.post(
                "/extract",
                files={"file": ("invoice.pdf", b"%PDF-1.4 mock pdf content", "application/pdf")}
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()["data"]
            self.assertEqual(data["InvoiceId"], "36259")
            self.assertEqual(data["VendorName"], "SuperStore")
            self.assertIn("Items", data)

    def test_extract_endpoint_invalid_confidence(self):
        from fastapi import HTTPException
        
        def mock_parse_with_error(pdf_bytes):
            raise HTTPException(status_code=400, detail="Invalid document. Please upload a valid invoice.")
        
        with patch('app.parse_invoice_from_pdf', side_effect=mock_parse_with_error):
            client = TestClient(app.app)
            response = client.post(
                "/extract",
                files={"file": ("low_conf.pdf", b"%PDF-1.4", "application/pdf")}
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("Invalid document", response.json()["detail"])

    # ----------------------------
    # Test /invoice/{id} endpoint
    # ----------------------------
    def test_get_invoice_by_id(self):
        # Insert invoice using queries layer
        from queries import save_invoice_extraction
        from db import SessionLocal
        db = SessionLocal()
        try:
            save_invoice_extraction(db, {
                "data": {
                    "InvoiceId": "1001",
                    "VendorName": "TestVendor",
                    "InvoiceDate": "2026-01-12",
                    "BillingAddressRecipient": "John Doe",
                    "ShippingAddress": "123 Street",
                    "SubTotal": 10,
                    "ShippingCost": 2,
                    "InvoiceTotal": 12,
                    "Items": []
                },
                "dataConfidence": {
                    "VendorName": 1,
                    "InvoiceDate": 1,
                    "BillingAddressRecipient": 1,
                    "ShippingAddress": 1,
                    "SubTotal": 1,
                    "ShippingCost": 1,
                    "InvoiceTotal": 1
                },
                "confidence": 1,
                "predictionTime": 0.1
            })
        finally:
            db.close()

        client = TestClient(app.app)
        response = client.get("/invoice/1001")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["InvoiceId"], "1001")
        self.assertEqual(response.json()["VendorName"], "TestVendor")

    def test_get_invoice_not_found(self):
        client = TestClient(app.app)
        response = client.get("/invoice/9999")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
