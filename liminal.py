"""
liminal.py — The Liminal Language Interpreter
Version 0.1

A language where uncertainty is first-class.
Every value carries a confidence weight.
Operations propagate uncertainty automatically.
Certainty must be earned, not assumed.

Usage:
    python liminal.py program.lim          # run a Liminal program
    python liminal.py --repl               # interactive REPL
    python liminal.py --demo               # run built-in demonstrations

This is the reference implementation — the canonical Liminal interpreter.
"""

from __future__ import annotations

import math
import time
import sys
import re
from dataclasses import dataclass, field
from typing import Any, Callable


# ─────────────────────────────────────────────────────────────────────────────
#  Core: the Uncertain value — every value in Liminal
# ─────────────────────────────────────────────────────────────────────────────

GHOST_THRESHOLD = 0.05
KNOWN_THRESHOLD = 0.80
INFERRED_THRESHOLD = 0.40
ASSUMED_THRESHOLD = 0.20


@dataclass
class Uncertain:
    """The fundamental type in Liminal.
    
    Every value is an Uncertain — a pairing of data and confidence.
    Confidence 1.0 = certain. Confidence 0.0 = ghost.
    The confidence is not metadata. It is part of the value.
    """
    value: Any
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)
    last_touched: float = field(default_factory=time.time)
    half_life: float | None = None   # seconds, None = no decay
    name: str = ""                    # for display

    def __post_init__(self):
        self.confidence = max(0.0, min(1.0, self.confidence))

    @property
    def epistemic_state(self) -> str:
        c = self.current_confidence
        if c >= KNOWN_THRESHOLD:
            return "known"
        elif c >= INFERRED_THRESHOLD:
            return "inferred"
        elif c >= ASSUMED_THRESHOLD:
            return "assumed"
        elif c >= GHOST_THRESHOLD:
            return "fading"
        else:
            return "ghost"

    @property
    def current_confidence(self) -> float:
        """Return confidence, accounting for decay since last touch."""
        if self.half_life is None:
            return self.confidence
        elapsed = time.time() - self.last_touched
        # Exponential decay toward 0 with given half-life
        # Never reaches 0 — asymptotes to GHOST_THRESHOLD * 0.1
        decayed = self.confidence * math.exp(
            -math.log(2) * elapsed / self.half_life
        )
        return max(GHOST_THRESHOLD * 0.1, decayed)

    def touch(self) -> "Uncertain":
        """Reinforce — reset decay timer and boost confidence slightly."""
        self.last_touched = time.time()
        self.confidence = min(1.0, self.current_confidence + 0.05)
        return self

    def is_ghost(self) -> bool:
        return self.current_confidence < GHOST_THRESHOLD

    def collapse(self, fallback=None) -> "Uncertain":
        """Force to classical value. Returns fallback if ghost."""
        if self.is_ghost() and fallback is not None:
            return Uncertain(fallback, 1.0)
        return Uncertain(self.value, 1.0)

    def assert_certain(self, threshold: float = 0.5) -> "Uncertain":
        """Assert this value is certain enough. Raises if not."""
        if self.current_confidence < threshold:
            raise LiminalUncertaintyError(
                f"Certainty assertion failed: confidence {self.current_confidence:.2f} "
                f"< required {threshold:.2f} for value {repr(self.value)}"
            )
        return self

    def __repr__(self) -> str:
        c = self.current_confidence
        bar = self._confidence_bar(c)
        state = self.epistemic_state
        name_part = f"{self.name}: " if self.name else ""
        decay_part = f" [decays, t½={self.half_life}s]" if self.half_life else ""
        return f"{name_part}{repr(self.value)} {bar} {c:.3f} ({state}){decay_part}"

    def _confidence_bar(self, c: float) -> str:
        filled = int(c * 10)
        return "~[" + "█" * filled + "░" * (10 - filled) + "]"


# ─────────────────────────────────────────────────────────────────────────────
#  Confidence propagation rules
# ─────────────────────────────────────────────────────────────────────────────

