"""Add SaaS models: plans, subscriptions, payments

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-25 12:59:07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    # Create subscriptionstatus enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE subscriptionstatus AS ENUM (
                'active','trialing','past_due','canceled',
                'incomplete','incomplete_expired','unpaid','paused'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Create paymentstatus enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymentstatus AS ENUM (
                'pending','succeeded','failed','refunded','canceled'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Create paymenttype enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymenttype AS ENUM (
                'subscription','upgrade','downgrade','refund'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    
    # Create plans table
    op.create_table(
        'plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_monthly', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('stripe_price_id', sa.String(length=255), nullable=True),
        sa.Column('monthly_executions', sa.Integer(), nullable=False),
        sa.Column('max_api_keys', sa.Integer(), nullable=False),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False),
        sa.Column('memory_limit_mb', sa.Integer(), nullable=False),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False),
        sa.Column('api_access_enabled', sa.Boolean(), nullable=False),
        sa.Column('priority_execution', sa.Boolean(), nullable=False),
        sa.Column('support_level', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_plans_key ON plans (key)")

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('plan_id', sa.String(length=36), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_price_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_subscriptions_user_id ON subscriptions (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_subscriptions_plan_id ON subscriptions (plan_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_subscriptions_stripe_customer_id ON subscriptions (stripe_customer_id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_subscriptions_stripe_subscription_id ON subscriptions (stripe_subscription_id)")

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('subscription_id', sa.String(length=36), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_charge_id', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('payment_type', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('receipt_url', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_user_id ON payments (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_subscription_id ON payments (subscription_id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_payments_stripe_payment_intent_id ON payments (stripe_payment_intent_id) WHERE stripe_payment_intent_id IS NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_stripe_invoice_id ON payments (stripe_invoice_id)")

    # Remove plan enum column from users table (only if it exists)
    op.execute("""
        ALTER TABLE users DROP COLUMN IF EXISTS plan;
    """)
    
    # Insert default plans
    op.execute("""
        INSERT INTO plans (id, created_at, updated_at, key, name, description, price_monthly, 
                          monthly_executions, max_api_keys, timeout_seconds, memory_limit_mb, 
                          rate_limit_per_minute, api_access_enabled, priority_execution, 
                          support_level, is_active, is_public, sort_order)
        VALUES 
            (gen_random_uuid(), NOW(), NOW(), 'free', 'Free', 
             'Perfect for learning and experimenting', 0.00,
             100, 0, 5, 128, 10, FALSE, FALSE, 'community', TRUE, TRUE, 1),
            (gen_random_uuid(), NOW(), NOW(), 'starter', 'Starter', 
             'For small projects and personal use', 9.00,
             1000, 2, 10, 256, 30, TRUE, FALSE, 'email', TRUE, TRUE, 2),
            (gen_random_uuid(), NOW(), NOW(), 'pro', 'Pro', 
             'For professional developers and teams', 19.00,
             5000, 5, 30, 512, 100, TRUE, TRUE, 'priority', TRUE, TRUE, 3),
            (gen_random_uuid(), NOW(), NOW(), 'business', 'Business', 
             'For businesses with high-volume needs', 49.00,
             25000, 20, 60, 1024, 300, TRUE, TRUE, 'priority', TRUE, TRUE, 4)
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS payments CASCADE")
    op.execute("DROP TABLE IF EXISTS subscriptions CASCADE")
    op.execute("DROP TABLE IF EXISTS plans CASCADE")
    op.execute("DROP TYPE IF EXISTS paymenttype")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus")
    # Re-add plan column
    op.execute("DO $$ BEGIN CREATE TYPE userplan AS ENUM ('FREE','DEVELOPER','PRO'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan userplan NOT NULL DEFAULT 'FREE'")
