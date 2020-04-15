from windmill import db
db.create_all()

from windmill import Job
job1 = Job(name='example', entry_point='example.py')
db.session.add(job1)
db.session.commit()

# Job.query.all()
# Job.query.first()
# Job.query.filter_by(name='example').all()
# Job.query.filter_by(name='example').first()
# Job.query.get(1)

db.drop_all()