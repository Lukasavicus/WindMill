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

class JobList():
	pass

# === Job - Model =============================================================
class Job():
	_id = None
	name = None
	entry_point = None
	start_at = None
	end_at = None
	schd_hours = 0
	schd_minutes = 0
	schd_seconds = 0
	last_exec_status = None#STATUS['not_running']
	no_runs = 0

	_pid = None
	_process_pointer = None
	agent = None

	def __init__(self, name, entry_point, start_at=None, end_at = None, schd_hours = 0, schd_minutes = 0, schd_seconds = 0):
		self.name = name
		self.entry_point = entry_point
		self.start_at = start_at
		self.end_at = end_at
		self.schd_hours = schd_hours
		self.schd_minutes = schd_minutes
		self.schd_seconds = schd_seconds

	def isAlive(self):
		return (self._process_pointer != None and self._process_pointer.poll() == None)

	def play(self):
		self.agent.execute_job()

	def stop(self):
		self.agent.kill_job()

	def jsonify(self):
		return {'_id': self._id, 'pid': self._pid, 'name': self.name, 'entry_point': self.entry_point,
                    'last_exec_status': self.last_exec_status, 'start_at': self.start_at}

	def __repr__(self):
		return f"JOB: id[{self._id}] name[{self.name}]"

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++