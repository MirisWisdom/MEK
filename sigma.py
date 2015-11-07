'''

A module for doing various calculus related things:
    Approximate integration using the below methods:
        midpoint, left-endpoint, right-endpoint, trapezoidal rule, simpson rule

    Approximate summation of a series of partial sums
    Approximate arc length of a function
    Display the terms in a sequence

    Forgive the lack of comments, this was initially made
    to help with the tedious parts of calculus homework

'''

import os
from time import time

from math import *
from decimal import *
from traceback import format_exc

def alt(x):
    #Returns -1 if |x| is odd. Returns 1 otherwise
    return 1-2*(abs(int(x))&1)

fact = factorial

class sigma():

    time = 0.0
    
    def __init__(self, y, n=10, a=0, b=1, **kwargs):
        self.n = n
        self.a = a
        self.b = b
        self._sum = 0
        self.stop_point = 0
        self.abs = bool(kwargs.get('abs'))
        self.precision = kwargs.get('precision', 13)
        self.y = y

    def eval(self, x):
        return round(self.y(x), self.precision)

    def arc_length_old(self, n=None, a=None, b=None):
        #OUTDATED BY THE BELOW FUNCTION
        '''
        This function needs significant improvements.
        Takes around 15 seconds to calculate the arc of sqrt(1-x*x) at
        10,000,000 pieces and is still only accurate to 2 decimal places.
        (spits out 3.14096039)
        '''
        self._sum = self.stop_point = s = 0
        self.time = 0.0
        start = time()
        
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(n)
            
        dx = (b-a)/n

        xa = y(a)

        try:
            for i in range(n):
                xb = y(a+dx*i)
                s += sqrt(dx*dx + pow(xb-xa, 2) )
                xa = xb
        except KeyboardInterrupt:
            self.time = time() - start
            self._sum = round(s, self.precision)
            raise
        
        self._sum = round(s, self.precision)
        self.time = time() - start
            
        return self._sum

    def arc_length(self, n=None, a=None, b=None):
        '''
        A slightly more accurate method for calculating arc length than
        the above method. Uses a simpsons rule style method for approximating
        arc length. The exact method can be found at the link below.
        
        Normal Human (http://math.stackexchange.com/users/147263/normal-human)
        Simpson's Rule like Method for Arc Length Approximation,
        URL (version: 2014-05-02): http://math.stackexchange.com/q/778533
        '''
        self._sum = self.stop_point = s = s_diff = 0
        self.time = 0.0
        start = time()
        
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(ceil(n/2))*2
            
        dx = (b-a)/n
        dx_sq = dx*dx
        y0 = y(a)

        try:
            for i in range(n):
                y1 = y(a + dx*i)
                s += sqrt(dx_sq + pow(y1-y0, 2) )
                y0 = y1

            dx = dx*2
            dx_sq = dx*dx
            y0 = y(a)
        except KeyboardInterrupt:
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round(s, self.precision)
            raise
            
        try:
            for i in range(n//2):
                y1 = y(a + dx*i)
                s_diff += sqrt(dx_sq + pow(y1-y0, 2) )
                y0 = y1
        except KeyboardInterrupt:
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round((4*s - s_diff)/3, self.precision)
            raise
        
        self.time = time() - start
        self._sum = round((4*s - s_diff)/3, self.precision)
        
        return self._sum
        

    def mid(self, n=None, a=None, b=None):
        self._sum = self.stop_point = s = 0
        self.time = 0.0
        start = time()
        
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(n)
            
        dx = (b-a)/n
        h_dx = dx/2

        try:
            if self.abs:
                for i in range(n):
                    s += abs(y(a+dx*i + h_dx))
                    
                s *= abs(dx)
            else:
                for i in range(n):
                    s += y(a+dx*i + h_dx)
                
                s *= dx
        except KeyboardInterrupt:
            if self.abs:
                s *= abs(dx)
            else:
                s *= dx
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round(s, self.precision)
            raise
            
        self.time = time() - start
        self._sum = round(s, self.precision)
        return self._sum

    def left(self, n=None, a=None, b=None):
        self._sum = self.stop_point = s = 0
        self.time = 0.0
        start = time()
        
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(n)
            
        dx = (b-a)/n

        try:
            if self.abs:
                for i in range(n):
                    s += abs(y(a+dx*i))
                    
                s *= abs(dx)
            else:
                for i in range(n):
                    s += y(a+dx*i)
                
                s *= dx
        except KeyboardInterrupt:
            if self.abs:
                s *= abs(dx)
            else:
                s *= dx
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round(s, self.precision)
            raise
            
        self.time = time() - start
        self._sum = round(s, self.precision)
        return self._sum

    def right(self, n=None, a=None, b=None):
        self._sum = self.stop_point = s = 0
        self.time = 0.0
        start = time()
        
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(n)
            
        dx = (b-a)/n
        
        try:
            if self.abs:
                for i in range(1, n+1):
                    s += abs(y(a+dx*i))
                    
                s *= abs(dx)
            else:
                for i in range(1, n+1):
                    s += y(a+dx*i)
                
                s *= dx
        except KeyboardInterrupt:
            if self.abs:
                s *= abs(dx)
            else:
                s *= dx
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round(s, self.precision)
            raise
            
        self.time = time() - start
        self._sum = round(s, self.precision)
        return self._sum

    def trapezoid(self, n=None, a=None, b=None):
        self._sum = self.stop_point = s = 0
        self.time = 0.0
        start = time()
        
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(n)
            
        dx = (b-a)/n
        
        try:
            if self.abs:
                for i in range(1, n):
                    s += abs(y(a+dx*i))
                s = (s + abs(y(a)) + abs(y(b)) ) * abs(dx/2)
            else:
                for i in range(1, n):
                    s += y(a+dx*i)
                s = (s + y(a) + y(b)) * dx/2
        except KeyboardInterrupt:
            if self.abs:
                s = (s + abs(y(a)) + abs(y(b)) ) * abs(dx/2)
            else:
                s = (s + y(a) + y(b)) * dx/2
                
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round(s, self.precision)
            raise
            
        self.time = time() - start
        self._sum = round(s, self.precision)
        return self._sum

    def simpson(self, n=None, a=None, b=None):
        self._sum = self.stop_point = s = 0
        self.time = 0.0
        start = time()
        
        if n is None: n = self.n
        if a is None: a = self.a
        if b is None: b = self.b
        if a == b:    return 0
        if n <= 0:    n = 1
        y = self.y;   n = int(ceil(n/2))*2
            
        dx = (b-a)/n

        try:
            if self.abs:
                for i in range(2, n, 2):
                    s += abs(2*y(a + dx*i)) + abs(4*y(a + dx*(i+1)))
                s = (s + abs(y(a)) + abs(y(b)) + abs(4*y(a+dx))) * abs(dx/3)
            else:
                for i in range(2, n, 2):
                    s += 2*y(a + dx*i) + 4*y(a + dx*(i+1))
                s = (s + y(a) + y(b) + 4*y(a+dx)) * dx/3
        except KeyboardInterrupt:
            if self.abs:
                s = (s + abs(y(a)) + abs(y(b)) + abs(4*y(a+dx))) * abs(dx/3)
            else:
                s = (s + y(a) + y(b) + 4*y(a+dx)) * dx/3
                
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round(s, self.precision)
            raise
        
        self.time = time() - start
        self._sum = round(s, self.precision)
        return self._sum

    def series_sum(self, n=None, a=None):
        self._sum = self.stop_point = s = 0
        self.time = 0.0
        start = time()
        
        if n is None: n = self.n
        if a is None: a = self.a
        if n <= 0:    n = 1
        y = self.y

        try:
            if self.abs:
                for i in range(int(a), int(n)):
                    s += abs(y(i))
            else:
                for i in range(int(a), int(n)):
                    s += y(i)
        except KeyboardInterrupt:
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round(s, self.precision)
            raise
            
        self.time = time() - start
        self._sum = round(s, self.precision)
        return self._sum

    def sequence(self, a=None, b=None):
        self.time = 0.0
        start = time()
        
        if a is None: a = self.a
        if b is None: b = self.b
        a, b = int(a), int(b)
        y = self.y
        p = self.precision
        
        if b < a: b, a = a, b

        sequence = [0]*(b-a)
        
        for i in range(a, b):
            sequence[i-a] = round(y(i), p)
            
            
        self.time = time() - start
        return sequence

    @property
    def sum(self):
        return self._sum


if __name__ == '__main__':

    init = 0
    help_str = ("You may use any of the below commands.\n"+
                "    'y = xxxx'  sets the function being approximated.\n"+
                "    'n = xxxx'  sets the precision of the approximation to xxxx.\n"+
                "    'a = xxxx'  sets the lower limit to xxxx.\n"+
                "    'b = xxxx'  sets the upper limit to xxxx.\n"+
                "    'p = xxxx'  sets the number of places to round final values to xxxx.\n"+
                "    'abs = t/f' sets whether or not using only absolute values.\n\n"+
                "    'n'   prints the current value of n.\n"+
                "    'a'   prints the current value of a.\n"+
                "    'b'   prints the current value of b.\n"+
                "    'p'   prints the current number of places to round final values to.\n"+
                "    'abs' prints whether or not using only absolute values.\n\n"+
                "    'mid'    calculates the integral using the midpoint rule.\n"+
                "    'left'   calculates the integral using the left endpoint rule.\n"+
                "    'right'  calculates the integral using the right endpoint rule.\n"+
                "    'trap'   calculates the integral using the trapezoidal rule.\n"+
                "    'simp'   calculates the integral using the simpsons rule.\n"+
                "    'series' calculates the series sum at the Nth value.\n"+
                "    'arc'    calculates the length of the arc of the function from a to b.\n"+
                "    'seq'    prints N terms in the sequence at a time until reaching b.\n\n"+
                "    'xxxx' evaluates the function at xxx and prints the result.\n"+
                "    'sum'  prints the last sum calculated.\n"+
                "    'quit' exits the program.\n"+
                "    'cls'  clears the window of all text.\n"+
                "    'time' prints the amount of seconds the last computation took.\n"+
                "    'help' prints this message.\n\n"+
                "    '\\xxxx' compiles and executes xxxx as python code.\n"+
                "         This is almost as if you were using the console.\n\n")
    while True:
        while init == 0:
            print('Enter a valid f(x) function(y). Must use python syntax.\n'+
                  'Examples include:\n'+
                  '    pow(2,x)  ----->  2^x\n'+
                  '    x*x/5     ----->  x^2/5\n'+
                  '    sqrt(ln(x)) --->  ln(x)^(1/2)\n'+
                  '    abs(x-1)  ----->  |x-1|\n'+
                  '    log(x, 10)  --->  log_base_10(x)\n'+
                  '    e%x + 15  ----->  15 + modulus divide e by x')
            try:
                exec('Y = lambda x: '+input().strip())
                #see if the function works
                Y(0)
                init = 1
            except ArithmeticError:
                #if the only error is arithmetic, keep going
                init = 1
            except KeyboardInterrupt:
                pass
            except Exception:
                print(format_exc())
            
        while init == 1:
            print('\nEnter the number of pieces to approximate by(n).\n'+
                  'Must be a natural/whole number.')
            try:
                N = int(input().strip()); init = 2
            except KeyboardInterrupt:
                pass
            except Exception:
                print(format_exc())
            
        while init == 2:
            print('\nEnter the function lower limit(a).\n'+
                  'This also is the starting index for series sums.')
            try:    A = float(input().strip()); init = 3
            except KeyboardInterrupt:
                pass
            except Exception:
                print(format_exc())
            
        while init == 3:
            print('\nEnter the function upper limit(b).\n'+
                  'This does nothing for a approximating series sum.')
            try:    B = float(input().strip()); init = 4
            except KeyboardInterrupt:
                pass
            except Exception:
                print(format_exc())

        exec('calc = sigma(Y, N, A, B)')

        print('\n'+help_str)
        while True:
            try:
                if (B-A)/N > 1:
                    print(("For everything other than series the width of each"+
                           "piece will be too large.\na = %s, b = %s, n = %s\n"+
                           "The width of each piece will be (b-a)/n = %s\n"+
                           "Choose either a lower b or a larger n so that "+
                           "(b-a)/n <= 1\n    You may still run the "+
                           "calculations, but they will likely be very wrong.")
                          % (A, B, N, (B-A)/N))
                if N > 50000000:
                    print("n is %s. Calculations will take a long time."%N)
                inp = input().strip()

                if len(inp) == 0:
                    continue
                    
                Y = calc.y
                N = calc.n
                A = calc.a
                B = calc.b
                P = calc.precision
                ABS  = calc.abs

                if N <= 0: N = 1
                
                if inp[0] == '\\':
                    try:
                        print('    %s'% eval(inp.lstrip('\\ ')))
                    except SyntaxError:
                        #if it couldn't evaluate due to a syntax error, it might
                        #be because the input is to be executed, not evaluated
                        exec(inp.lstrip('\\ '))
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
                        print('    abs == %s'%bool(calc.abs))
                elif inp.lower() in ('arc length', 'arc', 'al'):
                    print('   This function still needs work since it is slow '+
                          'and has low precision\n   Set N to a high integer, '+
                          'but even still take its result with a grain of salt.')
                    print('   ',calc.arc_length())
                elif inp.lower() in ('midpoint', 'mid', 'm'):
                    print('   ',calc.mid())
                elif inp.lower() in ('left endpoint', 'left', 'l'):
                    print('   ',calc.left())
                elif inp.lower() in ('right endpoint', 'right', 'r'):
                    print('   ',calc.right())
                elif inp.lower() in ('trapezoid', 'trapezoidal', 'trap', 't'):
                    print('   ',calc.trapezoid())
                elif inp.lower() in ('simpsons', 'simpson', 'quadratic',
                                     'simp', 'quad'):
                    print('   ',calc.simpson())
                elif inp.lower() in ('series sum', 'series', 'ss'):
                    print('   ',calc.series_sum())
                elif inp.lower() in ('sequence', 'seq'):
                    if A > B:
                        A, B, = B, A
                    XA = int(A)
                    XB = int(XA + N)
                    if XB > int(B):
                        XB = int(B)+1
                    while XB <= int(B)+1:
                        if int(XA + 2*N) >= int(B)+1:
                            print('    [%s to %s] == %s'%
                                  (XA,XB-1,calc.sequence(XA,XB)))
                        else:
                            input('    [%s to %s] == %s'%
                                  (XA,XB-1,calc.sequence(XA,XB)))
                        if XB >= int(B)+1:
                            break
                        XA += int(N)
                        XB = int(XA + N)
                        if XB > int(B):
                            XB = int(B)+1
                            
                elif inp.lower() == 'sum':
                    print('   ',calc.sum)
                elif inp.lower() in ('help', '?'):
                    print(help_str)
                elif inp.lower() in ('clear screen', 'clear', 'cls'):
                    os.system('cls')
                elif inp.lower() in ('quit', 'exit'):
                    raise SystemExit
                elif inp.lower() == 'time':
                    print('   ',calc.time)
                elif inp[0].lower() == 'y':
                    try:
                        exec('Y = lambda x: '+inp.strip('yY= '))
                        Y(0)
                    except ArithmeticError:
                        #if the only error is arithmetic, keep going
                        pass
                    except:
                        print(format_exc())
                elif inp[0].lower() == 'n':
                    inp = inp.strip('nN ')
                    if len(inp) and inp[0] == '=':
                        N = int(inp.strip('= '))
                    else:
                        print('    n == %s'%calc.n)
                elif inp[0].lower() == 'a':
                    inp = inp.strip('aA ')
                    if len(inp) and inp[0] == '=':
                        A = float(inp.strip('= '))
                    else:
                        print('    a == %s'%calc.a)
                elif inp[0].lower() == 'b':
                    inp = inp.strip('bB ')
                    if len(inp) and inp[0] == '=':
                        B = float(inp.strip('= '))
                    else:
                        print('    b == %s'%calc.b)
                elif inp[0].lower() == 'p':
                    inp = inp.strip('pP ')
                    if len(inp) and inp[0] == '=':
                        P = int(inp.strip('= '))
                    else:
                        print('    p == %s'%calc.precision)
                else:
                    #if nothing else fits the input then try to evaluate
                    #the function at it(first check if its a number)
                    try:
                        inp = float(inp)
                        print('   y(%s) == %s' % (inp, calc.eval(inp)))
                    except:
                        print(format_exc())
                    
                    
                calc.y = Y
                calc.n = N
                calc.a = A
                calc.b = B
                calc.precision = P
                calc.abs = ABS
                    
            except Exception:
                print(format_exc())
            except KeyboardInterrupt:
                print('Operation cancelled by user.')
                if calc.stop_point is not int(0):
                    print('Operation cancelled at x=%s' % calc.stop_point)
                    
                calc.stop_point = int(0)
                
            #make a space between inputs for ease of reading
            print()
