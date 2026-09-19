# KisanGati API

## Health

`GET /api/health`

Checks Flask-to-Supabase PostgreSQL connectivity.

## Queue

`GET /api/queue`

Returns the shared database-backed current queue token.

`POST /api/queue/next`

Admin only. Atomically advances the queue token.

## Registration

`POST /register`

Creates a farmer, allocates a database-backed digital token and initializes tracking, effort and lot-trace records.

## Tracking

`GET /api/tracking/<token>`

Read access is restricted to the authenticated farmer's own record or admin.

`POST /api/tracking/<token>/location`

Admin only. Stores current GPS coordinates.

`POST /api/tracking/<token>/stop`

Admin only. Stops GPS tracking.

`POST /api/tracking/<token>/stage`

Admin only. Updates the operational stage and synchronizes the Lot Trace where appropriate.

## Farmer Effort

`GET /api/effort/<token>`

Read-only metric for the authenticated farmer/admin.

`POST /api/effort/<token>/visit`

Admin only. Records a centre visit.

## Lot Trace

`GET /api/lot-trace/<token>`

Returns the farmer → quality → procurement → payment trace.

`POST /api/lot-trace/<token>/update`

Admin only. Enforces prerequisite step completion.

## Explainable Rejection

`GET /api/rejection/<token>`

Returns rejection history for the authenticated farmer/admin.

`POST /api/rejection/<token>`

Admin only. Saves the reason and actionable guidance.

## Admin

`GET /api/admin/summary`

Admin-only dashboard summary backed by PostgreSQL.

## AI

`POST /ai_assistant`

Uses current farmer, queue, slot and weather context. Registration data is read from Supabase PostgreSQL.
