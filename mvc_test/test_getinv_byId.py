# test_get_invoice_by_id.py
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, get_db
from models import Invoice, Item, Confidence
import app
from queries import save_invoice_extraction

# ----------------------------
# Test database (in-memory SQLite)
# ----------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)

# Override FastAPI dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.app.dependency_overrides[get_db] = override_get_db

class TestInvoiceById(unittest.TestCase):

    def setUp(self):
        # Clean and recreate DB before each test
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app.app)
        self.setup_test_data()

    def setup_test_data(self):
        """Insert a standard invoice for testing"""
        test_result = {
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
        db = next(override_get_db())
        save_invoice_extraction(db, test_result)

    def test_get_invoice_by_id_success(self):
        response = self.client.get("/invoice/36259")
        self.assertEqual(response.status_code, 200)
        result = response.json()

        self.assertEqual(result["InvoiceId"], "36259")
        self.assertEqual(result["VendorName"], "SuperStore")
        self.assertEqual(result["BillingAddressRecipient"], "Aaron Bergman")
        self.assertEqual(len(result["Items"]), 1)
        self.assertEqual(result["Items"][0]["Name"], "Newell 330 Art, Office Supplies, OFF-AR-5309")

    def test_get_invoice_by_id_not_found(self):
        response = self.client.get("/invoice/99999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Invoice not found")

    def test_get_invoice_by_id_empty_items(self):
        """Invoice with no items"""
        test_result = {
            "confidence": 1,
            "data": {
                "InvoiceId": "12345",
                "VendorName": "TestVendor",
                "InvoiceDate": "2023-01-01T00:00:00+00:00",
                "BillingAddressRecipient": "Test Recipient",
                "ShippingAddress": "Test Address",
                "SubTotal": 100.0,
                "ShippingCost": 10.0,
                "InvoiceTotal": 110.0,
                "Items": []
            },
            "dataConfidence": {},
            "predictionTime": 1.0
        }
        db = next(override_get_db())
        save_invoice_extraction(db, test_result)

        response = self.client.get("/invoice/12345")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["Items"], [])

    def test_get_invoice_by_id_multiple_items(self):
        """Invoice with multiple items"""
        test_result = {
            "confidence": 1,
            "data": {
                "InvoiceId": "67890",
                "VendorName": "MultiItemVendor",
                "InvoiceDate": "2023-02-01T00:00:00+00:00",
                "BillingAddressRecipient": "Multi Recipient",
                "ShippingAddress": "Multi Address",
                "SubTotal": 200.0,
                "ShippingCost": 20.0,
                "InvoiceTotal": 220.0,
                "Items": [
                    {"Description": "Item 1", "Name": "Product 1", "Quantity": 2, "UnitPrice": 50.0, "Amount": 100.0},
                    {"Description": "Item 2", "Name": "Product 2", "Quantity": 4, "UnitPrice": 25.0, "Amount": 100.0},
                ]
            },
            "dataConfidence": {},
            "predictionTime": 1.0
        }
        db = next(override_get_db())
        save_invoice_extraction(db, test_result)

        response = self.client.get("/invoice/67890")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(len(result["Items"]), 2)
        self.assertEqual(result["Items"][0]["Description"], "Item 1")
        self.assertEqual(result["Items"][1]["Description"], "Item 2")


if __name__ == '__main__':
    unittest.main()
