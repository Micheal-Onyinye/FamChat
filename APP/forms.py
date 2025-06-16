from wtforms import StringField, SubmitField, SelectMultipleField, FileField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed


class CreateGroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired()])
    description = StringField('Description')
    members = SelectMultipleField('Select Members', coerce=int)  # user IDs
    submit = SubmitField('Create Group')
    profile_pic = FileField('Upload Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
