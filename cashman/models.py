from datetime import datetime
from sqlalchemy import (Column, DateTime, ForeignKey, String, Numeric, Integer)
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from sqlalchemy.orm import relationship


db = SQLAlchemy()
Base = db.Model


class Category(Base):
    __tablename__ = u'category'

    id = Column(Integer, primary_key=True)
    name = Column(String)


class Wallet(Base):
    __tablename__ = u'wallet'

    id = Column(Integer, primary_key=True)
    name = Column(String)


class Transaction(Base):
    __tablename__ = u'transaction'

    id = Column(Integer, primary_key=True)
    amount = Column(Numeric)
    category_id = Column(ForeignKey(Category.id))
    wallet_id = Column(ForeignKey(Wallet.id))
    date = Column(DateTime)
    details = Column(String)

    category = relationship(Category)
    wallet = relationship(Wallet)


db_manager = Manager()

@db_manager.command
def setup():
    c = Category(name='categorie')
    w = Wallet(name='cash')
    db.session.add(c)
    db.session.add(w)
    db.session.commit()
    t = Transaction(amount=42, category=c, wallet=w, date=datetime.now())
    db.session.add(t)
    db.session.commit()
    print "Done!"
