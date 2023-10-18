from fastapi import HTTPException
from datetime import datetime
from database import get_mongo, get_cursor

def get_user_by_email(email: str, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def save_token_to_mongo(email, token, db):
    collection = db.tokens
    collection.update_one(
        {"email": email},   
        {"$set": {"email": email, "token": token, "created_at": datetime.utcnow()}},
        upsert=True
    )

def get_email_from_token(token: str):
    db = get_mongo()
    collection = db.tokens
    token_data = collection.find_one({"token": token})
    if token_data:
        return token_data["email"]
    return None

def get_codedata_from_token(token: str):
    db = get_mongo()
    collection = db.tokens
    token_data = collection.find_one({"token": token})
    # search user with email
    if token_data:
        email = token_data["email"]
        cursor = get_cursor()
        cursor.execute("SELECT * FROM usuario WHERE correo_electronico = %s", (email,))
        user = cursor.fetchone()
        print(user)
        print(user[-2])
        if user:
            return user[-1], user[-2] 
    
    return None

def get_id_from_token(token: str):
    db = get_mongo()
    collection = db.tokens
    token_data = collection.find_one({"token": token})
    # search user with email
    if token_data:
        email = token_data["email"]
        cursor = get_cursor()
        cursor.execute("SELECT * FROM usuario WHERE correo_electronico = %s", (email,))
        user = cursor.fetchone()
        if user:
            return user[0] 
    
    return None