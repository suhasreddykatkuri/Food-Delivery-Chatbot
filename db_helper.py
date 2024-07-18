# No need to import track_order here
import aiomysql
from decimal import Decimal
# MySQL database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Srikar@2024',
    'db': 'pandeyji_eatery'
}

async def get_mysql_connection():
    connection = await aiomysql.connect(**DB_CONFIG)
    return connection

# Function to fetch order status from the database
async def get_order_status(order_id: int, conn: aiomysql.Connection = None):
    if conn is None:
        conn = await get_mysql_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT status FROM order_tracking WHERE order_id = %s", (order_id,))
        result = await cursor.fetchone()
        if result:
            return {"order_id": order_id, "status": result[0]}
        else:
            return None

# Function to fetch the maximum order ID from the orders table
async def get_max_order_id(conn: aiomysql.Connection = None):
    if conn is None:
        conn = await get_mysql_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT MAX(order_id) FROM orders")
        result = await cursor.fetchone()
        if result[0] is not None:
            return result[0]
        else:
            return 0  # Return 0 if there are no orders in the table

async def insert_order(order_id, order_data):
    conn = await get_mysql_connection()
    async with conn.cursor() as cursor:
        t=0
        for food_item, quantity in order_data.items():
            # Retrieve item_id and price for the given food_item from the food_items table
            await cursor.execute("SELECT item_id, price FROM food_items WHERE name = %s", (food_item,))
            result = await cursor.fetchone()
            if result:
                item_id, price = result
                total_price = Decimal(quantity) * price  # Calculate total price
                t+=total_price
                # Insert order details into the orders table
                print(result,order_id,item_id,quantity,total_price)
                await cursor.execute("INSERT INTO orders (order_id, item_id, quantity, total_price) VALUES (%s, %s, %s, %s)",
                                     (order_id, item_id, quantity, total_price))
        await conn.commit()
    return t
    # No need to close the connection explicitly
#insert order status
async def insert_order_status(order_id, status):
    conn = await get_mysql_connection()
    async with conn.cursor() as cursor:
        # Insert order status into the order_tracking table
        await cursor.execute("INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)",
                             (order_id, status))
        await conn.commit()

