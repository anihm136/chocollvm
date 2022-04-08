x:int = 1
y:int = 2
a:bool = True
b:bool = False
c:str = ""
d:str = ""

b = a

printf("%d", x != y)
x = y
printf("%d", x == y)
x = 2
y = 2
printf("%d", x == y)
x = y = 0
printf("%d", x == 0)
printf("%d", y == 0)

printf("%d", a == b)
b = False
printf("%d", a != b)

printf("%s", c)
printf("%s", d)
d = c = "123"
printf("%s", c)
printf("%s", d)
d = "456"
printf("%s", c)
printf("%s", d)
d = "123"
printf("%s", c)
printf("%s\n", d)
