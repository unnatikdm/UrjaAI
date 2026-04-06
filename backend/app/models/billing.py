from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    period_type = Column(String, index=True) # "Weekly", "Monthly"
    period_id = Column(String) # "Wip-12", "April-2026"
    subtotal = Column(Float)
    gst = Column(Float)
    cess = Column(Float)
    grand_total = Column(Float)
    energy_cost = Column(Float)
    fixed_charge = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    items = relationship("InvoiceItem", back_populates="invoice")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    building_name = Column(String)
    daily_avg_kwh = Column(Float)
    total_kwh = Column(Float)
    cost = Column(Float)
    share_percentage = Column(Float)

    invoice = relationship("Invoice", back_populates="items")
