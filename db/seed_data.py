import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import random
from decimal import Decimal


def get_connection():

    return psycopg2.connect(
        dbname="restaurant_db",
        user="postgres",
        password="user@123",  
        host="localhost",
        port=5434,
    )


def insert_outlets(cur):
    outlets = [
        # West Coast
        ("Downtown Diner - Seattle", "Seattle", "WA", "98101",
         "123 Main St", "America/Los_Angeles", "08:00", "22:00", True, True),

        ("Bayview Bites - San Francisco", "San Francisco", "CA", "94105",
         "500 Embarcadero", "America/Los_Angeles", "09:00", "23:00", True, True),

        ("Sunset Grill - Los Angeles", "Los Angeles", "CA", "90013",
         "2400 Sunset Blvd", "America/Los_Angeles", "10:00", "23:59", True, True),

        # Central
        ("Windy City Grill - Chicago", "Chicago", "IL", "60601",
         "200 Lake Shore Dr", "America/Chicago", "07:30", "21:30", False, True),

        ("Lone Star Lunch - Austin", "Austin", "TX", "73301",
         "42 Congress Ave", "America/Chicago", "08:30", "22:30", True, True),

        ("Riverfront Eats - New Orleans", "New Orleans", "LA", "70130",
         "15 Canal St", "America/Chicago", "09:00", "22:00", True, True),

        # East Coast
        ("Big Apple Eats - Manhattan", "New York", "NY", "10001",
         "10 Broadway", "America/New_York", "10:00", "23:59", True, False),

        ("Harbor Grill - Boston", "Boston", "MA", "02110",
         "75 Harbor Way", "America/New_York", "08:00", "22:00", True, True),

        ("Liberty Square Diner - Philly", "Philadelphia", "PA", "19107",
         "300 Market St", "America/New_York", "09:00", "23:00", True, True),

        ("Capitol Bites - DC", "Washington", "DC", "20001",
         "1600 Pennsylvania Ave NW", "America/New_York", "08:00", "21:00", True, True),
    ]

    sql = """
    INSERT INTO outlets
    (name, city, state, zip_code, address, timezone,
     open_time, close_time, supports_delivery, supports_pickup)
    VALUES %s
    RETURNING id;
"""

    execute_values(cur, sql, outlets)
    outlet_ids = [row[0] for row in cur.fetchall()]
    return outlet_ids



def insert_menu_items(cur):
    
    menu_items = [
        ("Classic Burger", "Beef patty with lettuce, tomato, and cheese",
         "burger", 10.99, False, False),
        ("Veggie Burger", "Grilled veggie patty with avocado and greens",
         "burger", 9.49, True, False),
        ("Spicy Chicken Burger", "Crispy chicken with spicy mayo",
         "burger", 11.49, False, True),
        ("Caesar Salad", "Romaine, parmesan, croutons, caesar dressing",
         "salad", 8.99, True, False),
        ("Greek Salad", "Tomato, cucumber, olives, feta, olive oil",
         "salad", 9.49, True, False),
        ("Fries", "Crispy golden french fries",
         "side", 3.99, True, False),
        ("Onion Rings", "Battered and fried onion rings",
         "side", 4.49, True, False),
        ("Chicken Wings", "Fried wings tossed in buffalo sauce",
         "side", 8.49, False, True),
        ("Cola", "Carbonated soft drink",
         "drink", 2.49, True, False),
        ("Lemonade", "Fresh squeezed lemonade",
         "drink", 2.99, True, False),

        # ---- Indian cuisine ----
        ("Paneer Butter Masala", "Creamy tomato-based curry with paneer cubes",
         "indian_main", 12.99, True, False),
        ("Chicken Tikka Masala", "Char-grilled chicken in spiced creamy sauce",
         "indian_main", 13.99, False, True),
        ("Dal Tadka", "Yellow lentils tempered with ghee and spices",
         "indian_main", 10.49, True, True),
        ("Chole Bhature", "Spiced chickpea curry served with fried bread",
         "indian_main", 11.49, True, True),
        ("Vegetable Biryani", "Fragrant basmati rice with mixed vegetables",
         "indian_main", 11.99, True, True),
        ("Chicken Biryani", "Hyderabadi-style spiced chicken and rice",
         "indian_main", 13.49, False, True),
        ("Masala Dosa", "Crispy rice crepe stuffed with spiced potatoes",
         "indian_main", 9.99, True, True),
        ("Idli Sambar", "Steamed rice cakes with lentil stew",
         "indian_main", 8.49, True, True),
        ("Aloo Paratha", "Stuffed flatbread with spiced potatoes and butter",
         "indian_main", 8.99, True, False),
        ("Palak Paneer", "Spinach curry with cottage cheese cubes",
         "indian_main", 12.49, True, False),
        ("Tandoori Chicken", "Yogurt-marinated chicken grilled in tandoor",
         "indian_starter", 12.99, False, True),
        ("Samosa", "Crispy pastry filled with spiced potatoes and peas",
         "indian_starter", 5.49, True, True),
        ("Gulab Jamun", "Deep-fried milk dumplings in sugar syrup",
         "dessert", 4.99, True, False),
        ("Mango Lassi", "Sweet yogurt drink with mango pulp",
         "drink", 3.99, True, False),

        # ---- Chinese cuisine ----
        ("Veg Hakka Noodles", "Stir-fried noodles with vegetables",
         "chinese_main", 10.49, True, True),
        ("Chicken Hakka Noodles", "Stir-fried noodles with chicken and veggies",
         "chinese_main", 11.49, False, True),
        ("Vegetable Manchurian", "Fried veggie balls in spicy tangy sauce",
         "chinese_main", 10.99, True, True),
        ("Chicken Manchurian", "Crispy chicken in Indo-Chinese sauce",
         "chinese_main", 11.99, False, True),
        ("Kung Pao Chicken", "Stir-fried chicken with peanuts and chili",
         "chinese_main", 12.99, False, True),
        ("Mapo Tofu", "Silken tofu in spicy Sichuan chili sauce",
         "chinese_main", 11.49, True, True),
        ("Sweet and Sour Vegetables", "Mixed vegetables in sweet and sour sauce",
         "chinese_main", 10.49, True, False),
        ("Sweet and Sour Chicken", "Battered chicken in sweet and tangy sauce",
         "chinese_main", 11.49, False, False),
        ("Spring Rolls", "Crispy rolls stuffed with vegetables",
         "chinese_starter", 6.49, True, False),
        ("Hot and Sour Soup", "Spicy and tangy soup with vegetables",
         "chinese_starter", 8.49, True, True),
        ("Fried Rice", "Stir-fried rice with vegetables and protein",
         "chinese_main", 10.49, True, True),
        ("Chicken Chow Mein", "Stir-fried noodles with chicken and veggies",
         "chinese_main", 11.49, False, True),
        ("Vegetable Spring Rolls", "Crispy rolls stuffed with vegetables",
         "chinese_starter", 6.49, True, False),
    ]

    sql = """
    INSERT INTO menu_items
    (name, description, category, base_price, is_veg, is_spicy)
    VALUES %s
    RETURNING id;
"""


    execute_values(cur, sql, menu_items)
    menu_item_ids = [row[0] for row in cur.fetchall()]
    return menu_item_ids


