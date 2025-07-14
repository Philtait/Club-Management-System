# File: app/forms/feedback_form.py

from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class FeedbackForm(FlaskForm):
    event_id = IntegerField('Event ID', validators=[DataRequired()])
    message = TextAreaField('Feedback Message', validators=[DataRequired()])
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])

    submit = SubmitField('Submit Feedback')
