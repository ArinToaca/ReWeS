drop table if exists rain_history;
create table rain_history(
    rain_id integer primary key autoincrement,
    timestamp integer NOT NULL,
    rain integer NOT NULL
);
