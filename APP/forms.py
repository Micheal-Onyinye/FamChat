from wtforms import StringField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

class CreateGroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired()])
    description = StringField('Description')
    members = SelectMultipleField('Select Members', coerce=int)  # user IDs
    submit = SubmitField('Create Group')
