#!/bin/env python3

import functools
import xml.etree.ElementTree as ET


class Peripheral:
    def __init__(self, name):
        self.name = name
        self.description = "None"
        self.registers = dict()
        self.base_address = ""

    def add_register(self, register):
        self.registers[register.name] = register

    def _calc_xml_values(self):
        addr = functools.reduce(lambda x, reg: min(
            x, reg.address), self.registers.values(), 0xFFFFFFFF)
        self.base_address = addr

    def xml_append(self, peripherals_element):
        self._calc_xml_values()
        p = ET.SubElement(peripherals_element, 'peripheral')
        ET.SubElement(p, 'name').text = self.name
        ET.SubElement(p, 'baseAddress').text = hex(self.base_address)
        ET.SubElement(
            p, 'description').text = self.description if self.description else "None"

        ab = ET.SubElement(p, 'addressBlock')
        ET.SubElement(ab, 'offset').text = hex(0)
        ET.SubElement(ab, 'size').text = "0xffc"
        ET.SubElement(ab, 'usage').text = "register"

        interrupt = ET.SubElement(p, 'interrupt')
        ET.SubElement(interrupt, 'name').text = "???"
        ET.SubElement(interrupt, 'value').text = "99"

        regs = ET.SubElement(p, 'registers')
        for r_n, r in self.registers.items():
            r.xml_append(regs, self.base_address)

    def __str__(self):
        result = "Peripheral: {}\n\t{}".format(self.name, self.description)
        for n, r in self.registers.items():
            result += "\n\t\t{}".format(r.__str__())
        result += "\n"
        return result
