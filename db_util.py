import sqlite3
from contextlib import contextmanager


DB_PATH = "invoices.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                InvoiceId TEXT PRIMARY KEY,
                VendorName TEXT,
                InvoiceDate TEXT,
                BillingAddressRecipient TEXT,
                ShippingAddress TEXT,
                SubTotal REAL,
                ShippingCost REAL,
                InvoiceTotal REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidences (
                InvoiceId TEXT PRIMARY KEY,
                VendorName REAL,
                InvoiceDate REAL,
                BillingAddressRecipient REAL,
                ShippingAddress REAL,
                SubTotal REAL,
                ShippingCost REAL,
                InvoiceTotal REAL,
                FOREIGN KEY (InvoiceId) REFERENCES invoices(InvoiceId)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                InvoiceId TEXT,
                Description TEXT,
                Name TEXT,
                Quantity REAL,
                UnitPrice REAL,
                Amount REAL,
                FOREIGN KEY (InvoiceId) REFERENCES invoices(InvoiceId)
            )
        """)


def save_inv_extraction(result):
    data = result.get("data", {})
    data_confidence = result.get("dataConfidence", {})
    
    invoice_id = data.get("InvoiceId")
    if invoice_id:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Insert invoice
            cursor.execute("""
                INSERT OR REPLACE INTO invoices 
                (InvoiceId, VendorName, InvoiceDate, BillingAddressRecipient, 
                 ShippingAddress, SubTotal, ShippingCost, InvoiceTotal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                data.get("VendorName"),
                data.get("InvoiceDate"),
                data.get("BillingAddressRecipient"),
                data.get("ShippingAddress"),
                data.get("SubTotal"),
                data.get("ShippingCost"),
                data.get("InvoiceTotal")
            ))
            
            # Insert confidences
            cursor.execute("""
                INSERT OR REPLACE INTO confidences 
                (InvoiceId, VendorName, InvoiceDate, BillingAddressRecipient,
                 ShippingAddress, SubTotal, ShippingCost, InvoiceTotal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                data_confidence.get("VendorName"),
                data_confidence.get("InvoiceDate"),
                data_confidence.get("BillingAddressRecipient"),
                data_confidence.get("ShippingAddress"),
                data_confidence.get("SubTotal"),
                data_confidence.get("ShippingCost"),
                data_confidence.get("InvoiceTotal")
            ))
            
            # Insert line items
            line_items = data.get("Items", [])
            for item in line_items:
                cursor.execute("""
                    INSERT INTO items 
                    (InvoiceId, Description, Name, Quantity, UnitPrice, Amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    item.get("Description"),
                    item.get("Name"),
                    item.get("Quantity"),
                    item.get("UnitPrice"),
                    item.get("Amount")
                ))