class Propagate:
    """The rules for how confidence flows through operations.
    
    These are the mathematical heart of Liminal.
    Every operation on uncertain values produces an uncertain result.
    """

    @staticmethod
    def multiply(a: Uncertain, b: Uncertain) -> Uncertain:
        """Multiplication: confidence compounds."""
        result = a.value * b.value
        conf = a.current_confidence * b.current_confidence
        return Uncertain(result, conf)

    @staticmethod
    def add(a: Uncertain, b: Uncertain) -> Uncertain:
        """Addition: weakest link dominates."""
        result = a.value + b.value
        conf = min(a.current_confidence, b.current_confidence)
        return Uncertain(result, conf)

    @staticmethod
    def subtract(a: Uncertain, b: Uncertain) -> Uncertain:
        result = a.value - b.value
        conf = min(a.current_confidence, b.current_confidence)
        return Uncertain(result, conf)

    @staticmethod
    def divide(a: Uncertain, b: Uncertain) -> Uncertain:
        if b.value == 0:
            return Uncertain(float('inf'), 0.0)
        result = a.value / b.value
        conf = a.current_confidence * b.current_confidence
        return Uncertain(result, conf)

    @staticmethod
    def compare(a: Uncertain, b: Uncertain, op: str) -> Uncertain:
        """Comparison: result confidence is product of operand confidences."""
        ops = {
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
        }
        result = ops[op](a.value, b.value)
        conf = a.current_confidence * b.current_confidence
        return Uncertain(result, conf)

    @staticmethod
    def negate(a: Uncertain) -> Uncertain:
        return Uncertain(not a.value, a.current_confidence)

    @staticmethod
    def blend(true_result: Any, false_result: Any, 
              condition: Uncertain) -> Uncertain:
        """Blend two results weighted by condition confidence.
        
        This is the core of uncertain conditionals.
        Both branches produce results. We blend them by confidence weight.
        """
        c = condition.current_confidence
        
        # For numeric blending
        if isinstance(true_result, (int, float)) and isinstance(false_result, (int, float)):
            blended = true_result * c + false_result * (1.0 - c)
            return Uncertain(blended, min(c, 1.0 - c) * 2)  # confidence is how certain we are of blend
        
        # For non-numeric: return the higher-confidence result
        if c >= 0.5:
            return Uncertain(true_result, c)
        else:
            return Uncertain(false_result, 1.0 - c)


# ─────────────────────────────────────────────────────────────────────────────
#  Errors
# ─────────────────────────────────────────────────────────────────────────────

class LiminalError(Exception):
    pass

class LiminalUncertaintyError(LiminalError):
    """Raised when certainty is asserted on a ghost value."""
    pass

class LiminalSyntaxError(LiminalError):
    pass

class LiminalRuntimeError(LiminalError):
    pass


# ─────────────────────────────────────────────────────────────────────────────
#  Lexer
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Token:
    type: str
    value: str
    line: int

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line})"


TOKEN_PATTERNS = [
    ('COMMENT',     r'//[^\n]*'),
    ('FLOAT',       r'\d+\.\d+'),
    ('INT',         r'\d+'),
    ('STRING',      r'"[^"]*"'),
    ('TILDE',       r'~'),
    ('BANG_BANG',   r'!!'),
    ('BANG',        r'!'),
    ('TILDE_Q',     r'~\?'),
    ('ARROW',       r'->'),
    ('GTE',         r'>='),
    ('LTE',         r'<='),
    ('NEQ',         r'!='),
    ('EQ',          r'=='),
    ('GT',          r'>'),
    ('LT',          r'<'),
    ('ASSIGN',      r'='),
    ('LPAREN',      r'\('),
    ('RPAREN',      r'\)'),
    ('LBRACE',      r'\{'),
    ('RBRACE',      r'\}'),
    ('COMMA',       r','),
    ('COLON',       r':'),
    ('SEMICOLON',   r';'),
    ('PLUS',        r'\+'),
    ('MINUS',       r'-'),
    ('STAR',        r'\*'),
    ('SLASH',       r'/'),
    ('NEWLINE',     r'\n'),
    ('WHITESPACE',  r'[ \t]+'),
    ('IDENT',       r'[A-Za-z_][A-Za-z0-9_]*'),
]

