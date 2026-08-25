"""Replace Stripe columns with SafePay columns

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-25

Renames/replaces all stripe_* columns in subscriptions and payments
with safepay_* equivalents.
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    # ── subscriptions table ───────────────────────────────────────────────
    # Drop old stripe columns (idempotent)
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS stripe_customer_id")
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS stripe_subscription_id")
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS stripe_price_id")

    # Add safepay columns
    op.execute("""
        ALTER TABLE subscriptions
            ADD COLUMN IF NOT EXISTS safepay_tracker  VARCHAR(255),
            ADD COLUMN IF NOT EXISTS safepay_order_id VARCHAR(255);
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_subscriptions_safepay_tracker   ON subscriptions (safepay_tracker)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_subscriptions_safepay_order_id  ON subscriptions (safepay_order_id)")

    # ── payments table ────────────────────────────────────────────────────
    # Drop old stripe columns (idempotent)
    op.execute("DROP INDEX IF EXISTS ix_payments_stripe_payment_intent_id")
    op.execute("DROP INDEX IF EXISTS ix_payments_stripe_invoice_id")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS stripe_payment_intent_id")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS stripe_invoice_id")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS stripe_charge_id")

    # Add safepay columns
    op.execute("""
        ALTER TABLE payments
            ADD COLUMN IF NOT EXISTS safepay_tracker  VARCHAR(255),
            ADD COLUMN IF NOT EXISTS safepay_order_id VARCHAR(255);
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_payments_safepay_tracker  ON payments (safepay_tracker) WHERE safepay_tracker IS NOT NULL")
    op.execute("CREATE INDEX        IF NOT EXISTS ix_payments_safepay_order_id ON payments (safepay_order_id)")

    # ── plans table — drop stripe_price_id (not needed for SafePay) ───────
    op.execute("ALTER TABLE plans DROP COLUMN IF EXISTS stripe_price_id")


def downgrade():
    # Restore stripe columns in subscriptions
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS safepay_tracker")
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS safepay_order_id")
    op.execute("""
        ALTER TABLE subscriptions
            ADD COLUMN IF NOT EXISTS stripe_customer_id      VARCHAR(255),
            ADD COLUMN IF NOT EXISTS stripe_subscription_id  VARCHAR(255),
            ADD COLUMN IF NOT EXISTS stripe_price_id         VARCHAR(255);
    """)

    # Restore stripe columns in payments
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS safepay_tracker")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS safepay_order_id")
    op.execute("""
        ALTER TABLE payments
            ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS stripe_invoice_id         VARCHAR(255),
            ADD COLUMN IF NOT EXISTS stripe_charge_id          VARCHAR(255);
    """)

    # Restore stripe_price_id in plans
    op.execute("ALTER TABLE plans ADD COLUMN IF NOT EXISTS stripe_price_id VARCHAR(255)")
