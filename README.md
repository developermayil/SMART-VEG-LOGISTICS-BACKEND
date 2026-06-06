# Smart Veg Logistics – Python/FastAPI Backend

This is the full Python conversion of the original Node.js/Express backend.  
**Framework: FastAPI** (async, Pydantic v2, auto-generated Swagger docs)

## Stack

| Layer       | Tech                                     |
|-------------|------------------------------------------|
| Framework   | FastAPI                                  |
| Database    | MongoDB Atlas via Motor (async driver)   |
| ODM         | Beanie (Pydantic v2-based Mongo ODM)     |
| Auth        | python-jose (JWT) + passlib (bcrypt)     |
| Rate limit  | slowapi                                  |
| Server      | Uvicorn                                  |

## Project Structure

```
app/
├── main.py              # FastAPI app, CORS, rate limiter, routers
├── db/database.py       # MongoDB connection + Beanie init
├── middleware/auth.py   # JWT Bearer dependency
├── models/              # Beanie ODM documents
│   ├── user.py
│   ├── farmer.py
│   ├── customer.py
│   ├── order.py
│   ├── stock.py
│   ├── delivery.py
│   └── vehicle.py
└── routes/              # FastAPI routers (one per resource)
    ├── auth.py
    ├── dashboard.py
    ├── farmers.py
    ├── stocks.py
    ├── vehicles.py
    ├── deliveries.py
    ├── customers.py
    └── orders.py
```

## Setup

```bash
# 1. Create & activate virtualenv
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env – set MONGODB_URI and JWT_SECRET

# 4. Run development server
uvicorn app.main:app --reload --port 5000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 4
```

## API Docs (auto-generated)

Once running, open:
- Swagger UI → http://localhost:5000/docs
- ReDoc     → http://localhost:5000/redoc

## API Endpoints

| Method | Path                            | Auth | Description               |
|--------|---------------------------------|------|---------------------------|
| POST   | /api/auth/login                 | –    | Login                     |
| POST   | /api/auth/register              | –    | Register admin            |
| GET    | /api/auth/profile               | ✓    | Get profile               |
| GET    | /api/dashboard                  | ✓    | Dashboard stats           |
| GET    | /api/farmers                    | ✓    | List farmers              |
| POST   | /api/farmers                    | ✓    | Create farmer             |
| GET    | /api/farmers/{id}               | ✓    | Get farmer + supplies     |
| PUT    | /api/farmers/{id}               | ✓    | Update farmer             |
| DELETE | /api/farmers/{id}               | ✓    | Delete farmer             |
| GET    | /api/stocks                     | ✓    | List stocks               |
| GET    | /api/stocks/summary             | ✓    | Stock summary stats       |
| POST   | /api/stocks                     | ✓    | Add stock                 |
| PUT    | /api/stocks/{id}                | ✓    | Update stock              |
| DELETE | /api/stocks/{id}                | ✓    | Delete stock              |
| GET    | /api/vehicles                   | ✓    | List vehicles             |
| GET    | /api/vehicles/available         | ✓    | Available vehicles        |
| POST   | /api/vehicles                   | ✓    | Add vehicle               |
| PUT    | /api/vehicles/{id}              | ✓    | Update vehicle            |
| DELETE | /api/vehicles/{id}              | ✓    | Delete vehicle            |
| GET    | /api/deliveries                 | ✓    | List deliveries           |
| POST   | /api/deliveries                 | ✓    | Create delivery           |
| GET    | /api/deliveries/{id}            | ✓    | Get delivery              |
| PATCH  | /api/deliveries/{id}/status     | ✓    | Update delivery status    |
| DELETE | /api/deliveries/{id}            | ✓    | Delete delivery           |
| GET    | /api/customers                  | ✓    | List customers            |
| POST   | /api/customers                  | ✓    | Create customer           |
| PUT    | /api/customers/{id}             | ✓    | Update customer           |
| DELETE | /api/customers/{id}             | ✓    | Delete customer           |
| GET    | /api/orders                     | ✓    | List orders               |
| POST   | /api/orders                     | ✓    | Create order              |
| GET    | /api/orders/{id}                | ✓    | Get order                 |
| PUT    | /api/orders/{id}                | ✓    | Update order              |
| PATCH  | /api/orders/{id}/status         | ✓    | Update order status       |
| DELETE | /api/orders/{id}                | ✓    | Delete order              |
| GET    | /api/orders/customer/{id}       | ✓    | Orders by customer        |