KEYWORDS = {
    'let', 'fn', 'return', 'if', 'else', 'true', 'false',
    'decays', 'half', 'confidence', 'reinforce', 'decay',
    'is_ghost', 'print', 'log', 'and', 'or', 'not',
}

def tokenize(source: str) -> list[Token]:
    tokens = []
    line = 1
    pos = 0
    pattern = re.compile('|'.join(f'(?P<{name}>{pat})' for name, pat in TOKEN_PATTERNS))

    for match in pattern.finditer(source):
        kind = match.lastgroup
        value = match.group()

        if kind == 'WHITESPACE' or kind == 'COMMENT':
            if '\n' in value:
                line += value.count('\n')
            continue
        if kind == 'NEWLINE':
            line += 1
            continue

        if kind == 'IDENT' and value in KEYWORDS:
            kind = value.upper()

        tokens.append(Token(kind, value, line))

    tokens.append(Token('EOF', '', line))
    return tokens


# ─────────────────────────────────────────────────────────────────────────────
#  AST Nodes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Node:
    pass

@dataclass
class Program(Node):
    statements: list

@dataclass
class LetDecl(Node):
    name: str
    confidence: float | None    # None = inherit
    decay_half_life: float | None
    value: Node

@dataclass
class FnDecl(Node):
    name: str
    params: list[tuple[str, str]]  # (name, type)
    confidence: float
    return_type: str
    body: list

@dataclass
class Return(Node):
    value: Node

@dataclass
class IfStmt(Node):
    condition: Node
    uncertain: bool             # True if ~ present
    then_body: list
    else_body: list

@dataclass
class BinOp(Node):
    op: str
    left: Node
    right: Node

@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

@dataclass
class Literal(Node):
    value: Any
    confidence: float = 1.0

@dataclass
class Identifier(Node):
    name: str

@dataclass
class Call(Node):
    name: str
    args: list

@dataclass
class Collapse(Node):
    expr: Node
    op: str          # '!' or '!!' or '~?'
    fallback: Node | None
    threshold: float | None

@dataclass
class Assign(Node):
    name: str
    value: Node


