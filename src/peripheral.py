#!/bin/env python3

import functools
import xml.etree.ElementTree as ET
import string
import logging

logger = logging.getLogger(__name__)

class Peripheral:
    def __init__(self, name):
        self.name = name
        self.header_struct_name = name.rstrip(string.digits)
        self.description = "None"
        self.registers = dict()
        self.base_address = 0
        self.block_size = 0
        self.interrupts = []
        self.derived_from = None

    def add_register(self, register):
        self.registers[register.name] = register

    def add_interrupt(self, interrupt):
        logger.info("Attaching Interrupt {} to peripheral {}".format(interrupt.name, self.name))
        if not hasattr(self, 'interrupts'):
            self.interrupts = []
        self.interrupts.append(interrupt)

    def _calc_xml_values(self):
        min_addr = functools.reduce(lambda x, reg: min(
            x, reg.address), self.registers.values(), 0xFFFFFFFF)
        max_addr = functools.reduce(lambda x, reg: max(
            x, reg.max_address()), self.registers.values(), min_addr)
        self.base_address = min_addr
        self.block_size = max_addr - min_addr + 4

    def _xml_append_interrupts(self, p):
        if not hasattr(self, 'interrupts'):
            self.interrupts = []

        for i in self.interrupts:
            interrupt = ET.SubElement(p, 'interrupt')
            ET.SubElement(interrupt, 'name').text = i.name
            ET.SubElement(interrupt, 'value').text = str(i.index)

    def xml_append(self, peripherals_element):
        self._calc_xml_values()
        if self.derived_from:
            p = ET.SubElement(peripherals_element, 'peripheral', derivedFrom=self.derived_from)
            ET.SubElement(p, 'name').text = self.name
            ET.SubElement(p, 'baseAddress').text = hex(self.base_address)
            self._xml_append_interrupts(p)
            return
        
        p = ET.SubElement(peripherals_element, 'peripheral')
        ET.SubElement(p, 'name').text = self.name
        ET.SubElement(p, 'headerStructName').text = self.header_struct_name
        ET.SubElement(p, 'baseAddress').text = hex(self.base_address)
        ET.SubElement(
            p, 'description').text = self.description if self.description else "None"

        ab = ET.SubElement(p, 'addressBlock')
        ET.SubElement(ab, 'offset').text = hex(0)
        ET.SubElement(ab, 'size').text = hex(self.block_size)
        ET.SubElement(ab, 'usage').text = "registers"

        self._xml_append_interrupts(p)
        
        regs = ET.SubElement(p, 'registers')
        for r_n, r in self.registers.items():
            r.xml_append(regs, self.base_address)

    def __str__(self):
        result = "Peripheral: {}\n\t{}".format(self.name, self.description)
        for n, r in self.registers.items():
            result += "\n\t\t{}".format(r.__str__())
        result += "\n"
        return result
