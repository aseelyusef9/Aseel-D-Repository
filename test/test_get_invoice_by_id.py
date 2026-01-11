import unittest
import os
from fastapi.testclient import TestClient
from db_util import init_db, get_db, save_inv_extraction


class TestInvoiceById(unittest.TestCase):

    def setUp(self):
        """Set up test database and client before each test"""
        # Use a test database - set before importing app
        import db_util
        db_util.DB_PATH = "test_invoices_by_id.db"

        # Initialize database
        init_db()

        # Import app after database setup (app will use the updated DB_PATH)
        from app import app
        self.client = TestClient(app)

        # Insert test invoice data
        self.setup_test_data()

    def tearDown(self):
        """Clean up test database after each test"""
        if os.path.exists("test_invoices_by_id.db"):
            os.remove("test_invoices_by_id.db")

    def setup_test_data(self):
        """Insert test invoice data into database"""
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
        save_inv_extraction(test_result)

    def test_get_invoice_by_id_success(self):
        """Test successful retrieval of invoice by ID"""
        response = self.client.get("/invoice/36259")

        # Check response status
        self.assertEqual(response.status_code, 200)

        # Parse response
        result = response.json()

        # Validate response structure
        self.assertIn("InvoiceId", result)
        self.assertIn("VendorName", result)
        self.assertIn("InvoiceDate", result)
        self.assertIn("BillingAddressRecipient", result)
        self.assertIn("ShippingAddress", result)
        self.assertIn("SubTotal", result)
        self.assertIn("ShippingCost", result)
        self.assertIn("InvoiceTotal", result)
        self.assertIn("Items", result)

        # Validate values
        self.assertEqual(result["InvoiceId"], "36259")
        self.assertEqual(result["VendorName"], "SuperStore")
        self.assertEqual(result["InvoiceDate"], "2012-03-06T00:00:00+00:00")
        self.assertEqual(result["BillingAddressRecipient"], "Aaron Bergman")
        self.assertEqual(result["ShippingAddress"],
                         "98103, Seattle, Washington, United States")
        self.assertEqual(result["SubTotal"], 53.82)
        self.assertEqual(result["ShippingCost"], 4.29)
        self.assertEqual(result["InvoiceTotal"], 58.11)

        # Validate Items structure
        self.assertIsInstance(result["Items"], list)
        self.assertEqual(len(result["Items"]), 1)
        self.assertEqual(result["Items"][0]["Description"],
                         "Newell 330 Art, Office Supplies, OFF-AR-5309")
        self.assertEqual(result["Items"][0]["Name"],
                         "Newell 330 Art, Office Supplies, OFF-AR-5309")
        self.assertEqual(result["Items"][0]["Quantity"], 3)
        self.assertEqual(result["Items"][0]["UnitPrice"], 17.94)
        self.assertEqual(result["Items"][0]["Amount"], 53.82)

    def test_get_invoice_by_id_not_found(self):
        """Test 404 response for non-existent invoice ID"""
        response = self.client.get("/invoice/99999")

        # Check response status
        self.assertEqual(response.status_code, 404)

        # Parse response
        result = response.json()

        # Validate error message
        self.assertIn("detail", result)
        self.assertEqual(result["detail"], "Invoice not found")

    def test_get_invoice_by_id_empty_items(self):
        """Test invoice retrieval with no items"""
        # Insert invoice without items
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
        save_inv_extraction(test_result)

        response = self.client.get("/invoice/12345")

        # Check response status
        self.assertEqual(response.status_code, 200)

        # Parse response
        result = response.json()

        # Validate Items is empty list
        self.assertIsInstance(result["Items"], list)
        self.assertEqual(len(result["Items"]), 0)

    def test_get_invoice_by_id_multiple_items(self):
        """Test invoice retrieval with multiple items"""
        # Insert invoice with multiple items
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
                    {
                        "Description": "Item 1",
                        "Name": "Product 1",
                        "Quantity": 2,
                        "UnitPrice": 50.0,
                        "Amount": 100.0
                    },
                    {
                        "Description": "Item 2",
                        "Name": "Product 2",
                        "Quantity": 4,
                        "UnitPrice": 25.0,
                        "Amount": 100.0
                    }
                ]
            },
            "dataConfidence": {},
            "predictionTime": 1.0
        }
        save_inv_extraction(test_result)

        response = self.client.get("/invoice/67890")

        # Check response status
        self.assertEqual(response.status_code, 200)

        # Parse response
        result = response.json()

        # Validate Items count
        self.assertEqual(len(result["Items"]), 2)
        self.assertEqual(result["Items"][0]["Description"], "Item 1")
        self.assertEqual(result["Items"][1]["Description"], "Item 2")


if __name__ == '__main__':
    unittest.main()