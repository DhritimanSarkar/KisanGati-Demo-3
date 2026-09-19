# KisanGati Version 2 Architecture

```text
GitHub
  ↓
Vercel
  ↓
Flask (Python)
  ↓
Supabase PostgreSQL / Supavisor
  ↓
Persistent KisanGati records
```

## Runtime responsibilities

### GitHub
Source control and deployment trigger.

### Vercel
Runs the root-level Flask application using Vercel's current zero-configuration Flask support.

### Flask
Provides:

- role-based login
- farmer/admin pages
- registration
- queue APIs
- tracking APIs
- effort/lot/rejection APIs
- AI assistant
- weather integration

### Supabase PostgreSQL
Stores all application state that must survive a Vercel instance change:

- farmers
- bank details
- digital tokens
- slots/registration counts derived from farmers
- shipment tracking
- GPS history
- Farmer Effort Index
- Lot Trace
- rejection records
- current queue token
- next token number

## Why the queue moved into PostgreSQL

The previous prototype stored `CURRENT_QUEUE_TOKEN` in a Flask global. Serverless instances do not provide one shared Python process. Version 2 stores the queue counter in `app_state`, so all invocations read the same value.

## Why token generation moved into PostgreSQL

Version 1 calculated the next token from a local database count. Version 2 uses a database-backed counter and an atomic PostgreSQL update. This prevents two simultaneous registrations from receiving the same token.

## Database connection

Version 2 uses `psycopg` with:

- `DATABASE_URL`
- SSL required by default
- prepared statements disabled
- short connection timeout

The recommended Vercel connection is the Supabase Transaction Pooler connection string.
