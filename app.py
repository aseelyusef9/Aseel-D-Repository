from fastapi import FastAPI, UploadFile, File,HTTPException
import oci
import time
import base64
from db_util import init_db, save_inv_extraction,get_db

app = FastAPI()

# Load OCI config from ~/.oci/config
config = oci.config.from_file()

doc_client = oci.ai_document.AIServiceDocumentClient(config)


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    pdf_bytes = await file.read()

    # Base64 encode PDF
    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    document = oci.ai_document.models.InlineDocumentDetails(
        data=encoded_pdf
    )
    
    request = oci.ai_document.models.AnalyzeDocumentDetails(
        document=document,
        features=[
            oci.ai_document.models.DocumentFeature(
                feature_type="KEY_VALUE_EXTRACTION"
            ),
            oci.ai_document.models.DocumentClassificationFeature(
                max_results=5
            )
        ]
    )
    time_before=time.time()
    response = doc_client.analyze_document(request)
<<<<<<< HEAD

    #result = {
        #"confidence": "TBD...",
       # "data": "TBD...",
        #"dataConfidence": "TBD..."
    #}

    # TODO: call to save_inv_extraction(result)    ( no need to change this function)
    
    

=======
    time_after=time.time()
   
>>>>>>> 6729185fe1cc223bb82cfb4fe1d57be226ee0e40
    data = {}
    data_confidence = {}
    list_of_items = []

    for page in response.data.pages:
        if not page.document_fields:
            continue

        for field in page.document_fields:
            field_name = field.field_label.name if field.field_label else None
            field_confidence = field.field_label.confidence if field.field_label else None

            # normal fields
            if field_name and field_name.lower() != "items":
                data[field_name] = field.field_value.value
                data_confidence[field_name] = field_confidence
 
 

            #  Items
            else:
                    dict = {}
                    for items in field.field_value.items:
                        for texts in items.field_value.items:
                            field_value = texts.field_label.name
                            field_text = texts.field_value.value
                            dict[field_value] = field_text    
                    list_of_items.append(dict)

    print(list_of_items)
    # إضافة items للـ data
    data["Items"] = list_of_items



    if response.data.detected_document_types:
        is_valid = False

        for doc in response.data.detected_document_types:
            if doc.confidence >= 0.9:
                is_valid = True
                break

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid document. Please upload a valid PDF invoice with high confidence."
            )


    prediction_time=time_after-time_before
    result = {
        "confidence": 1,
        "data": data,
        "dataConfidence": data_confidence,
        "predictionTime": prediction_time
    }
    
    save_inv_extraction(result)
    print(result)
    return result

#http://127.0.0.1:8080/invoice/36259
@app.get('/invoice/{invoice_id}')
def get_invoice_by_id(invoice_id: str):
    with get_db() as conn: #ניהול חיבור לבסיס הנתונים
        cursor = conn.cursor() #מצביע (cursor) שרץ על מסד הנתונים ומבצע פקודות SQL

        cursor.execute("""
            SELECT InvoiceId, VendorName, InvoiceDate, BillingAddressRecipient,
                   ShippingAddress, SubTotal, ShippingCost, InvoiceTotal
            FROM invoices
            WHERE InvoiceId = ? 
        """, (invoice_id,)) #,כי SQLite מצפה ל־ tuple/ של פרמטרים ? = אבטחה ויציבות
       
        row = cursor.fetchone() #Tuple
        if not row:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice = {
            "InvoiceId": row[0],
            "VendorName": row[1],
            "InvoiceDate": row[2],
            "BillingAddressRecipient": row[3],
            "ShippingAddress": row[4],
            "SubTotal": row[5],
            "ShippingCost": row[6],
            "InvoiceTotal": row[7],
        }

        cursor.execute("""
            SELECT Description, Name, Quantity, UnitPrice, Amount
            FROM items
            WHERE InvoiceId = ?
            ORDER BY id ASC
        """, (invoice_id,))
        items_rows = cursor.fetchall()

        invoice["Items"] = [
            {
                "Description": r[0],
                "Name": r[1],
                "Quantity": r[2],
                "UnitPrice": r[3],
                "Amount": r[4],
            }
            for r in items_rows
        ]

        return invoice
    
#http://127.0.0.1:8080/invoices/vendor/SuperStore
@app.get("/invoices/vendor/{vendor_name}")
async def invoices_by_vendor(vendor_name: str):
    invoices = get_invoices_by_vendor(vendor_name)

    if not invoices:
        return {
            "VendorName": "Unknown Vendor",
            "TotalInvoices": 0,
            "invoices": []
        }

    return {
        "VendorName": vendor_name,
        "TotalInvoices": len(invoices),
        "invoices": invoices
    }


def get_invoices_by_vendor(vendor_name: str):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT InvoiceId
            FROM invoices
            WHERE VendorName = ?
            ORDER BY InvoiceDate ASC
        """, (vendor_name,))
        invoice_ids = [r[0] for r in cursor.fetchall()]


    invoices = []
    for inv_id in invoice_ids:
        inv = get_invoice_by_id(inv_id)
        if inv:
            invoices.append(inv)

    return invoices

@app.get('/health')
def health():
    return {'status': 'ok'}

if __name__ == "__main__":
    import uvicorn

    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8080)
    

    