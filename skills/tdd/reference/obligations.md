# Example obligation lists

## A new endpoint: GET /expenses/:id
OB-1: existing id -> 200 with the expense
OB-2: unknown id -> 404
OB-3: id that isn't a UUID -> 400

## A bug fix: totals off by a cent
OB-1 (regression): amounts 0.10 + 0.20 -> total "0.30" exactly
OB-2: empty list -> total "0.00"

## A validation rule: category is required
OB-1: valid category -> 201, category saved
OB-2: missing category -> 400
OB-3: empty string category -> 400
OB-4: category not in the allowed list -> 400
