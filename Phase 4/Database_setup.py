import sqlite3
from contextlib import closing

def get_db_connection(db_file_name):
    conn = sqlite3.connect(db_file_name)
    return conn

def execute_query(db_name, query):
    with closing(get_db_connection(db_name)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(query)
        connection.commit()
        return cursor.fetchall()

def create_table():
    execute_query(
         "dashboard.db",
         '''
            DROP TABLE IF EXISTS 'USERS';
         '''
    )
    execute_query(
        "dashboard.db",
        '''
            CREATE TABLE USERS (
                USER_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                NAME VARCHAR NOT NULL,
                MAX_TEMPERATURE_THRESHOLD DECIMAL NOT NULL,
                MAX_LIGHT_INTENSITY_THRESHOLD INT NOT NULL,
                RFID_TAG_NUMBER TEXT
        );
    '''
    )
    print("users table created successfully")

def insert_user(db_name, name, max_temperature, max_light_intensity, rfid_tag_number):
    query = f"""
        INSERT INTO USERS (NAME, MAX_TEMPERATURE_THRESHOLD, MAX_LIGHT_INTENSITY_THRESHOLD, RFID_TAG_NUMBER) 
        VALUES ('{name}', {max_temperature}, {max_light_intensity}, '{rfid_tag_number}')
    """
    execute_query(db_name, query)

def delete_user(conn, user_id, threshold_id):
    query = f"""
        DELETE FROM USERS 
        WHERE USER_ID = {user_id} AND THRESHOLD_ID = {threshold_id}
    """
    execute_query(conn, query) 

def select_user_by_rfid(db_name, rfid_tag_number):
    query = f"""
        SELECT *
        FROM USERS
        WHERE RFID_TAG_NUMBER = '{rfid_tag_number}'
    """
    result = execute_query(db_name, query)
    return result
