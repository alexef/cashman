import flask
from flask import views as fv, render_template, request, flash
from cashman.forms import AddForm
from cashman.models import Transaction, Wallet, db

views = flask.Blueprint('views', __name__)

@views.route('/')
def homepage():
    ts_in = Transaction.query.filter(Transaction.amount > 0)
    ts_out = Transaction.query.filter(Transaction.amount < 0)
    return render_template(
        'transactions.html', ts_in=ts_in, ts_out=ts_out,
    )


@views.route('/wallets')
def wallets():
    return render_template('wallets.html', wallets=Wallet.query.all())


@views.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        form = AddForm(request.form)
        if form.validate():
            t = Transaction()
            form.populate_obj(t)
            if form.direction.data == 'out':
                t.amount *= -1
            db.session.add(t)
            db.session.commit()
            flash('Transaction added!', 'success')
    else:
        form = AddForm()

    return render_template('add.html', form=form)
    
    
class TransactionView(fv.View):

    def get_queryset(self):
        return Transaction.query

    def dispatch_request(self):
        basequery = self.get_queryset()
        ts_in = basequery.filter(Transaction.amount >= 0)
        ts_out = basequery.filter(Transaction.amount < 0)
        return render_template(
            'transactions.html', ts_in=ts_in, ts_out=ts_out,
        )


class WalletView(TransactionView):

    def get_queryset(self):
        wallet_id = flask.request.args.get('wallet')
        return Transaction.query.filter(Transaction.wallet_id == wallet_id)


views.add_url_rule('/w', view_func=WalletView.as_view('wallet'))
