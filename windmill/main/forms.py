from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from windmill.models import User


class RegistrationForm(FlaskForm):
	username = StringField('Username', validators=[
			DataRequired(),	Length(min=2, max=20)
		])
	email = StringField('Email', validators=[
			DataRequired(), Email()
		])
	password = PasswordField('Password', validators=[
			DataRequired()
		])
	confirm_password = PasswordField('Confirm Password', validators=[
			DataRequired(), EqualTo('password')
		])
	submit = SubmitField('Sign Up')

	def validate_username_uniqueness(self, username):
		user = User.query_filter_by(username=username.data).first()
		if user:
			raise ValidationError('This username is already taken!')

	def validate_email_uniqueness(self, email):
		user = User.query_filter_by(email=email.data).first()
		if user:
			raise ValidationError('This email is already taken!')

class LoginForm(FlaskForm):
	email = StringField('Email', validators=[
			DataRequired(), Email()
		])
	password = PasswordField('Password', validators=[
			DataRequired()
		])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Log In')