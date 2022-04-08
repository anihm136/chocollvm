def f1():
    x:int = 1

def f2()->int:
    return 1

def f4(x:int)->int:
    return x + 1

def f6()->int:
    return f4(5)

def f7()->int:
    x:int = 0
    y:int = 0
    x = f4(10)
    y = f6()
    return x - y

def f8(x:int)->int:
    return x

x:int = 0

f1()
printf("%d", f2() == 1)
printf("%d", f4(1) == 2)
printf("%d", f4(f2()) == 2)
printf("%d", f4(x) == 1)
printf("%d", f6() == 6)
printf("%d", f7() == 5)
printf("%d", f8(0) == 0)
printf("%d", f8(1) == 1)
printf("%d\n", f8(f7()) == 5)
