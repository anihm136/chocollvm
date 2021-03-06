from .valuetype import ValueType


class ClassValueType(ValueType):
    def __init__(self, className: str):
        self.className = className

    def __eq__(self, other):
        if isinstance(other, ClassValueType):
            return self.className == other.className
        return False

    def isListType(self) -> bool:
        return self.className in {"<Empty>", "<None>"}

    def getJavaSignature(self, isList=False) -> str:
        if self.className == "bool":
            if isList:
                return "Ljava/lang/Boolean;"
            else:
                return "Z"
        elif self.className == "str":
            return "Ljava/lang/String;"
        elif self.className == "object":
            return "Ljava/lang/Object;"
        elif self.className == "int":
            if isList:
                return "Ljava/lang/Integer;"
            else:
                return "I"
        elif self.className == "<None>":
            return "Ljava/lang/Object;"
        elif self.className == "<Empty>":
            return "[Ljava/lang/Object;"
        else:
            return "L" + self.className + ";"

    def isNone(self):
        return self.className == "<None>"

    def isSpecialType(self):
        return self.className in ["int", "str", "bool"]

    def isJavaRef(self):
        return self.className not in ["int", "bool"]

    def getJavaName(self, isList=False):
        if self.className == "bool":
            if isList:
                return "java/lang/Boolean"
            else:
                return "boolean"
        elif self.className == "str":
            return "java/lang/String"
        elif self.className == "object":
            return "java/lang/Object"
        elif self.className == "<None>":
            return "java/lang/Object"
        elif self.className == "<Empty>":
            return "[Ljava/lang/Object;"
        elif self.className == "int":
            if isList:
                return "java/lang/Integer"
            else:
                return self.className
        else:
            return self.className

    def __str__(self):
        return self.className

    def __hash__(self):
        return str(self).__hash__()

    def toJSON(self, dump_location=True):
        return {"kind": "ClassValueType", "className": self.className}
