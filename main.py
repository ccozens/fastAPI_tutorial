from fastapi import FastAPI, Path, Query, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from enum import Enum
from typing import Union, List
from typing_extensions import Annotated
from pydantic import BaseModel
from datetime import datetime


# enum example
class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


# tags with Enums!
class Tag(Enum):
    items = "items"
    itemtitle = "itemtitle"
    itemlist = "itemlist"
    users = "users"
    models = "models"

tags_metadata = [ # note need 'openapi_tags=tags_metadata' in app = FastAPI(openapi_tags=tags_metadata)
    { # this will be the first tag group displayed, as this list determines the order in the docs
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "items",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]

fake_items_db = [
    {"item_id": 0, "item_name": "Fish"},
    {"item_id": 1, "item_name": "Bear"},
    {"item_id": 2, "item_name": "Bunny"},
]


# data model example
class Item(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None

    #  declare example data
    class Config:
        schema_extra = {
            "example": {
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2,
            }
        }

class ItemWithDate(BaseModel):
    title: str
    timestamp: datetime
    description: Union[str, None] = None


class User(BaseModel):
    username: str
    full_name: Union[str, None] = None


# app = FastAPI()
description = """
ChimichangApp API helps you do awesome stuff. 🚀

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""

app = FastAPI(
    title="ChimichangApp",
    description=description,
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_tags=tags_metadata, # custom tags
    # docs_url="/documentation", redoc_url=None # custom docs url, disbale redoc
)


@app.get("/items/")
async def read_items():
    return [{"name": "Katana"}]

@app.post(
    "/items/",
    status_code=201,
    tags=[Tag.items],
    summary="Create an item",
    description="Create an item with all the information, name, description, price, tax and a set of unique tags",
)
async def create_items(item: Item):
    item_dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict


@app.post("/items/", response_model=Item, summary="Create an item", tags=[Tag.items])
async def create_an_item(
    item: Item,
    response_description="The created item",
):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    return item


""" @app.put("/items/{item_id}")
async def create_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()} """


@app.post("/items_return_type/", tags=[Tag.items])
async def create_item(item: Item) -> Item:  # return type is Item
    return item


@app.get("/items_return_type/", tags=[Tag.items])
async def read_items() -> List[Item]:  # return type is List of Item
    return [
        Item(name="Portal Gun", price=42.0),
        Item(name="Plumbus", price=32.0),
    ]

@app.put("/items/{id}", tags=[Tag.items])
def update_item_json(id: str, item: Item):
    json_compatible_item_data = jsonable_encoder(item)
    fake_items_db[id] = json_compatible_item_data

@app.put("/items/{item_id}", tags=[Tag.items])
async def update_item(
    item_id: int,
    item: Item,
    user: User,
    importance: Annotated[int, Body(gt=0)],
    q: Union[str, None] = None,
):  # Body must be greater than 0
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    if q:
        results.update({"q": q})
    return results


"""
{
    "item": {
        "name": "Foo",
        "description": "The pretender",
        "price": 42.0,
        "tax": 3.2
    },
    "user": {
        "username": "dave",
        "full_name": "Dave Grohl"
    },
    "importance": 5
}
"""


@app.get("/")
async def root():
    return {"message": "hello World"}


@app.get("/items/", tags=[Tag.items])
async def read_item(
    q: Annotated[Union[str, None], Query(max_length=50, min_length=3)] = ...
):  # Ellipsis (...) explicitly marks the parameter as required
    # async def read_item(q: Annotated[Union[str, None], Query(max_length=50, min_length=3)] = Required) # Required is part of pydantic (needs import) and has same functionality as Ellipsis
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.get("/itemlist/", tags=[Tag.items])
async def read_item_list(
    q: Annotated[Union[List[str], None], Query()] = ["default1", "default2"]
):
    query_items = {"q": q}
    return query_items


# http://localhost:8000/itemlist/?q=foo&q=bar


@app.get("/itemtitle/", tags=["itemtitle"])
async def read_items(
    q: Annotated[
        Union[str, None],
        Query(
            title="Query string",
            description="Query string for the items to search in the database that have a good match",
            min_length=3,
            deprecated=True,
        ),
    ] = None
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.get("/items/{item_id}", tags=[Tag.items])
async def read_item(
    # item_id: str, q: Union[str, None] = None, short: bool = False
    item_id: Annotated[int, Path(title="The ID of the item to get")],
    q: Annotated[Union[str, None], Query(alias="item-query")] = None,
    short: bool = False,
):  # q is optional, with default value None
    if item_id not in fake_items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {
                "description": "short is boolean and accepts '?short=1', True, true, On, on, Yes, yes as True and short=0, False, false, Off, off, No, no as False"
            }
        )
    return item


@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: str, q: Union[str, None] = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {
                "description": "short is boolean and accepts '?short=1', True, true, On, on, Yes, yes as True and short=0, False, false, Off, off, No, no as False"
            }
        )
    return item


@app.get("/models/{model_name}", tags=[Tag.models])
async def get_model(model_name: ModelName):
    # compare enum member directly
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    # compare with enum member value
    if model_name.value == "lenet":  # or model_name == ModelName.lenet
        return {"model_name": model_name, "message": "LeCNN all the images"}
    # no if clause as this is the only other option
    return {"model_name": model_name, "message": "Have some residuals"}


# CORS
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

