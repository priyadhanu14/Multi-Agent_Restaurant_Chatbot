from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional
import pytz
import sys
import os
from agents import function_tool
from typing import List, Literal
from pydantic import BaseModel, ConfigDict
from .connection import get_connection


def _close_cursor(cur) -> None:
    """Close cursor and connection."""
    conn = cur.connection
    cur.close()
    conn.close()


@function_tool
def get_outlets_by_city_or_zip(city: str = "", zip_code: str = "") -> str:
    """
    Search for outlets by city name or zip code.
    Returns a formatted list of matching outlets with their details.
    """
    if not city.strip() and not zip_code.strip():
        return "Please provide either city or zip_code to search for outlets."

    conn = get_connection()
    cur = conn.cursor()
    try:
        conditions: List[str] = ["o.is_active = TRUE"]
        params: List[Any] = []

        if city.strip():
            conditions.append("o.city ILIKE %s")
            params.append(f"%{city.strip()}%")

        if zip_code.strip():
            conditions.append("o.zip_code ILIKE %s")
            params.append(f"%{zip_code.strip()}%")

        query = """
            SELECT 
                o.id,
                o.name,
                o.address,
                o.city,
                o.state,
                o.zip_code,
                o.supports_delivery,
                o.supports_pickup,
                o.open_time,
                o.close_time
            FROM outlets o
            WHERE """ + " AND ".join(conditions) + """
            ORDER BY o.city, o.name
        """

        cur.execute(query, params)
        rows = cur.fetchall()

        if not rows:
            return "No outlets found matching your search criteria."

        lines = ["Matching outlets:"]
        for (
            outlet_id,
            name,
            address,
            city_val,
            state,
            zip_val,
            supports_delivery,
            supports_pickup,
            open_time,
            close_time,
        ) in rows:
            services = []
            if supports_delivery:
                services.append("Delivery")
            if supports_pickup:
                services.append("Pickup")
            services_str = ", ".join(services) if services else "None"

            address_parts = [part for part in [address, city_val, state, zip_val] if part]
            address_str = ", ".join(address_parts) if address_parts else "Address not available"

            hours = f"{open_time} - {close_time}" if open_time and close_time else "Hours not set"

            lines.append(
                f"- #{outlet_id} {name} - {address_str} | "
                f"Services: {services_str} | Hours: {hours}"
            )

        return "\n".join(lines)
    finally:
        _close_cursor(cur)

