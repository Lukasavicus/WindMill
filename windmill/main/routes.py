# === imports =================================================================
#from flask import current_app as app
from windmill import app, db, bcrypt
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
from flask import send_file
import os

from werkzeug.utils import secure_filename
from zipfile import ZipFile
import shutil

from windmill.main.utils import trace, divisor, __resolve_path, uri_sep, MsgTypes
from windmill.main.forms import RegistrationForm, LoginForm

from windmill.models import User
from flask_login import login_user, current_user, logout_user, login_required

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

main = Blueprint('main', __name__)

@main.route('/register', methods=['GET', 'POST'])
def register():
	if(current_user.is_authenticated):
		return redirect(url_for('tasks.home'))

	form = RegistrationForm()
	if(form.validate_on_submit()):

		hashed_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data, email=form.email.data, password=hashed_pass)
		db.session.add(user)
		db.session.commit()

		print('Validation on register success')
		flash({'title' : 'Register Success', 'msg' : f'Account created {form.username.data}!', 'type' : MsgTypes['SUCCESS']})
		return redirect(url_for('tasks.home'))
	else:
		print('Validation on register failed')
	return render_template('register.html', title='Register', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
	if(current_user.is_authenticated):
		return redirect(url_for('tasks.home'))

	form = LoginForm()
	if(form.validate_on_submit()):
		print('Login Form correct')
		
		user = User.query.filter_by(email=form.email.data).first()
		
		if(user and bcrypt.check_password_hash(user.password, form.password.data)):
			login_user(user, remember=form.remember.data)
			flash({'title' : 'Logged In Success', 'msg' : f'Account logged: {form.email.data}!', 'type' : MsgTypes['SUCCESS']})

			next_page = request.args.get('next') or url_for('tasks.home')

			return redirect(next_page)
		else:
			flash({'title' : 'Logged In Error', 'msg' : f'Account or Password doesn\'t match' , 'type' : MsgTypes['ERROR']})
	else:
		print('Validation on login failed')
	return render_template('login.html', title='Register', form=form)

@main.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('main.login'))

@main.route('/account')
@login_required
def account():
	return render_template('account.html', title='Account')