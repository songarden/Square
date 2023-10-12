from pymongo import MongoClient

client = MongoClient("mongodb://test:test@54.180.100.137", 27017)
db = client.square

if __name__ == '__main__':
# db에 넣을 가데이터 나중에 제거해줘야함
    user_list = [
    {
        "userid": "123",
        "username": "john_doe",
        "password": "123",
        "prev_score" : 0,
        "max_score": 98.77,
        "max_score_date": "2023-10-12 16:18:45",
    },
    {
        "userid": "456",
        "username": "jane_smith",
        "password": "123",
        "prev_score" : 0,
        "max_score": 95.44,
        "max_score_date": "2023-10-12 16:18:40",
    },
    {
        "userid": "789",
        "username": "alice_wonderland",
        "password": "123",
        "prev_score": 0,
        "max_score": 90.22,
        "max_score_date": "2023-10-12 16:18:41",
    },
    {
        "userid": "101112",
        "username": "ghibli",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    },
    ]
    # 현재 db를 비우고 가데이터를 넣는다
    db.users.delete_many({})
    db.users.insert_many(user_list)