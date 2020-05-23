# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

"""
This file contains the DDDSelector grammar definition in EBNF format.
"""

selector_ebnf = r"""

TAG_KEY_STRING : /[a-zA-Z][a-zA-Z:_]*/
SINGLE_QUOTED_STRING  : /'[^']*'/

?value: dict
      | list
      | string
      | SIGNED_NUMBER     -> number
      | "true"            -> true
      | "false"           -> false
      | "null"            -> null

string: ESCAPED_STRING


datafilter: "[" datafilterkeyexpr [ datafilterop datafiltervalueexpr ] "]"

datafilterkeyexprprefix: "!" | "~"

datafilterkeyexprname: string | TAG_KEY_STRING

datafilterkeyexpr: datafilterkeyexprprefix? datafilterkeyexprname
datafiltervalueexpr: value

datafilterop: "="   -> equals
            | "!="  -> notequals
            | "~"   -> matches
            | "!~"  -> notmatches

list : "[" [value ("," value)*] "]"
dict : "{" [pair ("," pair)*] "}"
pair : string ":" value

selector: datafilter*

%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER

%import common.WS
%ignore WS


"""

