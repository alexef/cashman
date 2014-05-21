from sqlalchemy import cast, String
from wtforms import Form, SelectField, FloatField, StringField, DateField
from wtforms.validators import Optional
from cashman.models import Wallet, Category


class AddForm(Form):
    wallet_id = SelectField()
    direction = SelectField(choices=(('in', 'Income'), ('out', 'Outcome')))
    amount = FloatField()
    category_id = SelectField()
    details = StringField(validators=[Optional()])
    date = DateField()

    def __init__(self, *args, **kwargs):
        super(AddForm, self).__init__(*args, **kwargs)
        self.wallet_id.choices = (
            Wallet.query.with_entities(cast(Wallet.id, String), Wallet.name)
        )
        self.category_id.choices = (
            Category.query.with_entities(cast(Category.id, String), Category.name)
        )
