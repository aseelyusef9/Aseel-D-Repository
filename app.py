from fastapi import FastAPI, UploadFile, File,HTTPException
import oci
import time
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
                data[field_name] = field.field_value.text
                data_confidence[field_name] = field_confidence

            #  Items
            else:
                items_list = getattr(field.field_value, "items", None)
                if not items_list:
                    items_list = getattr(field.field_value, "_items", [])

                for raw_item in items_list:
                    fields = raw_item if isinstance(raw_item, list) else [raw_item]

                    item_dict = {
                        "Description": None,
                        "Name": None,
                        "Quantity": None,
                        "UnitPrice": None,
                        "Amount": None
                    }

                    for item_field in fields:
                        if not item_field.field_label:
                            continue  # تجاهل الحقول الفارغة

                        item_field_name = item_field.field_label.name
                        item_field_value = item_field.field_value.text

                        if item_field_name in item_dict:
                            item_dict[item_field_name] = item_field_value

                    list_of_items.append(item_dict)


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
        "dataConfidence": data_confidence
        "predictionTime": prediction_time
    }

    save_inv_extraction(result)
    print(result)
    return result



@app.get('/health')
def health():
    return {'status': 'ok'}

if __name__ == "__main__":
    import uvicorn

    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8080)
    

    