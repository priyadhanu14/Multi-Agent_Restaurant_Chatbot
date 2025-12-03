
-- Outlets (restaurants)
CREATE TABLE outlets (
  id                SERIAL PRIMARY KEY,
  name              VARCHAR(255) NOT NULL,
  address           TEXT,
  city              VARCHAR(100),
  state             VARCHAR(50),
  zip_code          VARCHAR(20),
  timezone          VARCHAR(100),
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  supports_delivery BOOLEAN NOT NULL DEFAULT TRUE,
  supports_pickup   BOOLEAN NOT NULL DEFAULT TRUE,
  open_time         TIME,              -- e.g. '08:00'
  close_time        TIME               -- e.g. '22:00'
);

-- Master menu items (outlet-agnostic)
CREATE TABLE menu_items (
  id          SERIAL PRIMARY KEY,
  name        VARCHAR(255) NOT NULL,
  description TEXT,
  category    VARCHAR(50) NOT NULL,    -- burger, side, drink, salad, breakfast, dessert...
  base_price  NUMERIC(10, 2) NOT NULL,
  is_veg      BOOLEAN NOT NULL DEFAULT FALSE,
  is_spicy    BOOLEAN NOT NULL DEFAULT FALSE,
  is_active   BOOLEAN NOT NULL DEFAULT TRUE
);

-- Per-outlet availability & time windows
CREATE TABLE outlet_menu_availability (
  id                  SERIAL PRIMARY KEY,
  outlet_id           INTEGER NOT NULL,
  menu_item_id        INTEGER NOT NULL,
  is_available        BOOLEAN NOT NULL DEFAULT TRUE,
  available_from_time TIME,             -- e.g. '06:00'
  available_to_time   TIME,             -- e.g. '11:00'
  available_days      VARCHAR(50),      -- 'Mon-Fri', 'All', etc.
  CONSTRAINT fk_oma_outlet
    FOREIGN KEY(outlet_id) REFERENCES outlets(id) ON DELETE CASCADE,
  CONSTRAINT fk_oma_menu_item
    FOREIGN KEY(menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE,
  CONSTRAINT uq_outlet_menu UNIQUE (outlet_id, menu_item_id)
);

-- Orders
CREATE TABLE orders (
  id               SERIAL PRIMARY KEY,
  outlet_id        INTEGER NOT NULL,
  status           VARCHAR(50) NOT NULL,      -- PENDING, IN_KITCHEN, READY, COMPLETED, CANCELLED
  fulfillment_type VARCHAR(50) NOT NULL,      -- PICKUP, DELIVERY
  customer_name    VARCHAR(255),
  customer_phone   VARCHAR(50),
  customer_address TEXT,                      -- for delivery, NULL for pickup
  created_at       TIMESTAMPTZ NOT NULL,
  updated_at       TIMESTAMPTZ NOT NULL,
  total_amount     NUMERIC(10, 2) NOT NULL,
  CONSTRAINT fk_orders_outlet
    FOREIGN KEY(outlet_id) REFERENCES outlets(id)
);

-- Order line items
CREATE TABLE order_items (
  id           SERIAL PRIMARY KEY,
  order_id     INTEGER NOT NULL,
  menu_item_id INTEGER NOT NULL,
  quantity     INTEGER NOT NULL,
  unit_price   NUMERIC(10, 2) NOT NULL,      -- price at time of order
  line_total   NUMERIC(10, 2) NOT NULL,
  CONSTRAINT fk_order_items_order
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
  CONSTRAINT fk_order_items_menu
    FOREIGN KEY(menu_item_id) REFERENCES menu_items(id),
  CONSTRAINT ck_order_items_quantity CHECK (quantity > 0)
);
