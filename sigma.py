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
    #Returns -1 if |x| is odd. Returns 1 otherwise.
    #REQUIRES THAT x BE AN INTEGER, NOT A DECIMAL
    return 1-2*(x%2)

fact = factorial
ln = log
log2  = lambda x: log(x, 2)
log10 = lambda x: log(x, 10)

inf = float('inf')
n_inf = float('-inf')

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

    def arc_length(self, n=None, a=None, b=None):
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
        dx_sq = dx*dx

        y0 = y(a)

        try:
            for i in range(1, n+1):
                y1 = y(a + dx*i)
                s += sqrt(dx_sq + pow(y1-y0, 2) )
                y0 = y1
        except KeyboardInterrupt:
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round(s, self.precision)
            raise
        
        self._sum = round(s, self.precision)
        self.time = time() - start
            
        return self._sum

    def volume_x_axis(self, n=None, a=None, b=None):
        '''approximates volume of the solid of revolution about the x axis
        from A to B using simpsons rule combined with the disc method.'''
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
            for i in range(2, n, 2):
                s += 2*pow(y(a + dx*i), 2) + 4*pow(y(a + dx*(i+1)), 2)
            s = (s + pow(y(a), 2) + pow(y(b), 2) + 4*pow(y(a+dx), 2))*(pi*dx)/3
        except KeyboardInterrupt:
            s = (s + pow(y(a), 2) + pow(y(b), 2) + 4*pow(y(a+dx), 2))*(pi*dx)/3
                
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round(s, self.precision)
            raise
        
        self.time = time() - start
        self._sum = round(s, self.precision)
        return self._sum

    def volume_y_axis(self, n=None, a=None, b=None):
        '''approximates volume of the solid of revolution about the y axis
        from A to B using simpsons rule combined with the shells method.'''
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
            for i in range(2, n, 2):
                s += (2*(a + dx*i) *y(a + dx*i) + 4*(a + dx*(i+1))*y(a + dx*(i+1)))
            s = (s + a*y(a) + b*y(b) + 4*(a+dx)*y(a+dx))*(2*pi*dx)/3
        except KeyboardInterrupt:
            s = (s + a*y(a) + b*y(b) + 4*(a+dx)*y(a+dx))*(2*pi*dx)/3
                
            self.time = time() - start
            self.stop_point = a + dx*i
            self._sum = round(s, self.precision)
            raise
        
        self.time = time() - start
        self._sum = round(s, self.precision)
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
                s = (s + (abs(y(a)) + abs(y(b)))/2) * abs(dx)
            else:
                for i in range(1, n):
                    s += y(a+dx*i)
                s = (s + (y(a) + y(b))/2) * dx
        except KeyboardInterrupt:
            if self.abs:
                s = (s + (abs(y(a)) + abs(y(b)))/2) * abs(dx)
            else:
                s = (s + (y(a) + y(b))/2) * dx
                
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

        if self.abs:
            for i in range(a, b):
                sequence[i-a] = round(abs(y(i)), p)
        else:
            for i in range(a, b):
                sequence[i-a] = round(y(i), p)
            
            
        self.time = time() - start
        return sequence

    @property
    def sum(self):
        return self._sum


