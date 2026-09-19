# Project Source

The Version 2 application is based on the supplied KisanGati Flask source (`KisanGati(6).py`) and the deployed Flask version reviewed before this update.

Preserved areas include:

- original UI
- 12-language translations
- farmer/admin separation
- bank details
- registration and slot booking
- queue UI
- weather assistance
- AI assistant
- GPS/shipment tracking
- Farmer Effort Index
- Lot Trace
- Explainable Rejection

Changed in Version 2:

- SQLite removed from the deployed app
- PostgreSQL adapter added
- Supabase schema added
- queue state moved to PostgreSQL
- token allocation moved to PostgreSQL
- database health endpoint added
- SQLite-to-Supabase migration helper added
- Vercel environment configuration updated
