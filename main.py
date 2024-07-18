from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from db_helper import get_order_status,get_max_order_id,insert_order,insert_order_status
from generic_helper import extract_session_id

# Create an instance of the FastAPI class
app = FastAPI()
global orders 
orders = {}
# Define a route using a decorator for handling POST requests

@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = extract_session_id(output_contexts[0]['name'])
    fun = {
        'track.order-context:ongoing-tracking':track_order,
        'order.add-context:ongoing-order':add_order,
        'order.complete-context:ongoing-order':complete_order,
        'order.remove-context:ongoing-order':remove_order,
        'new.order':new_order
    }
    if intent=='new.order':
        new_order(parameters,session_id)
    elif intent == 'track.order-context:ongoing-tracking' or intent == 'order.complete-context:ongoing-order':
        return await fun[intent](parameters, session_id)
    else:
        return fun[intent](parameters, session_id) 
    
def new_order(parameters,session_id):
    if session_id in orders:
        orders[session_id]={}
def remove_order(parameters,session_id):
    if session_id not in orders:
        return JSONResponse(content={"fulfillmentText":'Please place a new order first.'})
    current_order = orders[session_id]
    not_there_items,removed_items=[],[]
    food_item  = parameters['food-item']
    for item in food_item:
        if item not in current_order:
            not_there_items.append(item)
        else:
            del current_order[item]
            removed_items.append(item)
    if not food_item:
        fulfillment_text = 'Please enter valid items.'
    if len(removed_items)>0:
        fulfillment_text = f'Removed {" ".join(removed_items)} from your order.'
    if len(not_there_items)>0:
        fulfillment_text = f'Your current doesnt have {" ".join(not_there_items)}'
    result = ', '.join(f"{int(value)} {key}," for key, value in current_order.items())
    if current_order.keys()==0:
        fulfillment_text+=" Your order is empty!"
    else:
        fulfillment_text+=f'Whats left in your order is: {result} '
        print(orders)
    return JSONResponse(content={"fulfillmentText":fulfillment_text+'Anything else?'})
def add_order(parameters,session_id):
    food_item = parameters['food-item']
    quantity = parameters['number']
    if len(food_item)!=len(quantity):
        fulfillment_text = 'Sorry , I didnt understand.Can you specify food items and quantity clearly'
    else:
        fulfillment_text='yn'
        food_dict=dict(zip(food_item,quantity))
        if session_id in orders:
            for i in food_dict:
                if i in orders[session_id]:
                    orders[session_id][i]+=food_dict[i]
                else:
                    orders[session_id][i]=food_dict[i]
        else:
            orders[session_id]=food_dict
        print(orders)
        result = ', '.join(f"{int(value)} {key}," for key, value in orders[session_id].items())
        fulfillment_text=f'your order contains {result}.Anything else?'
    return JSONResponse(content={"fulfillmentText":fulfillment_text})

async def complete_order(parameters,session_id):
    if session_id not in orders:
        fulfillment_text = 'Sorry,couldnt process your order.Can you place a new order again?'
    else:
        new_order_id,total_price = await save_to_db(session_id)
        fulfillment_text = f'Order placed.Your order id is {new_order_id},Your order total price is : {total_price} , which you can pay at the time of delivery.'
        if new_order_id==0:
            fulfillment_text="Sorry,couldnt process your order.Can you place a new order again?"
    del orders[session_id]
    return JSONResponse(content={"fulfillmentText":fulfillment_text})
async def save_to_db(session_id):
    order_id = await get_max_order_id()
    new_order_id = order_id+1
    total_price = await insert_order(new_order_id,orders[session_id])
    await insert_order_status(new_order_id,"In Progress")
    return new_order_id,total_price

# Define track_order function
async def track_order(parameters: dict,session_id):
    order_id = int(parameters['order_id'])
    status_data = await get_order_status(order_id)  # Fetch order status
    if status_data is not None:
        status1 = status_data["status"]
        status = f'The status of Your order with order id {order_id} : {status1}'
    else:
        status = f"Order with order id {order_id} is not found"
    return JSONResponse(content={"fulfillmentText": status})

# Define a route using a decorator for handling GET requests
@app.get("/")
async def get_root():
    return {"message": "Hello, FastAPI!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
