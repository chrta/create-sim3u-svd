#!/bin/env python3

class Peripheral:
    def __init__(self, name):
        self.name = name
        self.description = ""
        self.registers = dict()

    def add_register(self, register):
        self.registers[register.name] = register

    def __str__(self):
        result = "Peripheral: {}\n\t{}".format(self.name, self.description)
        for n, r in self.registers.items():
            result += "\n\t\t{}".format(r.__str__())
        result += "\n"
        return result
