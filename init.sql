-- Czech Real Estate Tracker — Database Schema

CREATE TABLE IF NOT EXISTS properties (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,           -- 'sreality', 'bazos', 'bezrealitky'
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
