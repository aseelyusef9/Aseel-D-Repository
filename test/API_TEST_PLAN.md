1. What to Test:

The following API endpoints and functionalities will be tested:

API Endpoints

POST /extract

Valid PDF extraction

Invalid or missing file handling

Low-confidence documents

External service (OCI) failures

GET /invoice/{invoice_id}

Retrieve invoice by ID

Handle non-existing or invalid IDs

GET /invoices/vendor/{vendor_name}

Retrieve invoices by vendor

Handle vendors with no invoices

Validate vendor input

Functionalities

Correct HTTP status codes

Valid response structure

Database read/write integration

Error handling and validation

2. Test Design Strategy:

Integration Testing is used.

Tests written with unittest

API requests simulated using FastAPI TestClient

Prepared test data

Real test database used

External services (OCI) mocked using unittest.mock.patch

Each test is isolated, with database setup and cleanup before and after execution.

3. Test Environment:

GitHub Actions CI

Ubuntu latest runner

Tests executed automatically on Pull Requests to the main branch

4. Success Criteria:

100% API endpoint coverage

All tests pass successfully

Correct API responses and status codes

Database integration verified

External services fully mocked

Near 100% code coverage of API logic

5. Reporting:

Test results available in GitHub Actions logs

Pull Requests show pass/fail status

Failed tests block merging to main

Codecov Reporting



Summary:

This test plan validates the InvParser API using integration testing with FastAPI TestClient, a real database, and mocked external services, ensuring reliability and maintainability.