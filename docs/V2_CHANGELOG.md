# KisanGati Vercel Version 2 Changelog

## Removed from deployed persistence layer

- SQLite runtime database
- `/tmp/kisangati_procurement.db`
- Flask global `CURRENT_QUEUE_TOKEN`
- count-based token allocation from the local database

## Added

- `database.py` PostgreSQL adapter
- Supabase PostgreSQL schema
- Supavisor-compatible connection configuration
- database-backed `app_state`
- atomic token allocation
- atomic queue advancement
- `/api/health`
- SQLite → Supabase migration helper
- deployment documentation
- static smoke tests

## Preserved

- original farmer/admin UI
- 12 languages
- bank details
- weather assistance
- AI assistant
- live queue UI
- GPS/shipment tracking
- Farmer Effort Index
- Lot Trace
- Explainable Rejection
- role-based access control

## Registration Success Flow Update

- Successful farmer registration now opens a dedicated **Registration Complete** card instead of jumping directly to shipment tracking.
- The card displays the digital token (for example, `P101`), tracking ID (`KG-P101`), farmer name, crop, quantity, and booked slot.
- Added **View Dashboard** and **Track Shipment** actions.
- Added translations for the new success card across all 12 supported languages.
- Registration success details are stored in the Flask session only for the immediate post-registration page, while the actual farmer record remains persisted in Supabase PostgreSQL.
- Added `python-dotenv` to the project dependencies so local `.env` loading works consistently.
