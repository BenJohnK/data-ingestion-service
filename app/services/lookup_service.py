from sqlalchemy.orm import Session
from app.models.lookup import StoreBrand, StoreType, City, State, Country, Region

def get_or_create(db: Session, model, cache: dict, name: str):
    if not name:
        return None

    # Check cache first
    if name in cache:
        return cache[name]

    # Check DB
    instance = db.query(model).filter(model.name == name).first()

    if instance:
        cache[name] = instance.id
        return instance.id

    # Create new
    instance = model(name=name)
    db.add(instance)
    db.flush()  # get ID without full commit

    cache[name] = instance.id
    return instance.id

def resolve_store_lookups(db: Session, row: dict, lookup_cache: dict):
    return {
        "store_brand_id": get_or_create(db, StoreBrand, lookup_cache["store_brands"], row.get("store_brand")),
        "store_type_id": get_or_create(db, StoreType, lookup_cache["store_types"], row.get("store_type")),
        "city_id": get_or_create(db, City, lookup_cache["cities"], row.get("city")),
        "state_id": get_or_create(db, State, lookup_cache["states"], row.get("state")),
        "country_id": get_or_create(db, Country, lookup_cache["countries"], row.get("country")),
        "region_id": get_or_create(db, Region, lookup_cache["regions"], row.get("region")),
    }