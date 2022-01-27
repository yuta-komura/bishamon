import datetime
import time
import winsound

path = r"C:\Users\esfgs\bishamon\log\error_date.log"

error_date = None
while True:
    with open(path, mode='r') as f:
        f = f.read()
    if error_date and error_date != f:
        for i in range(1000):
            winsound.Beep(1000, 500)
            print(datetime.datetime.now(), "NG")
    error_date = f
    print(datetime.datetime.now(), "OK")
    time.sleep(1)
