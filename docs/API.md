# API contract

Base URL: `http://127.0.0.1:8000`.

## POST /api/evaluate

JSON object with exactly these numeric fields:

| Field | Allowed range | Meaning |
| --- | --- | --- |
| income | 1–100,000,000 | Monthly net income, AMD |
| expenses | 0–100,000,000 | Monthly living expenses, excluding debt |
| existing_debt | 0–100,000,000 | Existing monthly debt payments, AMD |
| amount | 1–100,000,000 | Requested principal, AMD |
| annual_rate | 0–60 | Nominal annual percentage |
| months | 1–360, integer | Term |
| late_days | 0–3650, integer | Longest current overdue duration |

```bash
curl http://127.0.0.1:8000/api/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"income":450000,"expenses":180000,"existing_debt":40000,"amount":2000000,"annual_rate":18,"months":36,"late_days":0}'
```

200: JSON containing `decision`, `monthly_payment`, `total_monthly_debt`, `dti_percent`, `disposable_income`, `total_repayment`, `reasons`, `policy_version`, and `id`. Monetary results are rounded to two decimals. `id` identifies the persisted record.

400: malformed JSON, invalid/missing/extra fields, non-finite numbers, booleans or out-of-range values. 403: browser Origin differs from server origin. 404: unsupported route. Maximum body size: 16 KiB.

## GET /api/history

Returns latest 100 records, newest first. Each record includes `id`, `created_at` in UTC, original `inputs`, and `result`. An empty database returns `[]`.

## Postman

Import `docs/CreditLens.postman_collection.json`. The collection includes a passing assessment, an invalid-income request and a history request, with status assertions. Base URL defaults to port 8000.

## Policy v2

`decision` is `PASS`, `REVIEW`, or `HIGH_RISK`. Reasons and validation errors are Armenian. There is no numeric score. Policy version: `demo-am-2.0`. Historical records retain their original policy version; older `DECLINE` values may appear in an existing database.

Income, expenses and existing debt must describe the same household budget. All amounts are AMD. The monthly payment excludes fees and insurance; this is not an effective APR calculator.
