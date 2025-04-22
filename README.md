# Stock Trading & Analysis System

This is a Flask-based web application designed to provide a platform for simulated stock trading and data analysis. It integrates user management, stock data display, simulated trading (market and limit orders), background order processing, Monte Carlo simulation, and an AI investment assistant powered by Google Gemini.

## 1. Project Overview

### 1.1 Summary

This system simulates a real stock trading environment, allowing users to register accounts, manage virtual funds, view real-time and historical stock data, execute buy/sell orders, and utilize data analysis tools and an AI assistant for investment decision support. The system includes user-facing and administrative interfaces, where administrators handle fund operations review and system management.

### 1.2 Technology Stack

*   **Backend Framework**: Flask 2.2.3
*   **Database ORM**: Flask-SQLAlchemy 3.0.3, SQLAlchemy 2.0.7
*   **Database**: MySQL (using PyMySQL 1.0.3 or mysql-connector-python 8.0.33)
*   **Database Migration**: Flask-Migrate 4.0.4
*   **User Authentication**: Flask-Login 0.6.2
*   **Web Server (Development)**: Werkzeug 2.2.3
*   **Frontend**: HTML, CSS, JavaScript, Bootstrap, Chart.js
*   **Data Retrieval**: yfinance 0.2.20 (Stock data)
*   **Data Processing**: Pandas 2.0.1, NumPy 1.24.3
*   **AI Assistant**: Google Generative AI (`google-generativeai` library)
*   **Background Tasks**: Standard Python `threading` (for order processor)
*   **CLI Output Formatting**: Rich (`rich` library)
*   **Dependency Management**: pip, `requirements.txt`
*   **Version Control**: Git

## 2. Quick Start Guide

### 2.1 Prerequisites

*   **Python**: 3.8 or higher
*   **MySQL**: 5.7 or higher
*   **Git**: For cloning the project repository
*   **pip**: Python package manager (usually installed with Python)
*   **Operating System**: Linux, macOS, or Windows

### 2.2 Configuration

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd <project_directory>
    ```

2.  **Create and Activate Virtual Environment**:
    ```bash
    # Create virtual environment
    python -m venv flask_env

    # Activate virtual environment (Linux/macOS)
    source flask_env/bin/activate
    # Or (Windows)
    # .\flask_env\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Database**:
    *   Ensure your MySQL service is running.
    *   Create a new database (e.g., `stock_data_v1`):
        ```sql
        CREATE DATABASE stock_data_v1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        ```
    *   Open the `config.py` file.
    *   Modify `SQLALCHEMY_DATABASE_URI` with your MySQL connection string, format:
        ```python
        # Example: mysql+pymysql://<username>:<password>@<hostname>:<port>/<database_name>
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:your_password@localhost:3306/stock_data_v1'
        ```
        *Note: Use `mysql+mysqlconnector://` prefix if using `mysql-connector-python`.*
    *   (Optional) Update the `DB_CONFIG` dictionary if parts of the project use it directly.

5.  **Configure API Keys**:
    *   **Google Gemini API**:
        *   Get an API key from [Google AI Studio](https://ai.google.dev/).
        *   Set the `GEMINI_API_KEY` value in `config.py` or set the environment variable `GEMINI_API_KEY`.
    *   **(Optional) Alpha Vantage API**:
        *   *Note: The project currently uses `yfinance` for stock data. If you intend to integrate Alpha Vantage directly, get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).*
        *   *If used, set `ALPHA_VANTAGE_API_KEY` in `config.py` or as an environment variable.*

6.  **Database Initialization & Migration**:
    *   First-time setup requires initializing the database schema. Flask-Migrate manages schema changes.
    *   Ensure the Flask app is discoverable (usually by setting the `FLASK_APP=app.py` environment variable).
    *   Run the following commands to generate and apply database migrations:
        ```bash
        # Set Flask app entry point (if not already set)
        export FLASK_APP=app.py # Linux/macOS
        # set FLASK_APP=app.py # Windows

        # Initialize migration environment (only needed once)
        flask db init

        # Generate initial migration script
        flask db migrate -m "Initial migration."

        # Apply migrations to the database
        flask db upgrade
        ```
    *   *Note: The `init_db(app)` function called in `app.py` handles table creation and potentially initial data seeding (like the default admin). `flask db upgrade` executes these creation operations.*

