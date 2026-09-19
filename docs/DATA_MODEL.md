# KisanGati PostgreSQL Data Model

## `farmers`

Stores the main farmer registration and payment information.

Key fields:

- `token` — unique digital token
- `name`
- `mobile`
- `farmer_id`
- `crop`
- `quantity`
- `slot`
- `status`
- `created_at`
- `bank_name`
- `account_holder`
- `account_number`
- `ifsc_code`
- `tracking_id`

## `shipment_tracking`

One current tracking record per farmer token.

Stores stage, location, coordinates, accuracy, last update and GPS state.

## `tracking_updates`

Historical GPS/stage updates.

## `farmer_effort`

Stores the observable event counters used by the Farmer Effort Index.

## `lot_trace`

Stores the four-step trace:

```text
Farmer Registration → Quality Check → Procurement → Payment
```

A unique `(token, step_key)` constraint prevents duplicate trace steps.

## `rejection_records`

Stores explainable rejection reason, actionable guidance and timestamp.

## `app_state`

Stores shared application state:

- `current_queue_token`
- `next_token_number`

This table is critical for serverless-safe shared state.
