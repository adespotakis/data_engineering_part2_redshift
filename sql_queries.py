import configparser


# CONFIG

config = configparser.ConfigParser()
config.read('dwh.cfg')
arn = config.get('IAM_ROLE', 'ARN')
log_manifest = config.get('S3', 'LOG_JSONPATH')
log_path = config.get('S3', 'LOG_DATA')
song_path = config.get('S3', 'SONG_DATA')
log_json_paths = config.get('S3', 'LOG_JSON_PATHS')
song_json_paths = config.get('S3', 'SONG_JSON_PATHS')

# DROP TABLES

songplay_table_drop = "DROP TABLE songplays;"
user_table_drop = "DROP TABLE users;"
song_table_drop = "DROP TABLE songs;"
artist_table_drop = "DROP TABLE artists;"
time_table_drop = "DROP TABLE time;"
staging_events_drop = "DROP TABLE staging_events;"
staging_songs_drop = "DROP TABLE staging_songs;"


# CREATE TABLES

staging_events_table_create = ("""
    CREATE TEMPORARY TABLE IF NOT EXISTS staging_logs (
        id INT IDENTITY(0,1) PRIMARY KEY NOT NULL,
        artist varchar,
        auth varchar,
        firstName varchar,
        gender varchar, 
        itemInSession int, 
        lastName varchar, 
        length numeric, 
        level varchar, 
        location varchar,
        method varchar,
        page varchar,
        registration numeric, 
        sessionId int,
        song varchar, 
        status int, 
        ts bigint,
        userAgent varchar,
        userId varchar
    );
""")


staging_songs_table_create = ("""
    CREATE TEMPORARY TABLE IF NOT EXISTS staging_songs (
        id INT IDENTITY(0,1) PRIMARY KEY NOT NULL,
        num_songs int,
        artist_id varchar,
        artist_latitude real,
        artist_longitude real, 
        artist_location varchar,
        artist_name varchar,
        song_id varchar,
        title varchar,
        duration real,
        year int
    );
""")


songplay_table_create = ("""
    CREATE TABLE IF NOT EXISTS songplays(
        songplay_id INT IDENTITY(0,1) PRIMARY KEY NOT NULL, 
        start_time timestamp NOT NULL, 
        user_id int NOT NULL, 
        level varchar(4), 
        song_id varchar,
        artist_id varchar, 
        session_id int, 
        user_agent varchar, 
        location varchar
    );
""")


user_table_create = ("""
    CREATE TABLE IF NOT EXISTS users (
        user_id int PRIMARY KEY NOT NULL,
        first_name varchar,
        last_name varchar,
        gender varchar(1), 
        level varchar(4)
    ); 
""")


song_table_create = ("""
    CREATE TABLE IF NOT EXISTS songs (
        song_id varchar PRIMARY KEY NOT NULL, 
        title varchar, 
        artist_id varchar NOT NULL, 
        year int, 
        duration real
    );
""")


artist_table_create = ("""
    CREATE TABLE IF NOT EXISTS artists (
        artist_id varchar PRIMARY KEY NOT NULL,
        name varchar, 
        location varchar, 
        latitude varchar, 
        longitude varchar
    );
""")


time_table_create = ("""
    CREATE TABLE IF NOT EXISTS time (
        start_time timestamp PRIMARY KEY NOT NULL,
        hour int,
        day int, 
        week int, 
        month int, 
        year int, 
        weekday varchar
    );
""")

# STAGING TABLES

staging_events_copy = ("""
    COPY staging_logs
    FROM {}
    IAM_ROLE {}
    REGION 'us-west-2'
    JSON {};
""").format(log_path, arn, log_json_paths)


staging_songs_copy = ("""
    COPY staging_songs
    FROM {}
    IAM_ROLE {}
    REGION 'us-west-2'
    JSON {};
""").format(song_path, arn, song_json_paths)


# INSERT INTO TABLES

songplay_table_insert = ("""
    INSERT INTO songplays (
        start_time, 
        user_id, 
        level, 
        session_id, 
        location, 
        user_agent,
        song_id, 
        artist_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""")


user_table_insert = ("""
    INSERT INTO users  (
        user_id, 
        first_name, 
        last_name, 
        gender,
        level)
    VALUES (%s, %s, %s, %s, %s)
""")


song_table_fast_insert = ("""
    INSERT INTO songs (
        song_id, 
        title, 
        artist_id, 
        year, 
        duration)
    SELECT DISTINCT song_id, title, artist_id, year, duration FROM staging_songs
""")


artist_table_fast_insert = ("""
    INSERT INTO artists (
        artist_id, 
        name, 
        location, 
        latitude, 
        longitude)
    SELECT 
        artist_id, 
        artist_name, 
        artist_location, 
        artist_latitude, 
        artist_longitude 
    FROM staging_songs
    GROUP BY artist_id, artist_name, artist_location, artist_latitude, artist_longitude
    ORDER BY MAX(id) DESC;
""")


time_table_insert = ("""
    INSERT INTO time (
        start_time,
        hour,
        day,
        week,
        month,
        year,
        weekday)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""")

# SELECT FROM STAGING

events_select = ("""
    SELECT 
        userId, 
        firstName,
        lastName, 
        gender,
        level,
        ts,
        artist,
        song, 
        length,
        location,
        sessionId,
        userAgent
    FROM staging_logs
    WHERE page = 'NextSong'
""")  # users and time tables


artists_select = ("""
    SELECT 
        songs.song_id,
        songs.title, 
        artists.artist_id, 
        artists.name
    FROM songs
    JOIN artists ON songs.artist_id = artists.artist_id
""")  # songs and artists tables


artist_and_song_id_select = ("""
    SELECT songs.song_id, artists.artist_id
    FROM artists
    JOIN songs ON songs.title=%s
    WHERE name = %s AND duration = %s;
""")


# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create,
                        user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_temp_table_queries = [staging_events_table_create, staging_songs_table_create]
