from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///restaurant_rules.db')
Session = sessionmaker(bind=engine)

class Rule(Base):
    __tablename__ = 'rules'
    
    id = Column(String, primary_key=True)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)
    note = Column(String)
    conditions = Column(JSON)

class AssessmentLog(Base):
    __tablename__ = 'assessments'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    area = Column(Integer)
    seats = Column(Integer)
    features = Column(JSON)
    results = Column(JSON)