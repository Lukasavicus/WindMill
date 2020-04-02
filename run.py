# =============================================================================
# WindMill 
#
# WindMill is a project to control the execution of jobs written in Python.
# WindMill provides a server (and a front-end interface) to control user's
# jobs, allowing to play, to stop, know which jobs are running, to schedule
# jobs and more features.
#
# lukasavicus at gmail dot com
# March 25, 2020 
# =============================================================================

from windmill import app

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')
