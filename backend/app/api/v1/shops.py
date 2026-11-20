from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models import Product, Shop
from app.schemas.shop import ProductRead, ShopDetail, ShopRead
from app.services.shops import distance_in_kilometers

router = APIRouter(prefix="/shops", tags=["Dükkânlar"])


@router.get(
    "",
    response_model=list[ShopRead],
    summary="Dükkânları ara ve yakına göre sırala",
)
def list_shops(
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    radius: float | None = Query(default=None, ge=0, le=500, description="Kilometre"),
    q: str | None = Query(default=None, max_length=100, description="İsim veya adres"),
    session: Session = Depends(get_db),
) -> list[ShopRead]:
    if (lat is None) != (lng is None):
        raise HTTPException(
            status_code=422,
            detail="Yakınlık sıralaması için lat ve lng birlikte gönderilmelidir.",
        )
    if radius is not None and lat is None:
        raise HTTPException(
            status_code=422,
            detail="radius kullanmak için lat ve lng de gönderilmelidir.",
        )

    statement = select(Shop)
    search_term = q.strip() if q else ""
    if search_term:
        pattern = f"%{search_term}%"
        statement = statement.where(
            Shop.name.ilike(pattern) | Shop.address.ilike(pattern)
        )

    shops = list(session.scalars(statement))
    results: list[tuple[float | None, ShopRead]] = []
    for shop in shops:
        distance = (
            distance_in_kilometers(lat, lng, shop.latitude, shop.longitude)
            if lat is not None and lng is not None
            else None
        )
        if radius is not None and distance is not None and distance > radius:
            continue
        results.append(
            (
                distance,
                ShopRead(
                    id=shop.id,
                    name=shop.name,
                    address=shop.address,
                    latitude=shop.latitude,
                    longitude=shop.longitude,
                    working_hours=shop.working_hours,
                    rating=shop.rating,
                    distance_km=round(distance, 2) if distance is not None else None,
                ),
            )
        )

    if lat is not None:
        results.sort(key=lambda item: (item[0], item[1].name))
    else:
        results.sort(key=lambda item: item[1].name.casefold())
    return [shop for _, shop in results]


@router.get(
    "/{shop_id}",
    response_model=ShopDetail,
    summary="Dükkân detayını ve menüsünü gör",
)
def read_shop(
    shop_id: int,
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    session: Session = Depends(get_db),
) -> ShopDetail:
    if (lat is None) != (lng is None):
        raise HTTPException(
            status_code=422,
            detail="Mesafe için lat ve lng birlikte gönderilmelidir.",
        )
    shop = session.get(Shop, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Dükkân bulunamadı.")

    distance = (
        distance_in_kilometers(lat, lng, shop.latitude, shop.longitude)
        if lat is not None and lng is not None
        else None
    )
    products = list(
        session.scalars(
            select(Product)
            .where(Product.shop_id == shop.id)
            .order_by(Product.name)
        )
    )
    return ShopDetail(
        id=shop.id,
        name=shop.name,
        address=shop.address,
        latitude=shop.latitude,
        longitude=shop.longitude,
        working_hours=shop.working_hours,
        rating=shop.rating,
        distance_km=round(distance, 2) if distance is not None else None,
        menu=products,
    )


@router.get(
    "/{shop_id}/menu",
    response_model=list[ProductRead],
    summary="Dükkân menüsünü gör",
)
def read_shop_menu(
    shop_id: int,
    session: Session = Depends(get_db),
) -> list[Product]:
    if session.get(Shop, shop_id) is None:
        raise HTTPException(status_code=404, detail="Dükkân bulunamadı.")
    return list(
        session.scalars(
            select(Product)
            .where(Product.shop_id == shop_id)
            .order_by(Product.name)
        )
    )
