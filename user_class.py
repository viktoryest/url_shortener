from flask_login import UserMixin


class UserLogin(UserMixin):
    def get_from_db(self, user_id, db):
        self.__user = db.execute(f"SELECT * FROM users WHERE id = {user_id} LIMIT 1").fetchone()
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user['id'])
