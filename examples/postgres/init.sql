CREATE TABLE IF NOT EXISTS public.user 
(
    id              INTEGER                     NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name            VARCHAR                     NOT NULL,
    nick_name       VARCHAR                     NULL,
    salary          INTEGER                     NOT NULL,
    registered_at   TIMESTAMP WITH TIME ZONE    NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE    NOT NULL,
    updated_at      TIMESTAMP WITH TIME ZONE    NOT NULL
);