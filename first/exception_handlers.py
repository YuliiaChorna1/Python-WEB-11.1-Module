from fastapi import HTTPException, Request, status, exception_handlers
from pydantic import ValidationError
from starlette.responses import JSONResponse
from main import app


## виняток зі статусом 404 Not Found, якщо ресурс не знайдено:
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    item = {"item_id": item_id, "name": "Foo"}
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


## невалідні дані, помилки аутентифікації, тощо. 
## виняток зі статусом 400 Bad Request, якщо валідація даних не пройдена:
@app.post("/items")
async def create_item(item: Item):
    if item.name is None:
        raise HTTPException(status_code=400, detail="Name is required")
    return item


## За допомогою декоратора @app.exception_handler() ви можете вказати функцію, 
## яка буде викликатися при виникненні винятків у всіх фукціях роутерів:
@app.exception_handler(HTTPException)
def handle_http_exception(request: Request, exc: HTTPException):
    return {"message": str(exc.detail)}


## У функції-обробника винятків ви можете використовувати аргументи request та exc 
## для отримання доступу до об'єкта запиту та об'єкта винятку відповідно. 
## Наприклад, повертати різноманітні повідомлення про помилки, залежно від типу винятку:
@app.exception_handler(ValidationError)
def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Invalid input data"}
    )

@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.exception_handler(Exception)
def unexpected_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred"},
    )


## Bласні класи винятків для обробки специфічних типів помилок:
class ItemNotFoundError(Exception):
    pass

@app.exception_handler(ItemNotFoundError)
def item_not_found_error_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Item not found"},
    )

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    item = get_item_by_id(item_id)
    if item is None:
        raise ItemNotFoundError
    return item


## USING Exception_handlers
## виняток HTTPException, якщо ціна товару від'ємна. 
## Після цього FastAPI буде викликати відповідну функцію-обробник винятків 
## через @app.exception_handler(HTTPException), для обробки цієї помилки
@app.post("/items/")
async def create_item(item: Item):
    if item.price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price should be a positive number",
        )
    return item


