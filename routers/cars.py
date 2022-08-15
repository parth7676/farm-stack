from typing import Optional, List

from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from models import CarBase, CarDB, CarUpdate

router = APIRouter()


@router.get("/", response_description="List all cars")
async def list_all_cars(
        request: Request,
        min_price: int = 0,
        max_price: int = 100000,
        brand: Optional[str] = None,
        page: int = 1,
) -> List[CarDB]:
    result_per_page = 25
    skip = (page - 1) * result_per_page
    query = {"price": {"$lt": max_price, "$gt": min_price}}
    if brand:
        query["brand"] = brand
    full_query = request.app.mongodb['cars1'].find(query).sort("_id", -1).skip(skip).limit(result_per_page)
    results = [CarDB(**raw_car) async for raw_car in full_query]
    return results


@router.post("/", response_description="Add new car")
async def create_car(request: Request, car: CarBase = Body(...)):
    car = jsonable_encoder(car)
    new_car = await request.app.mongodb["cars1"].insert_one(car)
    created_car = await request.app.mongodb["cars1"].find_one(
        {"_id": new_car.inserted_id}
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_car)


@router.get("/{id}", response_description="Get a single car")
async def show_car(id: str, request: Request):
    if (car := await request.app.mongodb["cars1"].find_one({"_id": id})) is not None:
        return CarDB(**car)
    raise HTTPException(status_code=404, detail=f"Car with {id} not found")


@router.patch("/{id}", response_description="Update car")
async def update_task(id: str, request: Request, car: CarUpdate = Body(...)):
    await request.app.mongodb['cars1'].update_one(
        {"_id": id}, {"$set": car.dict(exclude_unset=True)}
    )
    if (car := await request.app.mongodb['cars1'].find_one({"_id": id})) is not None:
        return CarDB(**car)
    raise HTTPException(status_code=404, detail=f"Car with {id} not found")


@router.delete("/{id}", response_description="Delete car")
async def delete_task(id: str, request: Request):
    delete_result = await request.app.mongodb['cars1'].delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    raise HTTPException(status_code=404, detail=f"Car with {id} not found")
