import flask
from flask import views as fv, render_template, request, flash, redirect,\
    url_for
from sqlalchemy import func
from cashman.forms import AddForm
from cashman.models import Transaction, Wallet, db, Category

views = flask.Blueprint('views', __name__)

@views.route('/')
def homepage():
    return redirect(url_for('.transactions'))


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

    def get_context_data(self):
        return {}

    def get_queryset(self):
        return Transaction.query

    def dispatch_request(self):
        basequery = self.get_queryset()
        ts_in = basequery.filter(Transaction.amount >= 0)
        ts_out = basequery.filter(Transaction.amount < 0)
        context = self.get_context_data()
        return render_template(
            'transactions.html', ts_in=ts_in, ts_out=ts_out, **context
        )

views.add_url_rule('/t', view_func=TransactionView.as_view('transactions'))


class WalletView(TransactionView):

    def get_context_data(self):
        wallet_id = flask.request.args.get('wallet')
        return {'wallet': Wallet.query.get_or_404(wallet_id)}

    def get_queryset(self):
        wallet_id = flask.request.args.get('wallet')
        return Transaction.query.filter(Transaction.wallet_id == wallet_id)


views.add_url_rule('/w', view_func=WalletView.as_view('wallet'))


class GraphView(fv.View):

    def get_context_data(self):
        return {}

    def get_queryset(self):
        return Transaction.query

    def dispatch_request(self):
        basequery = self.get_queryset()

        basequery = basequery.join(Category)

        def pack_data(data):
            return ','.join([':'.join([str(d) for d in p]) for p in data])

        income_data = (
            basequery
            .filter(Transaction.amount >= 0)
            .with_entities(Category.name, func.sum(Transaction.amount))
        )
        outcome_data = (
            basequery
            .filter(Transaction.amount < 0)
            .with_entities(Category.name, 0 - func.sum(Transaction.amount))
        )
        context = self.get_context_data()
        return render_template(
            'graphs.html',
            income_data=pack_data(income_data),
            outcome_data=pack_data(outcome_data),
            **context
        )


class WalletGraphView(GraphView):

    def get_context_data(self):
        wallet_id = request.args.get('wallet')
        return {'wallet': Wallet.query.get_or_404(wallet_id)}

    def get_queryset(self):
        wallet_id = request.args.get('wallet')
        return Transaction.query.filter_by(wallet_id=wallet_id)


views.add_url_rule('/graphs', view_func=GraphView.as_view('graphs'))
views.add_url_rule('/graphs/w',
                   view_func=WalletGraphView.as_view('wallet_graphs'))
