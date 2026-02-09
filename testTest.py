import platform

print(platform.python_version())
# print(platform.python_version_tuple())
# print(platform.python_build())
# print(platform.python_compiler())
# print(platform.python_branch())
# print(platform.python_implementation())
# print(platform.python_revision())
# print(platform.python_is_pypy())
# print(platform.python_is_64bit())
# print(platform.python_build())
# print(platform.python_compiler())
# print(platform.python_branch())


print("MOT1", "MOT2")

# 2- affiche "MOT1*MOT2*MOT3"
print("MOT1", "MOT2", "MOT3", sep="*")

# 3- affiche "MOT1 MOT2 MOT3"
print("MOT1", "MOT2", "MOT3")

# 4- affiche "MOT1 MOT2+MOT3 MOT4" en une seule ligne.
print("MOT1", "MOT2", end="+")
print("MOT3", "MOT4")


# 5- affiche "MOT1 MOT2+MOT3 MOT4" en une seule ligne.
print("MOT1", "MOT2", sep=",", end="\n")
print("MOT3", "MOT4")

# 6- affiche "MOT1|MOT2+MOT3|MOT4"
print("MOT1", "MOT2", sep="|", end="+")
print("MOT3", "MOT4", sep="|")


phrase4 = "\tBonjour le monde.\net \t bienvenue."
print(phrase4)


s = "Hello"
s = "C" + s[1:]
print(s)


s1 = "HellO World"
s2 = s1.swapcase()
print(s2)



s = "TEST"
s.center(20, '-')
print(s.center(20, '-'))