if __name__ == '__main__':
    help_str = ("You may use any of the below commands.\n"+
                "    'y = xxxx'  sets the function being approximated.\n"+
                "    Examples include:\n"+
                "        pow(2,x)  ----->  2^x\n"+
                "        x*x/5     ----->  x^2/5\n"+
                "        sqrt(ln(x)) --->  ln(x)^(1/2)\n"+
                "        abs(x-1)  ----->  |x-1|\n"+
                "        log(x, 10)  --->  log_base_10(x)\n"+
                "        e%x + 15  ----->  15 + modulus divide e by x\n\n"+
                "    'n = xxxx'  sets the precision of the approximation to xxxx.\n"+
                "    'a = xxxx'  sets the lower limit to xxxx.\n"+
                "    'b = xxxx'  sets the upper limit to xxxx.\n"+
                "    'p = xxxx'  sets the number of places to round final values to xxxx.\n"+
                "    'dx = xxxx' sets how wide each approximation piece is by using n = (b-a)/dx\n"+
                "    'abs = t/f' sets whether or not using only absolute values.\n\n"+
                "    'n'    prints the current value of n.\n"+
                "    'a'    prints the current value of a.\n"+
                "    'b'    prints the current value of b.\n"+
                "    'p'    prints the current number of places to round final values to.\n"+
                "    'dx'   prints how wide each approximation piece is.\n"+
                "    'abs'  prints whether or not using only absolute values.\n"+
                "    'vars' prints the current values of n, a, b, dx, p, abs, and sum.\n\n"+
                "    'mid'    calculates the integral using the midpoint rule.\n"+
                "    'left'   calculates the integral using the left endpoint rule.\n"+
                "    'right'  calculates the integral using the right endpoint rule.\n"+
                "    'trap'   calculates the integral using the trapezoidal rule.\n"+
                "    'simp'   calculates the integral using the simpsons rule.\n"+
                "    'series' calculates the series sum at the Nth value.\n"+
                "    'arc'    calculates the length of the arc of the function from a to b.\n"+
                "    'seq'    prints n terms in the sequence at a time until reaching b.\n\n"+
                "    'volx'   calculates the volume of the solid of revolution made\n"+
                "             by rotating f(x) about the x axis from a to b. approximation\n"+
                "             is done using simpsons rule and the disc volume method.\n"+
                "    'voly'   calculates the volume of the solid of revolution made\n"+
                "             by rotating f(x) about the y axis from a to b. approximation\n"+
                "             is done using simpsons rule and the shells volume method.\n\n"+
                "    'xxxx' evaluates the function at xxx and prints the result.\n"+
                "    'sum'  prints the last sum calculated.\n"+
                "    'quit' exits the program.\n"+
                "    'cls'  clears the window of all text.\n"+
                "    'time' prints the amount of seconds the last computation took.\n"+
                "    'help' prints this message.\n\n"+
                "    '\\xxxx' compiles and executes xxxx as python code.\n"+
                "         This is almost as if you were using the console.\n\n")
    while True:
        y_str = 'pow(e, -(x*x))'
        calc = sigma(lambda x: pow(e, -(x*x)), 1000000, -1000, 1000)

        print('\n'+help_str)
        warned = False
        while True:
            try:
                y = calc.y
                n = calc.n
                a = calc.a
                b = calc.b
                p = calc.precision
                ABS  = calc.abs

                if n <= 0: n = 1
                
                if not warned:
                    if (b-a)/n > 1:
                        print(("Excluding series, the width of each piece "+
                               "will be too large.\na = %s, b = %s, n = %s\n"+
                               "The width of each piece will be (b-a)/n = %s\n"+
                               "Choose to either lower 'b' or increase 'n' so "+
                               "that (b-a)/n <= 1\n    You may still run the "+
                               "calculations, but they will likely be very wrong.")
                              % (a, b, n, (b-a)/n))
                    if n > 5000000:
                        print("n is %s. Calculations will take a long time."%n)
                    
                INP = input().strip()
                warned = True

                if len(INP) == 0:
                    continue
                
                if INP[0] == '\\':
                    inp = INP.lstrip('\\ ')
                    try:
                        print('    %s'% eval(inp))
                    except SyntaxError:
                        #if it couldn't evaluate due to a syntax error, it might
                        #be because the input is to be executed, not evaluated
                        exec(inp)
                    continue
                elif len(INP) >= 3 and INP[:3].lower() == 'abs':
                    inp = INP.strip('aAbBsS ')
                    if len(inp) and inp[0] == '=':
                        inp = inp.strip('= ')
                        try:
                            inp = int(inp)
                        except:
                            if inp.lower() in ('false', 'no', 'f', 'n'):
                                inp = False
                            elif inp.lower() in ('true', 'yes', 't', 'y'):
                                inp = True
                            
                        calc.abs = bool(inp)
                    else:
                        print('    abs == %s'%bool(ABS))
                    continue
                elif INP.lower() in ('arc length', 'arc', 'al'):
                    print('   ',calc.arc_length())
                    continue
                elif INP.lower() in ('midpoint', 'mid', 'm'):
                    print('   ',calc.mid())
                    continue
                elif INP.lower() in ('left endpoint', 'left', 'l'):
                    print('   ',calc.left())
                    continue
                elif INP.lower() in ('right endpoint', 'right', 'r'):
                    print('   ',calc.right())
                    continue
                elif INP.lower() in ('trapezoid', 'trapezoidal', 'trap', 't'):
                    print('   ',calc.trapezoid())
                    continue
                elif INP.lower() in ('simpsons', 'simpson', 'quadratic',
                                     'simp', 'quad'):
                    print('   ',calc.simpson())
                    continue
                elif INP.lower() in ('series sum', 'series', 'ss'):
                    print('   ',calc.series_sum())
                    continue
                elif INP.lower() in ('volx', 'volume x', 'vol x', 'disc', 'discs'):
                    print('   ',calc.volume_x_axis())
                    continue
                elif INP.lower() in ('voly', 'volume y', 'vol y', 'shell', 'shells'):
                    print('   ',calc.volume_y_axis())
                    continue
                elif INP.lower() in ('sequence', 'seq'):
                    if a > b:
                        a, b, = b, a
                    XA = int(a)
                    XB = int(XA + n)
                    if XB > int(b):
                        XB = int(b)+1
                    while XB <= int(b)+1:
                        if int(XA + 2*n) >= int(b)+1:
                            print('    [%s to %s] == %s'%
                                  (XA,XB-1,calc.sequence(XA,XB)))
                        else:
                            input('    [%s to %s] == %s'%
                                  (XA,XB-1,calc.sequence(XA,XB)))
                        if XB >= int(b)+1:
                            break
                        XA += int(n)
                        XB = int(XA + n)
                        if XB > int(b):
                            XB = int(b)+1
                    continue
                elif INP.lower() == 'sum':
                    print('   ',calc.sum)
                    continue
                elif INP.lower() in ('help', '?'):
                    print(help_str)
                    continue
                elif INP.lower() in ('clear screen', 'clear', 'cls'):
                    os.system('cls')
                    continue
                elif INP.lower() in ('quit', 'exit'):
                    raise SystemExit
                elif INP.lower() == 'time':
                    print('   ',calc.time)
                    continue
                elif INP[0].lower() == 'y':
                    inp = INP.strip('yY= ')
                    if len(inp) == 0:
                        print('    y = %s'%y_str)
                        continue
                    
                    try:
                        exec('y = lambda x: '+inp)
                        y(0)
                        calc.y = y
                        y_str = inp
                    except ArithmeticError:
                        #if the only error is arithmetic, keep going
                        pass
                    except ValueError:
                        #if the only error is arithmetic, keep going
                        pass
                    except SyntaxError:
                        print('Invalid expression')
                    continue
                elif INP[0].lower() == 'n':
                    inp = INP.strip('nN ')
                    if len(inp) and inp[0] == '=':
                        calc.n = int(eval(inp.strip('= ')))
                        warned = False
                        continue
                    elif len(inp) == 0:
                        print('    n == %s'%n)
                        continue
                elif INP[0].lower() == 'a':
                    inp = INP.strip('aA ')
                    if len(inp) and inp[0] == '=':
                        calc.a = eval(inp.strip('= '))
                        warned = False
                        continue
                    elif len(inp) == 0:
                        print('    a == %s'%a)
                        continue
                elif INP[0].lower() == 'b':
                    inp = INP.strip('bB ')
                    if len(inp) and inp[0] == '=':
                        calc.b = eval(inp.strip('= '))
                        warned = False
                        continue
                    elif len(inp) == 0:
                        print('    b == %s'%b)
                        continue
                elif INP[0].lower() == 'p':
                    inp = INP.strip('pP ')
                    if len(inp) and inp[0] == '=':
                        calc.precision = int(eval(inp.strip('= ')))
                        continue
                    elif len(inp) == 0:
                        print('    p == %s'%p)
                        continue
                elif len(INP) >= 2 and INP[:2].lower() == 'dx':
                    inp = INP.strip('dDxX ')
                    if len(inp) and inp[0] == '=':
                        if eval(inp.strip('= ')) == 0:
                            print('    dx cannot be 0')
                            continue
                        calc.n = (b-a)/eval(inp.strip('= '))
                        warned = False
                        continue
                    elif len(inp) == 0:
                        print('    dx == %s'%((b-a)/n))
                        continue
                elif len(INP) >= 4 and INP[:4].lower() == 'vars':
                    print('    n == %s,  a == %s, b == %s'%(n, a, b))
                    print('    dx == %s, p == %s, abs == %s'%((b-a)/n, p, ABS))
                    continue

                #if nothing else fits the input then try to evaluate
                #the function at it(first check if its a number)
                try:
                    print('   y(%s) == %s' % (INP, calc.eval(eval(INP))))
                except:
                    print(format_exc())
                    
            except Exception:
                print(format_exc())
            except KeyboardInterrupt:
                print('Operation cancelled by user.')
                if calc.stop_point is not int(0):
                    print('Operation cancelled at x=%s' % calc.stop_point)
                    
                calc.stop_point = int(0)
                
            #make a space between inputs for ease of reading
            print()
