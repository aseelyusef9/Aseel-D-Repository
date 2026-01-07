import unittest
import os
from fastapi.testclient import TestClient
from db_util import init_db, get_db, save_inv_extraction


class TestInvoicesByVendor(unittest.TestCase):
    
    def setUp(self):
        """Set up test database and client before each test"""
        # Use a test database - set before importing app
        import db_util
        db_util.DB_PATH = "test_invoices_by_vendor.db"
        
        # Initialize database
        init_db()
        
        # Import app after database setup (app will use the updated DB_PATH)
        from app import app
        self.client = TestClient(app)
        
        # Insert test invoice data
        self.setup_test_data()
    
    def tearDown(self):
        """Clean up test database after each test"""
        if os.path.exists("test_invoices_by_vendor.db"):
            os.remove("test_invoices_by_vendor.db")
    
    def setup_test_data(self):
        """Insert test invoice data for multiple vendors"""
        # Insert invoices for SuperStore vendor
        test_result1 = {
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
            "dataConfidence": {},
            "predictionTime": 1.5
        }
        save_inv_extraction(test_result1)
        
        # Insert another invoice for SuperStore vendor (earlier date)
        test_result2 = {
            "confidence": 1,
            "data": {
                "InvoiceId": "36258",
                "VendorName": "SuperStore",
                "InvoiceDate": "2012-03-05T00:00:00+00:00",
                "BillingAddressRecipient": "John Doe",
                "ShippingAddress": "123 Main St",
                "SubTotal": 100.0,
                "ShippingCost": 10.0,
                "InvoiceTotal": 110.0,
                "Items": [
                    {
                        "Description": "Test Item",
                        "Name": "Test Product",
                        "Quantity": 1,
                        "UnitPrice": 100.0,
                        "Amount": 100.0
                    }
                ]
            },
            "dataConfidence": {},
            "predictionTime": 1.0
        }
        save_inv_extraction(test_result2)
        
        # Insert invoice for different vendor
        test_result3 = {
            "confidence": 1,
            "data": {
                "InvoiceId": "50000",
                "VendorName": "OtherVendor",
                "InvoiceDate": "2012-04-01T00:00:00+00:00",
                "BillingAddressRecipient": "Jane Smith",
                "ShippingAddress": "456 Oak Ave",
                "SubTotal": 200.0,
                "ShippingCost": 20.0,
                "InvoiceTotal": 220.0,
                "Items": []
            },
            "dataConfidence": {},
            "predictionTime": 1.0
        }
        save_inv_extraction(test_result3)
    
    def test_get_invoices_by_vendor_success(self):
        """Test successful retrieval of invoices by vendor name"""
        response = self.client.get("/invoices/vendor/SuperStore")
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        result = response.json()
        
        # Validate response structure
        self.assertIn("VendorName", result)
        self.assertIn("TotalInvoices", result)
        self.assertIn("invoices", result)
        
        # Validate values
        self.assertEqual(result["VendorName"], "SuperStore")
        self.assertEqual(result["TotalInvoices"], 2)
        self.assertIsInstance(result["invoices"], list)
        self.assertEqual(len(result["invoices"]), 2)
        
        # Validate invoices are ordered by date (ascending)
        # First invoice should be 36258 (earlier date)
        self.assertEqual(result["invoices"][0]["InvoiceId"], "36258")
        self.assertEqual(result["invoices"][1]["InvoiceId"], "36259")
        
        # Validate invoice structure
        invoice = result["invoices"][0]
        self.assertIn("InvoiceId", invoice)
        self.assertIn("VendorName", invoice)
        self.assertIn("InvoiceDate", invoice)
        self.assertIn("Items", invoice)
        self.assertEqual(invoice["VendorName"], "SuperStore")
    
    def test_get_invoices_by_vendor_not_found(self):
        """Test response for vendor with no invoices"""
        response = self.client.get("/invoices/vendor/NonExistentVendor")
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        result = response.json()
        
        # Validate response structure for unknown vendor
        self.assertEqual(result["VendorName"], "Unknown Vendor")
        self.assertEqual(result["TotalInvoices"], 0)
        self.assertIsInstance(result["invoices"], list)
        self.assertEqual(len(result["invoices"]), 0)
    
    def test_get_invoices_by_vendor_case_sensitive(self):
        """Test that vendor name matching is case sensitive"""
        # Search for lowercase vendor name
        response = self.client.get("/invoices/vendor/superstore")
        
        # Should return empty result (case sensitive)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["VendorName"], "Unknown Vendor")
        self.assertEqual(result["TotalInvoices"], 0)
    
    def test_get_invoices_by_vendor_single_invoice(self):
        """Test vendor with only one invoice"""
        response = self.client.get("/invoices/vendor/OtherVendor")
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Parse response
        result = response.json()
        
        # Validate response
        self.assertEqual(result["VendorName"], "OtherVendor")
        self.assertEqual(result["TotalInvoices"], 1)
        self.assertEqual(len(result["invoices"]), 1)
        self.assertEqual(result["invoices"][0]["InvoiceId"], "50000")
    
    def test_get_invoices_by_vendor_includes_all_fields(self):
        """Test that vendor invoices include all required fields"""
        response = self.client.get("/invoices/vendor/SuperStore")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Check first invoice has all fields
        invoice = result["invoices"][0]
        required_fields = [
            "InvoiceId", "VendorName", "InvoiceDate",
            "BillingAddressRecipient", "ShippingAddress",
            "SubTotal", "ShippingCost", "InvoiceTotal", "Items"
        ]
        
        for field in required_fields:
            self.assertIn(field, invoice, f"Missing field: {field}") 
    
    def test_get_invoices_by_vendor_empty_string(self):
        """Test vendor search with empty string"""
        response = self.client.get("/invoices/vendor/")
        
        # FastAPI will treat this as a different route, so it should return 404
        # But if it's handled, check the response
        if response.status_code == 200:
            result = response.json()
            self.assertEqual(result["TotalInvoices"], 0)


if __name__ == '__main__':
    unittest.main()