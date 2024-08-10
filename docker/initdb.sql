CREATE TABLE message (
    id SERIAL PRIMARY KEY,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP not null,
    estado VARCHAR(32) DEFAULT 'PENDIENTE' not null,
    topic varchar(64) not null,
    content VARCHAR(2000) not null
);

CREATE OR REPLACE FUNCTION clean_quotes() 
RETURNS TRIGGER AS $$
BEGIN
    -- Reemplaza &quot; con "
    NEW.content := REPLACE(NEW.content, '&quot;', '"');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER before_insert_clean_quotes
BEFORE INSERT ON message
FOR EACH ROW
EXECUTE FUNCTION clean_quotes();