# File: app/forms/mpesa_payment_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

class MpesaPaymentForm(FlaskForm):
    student_id = IntegerField('Student ID', validators=[DataRequired()])
    transaction_code = StringField('Transaction Code', validators=[DataRequired(), Length(max=100)])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    purpose = SelectField(
        'Purpose',
        choices=[('Membership', 'Membership'), ('Event', 'Event'), ('Donation', 'Donation')],
        validators=[DataRequired()]
    )
    related_id = IntegerField('Related ID (Event or Club ID)', validators=[DataRequired()])

    submit = SubmitField('Confirm Payment')
