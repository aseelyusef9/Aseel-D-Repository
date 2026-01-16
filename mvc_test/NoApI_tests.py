#This ensures your queries layer works independently of FastAPI.
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, get_db
from queries import save_invoice_extraction, get_invoice_by_id, get_invoices_by_vendor

class TestDBIntegration(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_save_and_get_invoice(self):
        invoice_data = {
            "InvoiceId": "123",
            "VendorName": "TestVendor",
            "InvoiceDate": "2023-01-01",
            "BillingAddressRecipient": "Alice",
            "ShippingAddress": "Address",
            "SubTotal": 100.0,
            "ShippingCost": 10.0,
            "InvoiceTotal": 110.0,
            "Items": []
        }
        save_invoice_extraction(self.db, {"confidence": 1, "data": invoice_data, "dataConfidence": {}, "predictionTime": 1.0})
        
        # Fetch by ID
        invoice = get_invoice_by_id(self.db, "123")
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice["VendorName"], "TestVendor")

    def test_get_invoices_by_vendor(self):
        invoice_data = {
            "InvoiceId": "124",
            "VendorName": "VendorX",
            "InvoiceDate": "2023-02-01",
            "BillingAddressRecipient": "Bob",
            "ShippingAddress": "Addr",
            "SubTotal": 50.0,
            "ShippingCost": 5.0,
            "InvoiceTotal": 55.0,
            "Items": []
        }
        save_invoice_extraction(self.db, {"confidence": 1, "data": invoice_data, "dataConfidence": {}, "predictionTime": 1.0})
        invoices = get_invoices_by_vendor(self.db, "VendorX")
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0]["InvoiceId"], "124")

