from flask.views import View
from flask import Blueprint, render_template, request, flash, redirect, url_for
from wtforms.ext.sqlalchemy.orm import model_form
from cashman.models import Wallet, db, Category


admin = Blueprint('admin', __name__)
admin.registered = []


def get_list_url(model):
    return url_for('.%s_list' % model)


def get_edit_url(model, id):
    return url_for('.%s_edit' % model, id=id)


def get_delete_url(model, id):
    return url_for('.%s_delete' % model, id=id)


def get_add_url(model):
    return url_for('.%s_add' % model, id=id)


class ModelAdmin(View):

    template_list = 'admin/list.html'
    template_add = 'admin/add.html'
    template_edit = 'admin/edit.html'
    template_confirm = 'admin/confirm.html'

    @classmethod
    def name(cls):
        return cls.model.__tablename__

    @classmethod
    def list(cls):
        return render_template(
            cls.template_list,
            object_list=cls.model.query.all(),
            model=cls.name(),
        )

    @classmethod
    def add(cls):
        form_cls = model_form(cls.model)
        form = form_cls(request.form)

        if request.method == 'POST':
            if form.validate():
                object = cls.model()
                form.populate_obj(object)
                db.session.add(object)
                db.session.commit()
                flash('Added', 'success')
                return redirect(get_list_url(cls.name()))

        return render_template(
            cls.template_add,
            form=form,
            model=cls.name(),
        )

    @classmethod
    def edit(cls, id):
        object = cls.model.query.get_or_404(id)
        form_cls = model_form(cls.model)
        form = form_cls(request.form, object)
        if request.method == 'POST':
            if form.validate():
                form.populate_obj(object)
                db.session.commit()
                flash('Saved', 'success')

        return render_template(
            cls.template_edit,
            object=object,
            form=form,
            model=cls.name(),
        )

    @classmethod
    def delete(cls, id):
        object = cls.model.query.get_or_404(id)

        if request.method == 'POST':
            db.session.delete(object)
            db.session.commit()
            flash('Deleted', 'success')
            return redirect(get_list_url(cls.name()))
        return render_template(
            cls.template_confirm,
            object=object,
            model=cls.name(),
        )

    @classmethod
    def register(cls, app):
        model = cls.model.__tablename__
        app.route('/%s/list/' % model, endpoint='%s_list' % model)(cls.list)
        app.route('/%s/add/' % model,
                  endpoint='%s_add' % model,
                  methods=('GET', 'POST'))(cls.add)
        app.route('/%s/<int:id>/edit/' % model,
                  endpoint='%s_edit' % model,
                  methods=('GET', 'POST'))(cls.edit)
        app.route('/%s/<int:id>/del/' % model,
                  endpoint='%s_delete' % model,
                  methods=('GET', 'POST'))(cls.delete)
        admin.registered.append(model)


class WalletAdmin(ModelAdmin):
    model = Wallet


class CategoryAdmin(ModelAdmin):
    model = Category


WalletAdmin.register(admin)
CategoryAdmin.register(admin)


@admin.app_context_processor
def inject():
    return dict(
        get_list_url=get_list_url,
        get_edit_url=get_edit_url,
        get_delete_url=get_delete_url,
        get_add_url=get_add_url,
        modules=admin.registered,
    )


@admin.route('/')
def home():
    return redirect(get_list_url('wallet'))
