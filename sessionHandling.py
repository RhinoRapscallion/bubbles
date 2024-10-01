from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import sqlite3
from jose import jwt
from jose.exceptions import *
import base64
import time

def init_password_database(db: str):
    con = sqlite3.connect(db)
    cur = con.cursor()

    res = cur.execute("SELECT name FROM sqlite_master WHERE name='users'")
    if res.fetchone() is None:
        print ("No Users Table, Creating One Now")

        res = cur.execute("CREATE TABLE users(user, author, passkey)")
        con.commit()
        res = cur.execute("SELECT name FROM sqlite_master WHERE name='users'")
        print(res.fetchone())
    
    con.close()

class sessionHandler():
    def __init__(self, jwt_secret: str, passwd_db: str):
        self.secret = jwt_secret
        self.db = passwd_db
    
    def new_user(self, username, password):
        ph = PasswordHasher()
        db_con = sqlite3.connect(self.db)
        db_cur = db_con.cursor()

        b64_username = base64.encodebytes(username.lower().encode()).decode()
        b64_author = base64.encodebytes(username.encode()).decode()
        passkey = ph.hash(password)

        res = db_cur.execute(f"SELECT user FROM users WHERE user='{b64_username}'")
        if not res.fetchone() is None: return False

        res = db_cur.execute(f"INSERT INTO users VALUES ('{b64_username}','{b64_author}','{passkey}')")
        db_con.commit()
        db_con.close()
        return True
    
    def login(self, username, password):
        ph = PasswordHasher()
        db_con = sqlite3.connect(self.db)
        db_cur = db_con.cursor()

        b64_username = base64.encodebytes(username.lower().encode()).decode()
        res = db_cur.execute(f"SELECT passkey FROM users WHERE user='{b64_username}'")
        passkey = res.fetchone()
        if passkey is None: return None

        try:
            if ph.verify(passkey[0], password):
                res = db_cur.execute(f"SELECT author FROM users WHERE user='{b64_username}'")
                cookie = jwt.encode({'author':res.fetchone()[0], "nbf":time.time(), 'exp':time.time()+3600}, self.secret)
                db_con.close()
                return cookie
            else:
                db_con.close()
                return None

        except VerifyMismatchError: 
            db_con.close()
            return None

    def verifyCookie(self, cookie):
        try:
            response = jwt.decode(cookie, self.secret)

            timenow = time.time()
            if response["exp"] < timenow or response["nbf"] > timenow:
                raise ValueError
            
            return base64.decodebytes(response["author"].encode()).decode()
        
        except (JWTError, JWTClaimsError, ExpiredSignatureError, KeyError, ValueError):
            return None


        

if __name__ == "__main__":
    init_password_database('usertest.db')
    sh = sessionHandler("TEST_SECRET", "usertest.db")
    print("Testing make New User")

    if sh.new_user("TESTUSER", "test_psk"): print("user TESTUSER created")
    

    print("Testing username checking")

    if sh.new_user("TESTUSER", "test_psk2") == 0: print("Test Failed")
    else: print("Test Passed")

    print('Logging into TESTUSER with correct psk')
    _jwt = sh.login("TESTUSER", "test_psk", "0.0.0.0")
    print(_jwt)

    if _jwt:
        print("Login Success, Trying JWT Verification")
        name = sh.verifyCookie(_jwt, "0.0.0.0")
        if name: print(name)
        else: print("JWT Verification Failed")
        

    print('Logging into TESTUSER with incorrect psk')
    print(sh.login("TESTUSER", "test", "0.0.0.0"))
