'''
expt_supp.py
Tools built on top of expt.py.
'''
import expt

def doct(t=.1):
    pc = expt.configure_counter(duration=t)
    with expt.counting(*pc):
        val = expt.do_count(*pc) / t
        return val