### 2.3 Running & Debugging

*   **Start Development Server**:
    ```bash
    flask run --debug
    ```
    *   The `--debug` flag enables debug mode, providing detailed error messages and auto-reloading on code changes.
    *   The application runs on `http://127.0.0.1:5003` by default (port defined in `config.py`).

*   **Accessing the Application**:
    *   Open your browser to `http://127.0.0.1:5003/`.
    *   Default admin account: username `admin`, password `admin123secure` (or as set in `config.py`/environment variables).
    *   Regular users need to register first.

*   **Background Tasks**:
    *   The limit order processor (`tasks/order_processor.py`) runs automatically in a background thread when the application starts.
    *   It attempts to stop gracefully upon application shutdown (`atexit`).

## 3. Core Features & Module Design

### 3.1 Main Features

*   **User Authentication**: Registration, login, logout for regular users; admin login.
*   **Account Management**: View account balance (available, frozen, total), simulate deposits/withdrawals (requires admin approval).
*   **Stock Market Data**: View stock list, search stocks, display real-time/near-real-time prices (`yfinance`), historical K-line charts (`yfinance`).
*   **Simulated Trading**: Create market and limit orders (buy/sell), view order history, cancel pending orders.
*   **Portfolio Management**: View current holdings, quantity, average cost, total cost, current market value, and profit/loss.
*   **Data Analysis**:
    *   Calculation and display of technical indicators based on historical data (integrated into charting libraries or backend calculations).
    *   Monte Carlo simulation to predict future stock price trends.
    *   Risk assessment (potential implementation in `utils/stock_data.py`).
*   **AI Assistant**: Interact with the Gemini AI model via `google-generativeai` for market analysis, stock information, or investment advice.
*   **Admin Functions**: User management, fund approval (deposit/withdrawal), order management (view, manual execution/rejection), data management.
*   **Background Order Processing**: Periodically checks market prices to execute pending limit orders that meet price conditions.

### 3.2 Module Logic & Technical Implementation

*   **Application Entry Point (`app.py`)**:
    *   Uses the `create_app()` factory pattern to create and configure the Flask application instance.
    *   Loads configuration from `config.py`.
    *   Initializes SQLAlchemy (`models.init_db`) and Flask-Migrate.
    *   Initializes Flask-Login (`auth.init_login_manager`).
    *   Registers blueprints (`routes.register_routes`) to modularize routes for different features.
    *   Starts the background order processor (`tasks.order_processor.start_order_processor`) and registers a cleanup function via `atexit`.
    *   Defines global error handlers (e.g., for Jinja2 undefined errors).
    *   Registers custom Jinja2 template filters (`safe_round`, `format_datetime`).
    *   Defines the root route `/`, redirecting to the appropriate dashboard or login page based on login status and role.

*   **Configuration (`config.py`)**:
    *   Stores application secrets, database URI, API keys, default admin credentials, stock ticker lists, order processing interval, etc.
    *   Using environment variables to override sensitive configurations is recommended best practice.

*   **Data Models (`models/`)**:
    *   Defines SQLAlchemy models for database tables (User, Admin, Order, Transaction, AccountBalance, FundTransaction, Portfolio, MarketData, etc.).
    *   The `init_db` function in `__init__.py` handles database initialization logic, including table creation and potential initial data population.

*   **Routes (`routes/`)**:
    *   Organizes blueprints by functionality (Auth, User, Admin, Core).
    *   Python files within each blueprint define specific view functions and their corresponding URL rules.
    *   Handles HTTP requests, calls service/utility functions, interacts with models, and renders HTML templates or returns JSON API responses.
    *   User routes (`user/`) contain endpoints for accounts, orders, stock data, analysis, AI assistant, etc.
    *   Admin routes (`admin/`) contain endpoints for administrative functions.
    *   Authentication routes (`auth/`) handle login, registration, logout.

*   **Background Tasks (`tasks/order_processor.py`)**:
    *   Implemented using Python's `threading` module.
    *   Periodically (controlled by `config.ORDER_CHECK_INTERVAL`) queries pending limit orders.
    *   Fetches current market prices for relevant stocks.
    *   Matches and executes orders meeting price criteria, updating order status and user balances/portfolios.
    *   Includes logic for starting and stopping the processor.

