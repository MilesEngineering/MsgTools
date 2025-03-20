import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

import msgtools.parser.cpp.language as language

#language.namespace = "<MSGFULLNAME>_"
#language.firstParam = "m_data"
#language.firstParamDecl = "uint8_t* m_data"
#language.const = ""
#language.enumNamespace = 1
#language.functionPrefix = "INLINE "
#language.enumClass = ""

enums = language.enums
accessors = language.accessors
declarations = language.declarations
structPacking = language.structPacking
structUnpacking = language.structUnpacking
initCode = language.initCode
