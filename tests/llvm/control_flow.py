y:str = "123"
z:str = ""
char:str = ""
a:bool = True
b:int = 0
c:int = 100

b = 0
if b == 0:
    b = 1
printf("%d", b == 1)

b = 0
if b != 0:
    b = 2
printf("%d", b == 0)

b = 0
if b != 0:
    b = 0
else:
    b = 1
printf("%d", b == 1)

b = 0
if b == 0:
    b = 1
else:
    b = 0
printf("%d", b == 1)

b = 0
if b > 0:
    b = 0
elif b < 0:
    b = 0
else:
    b = 1
printf("%d", b == 1)

b = 0
if b == 0:
    pass
elif b < 0:
    b = 1
else:
    b = 1
printf("%d", b == 0)

b = 5
if b == 0:
    b = 1
elif b < 0:
    b = 2
else:
    pass
printf("%d", b == 5)

b = -1
if b > 0:
    b = 0
elif b < 0:
    b = 1
else:
    b = 0
printf("%d", b == 1)

b = -1
while b > 0:
    b = b - 1
printf("%d", b == -1)

b = 5
while b > 0:
    b = b - 1
printf("%d\n", b == 0)
