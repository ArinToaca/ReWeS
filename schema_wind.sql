drop table if exists wind_history;
create table wind_history(
    wind_id integer primary key autoincrement,
    timestamp integer NOT NULL,
    wind_direction integer NOT NULL,
    wind_speed integer NOT NULL
);
