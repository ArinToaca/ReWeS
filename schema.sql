drop table if exists weather_history;
create table weather_history (
    weather_id integer primary key autoincrement,
    timestamp integer NOT NULL,
    temperature integer NOT NULL,
    pressure integer NOT NULL,
    humidity integer NOT NULL,
    dew_point integer NOT NULL,
    heat_index integer NOT NULL
);
