# KisanGati Features

Version 2 preserves the supplied feature set while replacing temporary SQLite persistence with Supabase PostgreSQL.

## Farmer side

- registration
- slot booking
- digital token
- live queue
- procurement/payment status
- bank details
- shipment/GPS tracking view
- Lot Trace view
- explainable rejection view
- Farmer Effort Index view
- weather assistance
- AI assistant
- 12 languages

## Admin side

- farmer records
- queue control
- shipment stage control
- GPS control
- Farmer Effort Index updates
- Lot Trace updates
- rejection recording
- admin summary

## Deployment-safe state

The following are now shared database state rather than process-local state:

- digital token allocation
- current queue token
- farmer registrations
- slot counts
- tracking state
- GPS history
- effort metrics
- Lot Trace
- rejection history
