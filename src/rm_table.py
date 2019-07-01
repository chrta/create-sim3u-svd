#!/bin/env python3


class RmTable:
    def __init__(self, table):
        self.table = table

    def is_bit_overview(self):
        df = self.table.df
        if df[0][0] != 'Bit':
            return False
        if df[0][1] != 'Name':
            return False
        if df[0][2] != 'Type':
            return False
        if df[0][3] != 'Reset':
            return False

        if df[0][5] != 'Bit':
            return False
        if df[0][6] != 'Name':
            return False
        if df[0][7] != 'Type':
            return False
        if df[0][8] != 'Reset':
            return False
        return True

    def is_bit_description(self):
        df = self.table.df
        if df[0][0] != 'Bit':
            return False
        if df[1][0] != 'Name':
            return False
        if df[2][0] != 'Function':
            return False

        return True
