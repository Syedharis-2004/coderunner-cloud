# Code Cloud SaaS - Quick Start Guide

## 🚀 Get Running in 10 Minutes

This guide gets your SaaS platform running locally with Stripe test mode.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis
- Stripe account (free)

---

## Step 1: Database Setup (2 minutes)

```bash
# Create database
createdb coderunner

# Set environment variable
export DATABASE_URL="postgresql://youruser:yourpass@localhost:5432/coderunner"
```

---

## Step 2: Backend Setup (3 minutes)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://youruser:yourpass@localhost:5432/coderunner
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-super-secret-jwt-key-minimum-32-characters-long!!
API_KEY_SECRET=your-api-key-hashing-secret-also-32-chars-min!!
STRIPE_SECRET_KEY=sk_test_51xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_51xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_STARTER_PRICE_ID=price_xxxxx
STRIPE_PRO_PRICE_ID=price_xxxxx
STRIPE_BUSINESS_PRICE_ID=price_xxxxx
ALLOWED_ORIGINS=http://localhost:4200
EOF

# Run migration (creates tables and seeds plans)
alembic upgrade head

# Verify plans created
psql $DATABASE_URL -c "SELECT key, name, price_monthly, api_access_enabled FROM plans;"
```

Expected output:
```
   key    |   name   | price_monthly | api_access_enabled 
----------|----------|---------------|-------------------
 free     | Free     |          0.00 | f
 starter  | Starter  |          9.00 | t
 pro      | Pro      |         19.00 | t
 business | Business |         49.00 | t
```

---

## Step 3: Stripe Setup (3 minutes)

### A. Get API Keys
1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy "Publishable key" → `STRIPE_PUBLISHABLE_KEY`
3. Copy "Secret key" → `STRIPE_SECRET_KEY`

### B. Create Products
1. Go to https://dashboard.stripe.com/test/products
2. Create 3 products:
   - **Starter Plan**: $9/month recurring
   - **Pro Plan**: $19/month recurring  
   - **Business Plan**: $49/month recurring
3. For each product, copy the Price ID (starts with `price_`)
4. Update `.env` with price IDs

### C. Update Database
```bash
# Replace with your actual Stripe Price IDs
psql $DATABASE_URL << EOF
UPDATE plans SET stripe_price_id = 'price_your_starter_id' WHERE key = 'starter';
UPDATE plans SET stripe_price_id = 'price_your_pro_id' WHERE key = 'pro';
UPDATE plans SET stripe_price_id = 'price_your_business_id' WHERE key = 'business';
EOF
```

### D. Setup Webhook (for local testing)
```bash
# Install Stripe CLI
# Mac: brew install stripe/stripe-cli/stripe
# Windows: scoop install stripe
# Linux: Download from https://stripe.com/docs/stripe-cli

# Login
stripe login

# Forward webhooks to local backend
stripe listen --forward-to localhost:8000/api/v1/payments/webhook

# Copy webhook signing secret from output → STRIPE_WEBHOOK_SECRET in .env
```

---

## Step 4: Start Services (2 minutes)

Open 3 terminal windows:

### Terminal 1: Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Celery Worker
```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

### Terminal 3: Frontend
```bash
cd frontend
npm install  # First time only
ng serve --port 4200
```

---

## Step 5: Test the System (5 minutes)

### A. Register & Login
1. Open http://localhost:4200
2. Click "Register" → Create account
3. Login with credentials

### B. Verify Free Tier
1. Go to Dashboard → See "Free Plan"
2. Go to API Keys → Try to generate key
3. **Expected**: Error message "Active subscription required"

### C. Test Payment Flow
1. Go to **Pricing** page
2. Click **"Subscribe"** on Starter plan
3. Redirected to Stripe Checkout
4. Use test card: **4242 4242 4242 4242**
   - Any future expiry date
   - Any 3-digit CVC
   - Any ZIP code
5. Complete payment
6. Redirected back to dashboard

### D. Verify Webhook
Check Terminal 2 (backend) for:
```
[Webhook received: checkout.session.completed]
[Subscription created/updated]
[Payment recorded: 9.00 USD]
```

### E. Test API Access
1. Dashboard → Should show "Starter Plan" and "Active" status
2. Go to **API Keys**
3. Click **"Generate API Key"** → Should succeed
4. Copy the key (shown once only)

### F. Test API Execution
```bash
curl -X POST http://localhost:8000/api/v1/executions/run \
  -H "X-API-Key: YOUR_GENERATED_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "code": "print(\"Hello from Code Cloud API!\")"
  }'
```

