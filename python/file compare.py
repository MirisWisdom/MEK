from struct import unpack
path1 = "test0.scenario"
path2 = "spv3c40_pre_merge.scenario"

with open(path1, "br") as f:
    file1 = f.read()
    
with open(path2, "br") as f:
    file2 = f.read()

found = False
difference = 0
check_against = b'\
abcdefghijklnmopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/\\'
for i in range(len(file1)):
    if file1[i] != file2[i]:
        if file1[i] in check_against or file2[i] in check_against:
            continue
        elif not found:
            float1 = unpack('>f', file1[i-3: i+1])[0]
            float2 = unpack('>f', file2[i-3: i+1])[0]
            if (abs(abs(float1) - abs(float2)) < 0.00001 and
                abs(float1) > 0.00001) and abs(float1) < 10000:
                # these are just about the same as floats
                print(i, float1, float2)
                continue
            print(i)
            found = True
            difference = 1
        else:
            difference += 1
    elif difference:
        print('    difference of %s bytes' % difference)
        difference = 0
        found = False

print('finished')
input()
