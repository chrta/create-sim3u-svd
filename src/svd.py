import logging
import sys
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


def setup_logger():
    handler = logging.StreamHandler(sys.stdout)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class SvdGenerator:
    def __init__(self, peripherals):
        setup_logger()
        self.peripherals = peripherals

    def generate(self, svd_filename):
        # pyxb.RequireValidWhenGenerating(False)
        device = ET.Element('device', attrib={'schemaVersion': '1.1'})
        svd = ET.ElementTree(device)

        ET.SubElement(device, 'name').text = "SiM3U167_B"
        ET.SubElement(device, 'version').text = "1"
        ET.SubElement(
            device, 'description').text = "USB, 256K Flash, 32K RAM, EMIF"

        cpu = ET.SubElement(device, 'cpu')
        ET.SubElement(cpu, 'name').text = "CM3"
        ET.SubElement(cpu, 'revision').text = "r2p0"
        ET.SubElement(cpu, 'endian').text = "little"
        ET.SubElement(cpu, 'mpuPresent').text = "false"
        ET.SubElement(cpu, 'fpuPresent').text = "false"
        ET.SubElement(cpu, 'nvicPrioBits').text = "4"
        ET.SubElement(cpu, 'vendorSystickConfig').text = "false"

        ET.SubElement(device, 'addressUnitBits').text = "8"
        ET.SubElement(device, 'width').text = "32"
        ET.SubElement(device, 'size').text = "32"
        ET.SubElement(device, 'access').text = "read-write"

        p_element = ET.SubElement(device, 'peripherals')

        serialized = set()
        for p_n, p in self.peripherals.items():
            if p.derived_from and (p.derived_from not in serialized):
                self.peripherals[p.derived_from].xml_append(p_element)
                serialized.add(p.derived_from)
            if p.name not in serialized:
                p.xml_append(p_element)
                serialized.add(p.name)
        # for p_n, p in self.peripherals.items():
        #    print("Peripheral: {}".format(p_n))
        #    print(p.get_xml())

        svd.write(svd_filename, encoding="utf-8", xml_declaration=True)
