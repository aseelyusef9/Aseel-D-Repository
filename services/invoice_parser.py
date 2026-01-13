# services/invoice_parser.py
import oci
import base64
import time
from fastapi import HTTPException

doc_client = None

def _init_doc_client():
    global doc_client
    if doc_client is not None:
        return
    try:
        config = oci.config.from_file()
        doc_client = oci.ai_document.AIServiceDocumentClient(config)
    except Exception:
        doc_client = None

def get_doc_client():
    if doc_client is None:
        _init_doc_client()
    return doc_client

def parse_invoice_from_pdf(pdf_bytes: bytes):
    client = get_doc_client()
    if client is None:
        raise HTTPException(status_code=500, detail="Document AI client not configured")

    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    document = oci.ai_document.models.InlineDocumentDetails(data=encoded_pdf)
    request = oci.ai_document.models.AnalyzeDocumentDetails(
        document=document,
        features=[
            oci.ai_document.models.DocumentFeature(feature_type="KEY_VALUE_EXTRACTION"),
            oci.ai_document.models.DocumentClassificationFeature(max_results=5)
        ]
    )

    start_time = time.time()
    response = client.analyze_document(request)

    data = {}
    data_confidence = {}
    items = []

    for page in response.data.pages:
        if not page.document_fields:
            continue
        for field in page.document_fields:
            field_name = field.field_label.name if field.field_label else None
            field_conf = field.field_label.confidence if field.field_label else None
            if field_name and field_name.lower() != "items":
                data[field_name] = field.field_value.value
                data_confidence[field_name] = field_conf
            else:
                item = {}
                for it in field.field_value.items:
                    for t in it.field_value.items:
                        item[t.field_label.name] = t.field_value.value
                items.append(item)

    data["Items"] = items

    # Validate document
    if response.data.detected_document_types:
        if not any(doc.confidence >= 0.9 for doc in response.data.detected_document_types):
            raise HTTPException(status_code=400, detail="Invalid document. Please upload a valid invoice.")

    return {
        "confidence": 1,
        "data": data,
        "dataConfidence": data_confidence,
        "predictionTime": time.time() - start_time
    }
