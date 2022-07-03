import atexit
import os
import uuid

import Bcrypt as Bcrypt
from flask import Flask, jsonify, request
from flask.views import MethodView
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.testing.pickleable import User

app = Flask("app")
bcrypt = Bcrypt(app)
engine = create_engine(os.getenv("PG_DSN"))
Base = declarative_base()
Session = sessionmaker(bind=engine)

atexit.register(lambda: engine.dispose())


class Advertisement(Base):
    __tablename__ = "Advertisement"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    description = Column(Text, nullable=True)
    creator = Column(User)

    @classmethod
    def register(cls, session: Session, title: str, description: str):
        new_adv = Advertisement(
            title=title,
            description=description,
        )
        session.add(new_adv)
        try:
            session.commit()
            return new_adv
        except IntegrityError:
            session.rollback()

    def to_dict(self):
        return {
            "user_name": self.user_name,
            "registration_time": int(self.registration_time.timestamp()),
            "id": self.id,
        }

    @classmethod
    def unregister(cls, session: Session, pk: int):
        session.query(Advertisement).filter(Advertisement.id == pk).delete()
        try:
            session.commit()
            return "Success"
        except IntegrityError:
            session.rollback()


Base.metadata.create_all(engine)


class UserView(MethodView):
    def get(self):
        with Session() as session:
            return jsonify(session.user.to_dict())

    def post(self):
        with Session() as session:
            return User.register(session, **request.json).to_dict()

    def delete(self):
        with Session() as session:
            return User.unregister(session, **request.json).to_dict()


app.add_url_rule(
    "/user/<int:user_id>/", view_func=UserView.as_view("get_user"), methods=["GET"]
)
app.add_url_rule(
    "/user/", view_func=UserView.as_view("register_user"), methods=["POST"]
)
