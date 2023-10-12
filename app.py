from functools import wraps
from flask import Flask, flash, render_template, request, jsonify, redirect
from pymongo import MongoClient
from dotenv import load_dotenv
import jwt
import os
from datetime import date, datetime, timedelta
import re
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

client = MongoClient("mongodb://test:test@54.180.100.137", 27017)
db = client.square
load_dotenv(dotenv_path="../.env")
SECRET_KEY = os.getenv("SECRET_KEY")

def requires_jwt(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token_receive = request.cookies.get('mytoken')
        if token_receive is None:
            print("쿠키가 없습니다.")
            return redirect("/")
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
            if payload['id'] != kwargs['user_id'] :
                return redirect("/")
            # 여기서 필요한 추가적인 유저 정보를 전달할 수 있습니다
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            print("쿠키가 만료되었습니다.")
            return redirect("/")
        except jwt.exceptions.DecodeError:
            print("쿠키 디코딩에 실패하였습니다.")
            return redirect("/")
        return func(*args, **kwargs)
    return decorated_function

@app.route("/ranking")
def show_rankings():
    # db에서 max_score가 0인 유저(=플레이 하지 않음)를 제외한 전체 데이터를 가져온다
    list_user = list(db.users.find({"max_score": {"$ne": 0}}))

    # db의 유저를 max_score 내림차순으로 정렬한다
    list_user.sort(key=lambda field: (-field["max_score"], field["max_score_date"], field["username"]))
    list_user = list_user[:10]
    # 순위를 계산하여 각 유저 데이터에 추가
    rank = 1
    for user in list_user:
        user['rank'] = rank
        rank += 1

    # 정렬된 유저 데이터를 적절히 가공해서 출력한다
    return render_template("ranking.html", list_user=list_user, is_ranking_page=True)

@app.route("/ranking/<string:user_id>")
@requires_jwt
def show_my_ranking(user_id):
    # 이전 점수와 비교하여 신기록을 달성한 경우 max_score를 갱신한다
    prev_score_cursor = db.users.find({"userid":user_id}, { "prev_score": 1})
    for d in prev_score_cursor:
        # 로우데이터인 점수를 소수점 둘째짜리까지 반올림 하는 과정을 추가한다
        prev_score_user = round(d.get("prev_score"), 2)
    max_score_cursor = db.users.find({"userid":user_id}, { "max_score": 1})
    for d in max_score_cursor:
        max_score_user = d.get("max_score")

    new_record = False    
    if prev_score_user > max_score_user:
        # 나중에 모덜을 띄우기 위한 bool
        new_record = True
        # max score를 prev_score_user로 갱신한다
        db.users.update_one({"userid":user_id},{"$set": {"max_score": prev_score_user}})
        # max score date를 갱신한다
        # utc시간을 받고 kst로 변경한다(+9h)
        current_time = datetime.utcnow() + timedelta(hours=9)
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        db.users.update_one({"userid":user_id},{"$set": {"max_score_date": formatted_time}})

    # db에서 max_score가 0인 유저(=플레이 하지 않음)를 제외한 전체 데이터를 가져온다

    list_user = list(db.users.find({"max_score": {"$ne": 0}}))
    
    # db의 유저를 max_score 내림차순으로 정렬하고, 상위 10명만 남긴다
    # max_score가 같을 경우 max_score_date 오름차순, 그래도 같으면 유저이름 순으로 정렬한다. 유저 이름은 중복되지 않기 때문에 여기까지만 하면 될거같음.
    list_user.sort(key=lambda field: (-field["max_score"], field["max_score_date"], field["username"]))
    list_user = list_user[:10]

    # 순위를 계산하여 각 유저 데이터에 추가
    rank = 1
    for user in list_user:
        user['rank'] = rank
        rank += 1

    # 정렬된 유저 데이터를 적절히 가공해서 출력한다
    return render_template("myranking.html",
                            list_user=list_user,
                            user_id=user_id, 
                            new_record=new_record, 
                            max_score=max_score_user, 
                            prev_score=prev_score_user, 
                            current_user_name=request.current_user.get('name'),
                            is_ranking_page=True
                          )

@app.route("/signup")
def show_signup():
    # 회원가입 페이지 렌더링
    return render_template("signup.html")

@app.route("/signup_process", methods=["POST"])
def signup_process():
    if request.method == "POST":
        # 사용자가 제출한 데이터 가져오기
        data = request.json

        userid = data["userid"]
        password = data["password"]
        password_confirm = data["password_confirm"]
        username = data["username"]

        # 에러를 받을 딕셔너리를 만든다
        errors = {}
        
        # 유저 id가 영문, 숫자가 아니면 에러 메세지를 반환한다
        pattern = "^[A-Za-z0-9]+$"
        if not re.match(pattern, userid):
            errors["useridError"] = "id는 영문 및 숫자로 구성되어야 합니다"
        

        # 유저 id의 길이가 적절하지 않으면 에러 메세지를 반환한다
        if not (4 <= len(userid) <= 20):
            errors["useridError"] = "아이디의 길이가 적절하지 않습니다"


        # 유저 id에 공백이 있으면 에러 메세지를 반환한다
        if ' ' in userid:
            errors["useridError"] = "아이디에는 공백이 없어야 합니다"
        
        # 유저 이름의 길이가 적절하지 않으면 에러 메세지를 반환한다
        if not (2 <= len(username) <= 10):
            errors["usernameError"] = "이름의 길이가 적절하지 않습니다"

        # 유저 이름에 공백이 있으면 에러 메세지를 반환한다
        if ' ' in username:
            errors["usernameError"] = "이름에는 공백이 없어야 합니다"
        
        # 패스워드가 너무 짧으면 에러 메세지를 반환한다
        if len(password) <= 3:
            errors["passwordconfirmError"] = "패스워드가 너무 짧습니다"

        # 패스워드가 일치하지 않으면 에러 메세지를 반환한다
        if password != password_confirm:
            errors["passwordconfirmError"] = "패스워드가 일치하지 않습니다"

        # 유저 id가 기존에 있는지 검증한다. 있으면 에러 메세지를 띄운다
        check_userid = db.users.find_one({"userid": userid})
        check_username = db.users.find_one({"username": username})
        if check_userid is not None:
            errors["useridError"] = "이미 등록된 아이디입니다"
        if check_username is not None:
            errors["usernameError"] = "이미 등록된 이름입니다"

        # 에러가 있으면 클라이언트에 반환한다
        if errors:
            return jsonify(errors)

        # 검증을 통과하면 db에 유저 정보를 저장한다.
        salt = SECRET_KEY
        password =  pbkdf2_sha256.hash(password + salt)
        user_new = {
            "userid": userid,
            "username": username,
            "password": password,
            "max_score": 0,
            "max_score_date": "",
        }
        db.users.insert_one(user_new)
        # # 성공하면 메인 페이지로 돌아간다
        return jsonify({"success":"회원 가입이 완료되었습니다!"})

@app.route('/')
def index():
    token_receive = request.cookies.get('mytoken')
    if token_receive is None:
        return render_template("home.html")
    else :
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
            print(payload)
            return redirect('/game/' + payload['id'])
        except jwt.ExpiredSignatureError:
            print("쿠키가 만료되었습니다.")
            return render_template("home.html")
        except jwt.exceptions.DecodeError:
            print("쿠키 디코딩에 실패하였습니다.")
            return render_template("home.html")

@app.route("/login", methods=['POST'])
def login_proc():
    # 클라이언트로부터 요청된 값
    input_data = request.get_json()
    user_id = input_data['id']
    user_pw = input_data['pw']
    salt = SECRET_KEY

    user = db.users.find_one({'userid': user_id })

    
    if user is None :
        return jsonify({'result':'fail'})
    
    check = pbkdf2_sha256.verify(user_pw+salt , user['password'])
    if check :
        payload = {
            'id': user['userid'],
            'name': user['username'],
            'max_score': user['max_score'],
            'exp': datetime.utcnow() + timedelta(seconds=600)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})

    # 아이디, 비밀번호가 일치하지 않는 경우
    else:
        return jsonify({'result': 'fail'})

