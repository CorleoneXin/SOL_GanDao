from solders.keypair import Keypair
import based58

# data = bytes.fromhex('0d9e0ddf5fd51c0640420f00000000000300000045544806000000307844656164')
# Identifier: b'\r\x9e\r\xdf_\xd5\x1c\x06'
def get_func_identifier(data: bytes):
    # 提取标识符
    identifier = data[:8]
    hexString = identifier.hex()
    byte_string = bytes.fromhex(hexString)
    print(f"Identifier: {byte_string}")