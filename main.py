from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()

class Pateint(BaseModel):

    id: Annotated[str, Field(..., description="The unique identifier for the pateint", example="P001")]
    name: Annotated[str, Field(..., description="The name of the pateint", example="Harsh")]
    city: Annotated[str, Field(..., description="The city where the pateint resides", example="Delhi")]
    age: Annotated[int, Field(..., description="The age of the pateint", example=30)]
    gender: Annotated[Literal['male', 'female', 'others'], Field(..., description='Gender of the pateint')]
    height: Annotated[float, Field(..., gt=0, description="The height of the pateint in cm", example=175.5)]
    weight: Annotated[float, Field(..., gt=0, description="Weight of the pateint in kg")]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight / ((self.height / 100) ** 2), 2)
        return bmi
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 24.9:
            return "Normal weight"
        elif 25 <= self.bmi < 29.9:
            return "Overweight"
        else:
            return "Obesity"
        
class PateintUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female', 'others']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]

def load_data():
    with open('pateints.json', 'r') as file:
        data = json.load(file)

    return data

def save_data(data):
    with open('pateints.json', 'w') as file:
        json.dump(data, file)

@app.get("/")
def hello():
    return {"message": "Hello, World!"}

@app.get("/about")
def about():
    return {"message": "This is a simple FastAPI application."}


@app.get("/view")
def view():
    data = load_data()
    return data

@app.get('/pateints/{pateint_id}')
def view_pateint(pateint_id: str = Path(..., description="The ID of the pateint to view", example="P001")):
    data = load_data()

    if pateint_id in data:
        return data[pateint_id]
    raise HTTPException(status_code=404, detail="Pateint not found")
                 

@app.get('/sort')
def sort_patients(
    sort_by: str = Query(..., description='Sort based on height, weight, or bmi'),
    order: str = Query('asc', description='Order of sorting: asc or desc')
):
    valid_fields = ['height', 'weight', 'bmi']
    
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid field — select from {valid_fields}")

    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Invalid order — use 'asc' or 'desc'")

    data = load_data()  # Assuming this returns a dictionary with required structure

    sort_order = False if order == 'desc' else True  # reverse = False if asc, True if desc

    try:
        sorted_data = sorted(data.values(), key=lambda x: x[sort_by], reverse=not sort_order)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sorting failed: {str(e)}")

    return sorted_data


@app.post('/create')
def create_pateint(pateint: Pateint):
   # Load existing data 
    data = load_data()
    # Check if pateint with the same ID already exists
    if pateint.id in data:
        raise HTTPException(status_code=400, detail="Pateint with this ID already exists")
    # Save the new pateint data
    data[pateint.id] = pateint.model_dump(exclude=['id'])

    # save into json file
    save_data(data)
    return JSONResponse(status_code=201, content={"message": "Pateint created successfully"})


@app.put('/edit/{pateint_id}')
def update_pateint(pateint_id:str, pateint_update: PateintUpdate):
    # Load existing data
    data = load_data()

    # Check if the pateint exists
    if pateint_id not in data:
        raise HTTPException(status_code=404, detail="Pateint not found")
    # Validate the update data
    existing_pateint_info = data[pateint_id]
    # Update the pateint data
    updated_pateint_info = pateint_update.model_dump(exclude_unset=True)

    for key, value in updated_pateint_info.items():
        if value is not None:
            existing_pateint_info[key] = value

    # Save the updated data
    existing_pateint_info['id'] = pateint_id
    pateint_pydantic_obj = Pateint(**existing_pateint_info)
    existing_pateint_info = pateint_pydantic_obj.model_dump(exclude=['id'])

    data[pateint_id] = existing_pateint_info
    save_data(data)
    # Return success response
    return JSONResponse(status_code=200, content={"message": "Pateint updated successfully"})


@app.delete('/delete/{pateint_id}')
def delete_pateint(pateint_id: str):
    # Load existing data
    data = load_data()

    # Check if the pateint exists
    if pateint_id not in data:
        raise HTTPException(status_code=404, detail="Pateint not found")

    # Delete the pateint data
    del data[pateint_id]

    # Save the updated data
    save_data(data)

    # Return success response
    return JSONResponse(status_code=200, content={"message": "Pateint deleted successfully"})

