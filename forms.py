from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, URLField
from wtforms.validators import ValidationError


class SignInForm(FlaskForm):
    username = StringField('Enter username')
    password = PasswordField('Enter password')
    remember = BooleanField(default=False)
    submit = SubmitField('Sign in')

    def validate_username(form, username):
        if len(username.data) == 0:
            raise ValidationError('Please, enter username')

    def validate_password(form, password):
        if len(password.data) < 6 or len(password.data) > 20:
            raise ValidationError('The password must contain between 6 and 20 characters')


class SignUpForm(FlaskForm):
    username = StringField('Enter username')
    password = PasswordField('Enter password')
    remember = BooleanField(default=False)
    submit = SubmitField('Sign up')

    def validate_username(form, username):
        if len(username.data) == 0:
            raise ValidationError('Please, enter username')

    def validate_password(form, password):
        if len(password.data) < 6 or len(password.data) > 20:
            raise ValidationError('The password must contain between 6 and 20 characters')


class URLShortingForm(FlaskForm):
    url = URLField('URL')
    short_url_name = StringField('Short URL name (optional)')
    submit = SubmitField('Submit')

    def validate_url(form, url):
        if len(url.data) == 0:
            raise ValidationError('URL is required')
