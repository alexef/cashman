from datetime import datetime
from sqlalchemy import (Column, DateTime, ForeignKey, String, Numeric, Integer,
                        Boolean)
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from sqlalchemy.orm import relationship


db = SQLAlchemy()
Base = db.Model


class Category(Base):
    __tablename__ = u'category'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    income = Column(Boolean)
    outcome = Column(Boolean)


class Wallet(Base):
    __tablename__ = u'wallet'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    active = Column(Boolean)


class Transaction(Base):
    __tablename__ = u'transaction'

    id = Column(Integer, primary_key=True)
    amount = Column(Numeric)
    category_id = Column(ForeignKey(Category.id))
    wallet_id = Column(ForeignKey(Wallet.id))
    transfer_id = Column(ForeignKey(Wallet.id), nullable=True, default=None)
    date = Column(DateTime)
    details = Column(String)

    category = relationship(Category)
    wallet = relationship(Wallet, foreign_keys=wallet_id)
    wallet_transfer = relationship(Wallet, foreign_keys=transfer_id)


db_manager = Manager()

@db_manager.command
def setup():
    db.create_all()
    c = Category(name='categorie')
    w = Wallet(name='cash')
    db.session.add(c)
    db.session.add(w)
    db.session.commit()
    t = Transaction(amount=42, category=c, wallet=w, date=datetime.now())
    db.session.add(t)
    db.session.commit()
    print "Done!"
