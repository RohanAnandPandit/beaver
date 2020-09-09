# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 08:58:06 2020

@author: rohan
"""
class Func:
    pass

class HFunction(Func):
    def __init__(self, precedence, associativity, func, 
                 noOfArgs, name, inputs = [], lazy = False):
        self.name = name
        self.precedence = precedence
        self.associativity = associativity 
        self.func = func
        self.noOfArgs = noOfArgs
        self.inputs = inputs
        self.lazy = lazy
    
    def execute(self, inputs):
        if (self.noOfArgs - len(inputs)) == 0:
            for arg in inputs:
                if not arg:
                    return False
            return True
        return False
    
    def apply(self, arg1 = None, arg2 = None, program_state = None):
        inputs = self.inputs.copy()
        if arg1:
            if len(inputs) > 1 and not inputs[-2]:
                    inputs[-2] = arg1
            else:
                inputs.append(arg1)
                
            if arg2:
                inputs.append(arg2)
                
        elif arg2:
            inputs.append(None)
            inputs.append(arg2)
            
        if self.execute(inputs):
            return self.call(inputs, program_state)
        
        return HFunction(self.precedence, self.associativity, self.func, 
                         self.noOfArgs, self.name, inputs = inputs, 
                         lazy = self.lazy) 
    
    def simplify(self, program_state):
        if self.execute(self.inputs):
            return self.func(program_state)
        return self
    
    def call(self, inputs, program_state):
        if self.noOfArgs == 1:
            return self.func(inputs[0], program_state)
        if self.noOfArgs == 2:
            return self.func(inputs[0], inputs[1], program_state)
        if self.noOfArgs == 3:
            return self.func(inputs[0], inputs[1], inputs[2], program_state)
        if self.noOfArgs == 4:
            return self.func(inputs[0], inputs[1], inputs[2], 
                             inputs[3], program_state)
        
    def __str__(self):
        return self.name
    
    def clone(self):
        return HFunction(self.precedence, 
                         self.associativity, self.func, self.noOfArgs,
                         self.name)
    
class Composition(Func):
    def __init__(self, second, first):        
        self.first = first
        self.second = second
        #self.precedence = first.precedence
        #self.associativity = first.associativity
        self.name = str(second) + '~' + str(first)
        self.lazy = self.first.lazy
    
    def simplify(self, program_state):
        return self
    
    def __str__(self):
        return self.name
    
    def apply(self, arg1 = None, program_state = None):
        if arg1 != None or self.first.name == '..':
            return self.second.apply(self.first.apply(arg1),
                                     program_state = program_state)
        return self

class Function(Func):
    def __init__(self, name, cases = [], inputs = []):
        self.name = name
        self.cases = cases
        self.inputs = inputs
        from Operators import Associativity
        self.associativity = Associativity.LEFT 
        self.precedence = 8
        self.lazy = False
    
    def clone(self):
        return Function(self.name,
                        cases = map(lambda case: case.clone(), self.cases),
                        inputs = self.inputs.copy())
        
    def simplify(self, program_state):
        value = self.checkCases(self.inputs, program_state)
        if value != None:
            return value
        return self
    
    def __str__(self):
        return self.name
    
    def apply(self, arg1 = None, arg2 = None, program_state = None):
        inputs = self.inputs.copy()
        if arg1:
            if len(inputs) > 1 and not inputs[-2]:
                inputs[-2] = arg1
            else:
                inputs.append(arg1)
            if arg2:
                inputs.append(arg2)

        elif arg2:
            inputs.append(None)
            inputs.append(arg2)

        value = self.checkCases(inputs, program_state)
        if value != None:
            return value
        return Function(self.name, cases = self.cases, inputs = inputs)
    
    def checkCases(self, inputs, program_state):
        for case in self.cases:
            arguments = case.arguments
            if len(arguments) == len(inputs):
                if self.matchCase(arguments, inputs, program_state):
                    for i in range(len(arguments)):
                        case = case.apply(inputs[i].simplify(program_state), 
                                          program_state = program_state) 
                    if not case:
                        continue
                    return case.simplify(program_state)
        #raise Exception('''Pattern match on arguments failed for all 
                        #definitions of function''', self.name) 
        return None

    def matchCase(self, arguments, inputs, program_state):
        from utils import patternMatch
        if len(inputs) != len(arguments):
            return False
        for i in range(len(arguments)):
            if not patternMatch(arguments[i], inputs[i], program_state):
                return False
        return True

class Lambda(Func):
    def __init__(self, name, expr, arguments = [], 
                 state = {}):
        self.name = name
        self.arguments = arguments
        self.expr = expr
        self.state = state
        self.noOfArgs = len(arguments)
        self.lazy = False
        
    def apply(self, arg1 = None, arg2 = None, program_state = None):
        from Operator_Functions import assign
        state = self.state.copy()
        arguments = self.arguments.copy()
        if arg1:
            assign(arguments[0], arg1, program_state, state)
            arguments = arguments[1:]
            if arg2: 
                assign(arguments[0], arg2, program_state, state)
                arguments = arguments[1:]

        elif arg2:
            assign(arguments[1], arg2, program_state, state)
            arguments = arguments[0] + arguments[2:]
            
        if arguments == []:
            return self.returnValue(state, program_state)
        
        return Lambda(self.name, self.expr, arguments = arguments, 
                      state = state)

    def __str__(self):
        string = '\\' + ' '.join(list(map(str, self.arguments)))
        if self.expr:
            string += ' -> ' + str(self.expr)
        return string
    
    def simplify(self, program_state):
        if self.arguments == []:
            return self.returnValue({}, program_state).simplify(program_state)
        return self

    def returnValue(self, state, program_state):
        program_state.frameStack.append(state)
        if self.expr:
            value = self.expr.simplify(program_state)
            #value = utils.replaceVariables(self.expr)
        else:
            value = None
        program_state.frameStack.pop(-1)
        if program_state.return_value != None:
            program_state.return_value = None
        return value
