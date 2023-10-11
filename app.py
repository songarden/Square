
from flask import Flask, render_template, request, jsonify, redirect
from pymongo import MongoClient
from dotenv import load_dotenv
import jwt
import os
from datetime import date, datetime, timedelta

app = Flask(__name__)



client = MongoClient('mongodb://test:test@54.180.100.137',27017)
db = client.square
# DB 설정 시 주석 풀고 체크

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_ID = os.getenv("ADMIN_ID")
ADMIN_PW = os.getenv("ADMIN_PW")


app.config.update(
			DEBUG = True,
			JWT_SECRET_KEY = SECRET_KEY
		)

@app.route('/')
def index():
    return render_template('home.html')


@app.route("/login", methods=['POST'])
def login_proc():
	
	# 클라이언트로부터 요청된 값
    input_data = request.get_json()
    user_id = input_data['id']
    user_pw = input_data['pw']
    user = db.users.find_one({'userid': user_id })
    
    if user_pw == user['password'] :
        payload = {
			'id': user['userid'],
			'name': user['username'],
			'max_score': user['max_score'],
			'exp': datetime.utcnow() + timedelta(seconds=60)  # 로그인 24시간 유지
		}
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})

	# 아이디, 비밀번호가 일치하지 않는 경우
    else:
        return jsonify({'result': 'fail'})
      
# @app.route('/user_only', methods=["GET"])
# @jwt_required()
# def user_only():
# 	cur_user = get_jwt_identity()
# 	if cur_user is None:
# 		return "User Only!"
# 	else:
# 		return "Hi!," + cur_user
	

@app.route('/login', methods=["GET"])
def home2():
	token_receive = request.cookies.get('mytoken')
	try:
		payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
		print(payload)
		return render_template('login.html',max_score = payload['max_score'])
	except jwt.ExpiredSignatureError:
		return redirect("/")
	except jwt.exceptions.DecodeError:
		return redirect("/")

def main():
    app.run("localhost", 5000)

if __name__ == "__main__":
    main()