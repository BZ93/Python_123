def nthUglyNum(n):
    count = 1
    num = 1
    res = set([1,2,3,5])
    while count < n:
        num += 1
        if num in res: #任意一个ugly number - K, 2*K, 3*K, 和5*K都是ugly number,利用动态规划的思想
            res.add(num*2)
            res.add(num*3)
            res.add(num*5)
            count += 1
    return num

print(nthUglyNum(7))