*   **Utility Functions (`utils/`)**:
    *   Encapsulates reusable logic, such as:
        *   `stock_data.py`: Fetching and processing stock data (`yfinance`).
        *   `monte_carlo.py`: Performing Monte Carlo simulation calculations.
        *   `chat_ai.py`: Interacting with the Gemini API (`google-generativeai`).
        *   `number_utils.py`: Safe number formatting.

*   **Frontend (`static/`, `templates/`)**:
    *   `templates/`: Uses Jinja2 templating engine to render dynamic HTML pages. Includes base layout (`layout.html`) and page templates for various features.
    *   `static/`: Stores static assets like CSS stylesheets, JavaScript files, and images.
        *   CSS organized by page or module.
        *   JavaScript handles frontend interactions, such as chart drawing (Chart.js), form submissions (AJAX), and UI updates.

### 3.3 Detailed Project Structure

```
/
├── .git/                       # Git version control directory
├── .gitignore                  # Git ignore configuration file
├── .cursor/                    # Cursor IDE configuration directory
├── .DS_Store                   # macOS folder attributes file (if on macOS)
├── __pycache__/                # Python compiled cache
├── flask_env/                  # Python virtual environment directory
├── logs/                       # Log file directory
│   ├── app.log                 # Application log file
│   └── error.log               # Error log file
├── test/                       # Unit and integration test directory
│   ├── __init__.py             # Test package initialization
│   ├── test_auth.py            # Authentication module tests
│   ├── test_models.py          # Data model tests
│   ├── test_routes.py          # Route module tests
│   └── test_utils.py           # Utility function tests
├── app.py                      # Application entry point
├── config.py                   # Configuration file
├── requirements.txt            # Project dependency list
├── README.md                   # Project documentation (this file)
├── auth/                       # Core authentication logic
│   ├── __init__.py             # Initialization file
│   └── login_manager.py        # Flask-Login configuration
├── models/                     # Database models
│   ├── __init__.py             # Model initialization
│   ├── user.py                 # User model
│   ├── admin.py                # Admin model
│   ├── trade.py                # Trading models (Order, Portfolio)
│   ├── finance.py              # Financial models (Account, Transaction)
│   └── market.py               # Market data model
├── routes/                     # Route modules
│   ├── __init__.py             # Route registration
│   ├── core/                   # Core routes (e.g., home, about)
│   │   ├── __init__.py         # Core blueprint initialization
│   │   └── welcome.py          # Welcome page routes
│   ├── auth/                   # Authentication routes
│   │   ├── __init__.py         # Authentication blueprint initialization
│   │   ├── login.py            # Login routes
│   │   ├── register.py         # Registration routes
│   │   └── admin_login.py      # Admin login routes
│   ├── user/                   # User feature routes
│   │   ├── __init__.py         # User blueprint initialization
│   │   ├── dashboard.py        # User dashboard routes
│   │   ├── account.py          # Account management routes
│   │   ├── order.py            # Order management routes
│   │   ├── stock.py            # Stock data routes
│   │   ├── monte_carlo.py      # Monte Carlo simulation routes
│   │   └── ai_assistant.py     # AI Assistant routes
│   └── admin/                  # Admin feature routes
│       ├── __init__.py         # Admin blueprint initialization
│       ├── dashboard.py        # Admin dashboard routes
│       ├── user_manage.py      # User management routes
│       ├── fund_manage.py      # Fund management routes
│       ├── order_manage.py     # Order management routes
│       └── data_manage.py      # Data management routes
├── static/                     # Static assets
│   ├── .DS_Store               # macOS folder attributes file
│   ├── chenyu.png              # Team member photo
│   ├── zhenghaowen.png         # Team member photo
│   ├── xumingyang.png          # Team member photo
│   ├── liaoqiyue.png           # Team member photo
│   ├── chenguanqi.png          # Team member photo
│   ├── frankie.png             # Team member photo
│   ├── css/                    # CSS stylesheets
│   │   ├── auth/               # Authentication styles
│   │   │   ├── auth.css        # Authentication common styles
│   │   │   └── auth_style.css  # Authentication additional styles
│   │   ├── admin/              # Admin styles
│   │   │   ├── admin_base.css              # Admin base styles
│   │   │   ├── admin_common.css            # Admin common styles
│   │   │   ├── admin_dashboard.css         # Admin dashboard styles
│   │   │   ├── admin_deposits.css          # Admin deposits styles
│   │   │   ├── admin_edit_user.css         # Admin edit user styles
│   │   │   ├── admin_fund_transactions.css # Admin fund transactions styles
│   │   │   ├── admin_layout.css            # Admin layout styles
│   │   │   ├── admin_orders.css            # Admin orders styles
│   │   │   ├── admin_user_detail.css       # Admin user detail styles
│   │   │   ├── admin_users.css             # Admin users list styles
│   │   │   └── admin_withdrawals.css       # Admin withdrawals styles
│   │   └── user/               # User styles
│   │       ├── about.css                   # About page styles
│   │       ├── account.css                 # Account page styles
│   │       ├── ai_assistant.css            # AI Assistant page styles
│   │       ├── main.css                    # Main user styles
│   │       ├── privacy.css                 # Privacy page styles
│   │       ├── stock.css                   # Stock page styles
│   │       ├── stock_analysis.css          # Stock analysis page styles
│   │       └── stock_chart.css             # Stock chart page styles
│   └── js/                     # JavaScript files
│       ├── .DS_Store           # macOS folder attributes file
│       ├── admin/              # Admin scripts
│       │   ├── admin_layout.js            # Admin layout scripts
│   │   │   ├── admin_users.js             # Admin users list scripts
│   │   │   ├── deposit_withdrawal.js      # Deposit/withdrawal management scripts
│   │   │   ├── deposits.js                # Deposits management scripts
│   │   │   ├── navigation.js              # Admin navigation scripts
│   │   │   └── withdrawals.js             # Withdrawals management scripts
│   │   ├── auth/               # Authentication scripts
│   │   │   ├── adminLogin.js              # Admin login scripts
│   │   │   ├── auth_script.js             # Authentication common scripts
│   │   │   ├── login.js                   # User login scripts
│   │   │   └── register.js                # User registration scripts
│   │   └── user/               # User scripts
│   │       ├── account.js                 # Account management scripts
│   │       ├── ai_assistant.js            # AI assistant interaction scripts
│   │       ├── navigation.js              # User navigation scripts
│   │       ├── stock_analysis.js          # Stock analysis scripts
│   │       ├── stock_chart.js             # Stock chart scripts
│   │       └── stock_chart_extra.js       # Additional stock chart functionality
├── templates/                  # Jinja2 HTML templates
│   ├── about.html              # About page template
│   ├── privacy.html            # Privacy policy template
│   ├── error.html              # Error page template
│   ├── admin/                  # Admin templates
│   │   ├── dashboard.html              # Admin dashboard template
│   │   ├── deposit_withdrawal.html     # Deposit/withdrawal management template
│   │   ├── deposits.html               # Deposits management template
│   │   ├── layout.html                 # Admin layout template
│   │   ├── order_management.html       # Order management template
│   │   ├── transaction_history.html    # Transaction history template
│   │   ├── user_detail.html            # User detail template
│   │   ├── user_edit.html              # User edit template
│   │   ├── user_management.html        # User management template
│   │   └── withdrawals.html            # Withdrawals management template
│   ├── auth/                   # Authentication templates
│   │   ├── admin_login.html            # Admin login template
│   │   ├── login.html                  # User login template
│   │   └── register.html               # User registration template
│   └── user/                   # User templates
│       ├── account.html                # Account management template
│       ├── ai_assistant.html           # AI assistant template
│       ├── layout.html                 # User layout template
│       ├── stock_analysis.html         # Stock analysis template
│       └── stock_chart.html            # Stock chart template
└── tasks/                      # Background tasks
    ├── __init__.py             # Task initialization
    └── order_processor.py      # Limit order processing task
```

