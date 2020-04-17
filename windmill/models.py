from windmill import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


# === User - Model ============================================================
# SQLite
# The usage of UserMixin is necessary to transform this class into something that uses Login utilities
class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	# image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
	password = db.Column(db.String(60), nullable=False)

	# double-underscored methods -> dunder methods -> magic methods
	def __repr__(self):
		return f"User('{self.id}', '{self.username}', '{self.email}')"

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === Job - Model =============================================================
# SQLite
class SQLJob(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20), unique=True, nullable=False)
	entry_point = db.Column(db.String(20), unique=True, nullable=False)
	start_at = db.Column(db.DateTime)
	end_at = db.Column(db.DateTime)
	schd_hours = db.Column(db.Integer)
	schd_minutes = db.Column(db.Integer)
	schd_seconds = db.Column(db.Integer)
	last_exec_status = db.Column(db.String(15))
	no_runs = db.Column(db.Integer)

	#pid
	#pointer
 

	# double-underscored methods -> dunder methods -> magic methods
	def __repr__(self):
		return f"User('{self.id}', '{self.name}', '{self.entry_point}')"
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++