def insert_outlet_menu_availability(cur, outlet_ids, menu_item_ids):

    availability_rows = []

    for outlet_id in outlet_ids:
        for menu_item_id in menu_item_ids:
            availability_rows.append(
                (outlet_id, menu_item_id, True, None, None)
            )

    sql = """
        INSERT INTO outlet_menu_availability
        (outlet_id, menu_item_id, is_available, available_from_time, available_to_time)
        VALUES %s;
    """

    execute_values(cur, sql, availability_rows)

def insert_orders(cur, outlet_ids):
    """
    Create a few sample orders for random outlets.
    """
    now = datetime.utcnow()
    orders = []

    # create 5 sample orders
    for i in range(5):
        outlet_id = random.choice(outlet_ids)
        created_at = now - timedelta(minutes=15 * i)
        status = "COMPLETED"
        fulfillment = random.choice(["PICKUP", "DELIVERY"])
        customer_name = f"Customer {i+1}"
        customer_phone = f"555-000{i+1}"
        customer_notes = None
        total_amount = Decimal("0.00")  # we'll update after items

        orders.append(
            (
                outlet_id,
                created_at,
                status,
                fulfillment,
                customer_name,
                customer_phone,
                customer_notes,
                total_amount,
            )
        )

    sql = """
        INSERT INTO orders
        (outlet_id, created_at, status, fulfillment_type,
         customer_name, customer_phone, customer_notes, total_amount)
        VALUES %s
        RETURNING id;
    """

    execute_values(cur, sql, orders)
    order_ids = [row[0] for row in cur.fetchall()]
    return order_ids

def insert_order_items(cur, order_ids, menu_item_ids):
    """
    For each order, add 2–3 random items and update total_amount.
    """
    order_items_rows = []
    order_totals = {order_id: Decimal("0.00") for order_id in order_ids}

    for order_id in order_ids:
        num_items = random.randint(2, 3)
        chosen_items = random.sample(menu_item_ids, num_items)

        for menu_item_id in chosen_items:
            quantity = random.randint(1, 3)

            # get base_price from menu_items
            cur.execute(
                "SELECT base_price FROM menu_items WHERE id = %s",
                (menu_item_id,),
            )
            (unit_price,) = cur.fetchone()
            unit_price = Decimal(str(unit_price))
            line_total = unit_price * quantity

            order_items_rows.append(
                (order_id, menu_item_id, quantity, unit_price, line_total)
            )
            order_totals[order_id] += line_total

    sql_items = """
        INSERT INTO order_items
        (order_id, menu_item_id, quantity, unit_price, line_total)
        VALUES %s;
    """
    execute_values(cur, sql_items, order_items_rows)

    # update total_amount on orders
    for order_id, total in order_totals.items():
        cur.execute(
            "UPDATE orders SET total_amount = %s WHERE id = %s",
            (total, order_id),
        )


def main():
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                print("Inserting outlets...")
                outlet_ids = insert_outlets(cur)

                print("Inserting menu items...")
                menu_item_ids = insert_menu_items(cur)

                print("Inserting outlet menu availability...")
                insert_outlet_menu_availability(cur, outlet_ids, menu_item_ids)

                print("Inserting orders...")
                order_ids = insert_orders(cur, outlet_ids)

                print("Inserting order items and updating totals...")
                insert_order_items(cur, order_ids, menu_item_ids)

    finally:
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()
