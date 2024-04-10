from flask import Flask, request, jsonify, render_template, redirect, make_response
from disambi import Server
from dotenv import load_dotenv
load_dotenv()
import os
from authorizer import *





app = Flask(__name__)
@app.post('/ci')
def ci():
    os.system("git pull && toolforge webservice --backend=kubernetes python3.11 restart &")
    return 'CI/CD is working'
@app.get('/api/disambiguate')
def disambiguate_query():
    try:
        title = request.args.get("title")
        language = request.args.get("language", "bn")
        access_token = request.cookies.get(COOKIE_NAME)
        if not access_token:
            return redirect(get_login_url(request.url))
        server = Server(language, access_token)
        response = server.main(title)
        return response
    except:
        pass
@app.get("/disambiguate")
def disambiguate():
    try:
        title = request.args.get("title", "উপজেলা")
        language = request.args.get("language", "bn")
        access_token = request.cookies.get(COOKIE_NAME)
        if not access_token:
            return redirect(get_login_url(request.url))
        username = request.cookies.get('username')
        return render_template("disambiguate.html",
                            language=language,
                            title=title,
                            username=username
        )
    except:
        pass
@app.post("/disambiguate")
def disambiguate_post():
    body = request.json
    title = body.get("title")
    language = body.get("language", "bn")
    fixed = body.get('fixed', 0)
    total = body.get('total', 0)
    text = body.get("text", "")
    access_token = request.cookies.get(COOKIE_NAME)
    if not access_token:
        return redirect(get_login_url(request.url))
    server = Server(language, access_token)
    summary = f"দ্ব্যর্থতা নিরসক সরঞ্জামের সাহায্যে {total}টির মধ্যে {fixed}টি দ্ব্যর্থতা নিরসন করা হয়েছে"
    response = server.edit(title, text, summary)
    return jsonify(response)
@app.get("/login")
def login_interface():
    return render_template("login.html", login_url=get_login_url())
@app.get("/user/callback")
def callback():
    try:
        code = request.args.get("code")
        state = request.args.get("state")
        redirect_uri = state
        endpoint = META_OAUTH_ACCESS_TOKEN_URL
        params = {
            'grant_type' : 'authorization_code',
            'code' : code,
            'client_id' : VERIFIER_OAUTH_CLIENT_ID,
            'client_secret' : VERIFIER_OAUTH_CLIENT_SECRET,
            'redirect_uri' : f'{HOSTNAME}/user/callback',
        }
        res = requests.post(endpoint, data=params).json()
        if 'error' in res:
            return COOKIE_NAME, '', '/error?code=' + res['error']
        access_token = res['access_token']
        profile = requests.get(META_PROFILE_URL, headers={'Authorization': f'Bearer {access_token}'}).json()
        username = profile['username']
        redirect_response = make_response(redirect(redirect_uri))
        redirect_response.set_cookie(COOKIE_NAME, access_token)
        redirect_response.set_cookie('username', username)
        return redirect_response
    except Exception as e:
        return render_template("callback.html", error=e)
    return render_template("callback.html")
@app.get("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host='', port=5000)