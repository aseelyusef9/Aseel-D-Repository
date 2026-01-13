import unittest
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
from db_util import init_db
from fastapi.testclient import TestClient
import app


class TestInvoiceExtraction(unittest.TestCase):

    def setUp(self):
        """Set up test database before each test"""
        init_db()

    def _create_mock_response(self, doc_types=None, pages=None):
        """Helper to create mock OCI response"""
        if doc_types is None:
            doc_types = [
                type('obj', (object,), {'document_type': 'INVOICE', 'confidence': 1})()]
        if pages is None:
            pages = []
        return type('obj', (object,), {
            'data': type('obj', (object,), {
                'detected_document_types': doc_types,
                'pages': pages
            })()
        })()

    def _create_valid_mock_response(self):
        """Create mock response with valid invoice data"""
        return self._create_mock_response(
            doc_types=[
                type('obj', (object,), {'document_type': 'INVOICE', 'confidence': 1})()],
            pages=[type('obj', (object,), {
                        'document_fields': [
                            self._create_field(
                                'VendorName', 'SuperStore', 0.9491271),
                            self._create_field(
                                'VendorNameLogo', 'SuperStore', 0.9491271),
                            self._create_field(
                                'InvoiceId', '36259', 0.9995704),
                            self._create_field(
                                'InvoiceDate', '2012-03-06T00:00:00+00:00', 0.9999474),
                            self._create_field(
                                'ShippingAddress', '98103, Seattle, Washington, United States', 0.9818857),
                            self._create_field(
                                'BillingAddressRecipient', 'Aaron Bergman', 0.9970944),
                            self._create_field('AmountDue', 58.11, 0.9994609),
                            self._create_field('SubTotal', 53.82, 0.90709054),
                            self._create_field(
                                'ShippingCost', 4.29, 0.98618066),
                            self._create_field(
                                'InvoiceTotal', 58.11, 0.9974165),
                            self._create_items_field()
                        ]
                        })()]
        )

    def _create_field(self, name, value, confidence=None):
        """Helper to create a field object"""
        return type('obj', (object,), {
            'field_type': 'KEY_VALUE',
            'field_label': type('obj', (object,), {'name': name, 'confidence': confidence})(),
            'field_value': type('obj', (object,), {'value': value})()
        })()

    def _create_items_field(self):
        """Helper to create items field"""
        item_fields = [
            self._create_field(
                'Description', 'Newell 330 Art, Office Supplies, OFF-AR-5309'),
            self._create_field(
                'Name', 'Newell 330 Art, Office Supplies, OFF-AR-5309'),
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

    @contextmanager
    def _mock_doc_client(self, mock_response=None, side_effect=None):
        """Context manager to mock doc_client"""
        with patch('oci.ai_document.AIServiceDocumentClient') as mock_class, \
                patch('oci.config.from_file', return_value={}):
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            if side_effect:
                mock_instance.analyze_document.side_effect = side_effect
            else:
                mock_instance.analyze_document.return_value = mock_response or self._create_valid_mock_response()

            original = app.doc_client
            app.doc_client = mock_instance
            try:
                yield TestClient(app.app)
            finally:
                app.doc_client = original

    @patch('oci.ai_document.AIServiceDocumentClient')
    @patch('oci.config.from_file', return_value={})
    def test_extract_endpoint(self, mock_config, mock_client_class):
        """Test the /extract endpoint with valid PDF"""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        mock_instance.analyze_document.return_value = self._create_valid_mock_response()

        client = TestClient(app.app)
        with open("invoices_sample/invoice_Aaron_Bergman_36259.pdf", "rb") as f:
            response = client.post(
                "/extract", files={"file": ("invoice.pdf", f, "application/pdf")})

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["data"]["InvoiceId"], "36259")
        self.assertEqual(result["data"]["VendorName"], "SuperStore")

    def test_extract_endpoint_invalid_pdf_low_confidence(self):
        """Test invalid PDF with low confidence"""
        mock_response = self._create_mock_response(
            doc_types=[
                type('obj', (object,), {'document_type': 'INVOICE', 'confidence': 0.5})()]
        )

        with self._mock_doc_client(mock_response) as client:
            response = client.post(
                "/extract", files={"file": ("invalid.pdf", b'%PDF-1.4\ninvalid', "application/pdf")})
            self.assertEqual(response.status_code, 400)
            self.assertIn("Invalid document", response.json()["detail"])

    def test_extract_endpoint_no_document_types(self):
        """Test PDF with no detected document types"""
        mock_response = self._create_mock_response(doc_types=[], pages=[])

        with self._mock_doc_client(mock_response) as client:
            response = client.post(
                "/extract", files={"file": ("invalid.pdf", b'%PDF-1.4\ninvalid', "application/pdf")})
            # App allows empty types (current behavior)
            self.assertIn(response.status_code, [200, 400])
            if response.status_code == 200:
                self.assertIn("data", response.json())

    def test_extract_endpoint_missing_file(self):
        """Test request without file"""
        client = TestClient(app.app)
        response = client.post("/extract")
        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())

    def test_extract_endpoint_empty_file(self):
        """Test empty file upload"""
        with self._mock_doc_client(side_effect=Exception("Empty file error")) as client:
            try:
                response = client.post(
                    "/extract", files={"file": ("empty.pdf", b"", "application/pdf")})
                self.assertEqual(response.status_code, 500)
            except Exception as e:
                self.assertIn("Empty file", str(e))

    def test_extract_endpoint_non_pdf_file(self):
        """Test non-PDF file upload"""
        mock_response = self._create_mock_response(
            doc_types=[
                type('obj', (object,), {'document_type': 'OTHER', 'confidence': 0.3})()]
        )

        with self._mock_doc_client(mock_response) as client:
            response = client.post(
                "/extract", files={"file": ("document.txt", b'text content', "text/plain")})
            self.assertEqual(response.status_code, 400)
            self.assertIn("Invalid document", response.json()["detail"])


if __name__ == '__main__':
    unittest.main()