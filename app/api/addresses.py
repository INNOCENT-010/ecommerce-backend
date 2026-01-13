# app/api/addresses.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import Address, User
from app.schemas.schemas import AddressCreate, AddressResponse
from app.core.security import get_current_user

router = APIRouter()

@router.get("/", response_model=List[AddressResponse])
async def get_user_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    addresses = db.query(Address).filter(Address.user_id == current_user.id).all()
    return addresses

@router.post("/", response_model=AddressResponse)
async def create_address(
    address_data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if address_data.is_default:
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})
    
    address = Address(
        user_id=current_user.id,
        street=address_data.street,
        city=address_data.city,
        state=address_data.state,
        country=address_data.country,
        postal_code=address_data.postal_code,
        is_default=address_data.is_default
    )
    
    db.add(address)
    db.commit()
    db.refresh(address)
    return address

@router.put("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: int,
    address_data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(Address).filter(
        (Address.id == address_id) &
        (Address.user_id == current_user.id)
    ).first()
    
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    if address_data.is_default and not address.is_default:
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})
    
    address.street = address_data.street
    address.city = address_data.city
    address.state = address_data.state
    address.country = address_data.country
    address.postal_code = address_data.postal_code
    address.is_default = address_data.is_default
    
    db.commit()
    db.refresh(address)
    return address

@router.delete("/{address_id}")
async def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = db.query(Address).filter(
        (Address.id == address_id) &
        (Address.user_id == current_user.id)
    ).first()
    
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    db.delete(address)
    db.commit()
    return {"message": "Address deleted"}