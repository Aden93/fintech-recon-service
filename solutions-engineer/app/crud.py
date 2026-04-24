from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from . import models, schemas
import logging

def ingest_event(db: Session, event: schemas.EventPayload):
    # 1. Explicit Idempotency Check
    existing_event = db.query(models.Event).filter(models.Event.id == event.event_id).first()
    if existing_event:
        logging.warning(f"Duplicate event detected and ignored: {event.event_id}")
        return {"status": "ignored", "message": "Duplicate event"}

    # 2. Upsert Merchant
    merchant = db.query(models.Merchant).filter(models.Merchant.id == event.merchant_id).first()
    if not merchant:
        merchant = models.Merchant(id=event.merchant_id, name=event.merchant_name)
        db.add(merchant)
        db.flush() # Push to DB session so the Transaction can reference it

    # 3. State Machine & Out-of-Order Event Handling (Upsert Transaction)
    tx = db.query(models.Transaction).filter(models.Transaction.id == event.transaction_id).first()

    if not tx:
        # First time seeing this transaction
        tx = models.Transaction(
            id=event.transaction_id,
            merchant_id=event.merchant_id,
            amount=event.amount,
            currency=event.currency,
            current_status=event.event_type,
            created_at=event.timestamp,
            updated_at=event.timestamp
        )
        db.add(tx)
    else:
        # Out-of-order handler: Update if the event is newer
        if event.timestamp > tx.updated_at:
            tx.current_status = event.event_type
            tx.updated_at = event.timestamp

    db.flush() # Push to DB session so the Event can reference this transaction

    # 4. Insert Event safely
    db_event = models.Event(
        id=event.event_id,
        transaction_id=event.transaction_id,
        event_type=event.event_type,
        timestamp=event.timestamp
    )
    db.add(db_event)

    # 5. Commit everything together (ACID compliance)
    db.commit()
    return {"status": "success", "message": "Event processed"}

def get_reconciliation_summary(db: Session):
    results = db.query(
        models.Transaction.merchant_id,
        models.Transaction.current_status,
        func.count(models.Transaction.id).label("total_transactions"),
        func.sum(models.Transaction.amount).label("total_volume")
    ).group_by(
        models.Transaction.merchant_id, 
        models.Transaction.current_status
    ).all()
    
    return [
        {
            "merchant_id": r.merchant_id,
            "status": r.current_status.value,
            "count": r.total_transactions,
            "volume": float(r.total_volume)
        } for r in results
    ]

def get_discrepancies(db: Session):
    """
    Identifies breaks in the financial state machine.
    """
    # 1. Settled but previously failed (Logical impossibility in standard flows)
    # We find transactions currently 'settled', but joined to an event that was 'payment_failed'
    failed_but_settled = db.query(models.Transaction.id).join(models.Event).filter(
        models.Transaction.current_status == models.TransactionStatus.settled,
        models.Event.event_type == models.TransactionStatus.payment_failed
    ).distinct().all()

    # 2. Processed but missing initiation (Data gap / API abuse)
    # Transactions currently processed or settled, but missing a 'payment_initiated' event
    initiated_subquery = db.query(models.Event.transaction_id).filter(
        models.Event.event_type == models.TransactionStatus.payment_initiated
    ).subquery()
    
    missing_initiation = db.query(models.Transaction.id).filter(
        models.Transaction.current_status.in_([models.TransactionStatus.payment_processed, models.TransactionStatus.settled]),
        ~models.Transaction.id.in_(initiated_subquery)
    ).all()

    return {
        "settled_but_had_failure": [tx.id for tx in failed_but_settled],
        "missing_initiation_event": [tx.id for tx in missing_initiation]
    }