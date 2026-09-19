# 🌾 KisanGati — Vercel Version 2

**Smart Agricultural Procurement & Farmer Assistance Platform**  
Smart India Hackathon — **SIH26032**

## Architecture

```text
GitHub
  ↓
Vercel
  ↓
Flask
  ↓
Supabase PostgreSQL
  ↓
Persistent KisanGati data
```

This Version 2 removes SQLite from the deployed architecture. Farmer registrations, tokens, queue state, slot counts, bank details, shipment/GPS records, Farmer Effort Index data, Lot Trace, and Explainable Rejection records are stored in **Supabase PostgreSQL** instead of Vercel's local filesystem.

Vercel currently supports Flask with zero configuration, so `app.py` stays at the repository root and no `vercel.json` is required. [Vercel Flask zero-configuration support](https://vercel.com/changelog/zero-configuration-flask-backends)

## What Version 2 fixes

### Version 1

```text
GitHub → Vercel → Flask → SQLite (/tmp)
                         ↓
                  temporary instance data
```

This could cause data to disappear or differ between serverless instances.

### Version 2

```text
GitHub → Vercel → Flask → Supabase PostgreSQL
                              ↓
                    persistent shared database
```

The queue counter and farmer token counter are also database-backed. They are no longer stored in a Flask global variable, so queue changes and new token allocation are shared across Vercel instances.

## Included features

- Farmer / Admin role-separated login
- 12-language interface
- Farmer registration and slot booking
- Bank details with validation
- Database-backed digital token generation
- Database-backed live queue
- Procurement and payment status workflow
- Live shipment / processing tracking
- Browser GPS updates for the admin procurement console
- OpenStreetMap tracking map
- Farmer Effort Index
- Lot Trace with ordered workflow enforcement
- Explainable Rejection with actionable guidance
- Weather assistance using browser geolocation and Open-Meteo
- KisanGati AI Assistant with live PostgreSQL context
- Browser voice input/output where supported
- Procurement-centre directions through Google Maps
- Responsive web UI

## Project structure

```text
KisanGati/
├── app.py
├── database.py
├── requirements.txt
├── runtime.txt
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── project-manifest.json
├── supabase/
│   └── schema.sql
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DATA_MODEL.md
│   ├── DEMO_FLOW.md
│   ├── DEPLOYMENT.md
│   ├── FEATURES.md
│   ├── PROJECT_SOURCE.md
│   └── TESTING.md
├── scripts/
│   ├── check_python.bat
│   ├── start_windows.bat
│   └── migrate_sqlite_to_supabase.py
├── screenshots/
│   ├── 01_login_page.png
│   ├── 02_farmer_dashboard.png
│   ├── 03_weather_assistance.png
│   ├── 04_admin_smart_features.png
│   ├── 05_registration_slot_booking.png
│   ├── 06_queue_and_payment_status.png
│   ├── 07_live_gps_tracking.png
│   ├── 08_language_selector.png
│   └── 09_ai_assistant.png
├── tests/
│   └── test_smoke.py
└── .github/workflows/
    └── python-check.yml
```

## 1. Create the Supabase database

Create a Supabase project and open its **Connect** panel. Supabase provides separate direct, session-pooler, and transaction-pooler connection strings. For a serverless Vercel backend, this project is configured for the **Transaction Pooler** connection string on port `6543`; Supabase documents transaction mode as the option intended for serverless/edge workloads and notes that prepared statements must be disabled. [Supabase PostgreSQL connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres)

Then open the Supabase SQL Editor and run:

```text
supabase/schema.sql
```

The schema creates:

- `farmers`
- `shipment_tracking`
- `tracking_updates`
- `farmer_effort`
- `lot_trace`
- `rejection_records`
- `app_state`

`app_state` stores the shared queue token and the next digital-token number.

## 2. Local setup

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set:

```text
SECRET_KEY=your-long-random-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
DATABASE_URL=your-supabase-transaction-pooler-connection-string
PGSSLMODE=require
```

Then run:

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

### Important

Version 2 intentionally does **not** create or use `procurement.db`. Local development and Vercel use the same PostgreSQL backend when `DATABASE_URL` is configured.

## 3. Vercel deployment

1. Push this repository to GitHub.
2. Import the GitHub repository into Vercel.
3. Keep the root directory as `./`.
4. Let Vercel detect Flask/Python automatically.
5. Do not add the old `/api` redirect structure.
6. Add these Vercel Environment Variables:

```text
SECRET_KEY=<long-random-secret>
ADMIN_USERNAME=<admin-username>
ADMIN_PASSWORD=<strong-admin-password>
DATABASE_URL=<Supabase-transaction-pooler-connection-string>
PGSSLMODE=require
```

7. Deploy.
8. Open the Vercel URL.
9. Test the health endpoint:

```text
/api/health
```

10. Test farmer registration, then log in using the generated token.

Vercel's current Flask deployment model recognizes Flask applications directly, so a root-level `app.py` is sufficient for the deployment. [Vercel Flask boilerplate](https://vercel.com/templates/python/flask-python-boilerplate)

## 4. Database health check

Version 2 includes:

```text
GET /api/health
```

A healthy deployment reports the application and database status. If `DATABASE_URL` is missing or the Supabase connection fails, the endpoint exposes the problem instead of silently falling back to local storage.

## 5. Migrating an existing SQLite demo

If you already have a local `procurement.db` from the previous KisanGati version, the repository includes a one-time migration helper.

PowerShell:

```powershell
$env:SQLITE_SOURCE="procurement.db"
$env:DATABASE_URL="your-supabase-connection-string"
python scripts/migrate_sqlite_to_supabase.py
```

The script imports farmer, tracking, GPS-update, effort, Lot Trace, and rejection records and advances the PostgreSQL token counter so future registrations continue after the highest imported P-token.

After migration, the deployed app does not need the SQLite file.

## 6. Demo admin login

Default demo values:

```text
Username: admin
Password: admin123
```

For deployment, set your own `ADMIN_USERNAME` and `ADMIN_PASSWORD` in Vercel.

## 7. Important architecture details

### Persistent farmer data

All business records are stored in Supabase PostgreSQL.

### Persistent queue

The current queue token is stored in `app_state.current_queue_token`.

### Persistent token generation

The next token number is stored in `app_state.next_token_number` and allocated atomically by PostgreSQL.

### No Vercel local database

There is no `/tmp/*.db` fallback in Version 2. This prevents the application from appearing to work while silently writing data to a temporary serverless filesystem.

### AI assistant

The existing KisanGati AI Assistant remains rule/data aware. Its farmer, registration, slot, queue and status context is now read from Supabase PostgreSQL. Weather is still supplied by the browser/Open-Meteo workflow.

### GPS

The existing browser GPS workflow is retained. GPS writes are stored in `shipment_tracking` and `tracking_updates`. Admin-only controls remain protected by the existing role checks.

## Screenshots

### Login

![Login](screenshots/01_login_page.png)

### Farmer dashboard

![Farmer dashboard](screenshots/02_farmer_dashboard.png)

### Weather assistance

![Weather](screenshots/03_weather_assistance.png)

### Admin smart features

![Admin](screenshots/04_admin_smart_features.png)

### Registration and slot booking

![Registration](screenshots/05_registration_slot_booking.png)

### Queue and payment status

![Queue](screenshots/06_queue_and_payment_status.png)

### Live GPS tracking

![GPS](screenshots/07_live_gps_tracking.png)

### Language selector

![Languages](screenshots/08_language_selector.png)

### AI assistant

![AI](screenshots/09_ai_assistant.png)

## API endpoints

### Authentication

- `POST /login`
- `GET /logout`

### Farmer

- `POST /register`
- `GET /api/tracking/<token>`
- `GET /api/effort/<token>`
- `GET /api/lot-trace/<token>`
- `GET /api/rejection/<token>`

### Queue

- `GET /api/queue`
- `POST /api/queue/next` — admin only

### Tracking

- `POST /api/tracking/<token>/location` — admin only
- `POST /api/tracking/<token>/stop` — admin only
- `POST /api/tracking/<token>/stage` — admin only

### Smart features

- `POST /api/effort/<token>/visit` — admin only
- `POST /api/lot-trace/<token>/update` — admin only
- `POST /api/rejection/<token>` — admin only
- `GET /api/admin/summary` — admin only

### AI / health

- `POST /ai_assistant`
- `GET /api/health`

## Verification checklist

- [ ] Supabase `schema.sql` executed successfully
- [ ] Vercel has `DATABASE_URL`
- [ ] Vercel has `SECRET_KEY`
- [ ] `/api/health` reports database `ok`
- [ ] Login page opens
- [ ] All 12 languages render
- [ ] Admin login works
- [ ] Farmer registration creates a persistent token
- [ ] Farmer can log in with mobile + token
- [ ] Slot counts update
- [ ] Queue changes persist after a new request
- [ ] A second Vercel invocation sees the same farmer data
- [ ] Tracking record loads
- [ ] Admin GPS update works with browser permission
- [ ] Farmer tracking view remains read-only
- [ ] Lot Trace enforces farmer → quality → procurement → payment order
- [ ] Explainable Rejection saves and appears to the farmer
- [ ] Farmer Effort Index loads and updates
- [ ] Weather loads with location permission
- [ ] AI assistant reads current PostgreSQL data

## Testing

Python syntax:

```bash
python -m py_compile app.py database.py
```

Unit/smoke checks:

```bash
python -m unittest discover -s tests -v
```

The GitHub Actions workflow installs the dependencies and runs the smoke tests on every push.

## Source basis

The application UI and feature logic are based on the supplied KisanGati Flask source, including its 12 languages, farmer/admin separation, bank details, GPS/shipment tracking, Farmer Effort Index, Lot Trace, Explainable Rejection, weather assistance and AI assistant. Version 2 changes the persistence layer and queue/token state so the deployment uses Supabase PostgreSQL instead of SQLite.
