DROP TABLE IF EXISTS prefixes;
DROP TABLE IF EXISTS emojify_toggles;

CREATE TABLE IF NOT EXISTS prefixes (
	guild BIGINT PRIMARY KEY,
	prefix TEXT
);

-- DROP TABLE prefixes
-- CREATE TABLE prefixes (guild bigint PRIMARY KEY, prefix text)

CREATE TABLE IF NOT EXISTS emojify_toggles (
	guild BIGINT PRIMARY KEY,
	emojify BOOLEAN
);

-- ALTER TABLE emojify_toggles
-- CREATE TABLE emojify_toggles (guild bigint PRIMARY KEY, emojify bool)