@app.route('/login', methods=["GET"])
@requires_jwt
def login():
    return render_template('login.html',max_score = request.current_user.get('max_score',0))

@app.route('/game/<string:user_id>')
@requires_jwt
def game(user_id):
    return render_template('game.html',current_user_name = request.current_user.get('name'))

@app.route("/send_result/<string:user_id>", methods=['POST'])
@requires_jwt
def send_result(user_id):
    data = request.get_json()
    scores = data['scores']
    sum = 0

    if (len(scores) != 3):
        return jsonify({"result": "fail"}), 500
    
    for score in scores:
        sum += score
    
    if sum > 300:
        return jsonify({"result": "fail"}), 500
    
    db.users.update_one({"userid": user_id}, {"$set": {"prev_score": sum}})
    user = db.users.find_one({"userid": user_id})
    return jsonify({"result": "success"}), 200

@app.route("/arch/<string:user_id>", methods=['POST'])
@requires_jwt
def process_achievement(user_id):
    data = request.get_json()
    scores = data['scores']
    sum = 0
    for i in scores:
        sum += i
    
    # 업적 로직 하드코딩
    # 점수 77.77점
    if 77.77 in scores:
        if check_and_achieve("1", user_id):
            return make_achievement_response("777", "77.77점 달성하기"), 200
        
    # 점수 100점
    if max(scores) >= 100:
        if check_and_achieve("2", user_id):
            return make_achievement_response("100점!", "100점 달성하기"), 200

    # 점수 50점 미만
    if min(scores) < 50:
        if check_and_achieve("3", user_id):
            return make_achievement_response("일부로 그러신거죠?", "50점 미만 달성하기"), 200
    
    # 총점 300점
    if sum == 300:
        if check_and_achieve("4", user_id):
            return make_achievement_response("완벽 그 자체", "총점 300점 달성하기"), 200

    # 총점 285점 이상    
    if sum >= 285:
        if check_and_achieve("5", user_id):
            return make_achievement_response("출발이 좋은데요?", "총점 285점 이상 달성하기"), 200
    
    if len(scores) == 3 and sum >= 150:
        if check_and_achieve("6", user_id):
            return make_achievement_response("반타작", "총점 150점 이상 달성하기"), 200
        
    # 점수 0.1점 미만
    if min(scores) < 0.1:
        if check_and_achieve("7", user_id):
            return make_achievement_response("반항아", "0.1점 미만 달성하기"), 200
        
    # 신호등
    condition_green = False
    condition_orange = False
    condition_red = False

    for score in scores:
        if score > 90:
            condition_green = True
        elif 70 < score <= 90:
            condition_orange = True
        elif score <= 70:
            condition_red = True

    if (condition_green and condition_orange and condition_red) :
        if check_and_achieve("8", user_id):
            return make_achievement_response("신호등", "세가지 색상의 스코어 달성"), 200
        
    # 3개의 점수가 1점 이내
    score_max = max(scores)
    score_min = min(scores)

    if (score_max-score_min < 1) and len(scores) == 3:
        if check_and_achieve("9", user_id):
            return make_achievement_response("균형의 수호자", "3개의 점수의 편차가 1점 이내"), 200

        
    return jsonify({"error": "달성할 업적이 없습니다."}), 400
    
def make_achievement_response(title, body):
    return jsonify({"title": title, "body": body})

def check_and_achieve(achievement_id, user_id):
    if db.achievement.find_one({"achievementid": achievement_id, "userid": user_id}) == None:
        db.achievement.insert_one({"achievementid": achievement_id, "userid": user_id, "date": datetime.now()})
        return True
    return False

app.run("0.0.0.0", port=5020, threaded=True, debug=True)
