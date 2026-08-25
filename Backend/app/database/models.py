from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from .connection import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    duration_minutes = Column(Integer)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    name = Column(String)
    lecture_id = Column(Integer, ForeignKey("lectures.id"))


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"))
    timestamp_sec = Column(Integer)
    feedback_type = Column(String)


class LectureAnalytics(Base):
    __tablename__ = "lecture_analytics"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"))
    minute = Column(Integer)

    difficult = Column(Integer, default=0)
    easy = Column(Integer, default=0)
    boring = Column(Integer, default=0)
    engaging = Column(Integer, default=0)

    net_difficulty = Column(Integer, default=0)
    net_engagement = Column(Integer, default=0)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"))
    question = Column(Text)
    suggestion = Column(Text)


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    action_taken = Column(Text)
    future_action = Column(Text)