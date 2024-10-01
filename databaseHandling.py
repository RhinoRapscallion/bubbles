import sqlite3
import html
import base64
import json
import secrets
import time

class databaseHandler():
    def __init__(self, db: str) -> None:
        self.con = sqlite3.connect(db)
        self.cur = self.con.cursor()

        res = self.cur.execute("SELECT name FROM sqlite_master WHERE name='posts'")
        #print(res.fetchone())
        if res.fetchone() is None:
            print ("No Posts Table, Creating One Now")

            res = self.cur.execute("CREATE TABLE posts(id, timestamp ,author, title, body)")
            self.con.commit()
            res = self.cur.execute("SELECT name FROM sqlite_master WHERE name='posts'")
            print(res.fetchone())
        
        res = self.cur.execute("SELECT name FROM sqlite_master WHERE name='comments'")
        #print(res.fetchone())
        if res.fetchone() is None:
            print ("No Comments Table, Creating One Now")

            res = self.cur.execute("CREATE TABLE comments(id, postid, timestamp, author, body)")
            self.con.commit()
            res = self.cur.execute("SELECT name FROM sqlite_master")
            print(res.fetchone())
    
    def close(self):
        self.con.close()
    
    def get_max_id(self, _from :str):
        res = self.cur.execute(f"SELECT MAX(id) FROM {str}")
        max_id = res.fetchone()[0]

        return 0 if max_id is None else max_id
    
    def create_post(self, author: str, title: str, body:str):
        _id = secrets.token_urlsafe(6)
        _title = base64.encodebytes(html.escape(title).encode())
        _author = base64.encodebytes(html.escape(author).encode())
        _body = base64.encodebytes(html.escape(body).encode())

        self.cur.execute(f"INSERT INTO posts(id , timestamp, author, title, body) VALUES ('{_id}', {time.time()}, '{_author.decode().replace("\n", "")}', '{_title.decode().replace("\n", "")}', '{_body.decode().replace("\n", "")}');")
        self.con.commit()
        return _id
    
    def create_comment(self, author: str, postid:int, body:str):
        _id = secrets.token_urlsafe(6)
        _author = base64.encodebytes(html.escape(author).encode())
        _body = base64.encodebytes(html.escape(body).encode())

        self.cur.execute(f"INSERT INTO comments(id, timestamp, postid, author, body) VALUES ('{_id}', {time.time()},'{postid}', '{_author.decode().replace("\n", "")}', '{_body.decode().replace("\n", "")}');")
        self.con.commit()
        return postid
    
    def get_post(self, id):
        res = self.cur.execute(f"SELECT author, title, body FROM posts WHERE id='{id}'")
        fetch = res.fetchall()
        
        if fetch == None: return ()

        return [base64.decodebytes(x.encode()).decode() for x in fetch[0]]
    
    def get_posts(self, limit, sort):
        res = self.cur.execute(f"SELECT id, title FROM posts ORDER BY {sort} DESC LIMIT {limit}")
        fetch = res.fetchall()
        
        if fetch == None: return ()

        return [[item[0], base64.decodebytes(item[1].encode()).decode()] for item in fetch]

    def get_comments(self, postid):
        res = self.cur.execute(f"SELECT author, body FROM comments WHERE postid='{postid}' ORDER BY timestamp DESC")
        fetch = res.fetchall()
        if fetch == None: return ()

        return [[base64.decodebytes(x.encode()).decode() if not isinstance(x, int) else x for x in item] for item in fetch]

if __name__ == '__main__':
    dh = databaseHandler("posts.db")
    for x in dh.get_posts(10, "id"):
        print(x)

    print("--------------")

    for x in dh.get_posts(10, "RANDOM()"):
        print(x)

    print("--------------")

    for x in dh.get_comments(2):
        print(x)



