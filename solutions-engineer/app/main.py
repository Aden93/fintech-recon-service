from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from . import models, schemas, crud
from .database import engine, get_db

# Create tables (In prod, use Alembic migrations instead)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fintech Reconciliation Service")

@app.post("/events", status_code=202)
def ingest_event(event: schemas.EventPayload, db: Session = Depends(get_db)):
    return crud.ingest_event(db, event)

@app.get("/transactions", response_model=List[schemas.TransactionResponse])
def list_transactions(
    merchant_id: Optional[str] = None,
    status: Optional[models.TransactionStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    query = db.query(models.Transaction)
    if merchant_id:
        query = query.filter(models.Transaction.merchant_id == merchant_id)
    if status:
        query = query.filter(models.Transaction.current_status == status)
    
    return query.order_by(models.Transaction.created_at.desc()).offset(skip).limit(limit).all()

@app.get("/transactions/{transaction_id}", response_model=schemas.TransactionResponse)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx

@app.get("/reconciliation/summary")
def get_summary(db: Session = Depends(get_db)):
    return crud.get_reconciliation_summary(db)

@app.get("/reconciliation/discrepancies")
def get_discrepancies(db: Session = Depends(get_db)):
    return crud.get_discrepancies(db)