## 4. Database Design & API Documentation

### 4.1 Database Schema

The system uses a MySQL database (named `stock_data_v1`) with the following table structure:

#### User-Related Tables

##### Users Table (`user`)
- `user_id`: Integer, Primary Key, Auto-increment
- `user_name`: String(64), Unique, Not Null
- `user_email`: String(120), Unique, Not Null
- `user_password`: String(128), Not Null (stores password hash)
- `created_at`: DateTime, Default current time

##### Admin Table (`admin`)
- `admin_id`: Integer, Primary Key, Auto-increment
- `admin_name`: String(64), Unique, Not Null
- `admin_password`: String(128), Not Null (stores password hash)

#### Finance-Related Tables

##### Account Balance Table (`account_balance`)
- `balance_id`: Integer, Primary Key, Auto-increment
- `user_id`: Integer, Foreign Key(user.user_id), Unique, Not Null
- `available_balance`: Decimal(15,2), Not Null, Default 0.00
- `frozen_balance`: Decimal(15,2), Not Null, Default 0.00
- `total_balance`: Decimal(15,2), Not Null, Default 0.00 (typically available + frozen)
- `updated_at`: DateTime, Default current time, Updated on change

##### Fund Transaction Table (`fund_transaction`)
- `transaction_id`: Integer, Primary Key, Auto-increment
- `user_id`: Integer, Foreign Key(user.user_id), Not Null
- `transaction_type`: String(10), Not Null ('deposit', 'withdrawal')
- `amount`: Decimal(15,2), Not Null
- `status`: String(10), Not Null ('pending', 'approved', 'rejected'), Default 'pending', Indexed
- `created_at`: DateTime, Default current time, Indexed
- `updated_at`: DateTime, Default current time, Updated on change
- `remark`: String(255), Nullable (e.g., rejection reason)
- `operator_id`: Integer, Foreign Key(admin.admin_id), Nullable (approving admin)

