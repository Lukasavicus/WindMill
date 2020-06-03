import os
# from enum import Enum

TRACE = True
divisor = "\n"*3+"="*50+"\n"*3

uri_sep = '/'

def trace(function_name):
    if(TRACE):
        print(function_name)

def __resolve_path(path):
    """
        This function is required to enable WindMill to run in both Windows and Linux Platforms
    """
    #return path.replace(os.path.sep, '/')
    #return path
    return path.replace('/', os.path.sep)


MsgTypes = {}

MsgTypes['SIMPLE']='primary'
MsgTypes['SIMPLE2']='secondary'
MsgTypes['SUCCESS']='success'
MsgTypes['ERROR']='danger'
MsgTypes['WARNING']='warning'
MsgTypes['INFO']='info'
MsgTypes['FADDED']='light'
MsgTypes['EMPHASY']='dark'

#class MsgTypes(Enum):
	# SIMPLE='primary'
	# SIMPLE2='secondary'
	# SUCCESS='success'
	# ERROR='danger'
	# WARNING='warning'
	# INFO='info'
	# FADDED='light'
	# EMPHASY='dark'
