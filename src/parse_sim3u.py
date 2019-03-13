#!/usr/bin/env python3
"""Generate the SiM3U SVD file from the reference manual

"""

import camelot
import pandas
import pickle
import re
import os
import sys
import argparse
import logging
from register import Register, RegisterBits, RegisterBitTableEntry, RegisterBitTableEntryCollection
from peripheral import Peripheral
from rm_table import RmTable
from pdf_doc import Document, Manual
from svd import SvdGenerator

logger = logging.getLogger(__name__)


def parse_peripheral_overview(pdf_filename, page_list):
    pages = "{}-{}".format(page_list[0], page_list[1])
    reg_overview_tables = camelot.read_pdf(pdf_filename, pages=pages)

    # flatten dfs
    dfs = [x.df for x in reg_overview_tables]
    table = pandas.concat(dfs)

    peripherals = dict()
    current_peripheral = None
    # get all peripheral names
    for row in table.iterrows():
        content = row[1]
        if 'Register Name' in content[0]:
            continue
        if ' Registers' in content[0]:
            name = content[0].replace(' Registers', '')
            logger.debug("New Peripheral {}".format(name))
            current_peripheral = Peripheral(name)
            peripherals[name] = current_peripheral
            continue
        if current_peripheral is None:
            continue

        logger.debug("New Register {}".format(content[0]))
        logger.debug(content)
        has_set = False
        has_clr = False
        has_msk = False
        if '\n' in content[0]:
            # parsing error of the table
            name = content[0].splitlines()[0]
            title = content[0].splitlines()[1]
            addr = content[0].splitlines()[2]
            if len(content[0].splitlines()) > 3:
                has_set = 'Y' in content[0].splitlines()[3]
            if len(content[0].splitlines()) > 4:
                has_clr = 'Y' in content[0].splitlines()[4]
            if len(content[0].splitlines()) > 5:
                has_msk = 'Y' in content[0].splitlines()[5]
        else:
            # normal case
            name = content[0]
            title = content[1]
            addr = content[2]
            has_set = 'Y' in content[3]
            has_clr = 'Y' in content[4]
            has_msk = 'Y' in content[5]

        # remove peripheral name from register name
        name = name.replace(current_peripheral.name + '_', '')
        reg = Register(name, title, int(addr, 0), has_set, has_clr, has_msk)
        current_peripheral.add_register(reg)
        #peripherals[current_peripheral.name] = current_peripheral
    return peripherals

class Interrupt():
    def __init__(self, content):
        self.index = int(content[0])
        self.name = content[2].replace(' ', '_')
        self.description = content[3]
        self.address = int(content[4], 0)
    
def parse_interrupts(pdf_filename, page_list):
    pages = "{}-{}".format(page_list[0], page_list[1])
    interrupts_tables = camelot.read_pdf(pdf_filename, pages=pages)

    # flatten dfs
    dfs = [x.df for x in interrupts_tables]
    table = pandas.concat(dfs)

    interrupts = []
    for row in table.iterrows():
        content = row[1]
        if not content[0]:
            #skipping entries without the position filled -> internal exceptions
            continue
        try:
            int_index = int(content[0])
        except:
            #skipping non-numerical entries, this might be a table header
            continue

        logger.debug("New Interrupt {}".format(content[2]))
        interrupts.append(Interrupt(content))
        
    return interrupts

map_int_to_periph = {'PBEXT0': 'PBCFG0',
                     'PBEXT1': 'PBCFG0',
                     'PMATCH0': 'PBCFG0',
                     'VDDLOW': 'VMON0',
                     'VREGLOW': 'VMON0',
                     'VBUS_Invalid': 'VMON0'
}

