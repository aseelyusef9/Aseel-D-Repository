# Invoice Parser Service

This is a FastAPI-based web service that extracts key information from invoice PDFs using Oracle Cloud Infrastructure (OCI) Document AI. The application analyzes invoices, extracts key-value pairs, and stores the results in a SQLite database for later retrieval.

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Configure OCI credentials in `~/.oci/config`

4. Run the application:
```bash
python app.py
```

The service will be available at http://localhost:8080

## API Endpoints

* `POST /extract` - Upload an invoice PDF for data extraction

## Testing the API

You can use tools like curl, Postman, or a web browser to test the endpoint. For example:

Upload an invoice:
```bash
curl -X POST -F "file=@invoices_sample/invoice_Aaron_Bergman_36259.pdf" http://localhost:8080/extract 