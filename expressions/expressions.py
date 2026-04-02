# flake8: noqa
class Expression: 

    def __init__(self, *operands):
        self.operands = operands
    
    def __add__(self, other):
        if isinstance(other, (int, float)):
            # can't say Number from python's inbuilt thing bc we're defining the subclass differently later
            from .expressions import Number
            other = Number(other) # can't do Number(tuple(other)) because then it doesn't unpack the values
            # and give tuple length 2 as desired
        from .expressions import Add
        return Add(self, other)
    
    def __radd__(self, other):
        if isinstance(other, (int, float)):
            from .expressions import Number
            other = Number(other)
        from .expressions import Add
        # can't just do self + other bc that reverses the order in string representation
        # and can't do other + self bc causes Recursion error
        # so just convert it to two expressions and then use the subclass operators
        return Add(other, self)
    
    def __sub__(self, other):
        if isinstance(other, (int, float)):
            from .expressions import Number
            other = Number(other)
        from .expressions import Sub
        return Sub(self, other)
    
    def __rsub__(self, other):
        if isinstance(other, (int, float)):
            from .expressions import Number
            return Number(other) - self
        elif isinstance(other, Expression):
            return other - self
    
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            from .expressions import Number
            other = Number(other)
        from .expressions import Mul
        return Mul(self, other)
    
    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            from .expressions import Number
            other = Number(other)
        from .expressions import Mul
        return Mul(other, self)
    
    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            if other == 0:
                raise ArithmeticError("Cannot divide by 0")
            from .expressions import Number
            other = Number(other)
        from .expressions import Div
        return Div(self, other)
    
    def __rtruediv__(self, other):
        if isinstance(other, (int, float)):
            return Number(other) / self
        elif isinstance(other, Expression):
            return other / self
    
    def __pow__(self, other):
        if isinstance(other, (int, float)):
            from .expressions import Number
            other = Number(other)
        from .expressions import Pow
        return Pow(self, other)
    
    def __rpow__(self, other):
        if isinstance(other, (int, float)):
            return Number(other) ** self
        elif isinstance(other, Expression):
            return other ** self

class Operator(Expression):
    
    # no need for an init because it inherits exactly the same stuff 
    # from the parent class and we aren't doing anything new with it
    def __repr__(self):
        return type(self).__name__ + repr(self.operands)
    
    def __str__(self):
        c1, c2 = self.operands
        s1, s2 = str(c1), str(c2)
        if c1.precedence < self.precedence:
            s1 = "(" + s1 + ")"
        if c2.precedence < self.precedence:
            s2 = "(" + s2 + ")"
        return s1 + " " + self.symbol + " " + s2

class Add(Operator):

    # same here - no init because it inherits exactly the same stuff 
    # from the parent class and we aren't doing anything new with it, all we need to
    # give it is class attributes, otherwise it's just a generic operator
    symbol = "+"
    precedence = 20

class Sub(Operator):

    symbol = "-"
    precedence = 10

class Mul(Operator):

    symbol = "*"
    precedence = 30

class Div(Operator):
    
    symbol = "/"
    precedence = 40


class Pow(Operator):
    
    symbol = "^"
    precedence = 50


class Terminal(Expression):

    precedence = 100
# highest precedence bc we don't want to put brackets around it
    def __init__(self, value):
        # bc the super init has splat operator next to operands, if we pass nothing in this then
        # it will take an empty tuple, which is exactly what we want
        # because a terminal has no children
        # in fact it's better they at least have an empty tuple rather than nothing at all, because
        # the postvisitor function in the test file will loop over the operands tuple regardless (0 times but that's fine)
        # so at least it gives it something to loop over and not cause an error
        # we don't have to define a specific case for it if it's a terminal instance
        super().__init__()
        self.value = value

    def __repr__(self):
        return repr(self.value)
    
    def __str__(self):
        return str(self.value)

class Number(Terminal):

    def __init__(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError
        super().__init__(value)

class Symbol(Terminal):

    def __init__(self, value):
        if not isinstance(value, str):
            raise TypeError
        super().__init__(value)

def postvisitor(expr, fn, **kwargs):
    stack = []
    visited = {}
    stack.append(expr)
    while stack:
        e = stack[-1]
        unvisited_children = []
        for o in e.operands:
            if o not in visited:
                unvisited_children.append(o)

        if unvisited_children:
            stack.extend(list(reversed(unvisited_children)))
        else:
            stack.pop()
            # Any children of e have been visited, so we can visit it.
            visited[e] = fn(e, *(visited[o] for o in e.operands), **kwargs)

    # When the stack is empty, we have visited every subexpression,
    # including expr itself.
    return visited[expr]

from functools import singledispatch
import expressions


@singledispatch
def differentiate(expr, var, *o, **kwargs):
    """Differentiate an expression node with respect to var.

    Parameters
    ----------
    expr: Expression
        The expression node to be differentiated.
    var:
        The variable which we are differentiating with respect to.
    *o: numbers.Number
        The results of differentiating the operands of expr.
    **kwargs:
        Any keyword arguments required to differentiate specific types of
        expression.
    symbol_map: dict
        A dictionary mapping Symbol names to numerical values, for
        example:

        {'x': 1}
    """
    raise NotImplementedError(
        f"Cannot differentiate a {type(expr).__name__}")


@differentiate.register(Number)
def _(expr, *o, **kwargs):
    return Number(0)


@differentiate.register(Symbol)
def _(expr, *o, **kwargs):
    var = kwargs['var']
    if expr.value == var:
        return Number(1)
    else:
        return Number(0)


@differentiate.register(Add)
def _(expr, *o, **kwargs):
    var = kwargs['var']
    return o[0] + o[1]


@differentiate.register(Sub)
def _(expr, *o, **kwargs):
    var = kwargs['var']
    return o[0] - o[1] # since o[0], o[1] are the children of the expression, they represent the already processed results of the differentiation.


@differentiate.register(Mul)
def _(expr, *o, **kwargs):
    var = kwargs['var']
    return expr.operands[0]*o[1] + expr.operands[1]*o[0]


@differentiate.register(Div)
def _(expr, *o, **kwargs):
    var = kwargs['var']
    return (expr.operands[1]*o[0] - expr.operands[0]*o[1]) / (expr.operands[1])**2


@differentiate.register(Pow)
def _(expr, *o, **kwargs):
    var = kwargs['var']
    return expr.operands[1] * o[0] * (expr.operands[0])**(expr.operands[1] - 1)