map_int_prefix_to_periph = {'DMA': 'DMACTRL0',
                            'TIMER0' : 'TIMER0',
                            'TIMER1' : 'TIMER1',
                            'I2S0' : 'I2S0',
                            'RTC0': 'RTC0',
}
def attach_interrupts_to_peripherals(peripherals, interrupts):
    for i in interrupts:
        logger.debug("Processing Interrupt {}".format(i.name))
        if i.name in peripherals:
            peripherals[i.name].add_interrupt(i)
            continue

        found = False
        for prefix, periph in map_int_prefix_to_periph.items():
            if i.name.startswith(prefix):
                peripherals[periph].add_interrupt(i)
                found = True
                break
        if found:
            continue
                
        try:
            peripheral_name = map_int_to_periph[i.name]
            peripherals[peripheral_name].add_interrupt(i)
            continue
        except:
            logger.error("No periph found for Interrupt {}".format(i.name))
            raise

map_derived_periph = {'PBSTD0': 'PBSTD2',
                      'PBSTD1': 'PBSTD2',
                      'PBSTD3': 'PBSTD2',
                      'UART1': 'UART0',
                      'USART1': 'USART0',
                      'TIMER1': 'TIMER0',
                      'SARADC1': 'SARADC0',
                      'SPI1': 'SPI0',
                      'SPI2': 'SPI0',
                      'I2C1': 'I2C0',
                      'PCA1': 'PCA0',
                      'CMP1': 'CMP0',
                      'IDAC1': 'IDAC0',

}
def populate_derived_from_info(peripherals):
    for p_n, p in peripherals.items():
        if p.name in map_derived_periph:
            p.derived_from = map_derived_periph[p.name]


def determine_register(peripheral, df):
    # tables[0] is the overview with reset values RW/R etc
    logger.debug("Peripheral is {}".format(peripheral.name))
    for row in df.iterrows():
        logger.debug("New row")
        content = row[1]
        for c in content:
            if peripheral.name + '_' in c:
                logger.debug("Found register name!!!")
                p = re.compile('([a-zA-Z0-9]+)_(\w+)\s*=\s*0x.*')
                for line in c.splitlines():
                    if line.startswith(peripheral.name + '_'):
                        m = p.match(line)
                        register_name = m.group(2)
                        return peripheral.registers[register_name]
    return None


def parse_reg_bit_description(register, df):
    logger.debug("Register is {}".format(register.name))
    logger.debug(df)
    if df[0][0] != 'Bit':
        raise Exception("Expected Bit")
    if df[1][0] != 'Name':
        raise Exception("Expected Name")
    if df[2][0] != 'Function':
        raise Exception("Expected Function")

    p_bits = re.compile('(\d+)(:(\d+))?')
    data = df.iloc[1:, :3]

    for index, content in data.iterrows():
        m = p_bits.match(content[0])
        if m:
            start_bit_index = int(m.group(1))
            end_bit_index = int(m.group(3)) if m.group(3) else start_bit_index
            bits = list(range(start_bit_index, end_bit_index - 1, -1))
            logger.debug("Bits from {}".format(bits))
            register.add_bit_info(bits, content[1], content[2])
        logger.debug(content)


def parse_reg_bit_overview(peripheral, df):
    # tables[0] is the overview with reset values RW/R etc
    logger.debug("Peripheral is {}".format(peripheral.name))
    register = determine_register(peripheral, df)
    if not register:
        return None
    logger.debug(register)

    if df[0][0] != 'Bit':
        raise Exception("Expected Bit")
    if df[0][1] != 'Name':
        raise Exception("Expected Name")
    if df[0][2] != 'Type':
        raise Exception("Expected Type")
    if df[0][3] != 'Reset':
        raise Exception("Expected Reset")

    if df[0][5] != 'Bit':
        raise Exception("Expected Bit")
    if df[0][6] != 'Name':
        raise Exception("Expected Name")
    if df[0][7] != 'Type':
        raise Exception("Expected Type")
    if df[0][8] != 'Reset':
        raise Exception("Expected Reset")

    df_bits_31_16 = df.iloc[:4, 1:]
    df_bits_15_0 = df.iloc[5:-1, 1:].rename(lambda x: x - 5)

    logger.debug(df_bits_31_16)
    logger.debug(df_bits_15_0)
    bit_entries = RegisterBitTableEntryCollection()
    for label, content in df_bits_31_16.iteritems():
        entry = RegisterBitTableEntry(content)
        bit_entries.append(entry)

    for label, content in df_bits_15_0.iteritems():
        entry = RegisterBitTableEntry(content)
        bit_entries.append(entry)

    bit_entries.verify()
    register.set_bits(bit_entries)
    logger.debug(bit_entries)
    return register


