from jinja2 import Template
import msgtools.parser.MsgUtils as msgutils

def enums(usedEnums):
    return ""
def accessors(msg):
    return ""
def declarations(msg):
    return ""
def initCode(msg):
    return ""


def ProcessFile(msg, replacements, template, firstTime):
    tmpl = Template(template, trim_blocks=True, lstrip_blocks=True, line_statement_prefix='$')
    globals = {}
    for key in replacements:
        newKey = key.lower().strip('<>')
        globals[newKey] = replacements[key]
    return tmpl.render(globals=globals, msg=msg, msgutils=msgutils)
