from flask import Flask, request, redirect, render_template, make_response
from databaseHandling import *
from sessionHandling import *
from server_secrets import *

app = Flask(__name__)

@app.get("/")
def landing_GET():
    sh = sessionHandler(JWT_SECRET, "users.db")
    cookies = request.cookies

    if "jwt" in cookies:
        _jwt = cookies.get("jwt")
        name = sh.verifyCookie(_jwt)
    else:
        name = None

    dbh = databaseHandler("posts.db")
    
    _recent = dbh.get_posts(15, "timestamp")
    _random = dbh.get_posts(15, "RANDOM()")

    retext = ''
    for x in _recent: retext += f"<br><a class='link' href='{f"/post?id={x[0]}"}'>&gt; {x[1]}</a>"

    ratext = ''
    for x in _random: ratext += f"<br><a class='link' href='{f"/post?id={x[0]}"}'>&gt; {x[1]}</a>"


    dbh.close()
    #return string
    ret = render_template("home.html",
                          usertext=f"{f"Logged in as {name} | " if name else ""}",
                          loginlink=f"{"/logout" if name else "/login"}", 
                          logintext=f"{"Logout" if name else "Login"}", 
                          recent=retext, 
                          random=ratext)
    resp = make_response(ret)
    resp.set_cookie("lastviewedpage", json.dumps({"page":"/"}))
    return resp

@app.get("/newpost")
def newpost_GET():
    sh = sessionHandler(JWT_SECRET, "users.db")
    cookies = request.cookies
    title = ""
    body = ""

    if "post" in cookies:
        post_content = json.loads(cookies.get("post"))
        print(post_content)
        title = post_content["title"]
        body = post_content["body"]
    if "jwt" in cookies:
        _jwt = cookies.get("jwt")
        name = sh.verifyCookie(_jwt)
        if name == None:
            return redirect("/login?exp=true")

    else:
        name = None

    ret = render_template("makepost.html",
                           author=f"{f"{name}" if name else "anon"}",
                           loginlink=f"{"/logout" if name else "/login"}",
                           logintext=f"{"Logout" if name else "Login"}",
                           posttitle=title,
                           body=body)
    
    resp = make_response(ret)
    resp.set_cookie("lastviewedpage", json.dumps({"page":"/newpost"}))
    return resp

@app.post("/newpost")
def newpost_POST():
    dbh = databaseHandler("posts.db")
    sh = sessionHandler(JWT_SECRET, "users.db")
    title = request.form.get("title")
    post_body = request.form.get("body")
    cookies = request.cookies

    author = "anon"

    if "jwt" in cookies:
        _jwt = cookies.get("jwt")
        author = sh.verifyCookie(_jwt)
        if author == None:
            cookiedata = {"title":title, "body":post_body}
            string = json.dumps(cookiedata)
            redr = redirect("/login?exp=true")
            redr.set_cookie("post", string)
            return redr
    

    _id = dbh.create_post(author, title, post_body)

    dbh.close()
    redr = redirect(f"/post?id={_id}")

    if "post" in cookies: redr.set_cookie("post","",0)
    return redr

@app.get("/login")
def login_GET(incorrect=False):
    message = ""
    if incorrect: message += "\nInvalid username or password"
    if request.args.get("exp") == 'true': message += "\nSession Expired"
    return render_template("login.html", title = 'Login',  action="/login", message = message, hideRtext="")

@app.post("/login")
def login_POST():
    sh = sessionHandler(JWT_SECRET, "users.db")
    token = sh.login(request.form.get('user'), request.form.get('psk'))

    cookies = request.cookies
    if "lastviewedpage" in cookies:
        lvp = json.loads(request.cookies.get("lastviewedpage"))
    else:
        lvp = {"page":"/"}

    if token:
        response = redirect(lvp["page"]+(f"?id={lvp["id"]}" if "id" in lvp else ""))
        response.set_cookie("jwt", token, httponly=True)
        return response
    else:
        return(login_GET(incorrect=True))

@app.get("/register")
def register_GET(UsernameTaken = False):
    message = ""
    if UsernameTaken: message += "\nUsername Taken"
    return render_template("login.html", title = 'Register',  action="/register", message = message, hideRtext="hidden")

@app.post("/register")
def register_POST():
    sh = sessionHandler(JWT_SECRET, "users.db")
    if sh.new_user(request.form.get('user'), request.form.get('psk')):
        return redirect("/login")
    else:
        return register_POST(UsernameTaken=True)

@app.route("/logout", methods=['GET', 'POST'])
def logout():
    cookies = request.cookies
    if "lastviewedpage" in cookies:
        lvp = json.loads(request.cookies.get("lastviewedpage"))
    else:
        lvp = {"page":"/"}

    response = redirect(lvp["page"]+(f"?id={lvp["id"]}" if "id" in lvp else ""))
    response.set_cookie("jwt", "", max_age=0)
    return response

@app.get("/post")
def post_GET():
    dbh = databaseHandler("posts.db")
    sh = sessionHandler(JWT_SECRET, "users.db")
    cookies = request.cookies

    author='anon'

    if "jwt" in cookies:
        _jwt = cookies.get("jwt")
        author = sh.verifyCookie(_jwt)
        if author == None:
            author = "anon"

    if "comment" in cookies:
        commentbody = json.loads(cookies.get("comment"))['body']
    else:
        commentbody = ""

    try:
        postid = request.args.get("id")
        post = dbh.get_post(postid)

        commentstring = ""

        for comment in dbh.get_comments(postid):
            commentstring += f"<div class='comment'><div class='commenttext'>{comment[0]}:<br>{comment[1]}</div></div>\n"

        dbh.close()

        ret =  render_template("post.html", title = post[1],
                               author = post[0], 
                               content=post[2], 
                               comments=commentstring, 
                               user=author, 
                               comment=commentbody,
                               loginlink=f"{"/logout" if not author == 'anon' else "/login"}",
                               logintext=f"{"Logout" if not author == 'anon' else "Login"}")
        resp = make_response(ret)
        resp.set_cookie("lastviewedpage", json.dumps({"page": "/post", "id":postid}))
        return resp
    except IndexError:
        dbh.close()
        return '<body style="background: black; color: white";><center><h1>Post Not Found</h1>'

@app.post("/comment")
def comment_POST():
    dbh = databaseHandler("posts.db")
    sh = sessionHandler(JWT_SECRET, "users.db")
    post_body = request.form.get("body")
    cookies = request.cookies

    author = "anon"

    if "jwt" in cookies:
        _jwt = cookies.get("jwt")
        author = sh.verifyCookie(_jwt)
        if author == None:
            cookiedata = {"body":post_body}
            string = json.dumps(cookiedata)
            redr = redirect("/login?exp=true")
            redr.set_cookie("comment", string)
            return redr
    
    try:
        if "lastviewedpage" in cookies:
            postid = json.loads(cookies.get("lastviewedpage"))["id"]
    except KeyError:
        return redirect("/")

    _id = dbh.create_comment(author, postid, post_body)

    dbh.close()
    redr = redirect(f"/post?id={_id}")

    if "comment" in cookies: redr.set_cookie("comment","",0)
    return redr
