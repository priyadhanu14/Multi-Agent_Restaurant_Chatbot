Multi-Agent Restaurant Chatbot

### Overview

**Multi-Agent_Restaurant_Chatbot** is a restaurant assistant built with a **multi‑agent architecture**.  
Instead of a single monolithic chatbot, the app uses several specialized agents that each handle a specific part of the restaurant experience and coordinate via a router:

- **Menu Agent**: Answers questions about the menu (items, categories, prices, recommendations, etc.).
- **Ordering Agent**: Helps users place orders, modify items, and confirm details.
- **Outlet Agent**: Provides information about restaurant outlets (locations, timings, contact info, availability, etc.).
- **Status Agent**: Tracks and reports order status.
- **Router Agent**: Analyzes each user message and routes it to the appropriate specialist agent.

The project uses a database (configured via the `db` module) to store menu data, outlet information, and conversation history.

### Project Structure

- **`app.py`**: Main application entry point that wires up the agents, database, and chat interface / API.
- **`app_agents/`**
  - `menu_agent.py`: Logic for answering menu-related queries.
  - `ordering_agent.py`: Logic for creating and managing orders.
  - `outlet_agent.py`: Logic for outlet/location‑related queries.
  - `status_agent.py`: Logic for checking and updating order status.
  - `router_agent.py`: Routes user messages to the correct agent.
- **`db/`**
  - `connection.py`: Database connection and configuration.
  - `queries.py`: SQL queries / data access helpers.
  - `schema_postgress.sql`: Database schema (tables for menu, orders, outlets, etc.).
  - `seed_data.py`: Script to seed initial data into the database.
- **`models.py`**: Data models / helper classes used across the app.
- **`update_status.py`**: Utility script to update order statuses (e.g., background runs or manual updates).
- **`conversations.db`**: Local SQLite (or similar) database file storing conversations and/or state (generated at runtime).

### Requirements

Install Python dependencies using `pip`:

```bash
pip install -r requirements.txt
```

Make sure you have:
- **Python** (version compatible with the packages in `requirements.txt`)
- A running **database** instance if you are using Postgres or another external DB (or adapt to SQLite as configured in `connection.py`).

### Database Setup

1. Create a database (e.g. in Postgres).
2. Run the schema script:

```bash
psql -d your_database_name -f db/schema_postgress.sql
```

3. Seed the database with initial data:

```bash
python -m db.seed_data
```

4. Adjust any connection settings in `db/connection.py` (host, port, user, password, database name) as needed.

> If you are using SQLite locally, you may skip the Postgres steps and rely on the existing `conversations.db` or adjust the configuration accordingly.

### Running the Application

From the project root:

```bash
python app.py
```

Depending on how `app.py` is implemented, this will either:
- Start a CLI/chat loop in the terminal, or
- Start a web server / API endpoint for the chatbot.

Check `app.py` for the exact interface; you can adapt it to your preferred frontend (CLI, web UI, or messaging platform).

### Typical User Flows

- **Ask about the menu**:  
  “What are your vegetarian options?” → Handled by `menu_agent`.

- **Place an order**:  
  “I’d like to order 2 Margherita pizzas and 1 Coke.” → Routed to `ordering_agent` for creation and confirmation.

- **Check outlet info**:  
  “Are you open at the Koramangala outlet after 10pm?” → Routed to `outlet_agent`.

- **Check order status**:  
  “What’s the status of my order #1234?” → Routed to `status_agent`.

### Pushing This Project to Another GitHub Repository

If you want to push this existing local project to a new GitHub repo:

```bash
cd Multi-Agent_Restaurant_Chatbot
git remote add neworigin https://github.com/your-username/new-repo.git
git push -u neworigin main
```

Or change the existing origin:

```bash
git remote set-url origin https://github.com/your-username/new-repo.git
git push -u origin main
```

### License

See `LICENSE` for licensing details.