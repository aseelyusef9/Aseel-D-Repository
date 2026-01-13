# queries.py
from sqlalchemy.orm import Session
from models import Invoice, Item, Confidence

# ----------------------
# Invoice CRUD
# ----------------------
def save_invoice_extraction(db: Session, data: dict):
    invoice = Invoice(
        InvoiceId=data["data"].get("InvoiceId"),
        VendorName=data["data"].get("VendorName"),
        InvoiceDate=data["data"].get("InvoiceDate"),
        BillingAddressRecipient=data["data"].get("BillingAddressRecipient"),
        ShippingAddress=data["data"].get("ShippingAddress"),
        SubTotal=data["data"].get("SubTotal"),
        ShippingCost=data["data"].get("ShippingCost"),
        InvoiceTotal=data["data"].get("InvoiceTotal")
    )

    # Items
    for it in data["data"].get("Items", []):
        item = Item(
            Description=it.get("Description"),
            Name=it.get("Name"),
            Quantity=it.get("Quantity"),
            UnitPrice=it.get("UnitPrice"),
            Amount=it.get("Amount")
        )
        invoice.items.append(item)

    # Confidence
    conf_data = data.get("dataConfidence", {})
    confidence = Confidence(
        VendorName=conf_data.get("VendorName"),
        InvoiceDate=conf_data.get("InvoiceDate"),
        BillingAddressRecipient=conf_data.get("BillingAddressRecipient"),
        ShippingAddress=conf_data.get("ShippingAddress"),
        SubTotal=conf_data.get("SubTotal"),
        ShippingCost=conf_data.get("ShippingCost"),
        InvoiceTotal=conf_data.get("InvoiceTotal")
    )
    invoice.confidence = confidence

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def get_invoice_by_id(db: Session, invoice_id: str):
    invoice = db.query(Invoice).filter_by(InvoiceId=invoice_id).first()
    if not invoice:
        return None
    return {
        "InvoiceId": invoice.InvoiceId,
        "VendorName": invoice.VendorName,
        "InvoiceDate": invoice.InvoiceDate,
        "BillingAddressRecipient": invoice.BillingAddressRecipient,
        "ShippingAddress": invoice.ShippingAddress,
        "SubTotal": invoice.SubTotal,
        "ShippingCost": invoice.ShippingCost,
        "InvoiceTotal": invoice.InvoiceTotal,
        "Items": [
            {
                "Description": i.Description,
                "Name": i.Name,
                "Quantity": i.Quantity,
                "UnitPrice": i.UnitPrice,
                "Amount": i.Amount
            } for i in invoice.items
        ]
    }


def get_invoices_by_vendor(db: Session, vendor_name: str):
    invoices = db.query(Invoice).filter_by(VendorName=vendor_name).order_by(Invoice.InvoiceDate.asc()).all()
    return [get_invoice_by_id(db, inv.InvoiceId) for inv in invoices]
