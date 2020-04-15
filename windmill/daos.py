from windmill import mongo
from datetime import datetime

STATUS = {}
STATUS['not_running'] = "Not Running"

#class DAO():


# === Job - Data Access Object ================================================
class JobDAO():
	name = None
	entry_point = None
	pid = None
	start_at = None
	end_at = None
	schd_hours = 0
	schd_minutes = 0
	schd_seconds = 0
	last_exec_status = STATUS['not_running']
	no_runs = 0

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

	@staticmethod
	def recover():
		return list(mongo.db.jobs.find({}))
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++