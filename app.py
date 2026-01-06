from fastapi import FastAPI, UploadFile, File
import oci
import base64
from db_util import init_db, save_inv_extraction

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

    response = doc_client.analyze_document(request)

    #result = {
        #"confidence": "TBD...",
       # "data": "TBD...",
        #"dataConfidence": "TBD..."
    #}

    # TODO: call to save_inv_extraction(result)    ( no need to change this function)
    
    

    data = {}
    data_confidence = {}
    items = []
####
    for page in response.data.pages:
        if page.document_fields:
            for field in page.document_fields:
                field_name = field.field_label.name if field.field_label else None
                field_confidence = field.field_label.confidence if field.field_label else None
                field_value = field.field_value.text
            
                data[field_name] = field_value
                data_confidence[field_name] = field_confidence
                if field_name == "Items" and field.field_value.value_type == "ARRAY":
                    for item in field.field_value.array_value:
                        item_data = {}

                        for sub_field in item.object_value:
                            sub_name = sub_field.field_label.name
                            sub_value = sub_field.field_value.text

                            item_data[sub_name] = sub_value

                        items.append(item_data)

                if items:
                   data["Items"] = items

                #document_confidence = response.data.pages.document_fields.fieldValue.confidence
                #document_confidence = response.data.document_classification.confidence
                document_confidence = 1
                if response.data.document_classification_results:
                    document_confidence = response.data.document_classification_results[0].confidence
                for page in pages:


    normalized_output = {
    "confidence": document_confidence,
    "data": {
        "VendorName": data.get("VendorName"),
        "VendorNameLogo": data.get("VendorNameLogo"),
        "InvoiceId": data.get("InvoiceId"),
        "InvoiceDate": data.get("InvoiceDate"),
        "ShippingAddress": data.get("ShippingAddress"),
        "BillingAddressRecipient": data.get("BillingAddressRecipient"),
        "AmountDue": data.get("AmountDue"),
        "SubTotal": data.get("SubTotal"),
        "ShippingCost": data.get("ShippingCost"),
        "InvoiceTotal": data.get("InvoiceTotal"),
        "Items": data.get("Items", [])
    },
    "dataConfidence": {
        "VendorName": data_confidence.get("VendorName"),
        "VendorNameLogo": data_confidence.get("VendorNameLogo"),
        "InvoiceId": data_confidence.get("InvoiceId"),
        "InvoiceDate": data_confidence.get("InvoiceDate"),
        "ShippingAddress": data_confidence.get("ShippingAddress"),
        "BillingAddressRecipient": data_confidence.get("BillingAddressRecipient"),
        "AmountDue": data_confidence.get("AmountDue"),
        "SubTotal": data_confidence.get("SubTotal"),
        "ShippingCost": data_confidence.get("ShippingCost"),
        "InvoiceTotal": data_confidence.get("InvoiceTotal")
    }
}

   

           #for item in items_list:
              #for item_fields in item.field_value.items:
                   
                   
        #result={
           # "confidence": field_confidence,
          #  "data" : data,
           # "data confidence": data_confidence

    return normalized_output

@app.get('/health')
def health():
    return {'status': 'ok'}

if __name__ == "__main__":
    import uvicorn

    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8080)
