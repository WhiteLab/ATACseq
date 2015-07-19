from time import time
import multiprocessing as mp
import subprocess

def f():
    subprocess.call('ls > /dev/null', shell=True)
    print 'hello'

begin = time()
print 'begin at ' + str(begin)

pool = mp.Pool()
for x in range(0,1000):
    pool.apply_async(f)
pool.close()
pool.join()
print 'elapsed time: ' + str(time() - begin) + ' seconds'
