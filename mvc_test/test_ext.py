# test_app.py
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, get_db
import app
from models import Invoice, Item, Confidence

# ----------------------------
# Test database setup (SQLite in-memory)
# ----------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)

# Dependency override
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.app.dependency_overrides[get_db] = override_get_db


class TestInvoiceExtractionMVC(unittest.TestCase):

    def setUp(self):
        # Ensure a fresh DB for each test
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    # ----------------------------
    # Mock helpers for OCI
    # ----------------------------
    def _create_field(self, name, value, confidence=None):
        return type('obj', (object,), {
            'field_type': 'KEY_VALUE',
            'field_label': type('obj', (object,), {'name': name, 'confidence': confidence})(),
            'field_value': type('obj', (object,), {'value': value})()
        })()

    def _create_items_field(self):
        item_fields = [
            self._create_field('Description', 'Newell 330 Art, Office Supplies, OFF-AR-5309'),
            self._create_field('Name', 'Newell 330 Art, Office Supplies, OFF-AR-5309'),
            self._create_field('Quantity', 3),
            self._create_field('UnitPrice', 17.94),
            self._create_field('Amount', 53.82)
        ]
        return type('obj', (object,), {
            'field_type': 'LINE_ITEM_GROUP',
            'field_label': type('obj', (object,), {'name': 'Items', 'confidence': None})(),
            'field_value': type('obj', (object,), {
                'items': [type('obj', (object,), {
                    'field_value': type('obj', (object,), {'items': item_fields})()
                })()]
            })()
        })()

    def _create_mock_response(self, doc_types=None, pages=None):
        if doc_types is None:
            doc_types = [type('obj', (object,), {'document_type': 'INVOICE', 'confidence': 1})()]
        if pages is None:
            pages = []
        return type('obj', (object,), {
            'data': type('obj', (object,), {
                'detected_document_types': doc_types,
                'pages': pages
            })()
        })()

    def _create_valid_mock_response(self):
        return self._create_mock_response(
            doc_types=[type('obj', (object,), {'document_type': 'INVOICE', 'confidence': 1})()],
            pages=[type('obj', (object,), {
                'document_fields': [
                    self._create_field('VendorName', 'SuperStore', 0.9491271),
                    self._create_field('InvoiceId', '36259', 0.9995704),
                    self._create_field('InvoiceDate', '2012-03-06T00:00:00+00:00', 0.9999474),
                    self._create_field('ShippingAddress', '98103, Seattle, Washington, United States', 0.9818857),
                    self._create_field('BillingAddressRecipient', 'Aaron Bergman', 0.9970944),
                    self._create_field('SubTotal', 53.82, 0.90709054),
                    self._create_field('ShippingCost', 4.29, 0.98618066),
                    self._create_field('InvoiceTotal', 58.11, 0.9974165),
                    self._create_items_field()
                ]
            })()]
        )

    # ----------------------------
    # Test /extract endpoint
    # ----------------------------
    def test_extract_endpoint_success(self):
        with patch('oci.ai_document.AIServiceDocumentClient') as mock_class, \
             patch('oci.config.from_file', return_value={}):
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            mock_instance.analyze_document.return_value = self._create_valid_mock_response()

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
        mock_response = self._create_mock_response(
            doc_types=[type('obj', (object,), {'document_type': 'INVOICE', 'confidence': 0.5})()]
        )
        with patch('oci.ai_document.AIServiceDocumentClient') as mock_class, \
             patch('oci.config.from_file', return_value={}):
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            mock_instance.analyze_document.return_value = mock_response

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
        db = next(override_get_db())
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
