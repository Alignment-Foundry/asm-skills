# Stripe API — Webhook Creation via CLI

Stripe's API allows creating webhook endpoints programmatically, bypassing the Stripe dashboard entirely. This is useful when the human has provided the live API key but you don't have dashboard access.

## Create Webhook Endpoint

```bash
STRIPE_SECRET="sk_live_..."

curl -s -X POST "https://api.stripe.com/v1/webhook_endpoints" \
  -u "${STRIPE_SECRET}:" \
  -d "url=https://<your-domain>/api/v1/webhooks/stripe" \
  -d "enabled_events[]=customer.subscription.created" \
  -d "enabled_events[]=customer.subscription.updated" \
  -d "enabled_events[]=customer.subscription.deleted" \
  -d "enabled_events[]=invoice.paid" \
  -d "enabled_events[]=invoice.payment_failed" \
  -d "enabled_events[]=checkout.session.completed" \
  -d "metadata[app]=<app-name>"
```

**Critical:** The `secret` field containing the webhook signing secret (`whsec_...`) is only returned ONCE — on creation. Store it immediately. You cannot retrieve it later via GET. If you lose it, delete and recreate the webhook.

## List Webhook Endpoints

```bash
STRIPE_SECRET="sk_live_..."

curl -s "https://api.stripe.com/v1/webhook_endpoints" \
  -u "${STRIPE_SECRET}:" | python3 -c "
import sys,json
for wh in json.load(sys.stdin).get('data',[]):
    print(f'{wh[\"id\"]} | {wh[\"url\"]} | livemode={wh[\"livemode\"]}')
"
```

## Delete and Recreate (if secret was lost)

```bash
WEBHOOK_ID="we_..."
curl -s -X DELETE "https://api.stripe.com/v1/webhook_endpoints/${WEBHOOK_ID}" \
  -u "${STRIPE_SECRET}:" > /dev/null

# Then recreate with the same POST command above to get a new secret
```

## Deploy to Fly.io

```bash
fly secrets set STRIPE_WEBHOOK_SECRET="whsec_..." -a <app-name>
```

## Important Notes

- The Stripe live mode webhook is **separate** from test mode — you must create it with a live secret key
- If the app is on Fly.io, `fly secrets set` with a rolling restart — the app will be briefly unavailable
- The Stripe webhook signature verification in your code uses the `whsec_` to verify incoming events are genuinely from Stripe
- Recommended events for subscription-based billing:
  - `customer.subscription.created` — new subscriber
  - `customer.subscription.updated` — plan change
  - `customer.subscription.deleted` — cancellation
  - `invoice.paid` — successful payment
  - `invoice.payment_failed` — payment failure (churn risk)
  - `checkout.session.completed` — checkout flow success