@function_tool
def get_outlet_menu(outlet_id: int) -> str:
    """
    Get the complete menu for a specific outlet, including availability status.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verify outlet exists
        cur.execute("SELECT name FROM outlets WHERE id = %s AND is_active = TRUE", (outlet_id,))
        outlet_row = cur.fetchone()
        if not outlet_row:
            return f"Outlet #{outlet_id} not found or is inactive."

        outlet_name = outlet_row[0]

        query = """
            SELECT 
                mi.id,
                mi.name,
                mi.description,
                mi.category,
                mi.base_price,
                mi.is_veg,
                mi.is_spicy,
                oma.is_available,
                oma.available_from_time,
                oma.available_to_time
            FROM menu_items mi
            INNER JOIN outlet_menu_availability oma ON oma.menu_item_id = mi.id
            WHERE oma.outlet_id = %s
              AND mi.is_active = TRUE
            ORDER BY mi.category, mi.name
        """

        cur.execute(query, (outlet_id,))
        rows = cur.fetchall()

        if not rows:
            return f"No menu items found for outlet #{outlet_id} ({outlet_name})."

        lines = [f"Menu for {outlet_name} (Outlet #{outlet_id}):"]
        current_category = None

        for (
            id,
            name,
            description,
            category,
            price,
            is_veg,
            is_spicy,
            is_available,
            avail_from,
            avail_to,
        ) in rows:
            # Group by category
            if category != current_category:
                current_category = category
                lines.append(f"\n{category.upper().replace('_', ' ')}:")

            # Build item description
            tags = []
            if is_veg:
                tags.append("Vegetarian")
            if is_spicy:
                tags.append("Spicy")
            tag_str = f" [{', '.join(tags)}]" if tags else ""

            availability = "Available" if is_available else "Currently Unavailable"
            if avail_from and avail_to:
                availability += f" ({avail_from} - {avail_to})"

            desc_text = f" - {description}" if description else ""
            lines.append(
                f"  #{id} {name}{tag_str} - ${price:.2f} | {availability}{desc_text}"
            )

        return "\n".join(lines)
    finally:
        _close_cursor(cur)


@function_tool
def filter_menu(
    outlet_id: int,
    category: str = "",
    is_veg: Optional[bool] = None,
    is_spicy: Optional[bool] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
) -> str:
    """
    Filter menu items for a specific outlet based on various criteria.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verify outlet exists
        cur.execute("SELECT name FROM outlets WHERE id = %s AND is_active = TRUE", (outlet_id,))
        outlet_row = cur.fetchone()
        if not outlet_row:
            return f"Outlet #{outlet_id} not found or is inactive."

        outlet_name = outlet_row[0]

        conditions: List[str] = [
            "oma.outlet_id = %s",
            "mi.is_active = TRUE",
            "oma.is_available = TRUE",
        ]
        params: List[Any] = [outlet_id]

        if category.strip():
            conditions.append("mi.category ILIKE %s")
            params.append(f"%{category.strip()}%")

        if is_veg is not None:
            conditions.append("mi.is_veg = %s")
            params.append(is_veg)

        if is_spicy is not None:
            conditions.append("mi.is_spicy = %s")
            params.append(is_spicy)

        if min_price is not None:
            conditions.append("mi.base_price >= %s")
            params.append(min_price)

        if max_price is not None:
            conditions.append("mi.base_price <= %s")
            params.append(max_price)

        query = """
            SELECT 
                mi.id,
                mi.name,
                mi.description,
                mi.category,
                mi.base_price,
                mi.is_veg,
                mi.is_spicy
            FROM menu_items mi
            INNER JOIN outlet_menu_availability oma ON oma.menu_item_id = mi.id
            WHERE """ + " AND ".join(conditions) + """
            ORDER BY mi.category, mi.base_price, mi.name
        """

        cur.execute(query, params)
        rows = cur.fetchall()

        if not rows:
            return f"No menu items found for outlet #{outlet_id} matching the filters."

        lines = [f"Filtered menu for {outlet_name} (Outlet #{outlet_id}):"]
        current_category = None

        for (
            id,
            name,
            description,
            cat,
            price,
            veg,
            spicy,
        ) in rows:
            if cat != current_category:
                current_category = cat
                lines.append(f"\n{cat.upper().replace('_', ' ')}:")

            tags = []
            if veg:
                tags.append("Vegetarian")
            if spicy:
                tags.append("Spicy")
            tag_str = f" [{', '.join(tags)}]" if tags else ""

            desc_text = f" - {description}" if description else ""
            lines.append(f"  #{id} {name}{tag_str} - ${price:.2f}{desc_text}")

        return "\n".join(lines)
    finally:
        _close_cursor(cur)


@function_tool
def is_outlet_open(outlet_id: int, current_time: Optional[str] = None) -> str:
    """
    Check if an outlet is currently open based on its operating hours and timezone.
    If current_time is not provided, uses the current system time.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT name, open_time, close_time, timezone
            FROM outlets
            WHERE id = %s AND is_active = TRUE
            """,
            (outlet_id,),
        )
        row = cur.fetchone()
        if not row:
            return f"Outlet #{outlet_id} not found or is inactive."

        outlet_name, open_time, close_time, timezone_str = row

        if not open_time or not close_time:
            return f"Outlet #{outlet_id} ({outlet_name}) does not have operating hours set."

        # Parse or compute current time in outlet's timezone
        try:
            tz = pytz.timezone(timezone_str) if timezone_str else None
        except Exception:
            tz = None

        if current_time:
            try:
                if "T" in current_time:
                    # ISO string, possibly with Z or offset
                    current_dt = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
                else:
                    # naive datetime string, assume outlet's local time if tz is known
                    naive_dt = datetime.strptime(current_time, "%Y-%m-%s %H:%M:%S")
                    if tz:
                        current_dt = tz.localize(naive_dt)
                    else:
                        current_dt = naive_dt
            except ValueError:
                return (
                    "Invalid current_time format. Use ISO format "
                    "(e.g., 2025-01-15T14:00:00) or YYYY-MM-DD HH:MM:SS."
                )
        else:
            # No time provided: use "now" in outlet's local timezone if available,
            # otherwise just system local time.
            if tz:
                current_dt = datetime.now(tz)
            else:
                current_dt = datetime.now()


        # Handle cases where close_time might be after midnight (e.g., 23:59 -> 08:00)
        if close_time < open_time:
            # Operating hours span midnight
            is_open = current_dt.time() >= open_time or current_dt.time() <= close_time
        else:
            # Normal operating hours
            is_open = open_time <= current_dt.time() <= close_time

        status = "OPEN" if is_open else "CLOSED"
        time_str = current_dt.strftime("%Y-%m-%s %H:%M:%S")
        if timezone_str:
            time_str += f" ({timezone_str})"

        return (
            f"Outlet #{outlet_id} ({outlet_name}) is {status}.\n"
            f"Operating hours: {open_time} - {close_time}\n"
            f"Current time: {time_str}"
        )
    finally:
        _close_cursor(cur)

