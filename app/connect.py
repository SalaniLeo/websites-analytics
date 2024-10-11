import psycopg2

def connect(config):
    """ Connect to the PostgreSQL database server """
    try:
        with psycopg2.connect(**config) as conn:
            print('Connected.')
            return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)