'''
This is a simple test to see how well high quality normal vectors
can be stored using just 2 bytes, one for theta and the other for phi.

The concept could be extended to include 4 1kb tables of floats for
fast lookup of the floats to multiply together to get the x, y, z coordinates

Instead of x = cos(2*pi*(t/255))*sin(pi*(p/255))
it would be x = table1[t]*table2[p]
'''
from math import cos, sin, pi
from traceback import format_exc
try:
    verts = [None]*(65536-255*2)

    obj_file = open('mod.obj', 'w')
    obj_file.write('#  normals test\n\n'+
                   'g \n')
    verts[0] = (0,0,1)
    obj_file.write('v 0 0 1\n')
                 
    for p in range(1, 255):  
        for t in range(256):
            #for some reason the y coordinate screws up if at t == 255
            if t == 255:
                verts[t+(p-1)*256] = vert = (cos(2*pi*(t/255))*sin(pi*(p/255)),
                                             0, cos(pi*(p/255)))
                obj_file.write('v %s 0 %s\n'%(str(vert[0])[:8], str(vert[2])[:8]))
            else:
                verts[t+(p-1)*256] = vert = (cos(2*pi*(t/255))*sin(pi*(p/255)),
                                             sin(2*pi*(t/255))*sin(pi*(p/255)),
                                             cos(pi*(p/255)))
                obj_file.write('v %s %s %s\n'%(str(vert[0])[:8],
                                               str(vert[1])[:8],
                                               str(vert[2])[:8]))
    verts[-1] = (0,0,-1)
    obj_file.write('v 0 0 -1\n')

    for i in range(len(verts)-2):
        i += 1
        if i&1:
            obj_file.write('f %s %s %s \n'% (i+1,i,i+2))
        else:
            obj_file.write('f %s %s %s \n'% (i,i+1,i+2))

    obj_file.close()
except:
    print(format_exc())
