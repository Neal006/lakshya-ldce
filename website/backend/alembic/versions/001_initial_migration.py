"""initial migration with all tables and indexes

Revision ID: 001
Revises:
Create Date: 2025-01-15 10:30:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table('profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='call_attender'),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('TRUE')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint("role IN ('admin', 'qa', 'call_attender')", name='profiles_role_check'),
    )
    op.create_index('idx_profiles_email', 'profiles', ['email'])
    op.create_index('idx_profiles_role', 'profiles', ['role'])

    op.create_table('customers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_customers_email', 'customers', ['email'])

    op.create_table('complaints',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(20), nullable=True),
        sa.Column('priority', sa.String(10), nullable=True),
        sa.Column('resolution_steps', sa.Text(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('submitted_via', sa.String(20), nullable=False, server_default='dashboard'),
        sa.Column('escalation_reason', sa.Text(), nullable=True),
        sa.Column('sla_deadline', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('sla_breached', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('escalated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint("category IN ('Product', 'Packaging', 'Trade')", name='complaints_category_check'),
        sa.CheckConstraint("priority IN ('High', 'Medium', 'Low')", name='complaints_priority_check'),
        sa.CheckConstraint("status IN ('open', 'in_progress', 'resolved', 'escalated')", name='complaints_status_check'),
        sa.CheckConstraint("submitted_via IN ('email', 'call', 'dashboard')", name='complaints_submitted_via_check'),
    )
    op.create_index('idx_complaints_customer_id', 'complaints', ['customer_id'])
    op.create_index('idx_complaints_status', 'complaints', ['status'])
    op.create_index('idx_complaints_created_at', 'complaints', [sa.text('created_at DESC')])
    op.create_index('idx_complaints_status_created', 'complaints', ['status', sa.text('created_at DESC')])
    op.create_index('idx_complaints_category_priority', 'complaints', ['category', 'priority'])
    op.create_index('idx_complaints_sla_breach', 'complaints', ['sla_deadline', 'sla_breached'])
    op.create_index('idx_complaints_submitted_via', 'complaints', ['submitted_via', sa.text('created_at DESC')])
    op.create_index('idx_complaints_customer_created', 'complaints', ['customer_id', sa.text('created_at DESC')])

    op.create_table('complaint_timeline',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('complaint_id', sa.String(36), sa.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('performed_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_timeline_complaint_id', 'complaint_timeline', ['complaint_id'])
    op.create_index('idx_timeline_complaint_created', 'complaint_timeline', ['complaint_id', 'created_at'])

    op.create_table('sla_config',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('priority', sa.String(10), nullable=False, unique=True),
        sa.Column('deadline_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint("priority IN ('High', 'Medium', 'Low')", name='sla_config_priority_check'),
    )

    op.create_table('daily_metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('date', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('total_complaints', sa.Integer(), server_default='0'),
        sa.Column('open_complaints', sa.Integer(), server_default='0'),
        sa.Column('resolved_complaints', sa.Integer(), server_default='0'),
        sa.Column('escalated_complaints', sa.Integer(), server_default='0'),
        sa.Column('avg_resolution_time_hours', sa.Float(), nullable=True),
        sa.Column('sla_compliance_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_metrics_date', 'daily_metrics', ['date'])


def downgrade() -> None:
    op.drop_table('daily_metrics')
    op.drop_table('sla_config')
    op.drop_table('complaint_timeline')
    op.drop_table('complaints')
    op.drop_table('customers')
    op.drop_table('profiles')