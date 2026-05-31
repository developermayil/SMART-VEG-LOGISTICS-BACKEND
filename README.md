# Smart Veg Logistics — Backend API

Express.js + SQL Server REST API for managing vegetable logistics from Tamil Nadu farmers to Kerala markets.

## Setup

```bash
cd backend
npm install
cp .env.example .env
# Edit .env with your SQL Server credentials
npm run dev
```

## API Endpoints

### Auth
| Method | Route | Description |
|--------|-------|-------------|
| POST | /api/auth/login | Admin login |
| POST | /api/auth/register | Register admin |
| GET | /api/auth/profile | Get profile (🔐) |

### Dashboard
| Method | Route | Description |
|--------|-------|-------------|
| GET | /api/dashboard/stats | Dashboard stats (🔐) |

### Stocks
| Method | Route | Description |
|--------|-------|-------------|
| GET | /api/stocks | List all stocks (🔐) |
| GET | /api/stocks/summary | Stock summary (🔐) |
| GET | /api/stocks/:id | Get stock (🔐) |
| POST | /api/stocks | Add stock (🔐) |
| PUT | /api/stocks/:id | Update stock (🔐) |
| DELETE | /api/stocks/:id | Delete stock (🔐) |

### Farmers
| Method | Route | Description |
|--------|-------|-------------|
| GET | /api/farmers | List all farmers (🔐) |
| GET | /api/farmers/:id | Get farmer + supplies (🔐) |
| POST | /api/farmers | Register farmer (🔐) |
| PUT | /api/farmers/:id | Update farmer (🔐) |
| DELETE | /api/farmers/:id | Delete farmer (🔐) |

### Vehicles
| Method | Route | Description |
|--------|-------|-------------|
| GET | /api/vehicles | List all vehicles (🔐) |
| GET | /api/vehicles/available | Available vehicles (🔐) |
| GET | /api/vehicles/:id | Get vehicle (🔐) |
| POST | /api/vehicles | Add vehicle (🔐) |
| PUT | /api/vehicles/:id | Update vehicle (🔐) |
| DELETE | /api/vehicles/:id | Delete vehicle (🔐) |

### Deliveries
| Method | Route | Description |
|--------|-------|-------------|
| GET | /api/deliveries | List all deliveries (🔐) |
| GET | /api/deliveries/:id | Get delivery + items (🔐) |
| POST | /api/deliveries | Create delivery (🔐) |
| PATCH | /api/deliveries/:id/status | Update status (🔐) |
| DELETE | /api/deliveries/:id | Delete delivery (🔐) |

🔐 = Requires `Authorization: Bearer <token>` header

## Database Tables

- **Users** — Admin accounts
- **Farmers** — Farmer profiles (Tamil Nadu)
- **Stocks** — Vegetable inventory
- **Vehicles** — Fleet management
- **Deliveries** — Delivery records
- **DeliveryItems** — Items in each delivery

## Environment Variables

See `.env.example` for all required variables.
