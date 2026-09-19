# Vercel + Supabase Deployment

## Target architecture

```text
GitHub → Vercel → Flask → Supabase PostgreSQL → persistent data
```

## 1. Supabase

1. Create a Supabase project.
2. Open the **Connect** panel.
3. Copy the **Transaction Pooler** PostgreSQL connection string.
4. Open SQL Editor.
5. Run `supabase/schema.sql`.

The transaction pooler is the recommended connection mode for serverless workloads. Keep the database password encoded if it contains reserved URL characters.

## 2. GitHub

Push the repository with `app.py` at the root.

## 3. Vercel

Import the GitHub repository and let Vercel detect Flask/Python automatically. No `vercel.json` is required for the current zero-configuration Flask model.

## 4. Environment variables

Set these for Production, Preview and Development as appropriate:

```text
SECRET_KEY=<long-random-secret>
ADMIN_USERNAME=<admin-username>
ADMIN_PASSWORD=<strong-admin-password>
DATABASE_URL=<Supabase-transaction-pooler-url>
PGSSLMODE=require
```

## 5. Deploy

Deploy from Vercel or push a new commit to GitHub.

## 6. Health check

Open:

```text
https://YOUR-APP.vercel.app/api/health
```

Expected response contains:

```json
{
  "ok": true,
  "database": "ok",
  "storage": "Supabase PostgreSQL"
}
```

## 7. First functional test

1. Open login page.
2. Select Farmer.
3. Register a farmer.
4. Record the generated token.
5. Log in with mobile + token.
6. Log out.
7. Log in as Admin.
8. Advance the queue.
9. Register another farmer.
10. Confirm the new token and queue state remain available after refreshing the page.
