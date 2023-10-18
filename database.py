import psycopg2
from dotenv import load_dotenv
import os
import pymongo
from pymongo import MongoClient

load_dotenv()

DATABASE_URL = os.environ['DATABASE_URL']
MONGODB_URL = os.environ['MONGODB_URL']

# Conexión a PostgreSQL
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

# Conexión a MongoDB
client = MongoClient(host=MONGODB_URL)
mongo_db = client.FCpay

def get_connection():
    return conn

def release_connection(conn):
    conn.close()

def get_cursor():
    return cursor

def get_mongo():
    return mongo_db
