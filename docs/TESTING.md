# Testing

## Static tests

Run:

```bash
python -m unittest discover -s tests -v
```

These checks verify:

- Python syntax
- no SQLite dependency in the deployed app
- PostgreSQL dependency and configuration
- required Supabase tables
- database-backed queue/token helpers
- health endpoint

## Deployment test

After deployment:

```text
GET /api/health
```

Then test:

1. Farmer registration.
2. Farmer login.
3. Slot count update.
4. Queue read.
5. Admin queue advance.
6. Refresh queue from another browser/session.
7. GPS tracking update.
8. Lot Trace update.
9. Rejection save/read.
10. AI assistant.

## Persistence test

The key Version 2 test is to prove the state survives a new Vercel invocation:

- Register farmer A.
- Note token P101 (or the next available token).
- Close/reopen the browser.
- Log in again.
- Confirm farmer A still exists.
- Advance queue as admin.
- Refresh `/api/queue`.
- Confirm the same queue value is returned.

## Migration test

If importing an old SQLite database, run:

```powershell
$env:SQLITE_SOURCE="procurement.db"
$env:DATABASE_URL="..."
python scripts/migrate_sqlite_to_supabase.py
```

Then check farmer counts and the highest imported token in Supabase.
