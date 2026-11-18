@router.post("/{rental_id}/return", response_model=schemas.RentalResponse)
def return_equipment(rental_id: int, db: Session = Depends(get_db)):
    """
    Возврат оборудования.
    1. Найти аренду по rental_id.
    2. Перевести статус аренды в 'RETURNED'.
    3. Найти связанный инструмент и вернуть ему статус 'AVAILABLE'.
    """
    rental = db.query(models.Rental).filter(models.Rental.id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Аренда не найдена")

    if rental.status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Можно вернуть только активную аренду"
        )

    rental.status = "RETURNED"

    equipment = (
        db.query(models.Equipment)
        .filter(models.Equipment.id == rental.equipment_id)
        .first()
    )
    if equipment:
        equipment.status = "AVAILABLE"

    db.commit()
    db.refresh(rental)
    return rental