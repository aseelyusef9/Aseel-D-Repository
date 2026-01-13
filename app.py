# app.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from db import get_db, Base, engine
from queries import save_invoice_extraction, get_invoice_by_id, get_invoices_by_vendor
from services.invoice_parser import parse_invoice_from_pdf

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# ----------------------
# API Endpoints
# ----------------------
@app.post("/extract")
async def extract_invoice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    pdf_bytes = await file.read()
    extracted_data = parse_invoice_from_pdf(pdf_bytes)
    save_invoice_extraction(db, extracted_data)
    return extracted_data

@app.get("/invoice/{invoice_id}")
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@app.get("/invoices/vendor/{vendor_name}")
def invoices_by_vendor_endpoint(vendor_name: str, db: Session = Depends(get_db)):
    invoices = get_invoices_by_vendor(db, vendor_name)
    return {
        "VendorName": vendor_name,
        "TotalInvoices": len(invoices),
        "invoices": invoices
    }

@app.get("/health")
def health():
    return {"status": "ok"}
