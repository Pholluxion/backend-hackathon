import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.environ['DATABASE_URL']
print(DATABASE_URL)

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

def get_connection():
    return conn

def release_connection(conn):
    conn.close()

def get_cursor():
    return cursor
