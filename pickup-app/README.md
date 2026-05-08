## Plastic-for-Plants (React + FastAPI microservices)

**Stage 1:** Pickup requests + admin status. **Stage 2:** **Eco-Points** from **vendor-verified plastic weight**, redeemable for **saplings, organic seeds, and compost**.

### Roles

- **Customer**: pickup requests, **Eco-Points** balance & history, **garden shop** redemptions.
- **Vendor**: on-site **weigh-in** — enters customer email + kg → **instant Eco-Points** credit.
- **Admin**: manage pickup request status (**Picked Up**).

### Services

- `auth-service`: JWT auth, users (Customer / Admin / Vendor).
- `pickups-service`: pickups, wallets, plastic verifications, reward catalog, redemptions.
- `gateway-service`: single entry URL for the browser (`http://localhost:8000`).

Persistence: **Postgres** (Docker).

### Prereqs

- Docker Desktop
- Node 18+ (for local frontend dev outside Docker)

### Run

1. Copy env:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Start:

   ```bash
   docker compose up --build
   ```

3. Open **frontend**: `http://localhost:5173`  
   **API gateway docs**: `http://localhost:8000/docs`

### “Failed to fetch” on login / register

The dev UI calls the API via **`/api` → Vite proxy → gateway** (same browser origin, no CORS). Ensure **`docker compose up`** is running and **gateway** is healthy on port **8000**. If you run the frontend with `npm run dev` on your PC only, start the stack with Docker (or run the gateway locally on `127.0.0.1:8000`).

### Default accounts (`.env`)

| Role     | Variables            |
|----------|----------------------|
| Admin    | `ADMIN_EMAIL`, `ADMIN_PASSWORD` |
| Vendor   | `VENDOR_EMAIL`, `VENDOR_PASSWORD` |

Customers register in the UI.

### Eco-Points

- `ECO_POINTS_PER_KG` in `.env` (default **100**): Eco-Points per **1 kg** verified plastic.
- Formula: `max(1, round(weight_kg * ECO_POINTS_PER_KG))`.

### Postgres enum / schema changes

If you created the database **before** the **Vendor** role or new tables existed, either:

- reset the volume: `docker compose down -v` then `docker compose up --build`, or  
- migrate manually (production-style).

### Direct service docs (optional)

- Auth: `http://localhost:8001/docs`
- Pickups: `http://localhost:8002/docs`
