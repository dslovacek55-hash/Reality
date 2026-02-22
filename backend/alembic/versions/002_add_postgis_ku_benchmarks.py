"""Add PostGIS extension, prague_ku, ku_price_stats, reference_benchmarks tables

Revision ID: 002
Revises: 001
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Add KÚ columns to properties
    op.add_column('properties', sa.Column('ku_kod', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('ku_nazev', sa.String(200), nullable=True))
    op.create_index('idx_properties_ku', 'properties', ['ku_kod'],
                    postgresql_where=sa.text('ku_kod IS NOT NULL'))

    # Prague KÚ polygon boundaries
    op.execute("""
        CREATE TABLE IF NOT EXISTS prague_ku (
            id SERIAL PRIMARY KEY,
            ku_kod INTEGER NOT NULL UNIQUE,
            ku_nazev VARCHAR(200) NOT NULL,
            geom GEOMETRY(MultiPolygon, 4326) NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_prague_ku_geom ON prague_ku USING GIST (geom)")

    # Computed price stats per KÚ
    op.execute("""
        CREATE TABLE IF NOT EXISTS ku_price_stats (
            id SERIAL PRIMARY KEY,
            ku_kod INTEGER NOT NULL,
            ku_nazev VARCHAR(200) NOT NULL,
            property_type VARCHAR(30),
            transaction_type VARCHAR(20) NOT NULL,
            median_price_m2 NUMERIC(14, 2),
            avg_price_m2 NUMERIC(14, 2),
            sample_count INTEGER DEFAULT 0,
            computed_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT uq_ku_price_stats UNIQUE (ku_kod, property_type, transaction_type)
        )
    """)

    # Shared external reference benchmarks table
    op.execute("""
        CREATE TABLE IF NOT EXISTS reference_benchmarks (
            id SERIAL PRIMARY KEY,
            source VARCHAR(50) NOT NULL,
            region VARCHAR(200) NOT NULL,
            property_type VARCHAR(30),
            transaction_type VARCHAR(20),
            price_m2 NUMERIC(14, 2),
            period VARCHAR(20),
            fetched_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT uq_ref_benchmark UNIQUE (source, region, property_type, transaction_type, period)
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS reference_benchmarks")
    op.execute("DROP TABLE IF EXISTS ku_price_stats")
    op.execute("DROP TABLE IF EXISTS prague_ku")
    op.drop_index('idx_properties_ku', 'properties')
    op.drop_column('properties', 'ku_nazev')
    op.drop_column('properties', 'ku_kod')
    op.execute("DROP EXTENSION IF EXISTS postgis")
