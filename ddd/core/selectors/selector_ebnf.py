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
      | "True"            -> true
      | "false"           -> false
      | "False"           -> false
      | "null"            -> null
      | "None"            -> null

string: ESCAPED_STRING
tagkeystring: TAG_KEY_STRING

datafilter: datafilter_attr_equals
          | datafilter_attr_regexp
          | datafilter_attr_def
          | datafilter_attr_undef
          | datafilter_attr_ext_in

datafilter_attr_def: "[" datafilterkeyexprname "]"
datafilter_attr_undef: "[" "!" datafilterkeyexprname "]"
datafilter_attr_equals: "[" datafilterkeyexprname "=" datafiltervalueexpr "]"
datafilter_attr_regexp: "[" datafilterkeyexprname "~" datafiltervalueexpr "]"

datafilter_attr_ext_in: "[" datafilterkeyexprname "in" list "]"

datafilterkeyexprname: string | tagkeystring

datafilterkeyexpr: datafilterkeyexprname
datafiltervalueexpr: value

list : "[" [value ("," value)*] "]"
dict : "{" [pair ("," pair)*] "}"
pair : string ":" value

datafilterand: datafilter*
selector: datafilterand

%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER

%import common.WS
%ignore WS


"""

