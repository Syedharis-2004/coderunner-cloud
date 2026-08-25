"""Initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-08-20

Creates all core tables:
    users, projects, executions, api_keys, usage_records
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('role', sa.Enum('USER', 'ADMIN', name='userrole'), nullable=False, server_default='USER'),
        sa.Column('plan', sa.Enum('FREE', 'DEVELOPER', 'PRO', name='userplan'), nullable=False, server_default='FREE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # ── api_keys ───────────────────────────────────────────────────────────────
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(32), nullable=False),
        sa.Column('key_hash', sa.String(128), nullable=False, unique=True, index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # ── projects ───────────────────────────────────────────────────────────────
    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('language', sa.String(50), nullable=False, server_default='python'),
        sa.Column('code', sa.Text(), nullable=False, server_default=''),
        sa.Column('stdin_data', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('public_share_id', sa.String(36), nullable=True, unique=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # ── executions ─────────────────────────────────────────────────────────────
    op.create_table(
        'executions',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('api_key_id', sa.String(36), sa.ForeignKey('api_keys.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('language', sa.String(50), nullable=False, index=True),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('stdin_data', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum(
            'QUEUED', 'RUNNING', 'SUCCESS', 'FAILED',
            'COMPILE_ERROR', 'RUNTIME_ERROR', 'TIMEOUT',
            'MEMORY_LIMIT', 'CPU_LIMIT', 'CANCELLED', 'SYSTEM_ERROR',
            name='executionstatus'
        ), nullable=False, server_default='QUEUED', index=True),
        sa.Column('source', sa.Enum('WEB_EDITOR', 'REST_API', name='executionsource'), nullable=False, server_default='WEB_EDITOR'),
        sa.Column('stdout', sa.Text(), nullable=True),
        sa.Column('stderr', sa.Text(), nullable=True),
        sa.Column('exit_code', sa.Integer(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('memory_used_bytes', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # ── usage_records ──────────────────────────────────────────────────────────
    op.create_table(
        'usage_records',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('billing_period', sa.String(7), nullable=False, index=True),
        sa.Column('total_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('api_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_compute_seconds', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'billing_period', name='uq_usage_user_period'),
    )


def downgrade() -> None:
    op.drop_table('usage_records')
    op.drop_table('executions')
    op.drop_table('projects')
    op.drop_table('api_keys')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS executionstatus")
    op.execute("DROP TYPE IF EXISTS executionsource")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS userplan")
