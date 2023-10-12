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
        "max_score_date": "2023-10-12 16:18:40",
    },
    {
        "userid": "456",
        "username": "jane_smith",
        "password": "123",
        "prev_score" : 0,
        "max_score": 98.77,
        "max_score_date": "2023-10-12 16:18:40",
    },
    {
        "userid": "789",
        "username": "alice_wonderland",
        "password": "123",
        "prev_score": 0,
        "max_score": 98.77,
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
        {
        "userid": "1011121",
        "username": "ghibli1",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    },
        {
        "userid": "1011122",
        "username": "ghibli2",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    },
        {
        "userid": "1011123",
        "username": "ghibli3",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    },
        {
        "userid": "1011124",
        "username": "ghibli4",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    },
        {
        "userid": "1011125",
        "username": "ghibli5",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    },
        {
        "userid": "1011126",
        "username": "ghibli6",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    },
        {
        "userid": "1011127",
        "username": "ghibli7",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    },
        {
        "userid": "1011128",
        "username": "ghibli8",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    },
        {
        "userid": "1011129",
        "username": "ghibli9",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    },
        {
        "userid": "10111210",
        "username": "ghibli10",
        "password": "pass123",
        "prev_score": 0,
        "max_score": 10.11,
        "max_score_date": "2023-10-12 16:18:42",
    }
    ]
    # 현재 db를 비우고 가데이터를 넣는다
    db.users.delete_many({})
    # db.users.insert_many(user_list)