#### Trading-Related Tables

##### Orders Table (`orders`)
- `order_id`: Integer, Primary Key, Auto-increment
- `user_id`: Integer, Foreign Key(user.user_id), Not Null, Indexed
- `ticker`: String(10), Not Null, Indexed
- `order_type`: String(4), Not Null ('buy', 'sell'), Indexed
- `order_execution_type`: String(6), Not Null ('market', 'limit'), Indexed
- `order_price`: Decimal(10,2), Nullable (null for market orders)
- `order_quantity`: Integer, Not Null
- `filled_quantity`: Integer, Not Null, Default 0 (filled amount)
- `order_status`: String(20), Not Null ('pending', 'filled', 'partially_filled', 'cancelled', 'rejected'), Default 'pending', Indexed
- `created_at`: DateTime, Default current time, Indexed
- `updated_at`: DateTime, Default current time, Updated on change
- `executed_at`: DateTime, Nullable (time of complete execution)
- `remark`: Text, Nullable

##### Transaction Records Table (`transaction`)
- `transaction_id`: Integer, Primary Key, Auto-increment
- `order_id`: Integer, Foreign Key(orders.order_id), Not Null, Indexed
- `user_id`: Integer, Foreign Key(user.user_id), Not Null, Indexed
- `ticker`: String(10), Not Null
- `transaction_type`: String(4), Not Null ('buy', 'sell')
- `transaction_price`: Decimal(10,2), Not Null
- `transaction_quantity`: Integer, Not Null
- `transaction_amount`: Decimal(15,2), Not Null (price * quantity)
- `transaction_time`: DateTime, Not Null, Default current time, Indexed
- `commission`: Decimal(10,2), Nullable (transaction fee)

##### Portfolio Table (`portfolio`)
- `id`: Integer, Primary Key, Auto-increment
- `user_id`: Integer, Foreign Key(user.user_id), Not Null
- `ticker`: String(10), Not Null
- `quantity`: Integer, Not Null
- `average_price`: Decimal(10,2), Not Null
- `total_cost`: Decimal(15,2), Not Null
- `last_updated`: DateTime, Default current time, Updated on change
- Constraint: `UNIQUE(user_id, ticker)`

#### Market Data Tables

##### Market Data Table (`market_data`)
- `ticker`: String(10), Part of Primary Key
- `date`: Date, Part of Primary Key
- `open`: Decimal(10,2)
- `high`: Decimal(10,2)
- `low`: Decimal(10,2)
- `close`: Decimal(10,2)
- `adj_close`: Decimal(10,2) (adjusted close price)
- `volume`: BigInt
- `data_collected_at`: DateTime, Default current time
- Primary Key: `PRIMARY KEY (ticker, date)`

##### Fundamental Data Table (`fundamental_data`)
- `ticker`: String(10), Part of Primary Key
- `date`: Date, Part of Primary Key (typically financial report date)
- `market_cap`: BigInt, Nullable
- `pe_ratio`: Decimal(10,2), Nullable
- `pb_ratio`: Decimal(10,2), Nullable
- `dividend_yield`: Decimal(10,2), Nullable
- `revenue`: BigInt, Nullable
- `net_income`: BigInt, Nullable
- `eps`: Decimal(10,2), Nullable (earnings per share)
- `data_collected_at`: DateTime, Default current time
- Primary Key: `PRIMARY KEY (ticker, date)`

