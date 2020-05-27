def abPlus(a,b):
    if a == 0:
        return b
    elif b ==0:
        return a
    else:
        s = a^b
        t = (a&b)<<1
        return abPlus(s,t)

print(abPlus(3,4))
