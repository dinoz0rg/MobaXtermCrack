import os
import time
import zipfile
import win32api


class LicenseType:
    Professional = 1
    Educational = 3
    Personal = 4


class Encoder:
    def __init__(self):
        self.VariantBase64Table = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
        self.VariantBase64Dict = {i: self.VariantBase64Table[i] for i in range(len(self.VariantBase64Table))}
        self.VariantBase64ReverseDict = {self.VariantBase64Table[i]: i for i in range(len(self.VariantBase64Table))}

    def VariantBase64Encode(self, bs: bytes):
        result = b''
        blocks_count, left_bytes = divmod(len(bs), 3)

        for i in range(blocks_count):
            coding_int = int.from_bytes(bs[3 * i:3 * i + 3], 'little')
            block = self.VariantBase64Dict[coding_int & 0x3f]
            block += self.VariantBase64Dict[(coding_int >> 6) & 0x3f]
            block += self.VariantBase64Dict[(coding_int >> 12) & 0x3f]
            block += self.VariantBase64Dict[(coding_int >> 18) & 0x3f]
            result += block.encode()

        if left_bytes == 0:
            return result

        elif left_bytes == 1:
            coding_int = int.from_bytes(bs[3 * blocks_count:], 'little')
            block = self.VariantBase64Dict[coding_int & 0x3f]
            block += self.VariantBase64Dict[(coding_int >> 6) & 0x3f]
            result += block.encode()
            return result
        else:
            coding_int = int.from_bytes(bs[3 * blocks_count:], 'little')
            block = self.VariantBase64Dict[coding_int & 0x3f]
            block += self.VariantBase64Dict[(coding_int >> 6) & 0x3f]
            block += self.VariantBase64Dict[(coding_int >> 12) & 0x3f]
            result += block.encode()
            return result

    def VariantBase64Decode(self, s: str):
        result = b''
        blocks_count, left_bytes = divmod(len(s), 4)

        for i in range(blocks_count):
            block = self.VariantBase64ReverseDict[s[4 * i]]
            block += self.VariantBase64ReverseDict[s[4 * i + 1]] << 6
            block += self.VariantBase64ReverseDict[s[4 * i + 2]] << 12
            block += self.VariantBase64ReverseDict[s[4 * i + 3]] << 18
            result += block.to_bytes(3, 'little')

        if left_bytes == 0:
            return result
        elif left_bytes == 2:
            block = self.VariantBase64ReverseDict[s[4 * blocks_count]]
            block += self.VariantBase64ReverseDict[s[4 * blocks_count + 1]] << 6
            result += block.to_bytes(1, 'little')
            return result
        elif left_bytes == 3:
            block = self.VariantBase64ReverseDict[s[4 * blocks_count]]
            block += self.VariantBase64ReverseDict[s[4 * blocks_count + 1]] << 6
            block += self.VariantBase64ReverseDict[s[4 * blocks_count + 2]] << 12
            result += block.to_bytes(2, 'little')
            return result
        else:
            raise ValueError('Invalid encoding.')

    @staticmethod
    def EncryptBytes(key: int, bs: bytes):
        result = bytearray()
        for i in range(len(bs)):
            result.append(bs[i] ^ ((key >> 8) & 0xff))
            key = result[-1] & key | 0x482D
        return bytes(result)

    @staticmethod
    def DecryptBytes(key: int, bs: bytes):
        result = bytearray()
        for i in range(len(bs)):
            result.append(bs[i] ^ ((key >> 8) & 0xff))
            key = bs[i] & key | 0x482D
        return bytes(result)


class Keygen:
    def __init__(self):
        self.encoder = Encoder()

    @staticmethod
    def get_file_version(file_path):
        try:
            info = win32api.GetFileVersionInfo(file_path, "\\")
            version = info['FileVersionMS']
            major = version >> 16
            minor = version & 0xFFFF
            build = info['FileVersionLS'] >> 16
            return major, minor
        except Exception as e:
            print(f"Error retrieving file version: {str(e)}")
            return None


    def generate_licence(self, LicenseType: int, Count: int, UserName: str, MajorVersion: int, MinorVersion):
        assert(Count >= 0)
        LicenseString = f'{LicenseType}#{UserName}|{MajorVersion}{MinorVersion}#{Count}#' \
                        f'{MajorVersion}3{MinorVersion}6{MinorVersion}#{0}#{0}#{0}#'

        EncodedLicenseString = self.encoder.VariantBase64Encode(self.encoder.EncryptBytes(0x787, LicenseString.encode())).decode()
        with zipfile.ZipFile('Custom.mxtpro', 'w') as f:
            f.writestr('Pro.key', data=EncodedLicenseString)


def main():
    exe_path = input('Enter MobaXterm path: ')
    owner_name = "Dino"

    keygen = Keygen()
    major_ver, minor_ver = keygen.get_file_version(exe_path)
    keygen.generate_licence(LicenseType.Professional, 1, owner_name, major_ver, minor_ver)

    print('[*] Success!')
    print('[*] File generated: %s' % os.path.join(os.getcwd(), 'Custom.mxtpro'))
    print('[*] Please move or copy the newly-generated file to MobaXterm\'s installation path.')
    time.sleep(2)


if __name__ == '__main__':
    main()

