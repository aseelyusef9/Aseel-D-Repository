# API Traceability Matrix – InvParser API

This document maps each implemented API endpoint to the corresponding
integration test cases to ensure full API coverage.

---

## Traceability Matrix

| API Endpoint | HTTP Method | Functionality | Test Case | Test File |
|-------------|------------|---------------|-----------|-----------|
| /invoice/{invoice_id} | GET | Retrieve invoice data by invoice ID | test_get_invoice_by_id success | tests/test_get_invoice_by_id.py |
| /invoice/{invoice_id} | GET | Return 404 when invoice ID does not exist |  test_get_invoice_by_id_not_found | tests/test_get_invoice_by_id.py |
| /invoices/vendor/{vendor_name} | GET | Retrieve all invoices for a specific vendor | test_get_invoices_by_vendor_success | tests/test_get_invoices_by_vendor.py |
| /invoices/vendor/{vendor_name} | GET | Return empty list or 404 when vendor has no invoices | test_get_invoices_by_vendor_empty_string | tests/test_get_invoice_by_vendor.py |
| /extract | POST | Extract invoice data from PDF and store in database | test_extract_endpoint | tests/test_extract.py |
| /extract | POST | Reject invalid or non-PDF files | test_extract_invalid_file | tests/test_extract.py |

---

## Coverage Summary

- All three API endpoints are covered by integration tests.
- Both success and failure scenarios are tested for each endpoint.
- Integration tests validate:
  - API request/response behavior
  - Database interaction
  - Error handling
- External dependencies (OCI Document AI service) are mocked.

---

## Notes

- Tests are implemented using Python `unittest`.
- FastAPI `TestClient` is used to simulate HTTP requests.
- SQLite database is used as a real persistence layer.
- Database is cleaned after each test to maintain isolation.
