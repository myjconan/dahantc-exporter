
import subprocess
command='ls /home/k8s/k8s_init/k8s_init/yaml/test'
subprocess.call(command, shell=True)

import datetime

since_seconds=600
current_time = datetime.datetime.now()
last_time = current_time - datetime.timedelta(
    seconds=int(since_seconds))

current_time_head = current_time.strftime("%Y-%m-%d")
current_time_tail = current_time.strftime("%H:%M:%S")

last_time_head=last_time.strftime("%Y-%m-%d")
last_time_tail=last_time.strftime("%H:%M:%S")

print(current_time_tail)
print(last_time_tail)

time_str = '{current_time_head}T{current_time_tail}'.format(current_time_head=current_time_head,
                                                            current_time_tail=current_time_tail)
print(time_str)