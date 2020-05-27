def knChecker(k,n):
    cm = 0
    for i in range(0,n+1):
        cm += str(i).count(str(k))
    return cm

print(knChecker(2,2145))
