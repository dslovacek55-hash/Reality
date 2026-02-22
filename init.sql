-- Czech Real Estate Tracker — Database Schema

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS properties (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,           -- 'sreality', 'bezrealitky', 'idnes'
    external_id VARCHAR(100) NOT NULL,
    url TEXT,
    title TEXT,
    description TEXT,
    property_type VARCHAR(30),             -- 'byt', 'dum', 'pozemek', 'komercni'
    transaction_type VARCHAR(20),          -- 'prodej', 'pronajem'
    disposition VARCHAR(20),              -- '1+kk', '2+1', '3+kk', etc.
    price NUMERIC(14, 2),
    price_currency VARCHAR(10) DEFAULT 'CZK',
    size_m2 NUMERIC(10, 2),
    rooms INTEGER,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    ku_kod INTEGER,
    ku_nazev VARCHAR(200),
    city VARCHAR(200),
    district VARCHAR(200),
    address TEXT,
    images JSONB DEFAULT '[]'::jsonb,
    raw_data JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'removed', 'sold'
    duplicate_of BIGINT REFERENCES properties(id) ON DELETE SET NULL,
    missed_runs INTEGER DEFAULT 0,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    search_vector TSVECTOR,
    CONSTRAINT uq_source_external UNIQUE (source, external_id)
);

CREATE TABLE IF NOT EXISTS price_history (
    id BIGSERIAL PRIMARY KEY,
    property_id BIGINT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    price NUMERIC(14, 2) NOT NULL,
    price_per_m2 NUMERIC(14, 2),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_filters (
    id BIGSERIAL PRIMARY KEY,
    telegram_chat_id BIGINT NOT NULL,
    name VARCHAR(200) DEFAULT 'My Filter',
    property_type VARCHAR(30),
    transaction_type VARCHAR(20),
    city VARCHAR(200),
    district VARCHAR(200),
    disposition TEXT,                      -- comma-separated: '1+kk,2+kk,2+1'
    price_min NUMERIC(14, 2),
    price_max NUMERIC(14, 2),
    size_min NUMERIC(10, 2),
    size_max NUMERIC(10, 2),
    notify_new BOOLEAN DEFAULT TRUE,
    notify_price_drop BOOLEAN DEFAULT TRUE,
    price_drop_threshold NUMERIC(5, 2) DEFAULT 5.0,  -- percentage
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    user_filter_id BIGINT REFERENCES user_filters(id) ON DELETE CASCADE,
    property_id BIGINT REFERENCES properties(id) ON DELETE CASCADE,
    notification_type VARCHAR(30) NOT NULL, -- 'new_listing', 'price_drop', 'removed'
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scrape_runs (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    listings_found INTEGER DEFAULT 0,
    listings_new INTEGER DEFAULT 0,
    listings_updated INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running'  -- 'running', 'completed', 'failed'
);

-- Price history trigger
CREATE OR REPLACE FUNCTION track_price_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.price IS DISTINCT FROM NEW.price THEN
        INSERT INTO price_history (property_id, price, price_per_m2)
        VALUES (
            NEW.id,
            NEW.price,
            CASE WHEN NEW.size_m2 > 0 THEN ROUND(NEW.price / NEW.size_m2, 2) END
        );
        NEW.updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_price_change
    BEFORE UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION track_price_change();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_updated_at
    BEFORE UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Insert initial price history on new listing
CREATE OR REPLACE FUNCTION record_initial_price()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.price IS NOT NULL THEN
        INSERT INTO price_history (property_id, price, price_per_m2)
        VALUES (
            NEW.id,
            NEW.price,
            CASE WHEN NEW.size_m2 > 0 THEN ROUND(NEW.price / NEW.size_m2, 2) END
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_initial_price
    AFTER INSERT ON properties
    FOR EACH ROW
    EXECUTE FUNCTION record_initial_price();

-- Indexes
CREATE INDEX IF NOT EXISTS idx_properties_filters
    ON properties (city, property_type, transaction_type);

CREATE INDEX IF NOT EXISTS idx_properties_price_active
    ON properties (price)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_properties_last_seen
    ON properties (last_seen_at);

CREATE INDEX IF NOT EXISTS idx_properties_status
    ON properties (status);

CREATE INDEX IF NOT EXISTS idx_properties_geo
    ON properties (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_properties_duplicate
    ON properties (duplicate_of)
    WHERE duplicate_of IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_price_history_property
    ON price_history (property_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_filters_chat
    ON user_filters (telegram_chat_id)
    WHERE active = TRUE;

CREATE INDEX IF NOT EXISTS idx_notifications_property
    ON notifications (property_id, notification_type);

-- Full-text search: generated column + GIN index
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

CREATE TRIGGER trg_search_vector
    BEFORE INSERT OR UPDATE OF title, city, district, address, description
    ON properties
    FOR EACH ROW
    EXECUTE FUNCTION properties_search_vector_update();

CREATE INDEX IF NOT EXISTS idx_properties_search
    ON properties USING GIN (search_vector);

-- Favorites table
CREATE TABLE IF NOT EXISTS favorites (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,       -- anonymous browser session or user id
    property_id BIGINT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_favorite UNIQUE (session_id, property_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_session
    ON favorites (session_id);

-- Email subscriptions table
CREATE TABLE IF NOT EXISTS email_subscriptions (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    property_type VARCHAR(30),
    transaction_type VARCHAR(20),
    city VARCHAR(200),
    disposition TEXT,
    price_min NUMERIC(14, 2),
    price_max NUMERIC(14, 2),
    size_min NUMERIC(10, 2),
    size_max NUMERIC(10, 2),
    notify_new BOOLEAN DEFAULT TRUE,
    notify_price_drop BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_subscriptions_email
    ON email_subscriptions (email)
    WHERE active = TRUE;

-- KÚ index on properties
CREATE INDEX IF NOT EXISTS idx_properties_ku
    ON properties (ku_kod)
    WHERE ku_kod IS NOT NULL;

-- Prague KÚ polygon boundaries
CREATE TABLE IF NOT EXISTS prague_ku (
    id SERIAL PRIMARY KEY,
    ku_kod INTEGER NOT NULL UNIQUE,
    ku_nazev VARCHAR(200) NOT NULL,
    geom GEOMETRY(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_prague_ku_geom ON prague_ku USING GIST (geom);

-- Computed price stats per KÚ
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
);

-- Shared external reference benchmarks table
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
);
