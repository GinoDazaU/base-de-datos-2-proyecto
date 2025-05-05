import struct

class HashIndex:

    def __init__(self, filename):
        self.filename = filename

    @staticmethod
    def build_index(filename, field):
        with open(filename, "r+b") as file:
            file.seek(4)