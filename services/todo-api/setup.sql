-- CNPG for some reason is creating this user with different password than what is specified in secret
ALTER ROLE todo_db_admin WITH PASSWORD 'secure_password_here';

-- Connect to the todo_db database
\c todo_db;

-- If this schema is created by postgres user, we need to change its owner to todo_db_admin
CREATE SCHEMA todo;
ALTER SCHEMA todo OWNER TO todo_db_admin;

-- We need to specify the search_path to todo
ALTER USER todo_db_admin SET search_path TO todo;