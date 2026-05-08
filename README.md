1) Prerequisites
Install Docker Desktop
Make sure Docker is running (WSL2 backend on Windows is fine)

2) Get the code
Download ZIP from GitHub or clone:
git clone https://github.com/Jayalakshmi-ctrl/FULL_STACK_DEVELOPMENT_Pickup_App.git
cd FULL_STACK_DEVELOPMENT_Pickup_App

3) Create the environment file
Copy .env.example → .env

PowerShell (Windows):

Copy-Item .env.example .env
(You can open .env and change passwords if you want; otherwise defaults work.)

4) Start everything (frontend + gateway + backend + database)
From the project root (where docker-compose.yml exists):

docker compose up --build
Wait until services are running.

5) Open the app + APIs
Frontend UI: http://localhost:5173
Gateway Swagger (main API): http://localhost:8000/docs
Auth Swagger: http://localhost:8001/docs
Pickups Swagger: http://localhost:8002/docs

6) Default accounts / usage
Customer: register in the UI, then log in.
Admin / Vendor: use credentials from .env:
ADMIN_EMAIL, ADMIN_PASSWORD
VENDOR_EMAIL, VENDOR_PASSWORD

7) Common troubleshooting
If you see DB/schema related 500s and you previously ran the app before:
docker compose down -v
docker compose up --build
To view logs:
docker compose logs -f gateway-service auth-service pickups-service
