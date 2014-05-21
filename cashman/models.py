from csv import DictReader
from datetime import datetime
from sqlalchemy import (Column, DateTime, ForeignKey, String, Numeric, Integer,
                        Boolean)
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from sqlalchemy.orm import relationship, backref


db = SQLAlchemy()
Base = db.Model


class Category(Base):
    __tablename__ = u'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    income = Column(Boolean)
    outcome = Column(Boolean)


class Wallet(Base):
    __tablename__ = u'wallet'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    active = Column(Boolean)


class Transaction(Base):
    __tablename__ = u'transaction'

    id = Column(Integer, primary_key=True)
    amount = Column(Numeric)
    category_id = Column(ForeignKey(Category.id))
    wallet_id = Column(ForeignKey(Wallet.id))
    transfer_id = Column(ForeignKey(Wallet.id), nullable=True, default=None)
    date = Column(DateTime)
    details = Column(String(512))

    category = relationship(Category, backref=backref('transactions',
                                                      cascade='all'))
    wallet = relationship(Wallet, foreign_keys=wallet_id)
    wallet_transfer = relationship(Wallet, foreign_keys=transfer_id)

    def __unicode__(self):
        return '%s %s' % (self.date, self.amount)


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


@db_manager.command
def import_csv(csv_path):
    def get_wallet(name):
        wallet = Wallet.query.filter_by(name=name).first()
        if not wallet:
            wallet = Wallet(name=name)
            db.session.add(wallet)
            db.session.flush()
        return wallet

    def get_category(name, amount):
        category = Category.query.filter_by(name=name).first()
        if not category:
            category = Category(name=name, income=(amount >= 0),
                                outcome=(amount < 0))
            db.session.add(category)
            db.session.flush()
        return category

    def add_transaction(wallet, category, data):
        filters = dict(
            wallet=wallet, category=category,
            date=data['Date'], amount=data['Amount'], details=data['Note'],
        )
        transaction = Transaction.query.filter_by(**filters).first()
        if not transaction:
            transaction = Transaction(**filters)
            db.session.add(transaction)
            print "Adding new", unicode(transaction)
        else:
            print "Skipping existing", unicode(transaction)
        return transaction

    transfers = []
    with open(csv_path, 'r') as fin:
        reader = DictReader(fin)

        for row in reader:
            row['Amount'] = float(row['Amount'])
            row['Date'] = datetime.strptime(row['Date'], '%Y-%m-%d')
            row['Note'] = unicode(row['Note'], 'utf-8')
            row['Description'] = unicode(row['Description'])
            row['Wallet'] = row['Wallet'][1:]
            if row['Description'] == 'Transfer':
                transfers.append(row)
            else:
                wallet = get_wallet(row['Wallet'])
                category = get_category(row['Description'], row['Amount'])
                add_transaction(wallet, category, row)
        db.session.commit()