class OrderItemInput(BaseModel):
    menu_item_id: int
    quantity: int

    model_config = ConfigDict(extra="forbid")  # no unknown keys

class CreateOrderPayload(BaseModel):
    outlet_id: int
    fulfillment_type: Literal["PICKUP", "DELIVERY"]
    customer_name: str
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    items: List[OrderItemInput]

    model_config = ConfigDict(extra="forbid")  # no unknown keys


@function_tool
def create_order(payload: CreateOrderPayload) -> str:
    """
    Create a new order with items.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # ---------- Basic validation ----------
        outlet_id = payload.outlet_id
        if not outlet_id:
            conn.rollback()
            return "ERROR: outlet_id is required."

        fulfillment_type = payload.fulfillment_type.upper()
        if fulfillment_type not in ["PICKUP", "DELIVERY"]:
            conn.rollback()
            return "ERROR: fulfillment_type must be 'PICKUP' or 'DELIVERY'."

        customer_name = (payload.customer_name or "").strip()
        if not customer_name:
            conn.rollback()
            return "ERROR: customer_name is required."

        customer_phone = (payload.customer_phone or "").strip() or None
        customer_address = (payload.customer_address or "").strip() or None

        if fulfillment_type == "DELIVERY" and not customer_address:
            conn.rollback()
            return "ERROR: customer_address is required for DELIVERY orders."

        items = payload.items
        if not items:
            conn.rollback()
            return "ERROR: At least one item is required in the order."

        # ---------- Verify outlet ----------
        cur.execute(
            "SELECT name, is_active FROM outlets WHERE id = %s",
            (outlet_id,),
        )
        outlet_row = cur.fetchone()
        if not outlet_row:
            conn.rollback()
            return f"ERROR: Outlet #{outlet_id} not found."

        outlet_name, is_active = outlet_row
        if not is_active:
            conn.rollback()
            return f"ERROR: Outlet #{outlet_id} ({outlet_name}) is not active."

        # ---------- Validate items & compute total ----------
        order_items: List[dict] = []
        total_amount = 0.0

        for item in items:
            menu_item_id = item.menu_item_id
            quantity = item.quantity

            if not menu_item_id or not quantity:
                conn.rollback()
                return "ERROR: Each item must have menu_item_id and quantity."

            if quantity <= 0:
                conn.rollback()
                return "ERROR: Quantity must be greater than zero."

            # Look up menu item & availability
            cur.execute(
                """
                SELECT mi.id, mi.name, mi.base_price, oma.is_available
                FROM menu_items mi
                INNER JOIN outlet_menu_availability oma ON oma.menu_item_id = mi.id
                WHERE mi.id = %s
                  AND oma.outlet_id = %s
                  AND mi.is_active = TRUE
                """,
                (menu_item_id, outlet_id),
            )
            menu_row = cur.fetchone()
            if not menu_row:
                conn.rollback()
                return (
                    f"ERROR: Menu item #{menu_item_id} not found "
                    f"or not available at this outlet."
                )

            item_id, item_name, unit_price, is_available = menu_row
            if not is_available:
                conn.rollback()
                return (
                    f"ERROR: Menu item #{menu_item_id} ({item_name}) "
                    f"is currently unavailable."
                )

            line_total = float(unit_price) * quantity
            total_amount += line_total

            order_items.append(
                {
                    "menu_item_id": item_id,
                    "quantity": quantity,
                    "unit_price": float(unit_price),
                    "line_total": line_total,
                }
            )

        # ---------- Insert into orders ----------
        now = datetime.now(timezone.utc)
        cur.execute(
            """
            INSERT INTO orders (
                outlet_id,
                status,
                fulfillment_type,
                customer_name,
                customer_phone,
                customer_address,
                created_at,
                updated_at,
                total_amount
            )
            VALUES (%s, 'PENDING', %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                outlet_id,
                fulfillment_type,
                customer_name,
                customer_phone,
                customer_address,
                now,
                now,
                total_amount,
            ),
        )
        order_id = cur.fetchone()[0]

        # ---------- Insert order_items ----------
        for item in order_items:
            cur.execute(
                """
                INSERT INTO order_items (
                    order_id,
                    menu_item_id,
                    quantity,
                    unit_price,
                    line_total
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    item["menu_item_id"],
                    item["quantity"],
                    item["unit_price"],
                    item["line_total"],
                ),
            )

        conn.commit()

        # ---------- Build confirmation message ----------
        items_summary = ", ".join(
            f"{item['quantity']}x item #{item['menu_item_id']}"
            for item in order_items
        )

        return (
            "SUCCESS: "
            f"Order #{order_id} created successfully for {outlet_name}.\n"
            f"Customer: {customer_name}\n"
            f"Type: {fulfillment_type}\n"
            f"Items: {items_summary}\n"
            f"Total: ${total_amount:.2f}"
        )

    except Exception as e:
        conn.rollback()
        return f"ERROR: Error creating order: {str(e)}"
    finally:
        cur.close()
        conn.close()



@function_tool
def get_order_status(order_id: int) -> str:
    """
    Get detailed status and information for a specific order.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Get order details
        cur.execute(
            """
            SELECT 
                o.id,
                o.status,
                o.fulfillment_type,
                o.customer_name,
                o.customer_phone,
                o.customer_address,
                o.total_amount,
                o.created_at,
                o.updated_at,
                o.outlet_id,
                out.name AS outlet_name
            FROM orders o
            INNER JOIN outlets out ON out.id = o.outlet_id
            WHERE o.id = %s
            """,
            (order_id,),
        )
        order_row = cur.fetchone()
        if not order_row:
            return f"Order #{order_id} not found."

        (
            _order_id,
            status,
            fulfillment_type,
            customer_name,
            customer_phone,
            customer_address,
            total_amount,
            created_at,
            updated_at,
            outlet_id,
            outlet_name,
        ) = order_row

        # Get order items
        cur.execute(
            """
            SELECT 
                oi.quantity,
                oi.unit_price,
                oi.line_total,
                mi.name,
                mi.category
            FROM order_items oi
            INNER JOIN menu_items mi ON mi.id = oi.menu_item_id
            WHERE oi.order_id = %s
            ORDER BY oi.id
            """,
            (order_id,),
        )
        items = cur.fetchall()

        lines = [
            f"Order #{order_id} Status: {status}",
            f"Outlet: {outlet_name} (Outlet #{outlet_id})",
            f"Customer: {customer_name}",
        ]

        if customer_phone:
            lines.append(f"Phone: {customer_phone}")

        lines.append(f"Fulfillment: {fulfillment_type}")
        if fulfillment_type == "DELIVERY" and customer_address:
            lines.append(f"Delivery Address: {customer_address}")

        lines.append(f"\nItems:")
        for quantity, unit_price, line_total, name, category in items:
            lines.append(
                f"  - {name} ({category}) x{quantity} @ ${unit_price:.2f} = ${line_total:.2f}"
            )

        lines.append(f"\nTotal Amount: ${total_amount:.2f}")
        lines.append(f"Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Last Updated: {updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)
    finally:
        _close_cursor(cur)


OrderStatusLiteral = Literal[
    "CONFIRMED",
    "IN_KITCHEN",
    "READY",
    "COMPLETED",
    "CANCELLED",
]


@function_tool
def update_order_status(order_id: int, new_status: OrderStatusLiteral) -> str:
    """
    Update the status of an existing order.

    Allowed statuses:
    - CONFIRMED
    - IN_KITCHEN
    - READY
    - COMPLETED
    - CANCELLED
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1) Check that the order exists and see its current status
        cur.execute(
            "SELECT status FROM orders WHERE id = %s",
            (order_id,),
        )
        row = cur.fetchone()
        if not row:
            return f"Order #{order_id} not found."

        current_status = row[0]

        # 2) If it's already in that status, no need to update
        if current_status == new_status:
            return f"Order #{order_id} is already in status {current_status}."

        # 3) Perform the update
        cur.execute(
            """
            UPDATE orders
            SET status = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (new_status, order_id),
        )
        conn.commit()

        return f"Order #{order_id} status updated from {current_status} to {new_status}."
    except Exception as e:
        conn.rollback()
        return f"Error updating order status: {str(e)}"
    finally:
        _close_cursor(cur)