def parse_peripheral_register(pdf_filename, peripheral, pages):
    tables = camelot.read_pdf(
        pdf_filename, pages="{}-{}".format(pages[0], pages[1]))

    # tables[0] is the overview with reset values RW/R etc

    descriptions = []
    register = None
    for t in tables:
        rm_table = RmTable(t)
        if rm_table.is_bit_overview():
            if descriptions and register:
                description_df = pandas.concat(descriptions, ignore_index=True)
                parse_reg_bit_description(register, description_df)
            register = parse_reg_bit_overview(peripheral, t.df)
            descriptions = []
            continue
        if rm_table.is_bit_description():
            descriptions.append(t.df)

    if descriptions and register:
        description_df = pandas.concat(descriptions, ignore_index=True)
        parse_reg_bit_description(register, description_df)


class Persistency:
    def __init__(self, filename):
        self.filename = filename

    def load(self):
        try:
            with open(self.filename, 'rb') as f:
                return pickle.load(f)
        except IOError:
            return None
        return None

    def save(self, data):
        with open(self.filename, 'wb') as f:
            pickle.dump(data, f)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Generate svd file')

    parser.add_argument("--input", default=None,
                        help="Filename of the reference manual to parse")

    parser.add_argument("--out", default=None,
                        help="Filename of the svd file to generate")

    return parser.parse_args()


def main():
    args = parse_args()
    pdf_filename = args.input
    svd_filename = args.out

    # setup the logger
    handler = logging.StreamHandler(sys.stdout)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # get the chapters and pages from the pdf
    doc = Document(pdf_filename)
    logger.info("Parsing toc of document".format(pdf_filename))
    manual = doc.parse_toc()
    logger.info("Done parsing toc")
    logger.debug(manual)

    persistency = Persistency('data.pickle')
    peripherals = persistency.load()

    if peripherals is None:
        logger.info(
            "Parsing peripheral overview from document {}".format(pdf_filename))
        peripherals = parse_peripheral_overview(pdf_filename, manual.get_chapter_pages(
            '3. SiM3U1xx/SiM3C1xx Register Memory Map'))
        logger.info("Done parsing peripheral overview")

    
        logger.info("Parsing interrupts from document {}".format(pdf_filename))
        pages = manual.get_chapter_pages('4.2. Interrupt Vector Table')
        interrupts = parse_interrupts(pdf_filename, pages)

        attach_interrupts_to_peripherals(peripherals, interrupts)

        populate_derived_from_info(peripherals)
   
        for p_n, p in peripherals.items():
            if p.derived_from:
                # skip peripherals that are derived from others
                continue
            pages = manual.get_pages_for_registers(p.name)
            logger.info("Peripheral {} pg. {}".format(p.name, pages))
            if pages:
                logger.info("Parsing registers for peripheral {}".format(p.name))
                parse_peripheral_register(pdf_filename, p, pages)
            else:
                logger.warning(
                    "Peripheral {} register description not found".format(p.name))
                # for n, r in p.registers.items():
                #    print("\tRegister {}".format(n))
                #    print(r)
        logger.info("Done parsing registers for peripherals")
        persistency.save(peripherals)

    svd = SvdGenerator(peripherals)
    svd.generate(svd_filename)


if __name__ == "__main__":
    # execute only if run as a script
    main()
