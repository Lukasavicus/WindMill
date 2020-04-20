import sys
import os
from apscheduler.schedulers.blocking import BlockingScheduler
import platform

python_cmd = 'python' if platform.system() == 'Windows' else 'python3'

def cronjob(): # script_name
    print("cronjob")
    cmd = '{} {}'.format(python_cmd, sys.argv[1]) # ' '.join(sys.argv[1:])
    print("cron cmd ", cmd)
    os.system(cmd)
    #os.system('python '+ script_name)


if __name__ == "__main__":
    #print("This is the name of the script: ", sys.argv[0])
    #print("Number of arguments: ", len(sys.argv))
    #print("The arguments are: " , str(sys.argv))
    # sys.argv[0]
    print("arguments ", sys.argv)
    scheduler = BlockingScheduler()

    interval = sys.argv[2]
    no_interval = int(sys.argv[3])

    print("(SCHDL) Executando {} com {}={}".format(sys.argv[1], sys.argv[2], sys.argv[3]))

    flag = False
    # Melhorar isso:
    if(interval == 'seconds'):
        scheduler.add_job(cronjob, 'interval', seconds=no_interval)
        flag = True
    elif(interval == 'minutes'):
        scheduler.add_job(cronjob, 'interval', minutes=no_interval)
        flag = True
    elif(interval == 'hours'):
        scheduler.add_job(cronjob, 'interval', hours=no_interval)
        flag = True
    
    if(flag):
        scheduler.start()
