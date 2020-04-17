from windmill import mongo
from datetime import datetime
from bson.objectid import ObjectId
from flask import current_app as app

# TODO: change to an Enum
STATUS = {}
STATUS['not_running'] = "Not Running"
STATUS['running'] = "Running"

#class DAO():


# === Job - Data Access Object ================================================
class JobDAO():
	_id = None
	name = None
	entry_point = None
	start_at = None
	end_at = None
	schd_hours = 0
	schd_minutes = 0
	schd_seconds = 0
	last_exec_status = STATUS['not_running']
	no_runs = 0

	_pid = None
	_process_pointer = None

	def __init__(self, name, entry_point, start_at=None, end_at = None, schd_hours = 0, schd_minutes = 0, schd_seconds = 0):
		self.name = name
		self.entry_point = entry_point
		self.start_at = start_at
		self.end_at = end_at
		self.schd_hours = schd_hours
		self.schd_minutes = schd_minutes
		self.schd_seconds = schd_seconds

	def insert(self):
		mongo.db.jobs.insert({
			'name' : self.name,
			'entry_point' : self.entry_point,
			'start_at' : self.start_at,
			'end_at' : self.end_at,
			'schd_hours' : self.schd_hours,
			'schd_minutes' : self.schd_minutes,
			'schd_seconds' : self.schd_seconds,
			'last_exec_status' : self.last_exec_status,
			'no_runs' : self.no_runs,
		})

	def isAlive(self):
		return (self._process_pointer != None and self._process_pointer.poll() == None)

	def play(self):
		log = open((self.name + '.txt'), 'a')  # so that data written to it will be appended
		#p = sub.Popen(['python3 ', (os.path.join(app.config['UPLOAD_FOLDER'], job["entry_point"]))], stdout=log)
		p = sub.Popen([(app.config['python_cmd'] + ' '), (os.path.join(app.config['UPLOAD_FOLDER'], self.entry_point ))], stdout=log)
		self._process_pointer = p
		self.pid = p.pid
		self.status = STATUS['running']

	def stop(self):
		self._process_pointer.kill()
		self.status = "not active"

	def delete(self):
		if(self._process_pointer):
			self._process_pointer.kill()
		mongo.db.jobs.delete_one( {"_id": ObjectId(self._id)});

	@staticmethod
	def recover():
		return list(mongo.db.jobs.find({}))

	@staticmethod
	def recover_by_id(id):
		return list(mongo.db.jobs.find_one({_id : ObjectId(id)}))

	@staticmethod
	def delete_by_id(id):
		return mongo.db.jobs.delete_one( {"_id": ObjectId(id)});

	def __repr__(self):
		return f"JOB: id[{self._id}] name[{self.name}]"
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++