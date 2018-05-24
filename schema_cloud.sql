drop table if exists cloud_history;
create table cloud_history (
    cloud_id integer primary key autoincrement,
    timestamp integer NOT NULL,
    cloud_coverage integer NOT NULL
);
