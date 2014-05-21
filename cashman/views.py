from datetime import datetime
import flask
from flask import views as fv, render_template, request, flash, redirect,\
    url_for
from sqlalchemy import func
from cashman.forms import AddForm, EditForm
from cashman.models import Transaction, Wallet, db, Category

views = flask.Blueprint('views', __name__)


def pack_data(data, sort=True):
    if sort:
        data = list(data)
        data.sort(key=lambda a: a[1])
    return ','.join([':'.join([str(d) for d in p]) for p in data])


@views.app_context_processor
def inject():
    return dict(pack_data=pack_data)


@views.route('/')
def homepage():
    return redirect(url_for('.transactions'))


@views.route('/wallets')
def wallets():
    return render_template('wallets.html', wallets=Wallet.query.all())


@views.route('/categories')
def categories():
    return render_template('categories.html',
                           categories=Category.query.order_by(Category.name))


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

@views.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    transaction = Transaction.query.get_or_404(id)
    form = EditForm(request.form, transaction)
    if request.method == 'POST':
        if form.validate():
            form.populate_obj(transaction)
            db.session.commit()
            flash('Transaction updated!', 'success')

    return render_template('edit.html', form=form)


class WalletMixin(object):

    def get_context_data(self):
        context = super(WalletMixin, self).get_context_data()
        wallet_id = self.kwargs.get('wallet')
        context.update({'wallet': Wallet.query.get_or_404(wallet_id)})
        return context

    def get_queryset(self):
        wallet_id = self.kwargs.get('wallet')
        qs = super(WalletMixin, self).get_queryset()
        return qs.filter(Transaction.wallet_id == wallet_id)


class CategoryMixin(object):

    def get_context_data(self):
        context = super(CategoryMixin, self).get_context_data()
        cat_id = request.args.get('category')
        context.update({'category': Category.query.get_or_404(cat_id)})
        return context

    def get_queryset(self):
        cat_id = request.args.get('category')
        qs = super(CategoryMixin, self).get_queryset()
        return qs.filter(Transaction.category_id == cat_id)


class TransactionView(fv.View):

    def extract_interval(self):
        start, end = None, None
        if 'start' in request.args:
            try:
                start = datetime.strptime(request.args['start'], '%Y-%m-%d')
            except ValueError:
                pass
        if 'end' in request.args:
            try:
                end = datetime.strptime(request.args['end'], '%Y-%m-%d')
            except ValueError:
                pass
        return start, end

    def get_context_data(self):
        start, end = self.extract_interval()
        if not start:
            start = (
                Transaction.query
                .with_entities(func.min(Transaction.date))
                .first()
            )[0]
        if not end:
            end = (
                Transaction.query
                .with_entities(func.max(Transaction.date))
                .first()
            )[0]
        return {'start': start, 'end': end}

    def get_queryset(self):
        qs = Transaction.query
        start, end = self.extract_interval()
        if start:
            qs = qs.filter(Transaction.date >= start)
        if end:
            qs = qs.filter(Transaction.date <= end)
        return qs

    def dispatch_request(self, **kwargs):
        self.kwargs = kwargs
        basequery = self.get_queryset()
        ts_in = basequery.filter(Transaction.amount >= 0)
        ts_out = basequery.filter(Transaction.amount < 0)
        context = self.get_context_data()
        total_in = ts_in.with_entities(func.sum(Transaction.amount)).first()[0]
        total_out = ts_out.with_entities(func.sum(Transaction.amount)).first()[0]

        return render_template(
            'transactions.html', ts_in=ts_in, ts_out=ts_out, total_in=total_in,
            total_out=total_out,
            **context
        )


class WalletView(WalletMixin, TransactionView):
    pass


class CategoryView(CategoryMixin, TransactionView):
    pass


views.add_url_rule('/t', view_func=TransactionView.as_view('transactions'))
views.add_url_rule('/w/<int:wallet>/', view_func=WalletView.as_view('wallet'))
views.add_url_rule('/c', view_func=CategoryView.as_view('category'))


class GraphView(TransactionView):

    def dispatch_request(self, **kwargs):
        self.kwargs = kwargs
        basequery = self.get_queryset()
        basequery = basequery.join(Category)

        income_data = (
            basequery
            .filter(Transaction.amount >= 0)
            .with_entities(Category.name, func.sum(Transaction.amount))
            .group_by(Transaction.category_id)
        )
        outcome_data = (
            basequery
            .filter(Transaction.amount < 0)
            .with_entities(Category.name, 0 - func.sum(Transaction.amount))
            .group_by(Transaction.category_id)
        )
        context = self.get_context_data()
        return render_template(
            'graphs.html',
            income_data=pack_data(income_data),
            outcome_data=pack_data(outcome_data),
            **context
        )


class WalletGraphView(WalletMixin, GraphView):
    pass

views.add_url_rule('/graphs', view_func=GraphView.as_view('graphs'))
views.add_url_rule('/graphs/w/<int:wallet>/',
                   view_func=WalletGraphView.as_view('wallet_graphs'))


class ReportView(TransactionView):

    template_name = 'report.html'

    def __init__(self, *args, **kwargs):
        if 'template_name' in kwargs:
            self.template_name = kwargs.pop('template_name')
        super(ReportView, self).__init__(*args, **kwargs)

    def dispatch_request(self, **kwargs):
        self.kwargs = kwargs
        basequery = self.get_queryset()

        income_data = (
            basequery
            .filter(Transaction.amount >= 0)
            .with_entities(
                func.year(Transaction.date) + '/' + func.month(Transaction.date),
                func.sum(Transaction.amount))
            .group_by(
                func.year(Transaction.date),
                func.month(Transaction.date),
            )
        )
        outcome_data = (
            basequery
            .filter(Transaction.amount < 0)
            .with_entities(
                func.year(Transaction.date) + '/' + func.month(Transaction.date),
                0 - func.sum(Transaction.amount))
            .group_by(
                func.year(Transaction.date),
                func.month(Transaction.date),
            )
        )
        all_data = (
            basequery
            .with_entities(
                func.year(Transaction.date) + '/' + func.month(Transaction.date),
                func.sum(Transaction.amount))
            .group_by(
                func.year(Transaction.date),
                func.month(Transaction.date),
            )
        )

        context = self.get_context_data()
        return render_template(
            self.template_name,
            income_data=income_data,
            outcome_data=outcome_data,
            all_data=all_data,
            **context
        )

views.add_url_rule('/report', view_func=ReportView.as_view('report'))
views.add_url_rule('/report/graph',
                   view_func=ReportView.as_view(
                       'report_graph',
                       template_name='report_graphs.html'))
