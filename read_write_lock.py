from threading import Condition, RLock


class RWLock:
    def __init__(self, read_write_lock):
        self.rwl = read_write_lock

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def acquire(self):
        pass

    def release(self):
        pass


class ReadRWLock(RWLock):
        
    def acquire(self):
        self.rwl.reader_condition.acquire()
        try:
            while self.rwl.writers:
                self.rwl.reader_condition.wait()
                
            self.rwl.readers += 1
        finally:
            self.rwl.reader_condition.release()

    def release(self):
        self.rwl.reader_condition.acquire()
        try:
            self.rwl.readers -= 1

            if self.rwl.writers and not self.rwl.readers:
                self.rwl.writer_condition.notify_all()
        finally:
            self.rwl.reader_condition.release()

class WriteRWLock(RWLock):

    def acquire(self):
        self.rwl.writer_condition.acquire()
        self.rwl.writers += 1
        
        while self.rwl.readers:
            self.rwl.writer_condition.wait()

    def release(self):
        self.rwl.writers -= 1
        if self.rwl.readers and not self.rwl.writers:
            self.rwl.reader_condition.acquire()
        self.rwl.writer_condition.release()
        

class ReadWriteLockMeta:

    def __init__(self):
        lock = RLock()
        self.reader_condition = Condition(lock)
        self.writer_condition = Condition(lock)
        self.readers = 0
        self.writers = 0


def get_RWLocks():
    rwlock_meta = ReadWriteLockMeta()
    return ReadRWLock(rwlock_meta), WriteRWLock(rwlock_meta)

def read_lock(method):
    def wrapper(self, *args, **kwargs):
        with self.read_lock:
            return method(self, *args, **kwargs)

    return wrapper

def write_lock(method):
    def wrapper(self, *args, **kwargs):
        with self.write_lock:
            return method(self, *args, **kwargs)

    return wrapper
