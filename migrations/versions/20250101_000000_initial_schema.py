"""Print Hub - Initial database schema.

Revision ID: initial_schema
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('building', sa.String(length=100), nullable=True),
        sa.Column('entrance', sa.String(length=50), nullable=True),
        sa.Column('room', sa.String(length=50), nullable=True),
        sa.Column('is_free_user', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=False)
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('prepared_file_path', sa.String(length=1000), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('print_mode', sa.String(length=50), nullable=True),
        sa.Column('copies', sa.Integer(), nullable=True),
        sa.Column('total_physical_pages', sa.Integer(), nullable=True),
        sa.Column('price_per_page', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('total_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_free_order', sa.Boolean(), nullable=False, default=False),
        sa.Column('status', sa.String(length=50), nullable=False, default='created'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('file_cleanup_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['telegram_id'], ['users.telegram_id'], )
    )
    op.create_index('ix_orders_telegram_id_status', 'orders', ['telegram_id', 'status'], unique=False)
    op.create_index('ix_orders_created_at', 'orders', ['created_at'], unique=False)
    op.create_index('ix_orders_status', 'orders', ['status'], unique=False)
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('provider_payment_id', sa.String(length=500), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, default='RUB'),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('webhook_payload', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.UniqueConstraint('order_id'),
        sa.UniqueConstraint('provider_payment_id'),
        sa.UniqueConstraint('idempotency_key')
    )
    op.create_index('ix_payments_order_id', 'payments', ['order_id'], unique=False)
    op.create_index('ix_payments_status', 'payments', ['status'], unique=False)
    op.create_index('ix_payments_provider_payment_id', 'payments', ['provider_payment_id'], unique=False)
    
    # Create print_agents table
    op.create_table(
        'print_agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_uuid', sa.String(length=100), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=True),
        sa.Column('mac_address', sa.String(length=50), nullable=True),
        sa.Column('printer_name', sa.String(length=255), nullable=True),
        sa.Column('printer_model', sa.String(length=500), nullable=True),
        sa.Column('is_online', sa.Boolean(), nullable=False, default=False),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('printer_status', sa.String(length=50), nullable=True),
        sa.Column('paper_status', sa.String(length=50), nullable=True),
        sa.Column('ink_status', sa.String(length=50), nullable=True),
        sa.Column('current_job_id', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('registered_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_uuid')
    )
    op.create_index('ix_print_agents_uuid', 'print_agents', ['agent_uuid'], unique=False)
    op.create_index('ix_print_agents_is_online', 'print_agents', ['is_online'], unique=False)
    
    # Create print_jobs table
    op.create_table(
        'print_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('print_job_uuid', sa.String(length=100), nullable=False),
        sa.Column('print_artifact_path', sa.String(length=1000), nullable=False),
        sa.Column('print_mode', sa.String(length=50), nullable=False),
        sa.Column('copies', sa.Integer(), nullable=False),
        sa.Column('start_page', sa.Integer(), nullable=False, default=1),
        sa.Column('end_page', sa.Integer(), nullable=True),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('pages_printed', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('sent_to_agent_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('printing_started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['agent_id'], ['print_agents.id'], ),
        sa.UniqueConstraint('print_job_uuid')
    )
    op.create_index('ix_print_jobs_order_id_status', 'print_jobs', ['order_id', 'status'], unique=False)
    op.create_index('ix_print_jobs_agent_id', 'print_jobs', ['agent_id'], unique=False)
    
    # Create pricing_rules table
    op.create_table(
        'pricing_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('print_mode', sa.String(length=50), nullable=False),
        sa.Column('price_per_page', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('valid_from', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_type', 'print_mode', 'valid_from', name='uq_pricing_rule_unique')
    )
    op.create_index('ix_pricing_rules_active', 'pricing_rules', ['is_active'], unique=False)
    
    # Create admin_actions table
    op.create_table(
        'admin_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=True),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('old_state', sa.String(length=500), nullable=True),
        sa.Column('new_state', sa.String(length=500), nullable=True),
        sa.Column('action_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_admin_actions_admin_id', 'admin_actions', ['admin_telegram_id'], unique=False)
    op.create_index('ix_admin_actions_created_at', 'admin_actions', ['created_at'], unique=False)
    op.create_index('ix_admin_actions_action_type', 'admin_actions', ['action_type'], unique=False)
    
    # Create file_cleanup_log table
    op.create_table(
        'file_cleanup_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('original_file_path', sa.String(length=1000), nullable=False),
        sa.Column('prepared_file_path', sa.String(length=1000), nullable=True),
        sa.Column('print_artifact_path', sa.String(length=1000), nullable=True),
        sa.Column('reason', sa.String(length=100), nullable=False, default='retention_policy'),
        sa.Column('deleted_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], )
    )
    op.create_index('ix_file_cleanup_log_order_id', 'file_cleanup_log', ['order_id'], unique=False)
    op.create_index('ix_file_cleanup_log_deleted_at', 'file_cleanup_log', ['deleted_at'], unique=False)


def downgrade() -> None:
    op.drop_table('file_cleanup_log')
    op.drop_table('admin_actions')
    op.drop_table('pricing_rules')
    op.drop_table('print_jobs')
    op.drop_table('print_agents')
    op.drop_table('payments')
    op.drop_table('orders')
    op.drop_table('users')
