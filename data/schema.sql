CREATE TABLE guilds (
    guild_id BIGINT PRIMARY KEY,
    prefix TEXT NOT NULL,
    emojify_toggle BOOLEAN NOT NULL
);