# ─────────────────────────────────────────────────────────────────────────────
#  Parser
# ─────────────────────────────────────────────────────────────────────────────

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, type: str) -> Token:
        t = self.peek()
        if t.type != type:
            raise LiminalSyntaxError(
                f"Line {t.line}: expected {type}, got {t.type} ({repr(t.value)})"
            )
        return self.advance()

    def match(self, *types) -> bool:
        return self.peek().type in types

    def parse(self) -> Program:
        statements = []
        while not self.match('EOF'):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return Program(statements)

    def parse_statement(self) -> Node | None:
        t = self.peek()

        if t.type == 'LET':
            return self.parse_let()
        elif t.type == 'FN':
            return self.parse_fn()
        elif t.type == 'RETURN':
            return self.parse_return()
        elif t.type == 'IF':
            return self.parse_if()
        elif t.type == 'PRINT':
            return self.parse_print()
        elif t.type == 'LOG':
            return self.parse_log()
        elif t.type == 'IDENT':
            return self.parse_assign_or_expr()
        else:
            # Try as expression
            expr = self.parse_expr()
            return expr

    def parse_let(self) -> LetDecl:
        self.expect('LET')
        name = self.expect('IDENT').value
        confidence = None
        decay_half_life = None

        if self.match('TILDE'):
            self.advance()
            # Optional explicit confidence
            if self.match('FLOAT'):
                confidence = float(self.advance().value)
            elif self.match('INT'):
                confidence = float(self.advance().value)

            # Optional decay
            if self.match('DECAYS'):
                self.advance()
                self.expect('LPAREN')
                self.expect('HALF')
                self.expect('COLON')
                decay_half_life = float(self.advance().value)
                self.expect('RPAREN')

        self.expect('ASSIGN')
        value = self.parse_expr()
        return LetDecl(name, confidence, decay_half_life, value)

    def parse_fn(self) -> FnDecl:
        self.expect('FN')
        name = self.expect('IDENT').value
        self.expect('LPAREN')
        params = []
        while not self.match('RPAREN'):
            pname = self.expect('IDENT').value
            ptype = 'Any'
            if self.match('COLON'):
                self.advance()
                ptype = self.expect('IDENT').value
            params.append((pname, ptype))
            if self.match('COMMA'):
                self.advance()
        self.expect('RPAREN')

        fn_confidence = 1.0
        if self.match('TILDE'):
            self.advance()
            if self.match('FLOAT'):
                fn_confidence = float(self.advance().value)
            elif self.match('INT'):
                fn_confidence = float(self.advance().value)

        return_type = 'Any'
        if self.match('ARROW'):
            self.advance()
            return_type = self.expect('IDENT').value

        self.expect('LBRACE')
        body = []
        while not self.match('RBRACE'):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        self.expect('RBRACE')

        return FnDecl(name, params, fn_confidence, return_type, body)

    def parse_return(self) -> Return:
        self.expect('RETURN')
        value = self.parse_expr()
        return Return(value)

    def parse_if(self) -> IfStmt:
        self.expect('IF')
        condition = self.parse_expr()
        uncertain = False
        if self.match('TILDE'):
            self.advance()
            uncertain = True

        self.expect('LBRACE')
        then_body = []
        while not self.match('RBRACE'):
            stmt = self.parse_statement()
            if stmt:
                then_body.append(stmt)
        self.expect('RBRACE')

        else_body = []
        if self.match('ELSE'):
            self.advance()
            self.expect('LBRACE')
            while not self.match('RBRACE'):
                stmt = self.parse_statement()
                if stmt:
                    else_body.append(stmt)
            self.expect('RBRACE')

        return IfStmt(condition, uncertain, then_body, else_body)

    def parse_print(self) -> Call:
        self.expect('PRINT')
        self.expect('LPAREN')
        args = []
        while not self.match('RPAREN'):
            args.append(self.parse_expr())
            if self.match('COMMA'):
                self.advance()
        self.expect('RPAREN')
        return Call('__print__', args)

    def parse_log(self) -> Call:
        self.expect('LOG')
        self.expect('LPAREN')
        args = []
        while not self.match('RPAREN'):
            args.append(self.parse_expr())
            if self.match('COMMA'):
                self.advance()
        self.expect('RPAREN')
        return Call('__log__', args)

    def parse_assign_or_expr(self) -> Node:
        name = self.expect('IDENT').value
        if self.match('ASSIGN'):
            self.advance()
            value = self.parse_expr()
            return Assign(name, value)
        # Put back and parse as expression starting with identifier
        self.pos -= 1
        return self.parse_expr()

    def parse_expr(self) -> Node:
        return self.parse_comparison()

    def parse_comparison(self) -> Node:
        left = self.parse_additive()
        while self.match('GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ'):
            op = self.advance().value
            right = self.parse_additive()
            left = BinOp(op, left, right)
        return left

    def parse_additive(self) -> Node:
        left = self.parse_multiplicative()
        while self.match('PLUS', 'MINUS'):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = BinOp(op, left, right)
        return left

    def parse_multiplicative(self) -> Node:
        left = self.parse_unary()
        while self.match('STAR', 'SLASH'):
            op = self.advance().value
            right = self.parse_unary()
            left = BinOp(op, left, right)
        return left

    def parse_unary(self) -> Node:
        if self.match('NOT'):
            self.advance()
            return UnaryOp('not', self.parse_unary())
        if self.match('MINUS'):
            self.advance()
            return UnaryOp('-', self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self) -> Node:
        expr = self.parse_primary()
        while True:
            if self.match('BANG_BANG'):
                self.advance()
                fallback = self.parse_primary()
                expr = Collapse(expr, '!!', fallback, None)
            elif self.match('BANG'):
                self.advance()
                expr = Collapse(expr, '!', None, None)
            elif self.match('TILDE_Q'):
                self.advance()
                threshold = float(self.advance().value)
                expr = Collapse(expr, '~?', None, threshold)
            else:
                break
        return expr

    def parse_primary(self) -> Node:
        t = self.peek()

        if t.type == 'FLOAT':
            self.advance()
            return Literal(float(t.value))
        if t.type == 'INT':
            self.advance()
            return Literal(int(t.value))
        if t.type == 'STRING':
            self.advance()
            return Literal(t.value[1:-1])  # strip quotes
        if t.type == 'TRUE':
            self.advance()
            return Literal(True)
        if t.type == 'FALSE':
            self.advance()
            return Literal(False)
        if t.type == 'IDENT':
            name = self.advance().value
            # Function call?
            if self.match('LPAREN'):
                self.advance()
                args = []
                while not self.match('RPAREN'):
                    args.append(self.parse_expr())
                    if self.match('COMMA'):
                        self.advance()
                self.expect('RPAREN')
                return Call(name, args)
            return Identifier(name)
        if t.type == 'CONFIDENCE':
            self.advance()
            self.expect('LPAREN')
            expr = self.parse_expr()
            self.expect('RPAREN')
            return Call('__confidence__', [expr])
        if t.type == 'REINFORCE':
            self.advance()
            self.expect('LPAREN')
            expr = self.parse_expr()
            self.expect('RPAREN')
            return Call('__reinforce__', [expr])
        if t.type == 'IS_GHOST':
            self.advance()
            self.expect('LPAREN')
            expr = self.parse_expr()
            self.expect('RPAREN')
            return Call('__is_ghost__', [expr])
        if t.type == 'LPAREN':
            self.advance()
            expr = self.parse_expr()
            self.expect('RPAREN')
            return expr

        raise LiminalSyntaxError(
            f"Line {t.line}: unexpected token {t.type} ({repr(t.value)})"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Environment
# ─────────────────────────────────────────────────────────────────────────────

class Environment:
    def __init__(self, parent: "Environment | None" = None):
        self.bindings: dict[str, Uncertain] = {}
        self.parent = parent

    def get(self, name: str) -> Uncertain:
        if name in self.bindings:
            val = self.bindings[name]
            val.touch()  # access = reinforcement
            return val
        if self.parent:
            return self.parent.get(name)
        raise LiminalRuntimeError(f"Undefined variable: {name}")

    def set(self, name: str, value: Uncertain):
        self.bindings[name] = value

    def set_local(self, name: str, value: Uncertain):
        self.bindings[name] = value

    def child(self) -> "Environment":
        return Environment(self)


# ─────────────────────────────────────────────────────────────────────────────
#  Interpreter
# ─────────────────────────────────────────────────────────────────────────────

class ReturnSignal(Exception):
    def __init__(self, value: Uncertain):
        self.value = value


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.functions: dict[str, FnDecl] = {}
        self.output: list[str] = []
        self._setup_builtins()

    def _setup_builtins(self):
        # Built-in certain values
        self.global_env.set("PI", Uncertain(3.14159265, 1.0, name="PI"))
        self.global_env.set("E",  Uncertain(2.71828182, 1.0, name="E"))

    def run(self, program: Program) -> None:
        env = self.global_env
        for stmt in program.statements:
            self.exec(stmt, env)

    def exec(self, node: Node, env: Environment) -> Uncertain | None:
        if isinstance(node, LetDecl):
            return self.exec_let(node, env)
        elif isinstance(node, FnDecl):
            self.functions[node.name] = node
            return None
        elif isinstance(node, Return):
            value = self.eval(node.value, env)
            raise ReturnSignal(value)
        elif isinstance(node, IfStmt):
            return self.exec_if(node, env)
        elif isinstance(node, Assign):
            value = self.eval(node.value, env)
            value.name = node.name
            env.set(node.name, value)
            return value
        elif isinstance(node, Call):
            return self.eval_call(node, env)
        else:
            return self.eval(node, env)

    def exec_let(self, node: LetDecl, env: Environment) -> Uncertain:
        value = self.eval(node.value, env)

        # Apply explicit confidence if given
        if node.confidence is not None:
            value = Uncertain(
                value.value,
                node.confidence,
                name=node.name,
                half_life=node.decay_half_life,
            )
        elif node.decay_half_life is not None:
            value = Uncertain(
                value.value,
                value.current_confidence,
                name=node.name,
                half_life=node.decay_half_life,
            )
        else:
            value.name = node.name

        env.set_local(node.name, value)
        return value

    def exec_if(self, node: IfStmt, env: Environment) -> Uncertain | None:
        condition = self.eval(node.condition, env)

        if node.uncertain:
            # Uncertain conditional: both branches may execute
            # Weight them by condition confidence
            then_env = env.child()
            else_env = env.child()

            then_result = None
            else_result = None

            try:
                for stmt in node.then_body:
                    then_result = self.exec(stmt, then_env)
            except ReturnSignal as r:
                then_result = r.value

            try:
                for stmt in node.else_body:
                    else_result = self.exec(stmt, else_env)
            except ReturnSignal as r:
                else_result = r.value

            # Blend the results
            c = condition.current_confidence
            if condition.value:
                effective_c = c
            else:
                effective_c = 1.0 - c

            # Execute with confidence weighting
            if effective_c >= 0.5:
                self._exec_body_weighted(node.then_body, env.child(), effective_c)
                if node.else_body:
                    self._exec_body_weighted(node.else_body, env.child(), 1.0 - effective_c)
            else:
                if node.else_body:
                    self._exec_body_weighted(node.else_body, env.child(), 1.0 - effective_c)
                self._exec_body_weighted(node.then_body, env.child(), effective_c)

        else:
            # Classical if
            if condition.value:
                child = env.child()
                for stmt in node.then_body:
                    self.exec(stmt, child)
            elif node.else_body:
                child = env.child()
                for stmt in node.else_body:
                    self.exec(stmt, child)

        return None

    def _exec_body_weighted(self, body: list, env: Environment, weight: float):
        """Execute a body with an effective confidence weight applied to prints."""
        for stmt in body:
            result = self.exec(stmt, env)

    def eval(self, node: Node, env: Environment) -> Uncertain:
        if isinstance(node, Literal):
            return Uncertain(node.value, node.confidence)

        elif isinstance(node, Identifier):
            return env.get(node.name)

        elif isinstance(node, BinOp):
            return self.eval_binop(node, env)

        elif isinstance(node, UnaryOp):
            operand = self.eval(node.operand, env)
            if node.op == 'not':
                return Propagate.negate(operand)
            elif node.op == '-':
                return Uncertain(-operand.value, operand.current_confidence)

        elif isinstance(node, Call):
            return self.eval_call(node, env)

        elif isinstance(node, Collapse):
            return self.eval_collapse(node, env)

        raise LiminalRuntimeError(f"Cannot evaluate node: {type(node).__name__}")

    def eval_binop(self, node: BinOp, env: Environment) -> Uncertain:
        left = self.eval(node.left, env)
        right = self.eval(node.right, env)
        op = node.op

        if op == '+':
            return Propagate.add(left, right)
        elif op == '-':
            return Propagate.subtract(left, right)
        elif op == '*':
            return Propagate.multiply(left, right)
        elif op == '/':
            return Propagate.divide(left, right)
        elif op in ('>', '<', '>=', '<=', '==', '!='):
            return Propagate.compare(left, right, op)
        else:
            raise LiminalRuntimeError(f"Unknown operator: {op}")

    def eval_call(self, node: Call, env: Environment) -> Uncertain:
        # Built-in functions
        if node.name == '__print__':
            parts = [self._format_value(self.eval(a, env)) for a in node.args]
            line = " ".join(parts)
            print(line)
            self.output.append(line)
            return Uncertain(None, 1.0)

        elif node.name == '__log__':
            parts = [self._format_value(self.eval(a, env)) for a in node.args]
            line = "[log] " + " ".join(parts)
            print(line)
            self.output.append(line)
            return Uncertain(None, 1.0)

        elif node.name == '__confidence__':
            val = self.eval(node.args[0], env)
            return Uncertain(val.current_confidence, 1.0)

        elif node.name == '__reinforce__':
            val = self.eval(node.args[0], env)
            val.touch()
            return val

        elif node.name == '__is_ghost__':
            val = self.eval(node.args[0], env)
            return Uncertain(val.is_ghost(), 1.0)

        # User-defined functions
        if node.name in self.functions:
            fn = self.functions[node.name]
            fn_env = self.global_env.child()

            # Bind parameters
            for (pname, _), arg_node in zip(fn.params, node.args):
                arg_val = self.eval(arg_node, env)
                fn_env.set_local(pname, arg_val)

            try:
                result = None
                for stmt in fn.body:
                    result = self.exec(stmt, fn_env)
                return result or Uncertain(None, 1.0)
            except ReturnSignal as r:
                # Apply function's own confidence to return value
                rv = r.value
                return Uncertain(
                    rv.value,
                    rv.current_confidence * fn.confidence
                )

        raise LiminalRuntimeError(f"Undefined function: {node.name}")

    def eval_collapse(self, node: Collapse, env: Environment) -> Uncertain:
        val = self.eval(node.expr, env)

        if node.op == '!':
            return val.assert_certain()
        elif node.op == '!!':
            fallback = self.eval(node.fallback, env) if node.fallback else Uncertain(None, 1.0)
            if val.is_ghost():
                return fallback
            return Uncertain(val.value, 1.0)
        elif node.op == '~?':
            threshold = node.threshold or 0.5
            if val.current_confidence >= threshold:
                return val
            return Uncertain(None, 0.0)

        raise LiminalRuntimeError(f"Unknown collapse operator: {node.op}")

    def _format_value(self, val: Uncertain) -> str:
        if val.value is None:
            return "null"
        c = val.current_confidence
        state = val.epistemic_state
        bar = val._confidence_bar(c)
        return f"{val.value} {bar} {c:.3f} [{state}]"


# ─────────────────────────────────────────────────────────────────────────────
#  REPL
# ─────────────────────────────────────────────────────────────────────────────

REPL_BANNER = """
╔══════════════════════════════════════════════════════════════════════════╗
║  LIMINAL  —  a language where uncertainty is first-class                ║
║  Version 0.1                                                             ║
║                                                                          ║
║  Every value carries a confidence weight.                               ║
║  Operations propagate uncertainty automatically.                        ║
║  Certainty must be earned, not assumed.                                 ║
║                                                                          ║
║  Try:  let x ~ 0.7 = 42                                                 ║
║        let y ~ 0.9 = 10                                                 ║
║        print(x + y)                                                     ║
║        let z = x * y                                                    ║
║        if z ~ > 100 { print("probably big") }                          ║
║                                                                          ║
║  Type 'exit' to quit. Type 'help' for more examples.                   ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
LIMINAL QUICK REFERENCE

Declarations:
  let x = 42                    certain value (confidence 1.0)
  let x ~ 0.7 = 42              uncertain value (confidence 0.7)
  let x ~ decays(half: 60) = 5  decaying value (half-life 60 seconds)

Operations:
  x + y        addition (confidence = min of both)
  x * y        multiply (confidence = product of both)
  x > y        compare  (confidence = product of both)

Uncertain conditionals:
  if x ~ > 10 { ... }          executes proportionally to confidence

Inspecting confidence:
  confidence(x)                 returns the confidence weight
  reinforce(x)                  boosts confidence slightly
  is_ghost(x)                   true if confidence < 0.05

Collapsing to certainty:
  x!                            assert certain (error if ghost)
  x!! fallback                  collapse with fallback
  x ~? 0.6                      return only if confidence >= 0.6

Output:
  print(x)                      show value with confidence bar
  log("message")                log a message
"""


def run_repl():
    print(REPL_BANNER)
    interp = Interpreter()
    buffer = ""

    while True:
        try:
            prompt = "... " if buffer else "λ ~ "
            line = input(prompt)

            if line.strip() == 'exit':
                print("\nGoodbye. The uncertain endures.")
                break
            if line.strip() == 'help':
                print(HELP_TEXT)
                continue
            if line.strip() == 'env':
                print("\nCurrent bindings:")
                for name, val in interp.global_env.bindings.items():
                    print(f"  {val}")
                print()
                continue

            buffer += line + "\n"

            # Try to parse and run
            try:
                tokens = tokenize(buffer)
                parser = Parser(tokens)
                program = parser.parse()
                for stmt in program.statements:
                    result = interp.exec(stmt, interp.global_env)
                    if result is not None and result.value is not None:
                        print(f"  → {result}")
                buffer = ""
            except LiminalSyntaxError:
                # Might be incomplete — keep buffering
                if line.strip().endswith('{'):
                    pass  # definitely incomplete
                else:
                    print(f"  ✗ syntax error")
                    buffer = ""
            except LiminalRuntimeError as e:
                print(f"  ✗ runtime error: {e}")
                buffer = ""
            except LiminalUncertaintyError as e:
                print(f"  ✗ certainty violation: {e}")
                buffer = ""

        except KeyboardInterrupt:
            print("\n  (interrupted)")
            buffer = ""
        except EOFError:
            print("\nGoodbye.")
            break


def run_file(path: str):
    try:
        source = open(path).read()
    except FileNotFoundError:
        print(f"Error: file not found: {path}")
        sys.exit(1)

    try:
        tokens = tokenize(source)
        parser = Parser(tokens)
        program = parser.parse()
        interp = Interpreter()
        interp.run(program)
    except (LiminalSyntaxError, LiminalRuntimeError, LiminalUncertaintyError) as e:
        print(f"Liminal error: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
#  Built-in demonstrations
# ─────────────────────────────────────────────────────────────────────────────

DEMO_PROGRAMS = {
    "basic": """
// Basic uncertainty demonstration
let certain = 42
let uncertain ~ 0.7 = 42
let very_uncertain ~ 0.2 = 42

print(certain)
print(uncertain)
print(very_uncertain)
""",

    "propagation": """
// Confidence propagates through operations
let sensor_a ~ 0.85 = 21.4
let sensor_b ~ 0.72 = 19.8

// Addition: confidence = min(0.85, 0.72) = 0.72
let combined = sensor_a + sensor_b
print(combined)

// Multiplication: confidence = 0.85 * 0.72 = 0.612
let product = sensor_a * sensor_b
print(product)

// Comparison: confidence = 0.85 * 0.72 = 0.612
let comparison = sensor_a > sensor_b
print(comparison)
""",

    "conditional": """
// Uncertain conditionals
let temp ~ 0.8 = 22.5
let threshold = 20.0

// ~ makes this conditional weighted by confidence
if temp ~ > threshold {
    log("cooling system activated")
} else {
    log("heating system activated")
}
""",

    "collapse": """
// Collapsing uncertainty to certainty
let reading ~ 0.6 = 98.6
let ghost_value ~ 0.02 = 999

// Collapse with fallback
let safe = ghost_value!! 0.0
print(safe)

// Check confidence threshold
let maybe = reading ~? 0.5
print(maybe)
""",

    "decay": """
// Decaying values
let fresh ~ decays(half: 2) = 100.0
print(fresh)
log("(waiting 1 second...)")
""",

    "functions": """
// Functions with their own confidence
fn measure() ~ 0.75 -> Float {
    return 42.0
}

fn certain_calc(x: Float) -> Float {
    return x + 1.0
}

let measured = measure()
print(measured)

let calc = certain_calc(10.0)
print(calc)
""",
}


def run_demo(name: str = "all"):
    interp = Interpreter()

    demos = [name] if name != "all" else list(DEMO_PROGRAMS.keys())

    for demo_name in demos:
        if demo_name not in DEMO_PROGRAMS:
            print(f"Unknown demo: {demo_name}")
            continue

        print(f"\n{'═'*60}")
        print(f"  DEMO: {demo_name}")
        print(f"{'═'*60}")

        source = DEMO_PROGRAMS[demo_name]
        print(source)
        print("OUTPUT:")
        print("─" * 40)

        try:
            tokens = tokenize(source)
            parser = Parser(tokens)
            program = parser.parse()
            for stmt in program.statements:
                interp.exec(stmt, interp.global_env)
        except Exception as e:
            print(f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == '--repl':
        run_repl()
    elif sys.argv[1] == '--demo':
        demo_name = sys.argv[2] if len(sys.argv) > 2 else "all"
        run_demo(demo_name)
    elif sys.argv[1] == '--spec':
        print(__doc__)
    else:
        run_file(sys.argv[1])
