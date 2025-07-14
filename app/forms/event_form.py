# File: app/forms/event_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=255)])
    event_date = DateTimeField('Event Date', validators=[DataRequired()], format='%Y-%m-%d %H:%M')
    registration_deadline = DateTimeField('Registration Deadline', validators=[Optional()], format='%Y-%m-%d %H:%M')
    max_attendees = IntegerField('Maximum Attendees', validators=[Optional()])
    image_url = StringField('Image URL (optional)', validators=[Optional(), Length(max=255)])

    submit = SubmitField('Create Event')