#### Database Relationship Diagram (Text Format)

```text
User-Related
└── user (Users Table)
    ├── 1:1 account_balance (Account Balance Table)
    ├── 1:N fund_transaction (Fund Transaction Table)
    ├── 1:N orders (Orders Table)
    ├── 1:N transaction (Transaction Records Table)
    └── 1:N portfolio (Portfolio Table)

Admin-Related
└── admin (Admin Table)
    └── 1:N fund_transaction (Fund Transaction Table, as operator_id)

Trading-Related
├── orders (Orders Table)
│   └── 1:N transaction (Transaction Records Table) (one order may be filled in multiple transactions)
└── portfolio (Portfolio Table)
    └── N:1 user (Users Table)

Market Data-Related (typically no direct foreign key relationships with user/trading data)
├── market_data (Market Data Table)
│   └── (ticker, date) compound primary key
└── fundamental_data (Fundamental Data Table)
    └── (ticker, date) compound primary key
```

### 4.2 API Documentation

The application provides the following API endpoints:

#### Core Routes

*   **GET /**: Root path, redirects based on login status.
*   **GET /about**: About page.
*   **GET /privacy**: Privacy policy page.
*   **GET /logout**: Logout operation (redirects to `auth.logout`).

#### Authentication Routes (`/auth`)

*   **GET /**: Authentication blueprint root (typically redirects).
*   **GET, POST /login**: User login.
*   **GET, POST /register**: User registration.
*   **GET, POST /admin-login**: Admin login.
*   **GET /logout**: User/admin logout.

#### User Routes (`/user`)

*   **GET /dashboard**: User dashboard (typically redirects to `/user/stock_chart`).
*   **GET /account**: User account page.
*   **POST /api/deposit**: User deposit API.
    *   Request Body: `{ "amount": float }`
    *   Response: `{ "success": boolean, "message": string, "transaction_id": integer }`

*   **POST /api/withdraw**: User withdrawal API.
    *   Request Body: `{ "amount": float }`
    *   Response: `{ "success": boolean, "message": string, "transaction_id": integer }`

*   **GET /api/orders**: Get user orders list API (supports pagination and filtering).
    *   Query Parameters:
        *   `page`: integer (page number)
        *   `limit`: integer (items per page)
        *   `status`: string (filter by status)
        *   `ticker`: string (filter by ticker)
        *   `type`: string (filter by order type)
    *   Response: `{ "success": boolean, "orders": array, "pagination": object }`

*   **POST /api/create_order**: Create trading order API (market/limit).
    *   Request Body:
        ```json
        {
          "ticker": "string",
          "order_type": "string (buy/sell)",
          "execution_type": "string (market/limit)",
          "quantity": integer,
          "price": float (nullable for market orders)
        }
        ```
    *   Response: `{ "success": boolean, "message": string, "order_id": integer }`

*   **POST /orders/<order_id>/cancel**: Cancel order API.
    *   URL Parameters: `order_id`: integer
    *   Response: `{ "success": boolean, "message": string }`

*   **GET /stock_chart**: Stock chart and trading page.
*   **GET /stock_analysis**: Stock analysis page.

*   **POST /api/stock_analysis**: Stock risk analysis API.
    *   Request Body: `{ "ticker": string, "window": integer }`
    *   Response: `{ "success": boolean, "data": object, "metrics": object }`

*   **GET /api/market_data**: Get stock historical market data API.
    *   Query Parameters:
        *   `ticker`: string (stock symbol)
        *   `period`: string (e.g., "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max")
    *   Response: `{ "success": boolean, "data": array }`

*   **GET /api/fundamental_data**: Get stock fundamental data API.
    *   Query Parameters: `ticker`: string (stock symbol)
    *   Response: `{ "success": boolean, "data": object }`

*   **GET /api/balance_sheet**: Get balance sheet API.
    *   Query Parameters: `ticker`: string (stock symbol)
    *   Response: `{ "success": boolean, "data": object }`

*   **GET /api/income_statement**: Get income statement API.
    *   Query Parameters: `ticker`: string (stock symbol)
    *   Response: `{ "success": boolean, "data": object }`

*   **GET /api/real_time_stock_data**: Get real-time/near-real-time quotes API.
    *   Query Parameters: `ticker`: string (stock symbol)
    *   Response: `{ "success": boolean, "data": object, "last_updated": string }`

*   **GET /api/monte-carlo/<ticker>**: Get Monte Carlo simulation results API.
    *   URL Parameters: `ticker`: string (stock symbol)
    *   Query Parameters:
        *   `days`: integer (prediction days)
        *   `simulations`: integer (number of simulations)
    *   Response: `{ "success": boolean, "predictions": array, "statistics": object }`

*   **GET /ai_assistant**: AI assistant page.

*   **POST /api/chat**: Chat with AI assistant API.
    *   Request Body: `{ "message": string }`
    *   Response: `{ "success": boolean, "response": string }`

#### Admin Routes (`/admin`)

*   **GET /, /dashboard**: Admin dashboard.
*   **GET /fund-transactions**: View fund transactions list (deposits/withdrawals).
*   **GET /deposits**: View deposits list (filtered view of `/fund-transactions`).
*   **GET /withdrawals**: View withdrawals list (filtered view of `/fund-transactions`).

*   **POST /fund-transactions/<transaction_id>/approve**: Approve fund transaction API.
    *   URL Parameters: `transaction_id`: integer
    *   Response: `{ "success": boolean, "message": string }`

*   **POST /fund-transactions/<transaction_id>/reject**: Reject fund transaction API.
    *   URL Parameters: `transaction_id`: integer
    *   Request Body: `{ "reason": string }`
    *   Response: `{ "success": boolean, "message": string }`

*   **GET /orders**: View all user orders list.

*   **POST /orders/<order_id>/execute**: Manually execute order API.
    *   URL Parameters: `order_id`: integer
    *   Response: `{ "success": boolean, "message": string }`

*   **POST /orders/<order_id>/reject**: Manually reject order API.
    *   URL Parameters: `order_id`: integer
    *   Request Body: `{ "reason": string }`
    *   Response: `{ "success": boolean, "message": string }`

*   **GET /user_management**: User management page.

## 5. Usage Notes

*   **Database**: Ensure your MySQL server is running before starting the application. The required tables will be created by `flask db upgrade`.
*   **API Keys**: The application requires a Google Gemini API key to be configured for the AI assistant feature to work.
*   **Background Worker**: The order processor runs in a separate thread. Check application logs (`logs/app.log`) for its status or errors.
*   **Development Mode**: Running with `flask run --debug` provides helpful debugging information but is not suitable for production.

## 6. Future Enhancements and System Improvement Directions

Compared to mature commercial stock trading systems, this system still has significant room for improvement in terms of functional depth, system performance, and robustness. Here are some key enhancement directions aimed at bringing the system closer to professional standards:

### 6.1 Functional Enhancements

*   **Advanced Order Types**:
    *   **Stop-Loss** and **Take-Profit Orders**: Automatically trigger sell/buy orders when preset loss or profit prices are reached.
    *   **Trailing Stop-Loss Orders**: Stop-loss price dynamically adjusts as the market price moves favorably.
    *   **Iceberg Orders**: Split large orders into multiple smaller ones to hide the true trading intention.
*   **Extended Data Analysis**:
    *   **More Technical Indicators**: Integrate a broader library of technical analysis indicators (e.g., TA-Lib) and allow users to customize indicator parameters.
    *   **Fundamental Analysis Integration**: Deeper integration of financial statement data (balance sheet, income statement, cash flow statement), calculation of key financial ratios, and visual presentation.
    *   **Event-Driven Analysis**: Integrate financial news, company announcements, earnings release dates, and other event information to analyze their potential impact on stock prices.
    *   **Backtesting System**: Provide historical data backtesting functionality to allow users to test the effectiveness of trading strategies.
*   **Margin Trading & Short Selling**: Simulate margin buying and short selling functions, increasing the complexity of trading strategies (requires careful risk control design).
*   **Options and Derivatives Trading**: Extend the system to support simulated trading of options, futures, and other derivatives.
*   **Personalized User Experience**:
    *   **Customizable Dashboard**: Allow users to customize layouts, watchlists, and chart settings.
    *   **Advanced Alert System**: Set complex alert conditions based on price, volume, technical indicators, news events, etc.

### 6.2 High Concurrency, High Availability, and Performance Optimization

Mature trading systems need to handle massive concurrent requests while ensuring low latency and high availability.

*   **Market Data System Optimization**:
    *   **Market Data Push**: Use **WebSocket** or **Server-Sent Events (SSE)** instead of polling (`/api/real_time_stock_data`) to achieve real-time, low-latency push of market data.
    *   **Market Data Source**: Connect to more professional real-time market data sources to reduce reliance on libraries like `yfinance` which may have higher latency or request limits.
*   **Trade Matching Engine**:
    *   **In-Memory Matching**: Move the order book and matching logic to in-memory processing to significantly increase order processing speed. The current background thread (`tasks/order_processor.py`) only handles limit orders and is relatively inefficient.
    *   **Distributed Matching**: For extremely high concurrency scenarios, consider distributing the matching logic for different stocks or markets across multiple service nodes.
*   **Message Queue**:
    *   **Asynchronous Decoupling**: Use message queues like **Redis Streams**, **Kafka**, or **RabbitMQ** to handle order submissions, status updates, trade notifications, etc. For example, after a user submits an order, the request returns quickly, and the order processing logic is placed in the queue for asynchronous execution, improving system responsiveness and throughput.
    *   **Peak Shaving**: During market open or periods of high volatility, message queues can buffer instantaneous high concurrency requests, preventing system overload.
*   **Caching**:
    *   **Data Caching**: Use **Redis** or **Memcached** to cache frequently accessed data, such as user information, basic stock information, historical K-line data (especially for less frequently changing periods), and calculated technical indicators, to reduce database pressure.
    *   **Market Data Snapshot Caching**: Cache the latest market data snapshots for use by features with less stringent real-time requirements (e.g., portfolio valuation).
*   **Database Optimization**:
    *   **Read/Write Splitting**: Implement read/write splitting for the database, directing read-intensive operations (like querying market data, historical orders) to read-only replicas.
    *   **Database Sharding**: For scenarios with massive user numbers and transaction volumes, consider sharding core tables like orders, transaction records, and portfolio holdings based on user ID or time range.
    *   **Index Optimization**: Continuously monitor slow queries and optimize database indexes.
*   **High Availability Deployment**:
    *   **Load Balancing**: Deploy a load balancer in front of multiple application server instances.
    *   **Service Redundancy**: Deploy multiple instances of critical services (e.g., market data service, trading service, user service) to achieve failover.
    *   **Database High Availability**: Use master-slave replication, clusters, etc., to ensure high availability of database services.

### 6.3 Security Enhancements

Security is paramount for financial systems.

*   **Authentication and Authorization**:
    *   **Two-Factor Authentication (2FA)**: Add 2FA for user login and sensitive operations (like withdrawals, password changes).
    *   **Fine-Grained Access Control**: Implement more granular permission management for admin and user operations.
    *   **API Authentication**: Enforce strict authentication and authorization checks (e.g., using JWT or OAuth2) for all API endpoints.
*   **Transaction Security**:
    *   **Replay Attack Prevention**: Implement mechanisms like nonces or timestamps in API requests.
    *   **Transaction Risk Control**: Implement simple transaction risk control rules, such as maximum order amount per transaction, maximum daily transaction volume, price anomaly limits, etc.
    *   **Fund Password**: Set up a separate fund password for critical fund operations like withdrawals.
*   **Data Security**:
    *   **Sensitive Data Encryption**: Encrypt sensitive data stored in the database, such as passwords, API keys, and user personal information.
    *   **Transport Encryption**: Enforce HTTPS sitewide.
    *   **Log Auditing**: Record logs for all critical operations for auditing and tracking purposes.
*   **Infrastructure Security**:
    *   **Web Application Firewall (WAF)**: Deploy a WAF to defend against common web attacks (SQL injection, XSS, etc.).
    *   **Regular Security Audits and Penetration Testing**: Conduct regular code audits and security testing.

### 6.4 Architectural Evolution

*   **Microservices**: Consider breaking down the system into smaller, independently deployable services, such as user service, market data service, order service, account service, etc., to improve maintainability, scalability, and team collaboration efficiency.
*   **Containerization and Orchestration**: Use **Docker** for containerized deployment and leverage **Kubernetes (K8s)** for container orchestration to simplify deployment, scaling, and management processes.