Expected response:
```json
{
  "success": true,
  "message": "Execution completed: SUCCESS",
  "data": {
    "execution_id": "...",
    "status": "SUCCESS",
    "stdout": "Hello from Code Cloud API!\n",
    "stderr": "",
    "exit_code": 0,
    "execution_time": 0.15
  }
}
```

---

## ✅ Verification Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:4200
- [ ] Celery worker running (no errors)
- [ ] Stripe CLI forwarding webhooks
- [ ] Can register and login
- [ ] Free users blocked from API keys
- [ ] Checkout redirects to Stripe
- [ ] Test payment completes
- [ ] Webhook received and processed
- [ ] Subscription shows as "Active"
- [ ] Can generate API key after payment
- [ ] API execution works with key
- [ ] Rate limiting applied (check logs)
- [ ] Usage tracking increments

---

## 🧪 Test Cards

Use these in Stripe test mode:

| Card Number      | Result                  |
|------------------|-------------------------|
| 4242424242424242 | Success                 |
| 4000000000000002 | Card declined           |
| 4000002500003155 | Authentication required |
| 4000000000009995 | Insufficient funds      |

More: https://stripe.com/docs/testing#cards

---

## 🎯 What You Built

✅ Full Stripe subscription payments
✅ 4-tier pricing (Free, Starter, Pro, Business)
✅ Subscription-gated API key generation  
✅ Webhook-verified payment processing
✅ Usage tracking & monthly limits
✅ Plan-based rate limiting
✅ Customer portal for self-service
✅ Payment history tracking
✅ Subscription management (cancel/reactivate)
✅ Production-ready security

---

## 🚨 Common Issues

### "Migration failed"
```bash
# Reset database
dropdb coderunner && createdb coderunner
alembic upgrade head
```

### "Stripe checkout returns error"
- Verify `stripe_price_id` in plans table matches your Stripe dashboard
- Check `.env` has correct `STRIPE_SECRET_KEY`

### "Webhook not received"
- Make sure Stripe CLI is running: `stripe listen --forward-to localhost:8000/api/v1/payments/webhook`
- Copy the `whsec_` secret it displays to `.env` → `STRIPE_WEBHOOK_SECRET`
- Restart backend after updating `.env`

### "API key generation still fails after payment"
- Check backend logs for webhook processing
- Verify subscription status: `GET http://localhost:8000/api/v1/subscriptions/status`
- Should show `"status": "active"`

### "Rate limit not working"
- Verify Redis is running: `redis-cli ping` → `PONG`
- Check `REDIS_URL` in `.env`

---

## 🎓 Next Steps

### To Deploy to Production:

1. **Update Stripe to Live Mode**
   - Get live API keys from https://dashboard.stripe.com/apikeys
   - Create live products and price IDs
   - Configure live webhook endpoint (requires HTTPS)

2. **Set Production Environment Variables**
   ```bash
   ENVIRONMENT=production
   DEBUG=False
   STRIPE_SECRET_KEY=sk_live_xxx  # Live key
   STRIPE_WEBHOOK_SECRET=whsec_xxx  # Live webhook secret
   ```

3. **Secure Secrets**
   - Use environment variable management (AWS Secrets Manager, Azure Key Vault, etc.)
   - Never commit `.env` files to Git

4. **Set Up Monitoring**
   - Monitor webhook failures
   - Alert on payment failures
   - Track MRR (Monthly Recurring Revenue)

5. **Test Production Flow**
   - Test with real card in private browsing
   - Verify emails sent (if configured)
   - Check webhook delivery in Stripe dashboard

---

## 📚 Documentation

- **API Reference**: See `SAAS_IMPLEMENTATION_SUMMARY.md`
- **Full Implementation Details**: See `IMPLEMENTATION_STATUS.md`
- **Stripe Docs**: https://stripe.com/docs
- **Stripe Testing**: https://stripe.com/docs/testing

---

## 💬 Support

If you encounter issues:
1. Check backend logs for error messages
2. Verify all environment variables set correctly
3. Ensure Redis and PostgreSQL are running
4. Check Stripe dashboard for webhook events
5. Review `IMPLEMENTATION_STATUS.md` troubleshooting section

---

**You're all set!** 🎉

Your Code Cloud SaaS platform is now running with:
- ✅ Secure payment processing
- ✅ Subscription management
- ✅ API access control
- ✅ Usage enforcement
- ✅ Rate limiting

**Time to make it yours!** Add your branding, customize plans, and deploy to production.
