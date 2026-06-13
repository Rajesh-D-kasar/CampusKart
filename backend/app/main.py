from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "CampusKart backend is running"}

@app.get("/products")
def get_products():
    return [
        {"id": 1, "name": "Maggi", "price": 15},
        {"id": 2, "name": "Milk", "price": 60},
        {"id": 3, "name": "Bread", "price": 40},
    ]
