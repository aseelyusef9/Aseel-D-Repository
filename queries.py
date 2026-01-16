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


# ----------------------
# Invoice: update, delete
# ----------------------
def update_invoice(db: Session, invoice_id: str, data: dict):
    invoice = db.query(Invoice).filter_by(InvoiceId=invoice_id).first()
    if not invoice:
        return None

    # update scalar fields
    for field in (
        "VendorName",
        "InvoiceDate",
        "BillingAddressRecipient",
        "ShippingAddress",
        "SubTotal",
        "ShippingCost",
        "InvoiceTotal",
    ):
        if field in data:
            setattr(invoice, field, data.get(field))

    # replace items if provided
    if "Items" in data:
        # remove existing items
        for it in list(invoice.items):
            db.delete(it)
        invoice.items = []
        for it in data.get("Items", []):
            item = Item(
                Description=it.get("Description"),
                Name=it.get("Name"),
                Quantity=it.get("Quantity"),
                UnitPrice=it.get("UnitPrice"),
                Amount=it.get("Amount"),
            )
            invoice.items.append(item)

    # update or create confidence
    conf_data = data.get("dataConfidence") or data.get("Confidence") or {}
    if conf_data:
        if invoice.confidence:
            for f in (
                "VendorName",
                "InvoiceDate",
                "BillingAddressRecipient",
                "ShippingAddress",
                "SubTotal",
                "ShippingCost",
                "InvoiceTotal",
            ):
                if f in conf_data:
                    setattr(invoice.confidence, f, conf_data.get(f))
        else:
            confidence = Confidence(
                InvoiceId=invoice.InvoiceId,
                VendorName=conf_data.get("VendorName"),
                InvoiceDate=conf_data.get("InvoiceDate"),
                BillingAddressRecipient=conf_data.get("BillingAddressRecipient"),
                ShippingAddress=conf_data.get("ShippingAddress"),
                SubTotal=conf_data.get("SubTotal"),
                ShippingCost=conf_data.get("ShippingCost"),
                InvoiceTotal=conf_data.get("InvoiceTotal"),
            )
            invoice.confidence = confidence

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def delete_invoice(db: Session, invoice_id: str):
    invoice = db.query(Invoice).filter_by(InvoiceId=invoice_id).first()
    if not invoice:
        return False
    db.delete(invoice)
    db.commit()
    return True


# ----------------------
# Item CRUD
# ----------------------
def create_item(db: Session, invoice_id: str, item_data: dict):
    item = Item(
        InvoiceId=invoice_id,
        Description=item_data.get("Description"),
        Name=item_data.get("Name"),
        Quantity=item_data.get("Quantity"),
        UnitPrice=item_data.get("UnitPrice"),
        Amount=item_data.get("Amount"),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item_by_id(db: Session, item_id: int):
    item = db.query(Item).filter_by(id=item_id).first()
    if not item:
        return None
    return {
        "id": item.id,
        "InvoiceId": item.InvoiceId,
        "Description": item.Description,
        "Name": item.Name,
        "Quantity": item.Quantity,
        "UnitPrice": item.UnitPrice,
        "Amount": item.Amount,
    }


def update_item(db: Session, item_id: int, data: dict):
    item = db.query(Item).filter_by(id=item_id).first()
    if not item:
        return None
    for field in ("Description", "Name", "Quantity", "UnitPrice", "Amount"):
        if field in data:
            setattr(item, field, data.get(field))
    if "InvoiceId" in data:
        item.InvoiceId = data.get("InvoiceId")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: int):
    item = db.query(Item).filter_by(id=item_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


# ----------------------
# Confidence CRUD
# ----------------------
def create_confidence(db: Session, invoice_id: str, conf_data: dict):
    confidence = Confidence(
        InvoiceId=invoice_id,
        VendorName=conf_data.get("VendorName"),
        InvoiceDate=conf_data.get("InvoiceDate"),
        BillingAddressRecipient=conf_data.get("BillingAddressRecipient"),
        ShippingAddress=conf_data.get("ShippingAddress"),
        SubTotal=conf_data.get("SubTotal"),
        ShippingCost=conf_data.get("ShippingCost"),
        InvoiceTotal=conf_data.get("InvoiceTotal"),
    )
    db.add(confidence)
    db.commit()
    db.refresh(confidence)
    return confidence


def get_confidence_by_invoice(db: Session, invoice_id: str):
    conf = db.query(Confidence).filter_by(InvoiceId=invoice_id).first()
    if not conf:
        return None
    return {
        "InvoiceId": conf.InvoiceId,
        "VendorName": conf.VendorName,
        "InvoiceDate": conf.InvoiceDate,
        "BillingAddressRecipient": conf.BillingAddressRecipient,
        "ShippingAddress": conf.ShippingAddress,
        "SubTotal": conf.SubTotal,
        "ShippingCost": conf.ShippingCost,
        "InvoiceTotal": conf.InvoiceTotal,
    }


def update_confidence(db: Session, invoice_id: str, conf_data: dict):
    conf = db.query(Confidence).filter_by(InvoiceId=invoice_id).first()
    if not conf:
        return None
    for field in (
        "VendorName",
        "InvoiceDate",
        "BillingAddressRecipient",
        "ShippingAddress",
        "SubTotal",
        "ShippingCost",
        "InvoiceTotal",
    ):
        if field in conf_data:
            setattr(conf, field, conf_data.get(field))
    db.add(conf)
    db.commit()
    db.refresh(conf)
    return conf


def delete_confidence(db: Session, invoice_id: str):
    conf = db.query(Confidence).filter_by(InvoiceId=invoice_id).first()
    if not conf:
        return False
    db.delete(conf)
    db.commit()
    return True
