"""Add search_vector, favorites, and email_subscriptions

Revision ID: 001
Revises:
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add search_vector column to properties
    op.add_column('properties', sa.Column('search_vector', TSVECTOR()))

    # Create GIN index for full-text search
    op.create_index('idx_properties_search', 'properties', ['search_vector'],
                     postgresql_using='gin')

    # Create FTS trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION properties_search_vector_update()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('simple', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('simple', COALESCE(NEW.city, '')), 'A') ||
                setweight(to_tsvector('simple', COALESCE(NEW.district, '')), 'B') ||
                setweight(to_tsvector('simple', COALESCE(NEW.address, '')), 'B') ||
                setweight(to_tsvector('simple', COALESCE(NEW.description, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_search_vector
            BEFORE INSERT OR UPDATE OF title, city, district, address, description
            ON properties
            FOR EACH ROW
            EXECUTE FUNCTION properties_search_vector_update();
    """)

    # Backfill existing rows
    op.execute("""
        UPDATE properties SET search_vector =
            setweight(to_tsvector('simple', COALESCE(title, '')), 'A') ||
            setweight(to_tsvector('simple', COALESCE(city, '')), 'A') ||
            setweight(to_tsvector('simple', COALESCE(district, '')), 'B') ||
            setweight(to_tsvector('simple', COALESCE(address, '')), 'B') ||
            setweight(to_tsvector('simple', COALESCE(description, '')), 'C');
    """)

    # Create favorites table
    op.create_table(
        'favorites',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('property_id', sa.BigInteger(), sa.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('session_id', 'property_id', name='uq_favorite'),
    )
    op.create_index('idx_favorites_session', 'favorites', ['session_id'])

    # Create email_subscriptions table
    op.create_table(
        'email_subscriptions',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('property_type', sa.String(30)),
        sa.Column('transaction_type', sa.String(20)),
        sa.Column('city', sa.String(200)),
        sa.Column('disposition', sa.Text()),
        sa.Column('price_min', sa.Numeric(14, 2)),
        sa.Column('price_max', sa.Numeric(14, 2)),
        sa.Column('size_min', sa.Numeric(10, 2)),
        sa.Column('size_max', sa.Numeric(10, 2)),
        sa.Column('notify_new', sa.Boolean(), server_default='true'),
        sa.Column('notify_price_drop', sa.Boolean(), server_default='true'),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_email_subscriptions_email', 'email_subscriptions', ['email'])


def downgrade() -> None:
    op.drop_index('idx_email_subscriptions_email')
    op.drop_table('email_subscriptions')
    op.drop_index('idx_favorites_session')
    op.drop_table('favorites')
    op.execute("DROP TRIGGER IF EXISTS trg_search_vector ON properties")
    op.execute("DROP FUNCTION IF EXISTS properties_search_vector_update()")
    op.drop_index('idx_properties_search')
    op.drop_column('properties', 'search_vector')
