import argparse
import os
import sys
import signal
import threading
from time import sleep
from multiprocessing import Process

SIGNALS_CAUGHT = (
  signal.SIGHUP, 
  signal.SIGINT,
  signal.SIGQUIT,
  signal.SIGUSR1,
 )
 
NUM_PROCESSES = 2

 
def set_up_signal_handlers():
  for signal_caught in SIGNALS_CAUGHT:
    signal.signal(signal_caught, _signal_handler)

def _signal_handler(sig, frame):
  print "==> Caught signal {sig} in PID {pid}".format(sig=sig, pid=os.getpid())

def worker(parent_pid=None):
  pid = os.getpid()

  if not parent_pid:
    print "PARENT process PID {pid}".format(pid=pid)
  else:
    print "CHILD process (PID {pid}) of parent PID {parent_pid}".format(pid=pid, parent_pid=parent_pid)
    
  while True:
    sleep(1)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='An example program used to understand POSIX signals handling')
  parser.add_argument('--processes', '-p', action="store_true", default=False, 
    help="Spawn subprocesses")    
  parser.add_argument('--catch-sigterm', '-c', action="store_true", default=False, 
    help="Catch SIGTERM")
  
  args = vars(parser.parse_args())
  enable_multiprocessing = args['processes']
  catch_sigterm = args['catch_sigterm']
  
  if catch_sigterm:
    SIGNAL_CAUGHT = SIGNALS_CAUGHT + (signal.SIGTERM,)

  set_up_signal_handlers()
  
  if enable_multiprocessing:
    parent_pid = os.getpid()
    for i in xrange(NUM_PROCESSES):
      Process(target=worker, args=(parent_pid,)).start()
  
  worker()