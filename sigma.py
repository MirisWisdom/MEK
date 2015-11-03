'''

A module for doing various calculus related things:
    Approximate integration using the below methods:
        midpoint, left-endpoint, right-endpoint, trapezoidal rule, simpson rule

    Approximate summation of a series of partial sums
    Display the terms in a sequence

    Forgive the lack of comments, this was initially made
    to help with the tedious parts of calculus homework

'''


from math import *
from decimal import *
from traceback import format_exc

class sigma():
    
    def __init__(self, y, n=10, a=0, b=1, **kwargs):
        self.n = n
        self.a = a
        self.b = b
        self._sum = 0
        self.abs = bool(kwargs.get('abs'))

        self.y = y

    def mid(self, n=None, a=None, b=None):
        self._sum = s = 0
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(n)
            
        dx = (b-a)/n
        h_dx = dx/2
        
        if self.abs:
            for i in range(n):
                s += abs(y(a+dx*i + h_dx))
                
            self._sum = s*abs(dx)
        else:
            for i in range(n):
                s += y(a+dx*i + h_dx)
            
            self._sum = s*dx
            
        return self._sum

    def left(self, n=None, a=None, b=None):
        self._sum = s = 0
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(n)
            
        dx = (b-a)/n

        if self.abs:
            for i in range(n):
                s += abs(y(a+dx*i))
                
            self._sum = s*abs(dx)
        else:
            for i in range(n):
                s += y(a+dx*i)
            
            self._sum = s*dx
            
        return self._sum

    def right(self, n=None, a=None, b=None):
        self._sum = s = 0
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(n)
            
        dx = (b-a)/n

        if self.abs:
            for i in range(1, n+1):
                s += abs(y(a+dx*i))
                
            self._sum = s*abs(dx)
        else:
            for i in range(1, n+1):
                s += y(a+dx*i)
            
            self._sum = s*dx
            
        return self._sum

    def trapezoid(self, n=None, a=None, b=None):
        self._sum = s = 0
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(n)
            
        dx = (b-a)/n

        if self.abs:
            for i in range(1, n):
                s += abs(y(a+dx*i))
                
            s += abs(y(a)) + abs(y(b))/2
            s *= abs(dx)
        else:
            for i in range(1, n):
                s += y(a+dx*i)
            
            s += (y(a) + y(b))/2
            s *= dx
        
        self._sum = s
        return self._sum

    def simpson(self, n=None, a=None, b=None):
        self._sum = s = 0
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(ceil(n/2))*2
            
        dx = (b-a)/n
        
        if self.abs:
            for i in range(2, n, 2):
                s += abs(2*y(a + dx*i)) + abs(4*y(a + dx*(i+1)))
                
            s += abs(y(a)) + abs(y(b)) + abs(4*y(a+dx))
            s *= abs(dx/3)
        else:
            for i in range(2, n, 2):
                s += 2*y(a + dx*i) + 4*y(a + dx*(i+1))
            
            s += y(a) + y(b) + 4*y(a+dx)
            s *= dx/3
        
        self._sum = s
        
        return self._sum

    def series_sum(self, n=None, a=None):
        self._sum = s = 0
        
        if n is None: n = self.n
        if a is None: a = self.a
        if n <= 0:    n = 1
        y = self.y

        if self.abs:
            for i in range(int(a), int(n)):
                s += abs(y(i))
        else:
            for i in range(int(a), int(n)):
                s += y(i)
            
            
        self._sum = s
        
        return self._sum

    def sequence(self, a=None, b=None):
        if a is None: a = self.a
        if b is None: b = self.b
        a, b = int(a), int(b)
        y = self.y
        
        if b < a: b, a = a, b

        sequence = [0]*(b-a)

        for i in range(a, b):
            sequence[i-a] = (y(i))
            
        return sequence

    @property
    def sum(self):
        return self._sum



