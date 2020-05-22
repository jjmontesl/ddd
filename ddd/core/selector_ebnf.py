
selector_ebnf = r"""

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

datafilterkeyexprname: string

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

