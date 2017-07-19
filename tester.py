'''
sjha_tools_tester.py
Just junk for quick tests. Will frequently be rewritten.
'''

#Figuring out how to call functions defined within a class
#from within the class.

def inter(val):
    return int(val)

class classy():
    def __init__(self, val):
        self.val = val
    
    def successor(num):
        if type(num) != int:
            num = int(num)
        return num + 1
    
    def successor_sq(num):
        num = classy.successor(num)
        return num + 1