if __name__ == '__main__':

    init = 0
    help_str = ("You may use any of the below commands.\n"+
                "    'y = xxx' sets the function being approximated.\n"+
                "    'n = xxx' sets the precision of the approximation to xxx.\n"+
                "    'a = xxx' sets the lower limit to xxx.\n"+
                "    'b = xxx' sets the upper limit to xxx.\n"+
                "    'abs = True/False' sets whether or not using only absolute values.\n\n"+
                "    'n' prints the current value of n.\n"+
                "    'a' prints the current value of a.\n"+
                "    'b' prints the current value of b.\n"+
                "    'abs' prints whether or not using only absolute values.\n\n"+
                "    'mid'    calculates the integral using the midpoint rule.\n"+
                "    'left'   calculates the integral using the left endpoint rule.\n"+
                "    'right'  calculates the integral using the right endpoint rule.\n"+
                "    'trap'   calculates the integral using the trapezoidal rule.\n"+
                "    'simp'   calculates the integral using the simpsons rule.\n"+
                "    'series' calculates the series sum at the Nth value.\n"+
                "    'seq'    prints N terms in the sequence at a time until reaching b.\n\n"+
                "    'sum'  prints the last sum calculated.\n"+
                "    'quit' exits the program.\n"+
                "    'help' prints this message.\n\n")
    while True:
        while init == 0:
            print('Enter a valid f(x) function(y). Must use python syntax.\n'+
                  'Examples include:\n'+
                  '    pow(2,x)  ----->  2^x\n'+
                  '    x*x/5     ----->  x^2/5\n'+
                  '    sqrt(ln(x)) --->  ln(x)^(1/2)\n'+
                  '    abs(x-1)  ----->  |x-1|\n'+
                  '    log(x, 10)  --->  log_base_10(x)\n'+
                  '    e%x + 15  ----->  modulus divide e by x')
            try:    exec('Y = lambda x: '+input().strip()); init = 1
            except: print(format_exc())
            
        while init == 1:
            print('\nEnter the number of pieces to approximate by(n).\n'+
                  'Must be a natural/whole number.')
            try:    N = int(input().strip()); init = 2
            except: print(format_exc())
            
        while init == 2:
            print('\nEnter the function lower limit(a).\n'+
                  'This also is the starting index for series sums.')
            try:    A = float(input().strip()); init = 3
            except: print(format_exc())
            
        while init == 3:
            print('\nEnter the function upper limit(b).\n'+
                  'This does nothing for a approximating series sum.')
            try:    B = float(input().strip()); init = 4
            except: print(format_exc())

        exec('test = sigma(Y, N, A, B)')

        print('\n'+help_str)
        while True:
            try:
                inp = input().strip()

                if len(inp) == 0:
                    continue
                    
                Y = test.y
                N = test.n
                A = test.a
                B = test.b
                ABS  = test.abs

                if inp[0].lower() == 'y':
                    try:
                        exec('Y = lambda x: '+inp.strip('yY= '))
                    except:
                        print(format_exc())
                elif len(inp) >= 3 and inp[:3].lower() == 'abs':
                    inp = inp.strip('aAbBsS ')
                    if len(inp) and inp[0] == '=':
                        inp = inp.strip('= ')
                        try:
                            inp = int(inp)
                        except:
                            if inp.lower() in ('false', 'no', 'f', 'n'):
                                inp = False
                            elif inp.lower() in ('true', 'yes', 't', 'y'):
                                inp = True
                            
                        ABS = bool(inp)
                    else:
                        print('    abs == %s'%bool(test.abs))
                elif inp[0].lower() == 'n':
                    inp = inp.strip('nN ')
                    if len(inp) and inp[0] == '=':
                        N = int(inp.strip('= '))
                    else:
                        print('    n == %s'%test.n)
                elif inp[0].lower() == 'a':
                    inp = inp.strip('aA ')
                    if len(inp) and inp[0] == '=':
                        A = float(inp.strip('= '))
                    else:
                        print('    A == %s'%test.a)
                elif inp[0].lower() == 'b':
                    inp = inp.strip('bB ')
                    if len(inp) and inp[0] == '=':
                        B = float(inp.strip('= '))
                    else:
                        print('    b == %s'%test.b)
                elif inp.lower() in ('midpoint', 'mid', 'm'):
                    print('   ',test.mid())
                elif inp.lower() in ('left endpoint', 'left', 'l'):
                    print('   ',test.left())
                elif inp.lower() in ('right endpoint', 'right', 'r'):
                    print('   ',test.right())
                elif inp.lower() in ('trapezoid', 'trapezoidal', 'trap', 't'):
                    print('   ',test.trapezoid())
                elif inp.lower() in ('simpsons', 'simpson', 'quadratic',
                                     'simp', 'quad'):
                    print('   ',test.simpson())
                elif inp.lower() in ('series sum', 'series'):
                    print('   ',test.series_sum())
                elif inp.lower() in ('sequence', 'seq'):
                    if A == B:
                        continue
                    XA = int(A)
                    XB = int(XA + N)
                    if XB > int(B):
                        XB = int(B)
                    while XB <= int(B):
                        if int(XA + 2*N) >= int(B):
                            print('    [%s to %s] == %s'%
                                  (XA,XB-1,test.sequence(XA,XB)))
                        else:
                            input('    [%sto %s] == %s'%
                                  (XA,XB-1,test.sequence(XA,XB)))
                        if XB >= int(B):
                            break
                        XA += int(N)
                        XB = int(XA + N)
                        if XB > int(B):
                            XB = int(B)
                            
                elif inp.lower() == 'sum':
                    print('   ',test.sum)
                elif inp.lower() in ('help', '?'):
                    print(help_str)
                elif inp.lower() in ('quit', 'exit'):
                    raise SystemExit
                    
                    
                test.y = Y
                test.n = N
                test.a = A
                test.b = B
                test.abs = ABS
            except Exception:
                print(format_exc())
            except KeyboardInterrupt:
                print('Operation cancelled by user.')
