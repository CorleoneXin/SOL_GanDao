from solders.keypair import Keypair
import based58
from modules import dbconnect, utils


# Base58 Encoded str: 4uBUTXFmtWRTG3g17FbE5brVx5WtSP14SZsNLeFveqmjqka7fSEWNPzG8FntDd9VMw2XFypyakJmyRWPyveVUqhL
# Dy6wpRQKq4JXxPmd7V1ikyTLLgrBRY4sBHmfpZzkdVuL

# BgQEgwo1mAp9K8Kmys4PUZ1VQqJ77GJaQXySyHc12NKZ
# Base58 Encoded: b'Myp4EnXBg6fzo4rvEcXc9ZAu2pDEqVN3oramhQn9HReUcihML4SvjeoK17tGqUgEn15NueZJWLHQdSYTDS8ex3h'
# Base58 Encoded str: Myp4EnXBg6fzo4rvEcXc9ZAu2pDEqVN3oramhQn9HReUcihML4SvjeoK17tGqUgEn15NueZJWLHQdSYTDS8ex3h

# devnet teset account
# qA6ZME5AnRKcskssUMvKCpfX5pYrpv5swBiCdvwYDPEYBi3F96ohPqDJmVuUjH8B1ApMpLQZSU9jLwDTsvk4s3z
# Dyw8nZe4AgbXQ6R7dySEEsegLejBnVsuyMxdpQ7aj7cQ

def GenerateKey(db:str, key_amount: int):
    db_name=f'db/{db}.db'
    db_account = dbconnect.DBSqlite(db_name)
    sql = f'CREATE TABLE BatchWallet (address CHAR(100) NOT NULL, privekey TEXT NOT NULL);'
    db_account.createTable(sql)

    for i in range(key_amount):
        key = Keypair()
        privKey = key.__bytes__()
        pubKey = key.pubkey()
        base58_encoded = based58.b58encode(privKey)
        decoded_str = base58_encoded.decode('utf-8', errors='ignore')
        print(decoded_str)
        print(pubKey)
        
        sql = f"INSERT INTO BatchWallet VALUES"
        sql_value = " ('%s','%s')"%(pubKey ,decoded_str)
        sql_exec = sql + sql_value
        db_account.insertData(sql_exec)

    print('generate key success')

def showDB(db:str, retry_idx:int):
    db_name=f'db/{db}.db'
    db_account = dbconnect.DBSqlite(db_name)
    sql_data = f"select * from BatchWallet"
    accounts = db_account.getData(sql_data)
    account_count  = len(accounts)
    for index in range(retry_idx, account_count):
        address = accounts[index][0]
        privkey = accounts[index][1]
        print(f"{index}-address: {address}")
        print(f" -privkey: {privkey}")

# GenerateKey('db', 3)
# showDB('db', 0)

# data = bytes.fromhex('0d9e0ddf5fd51c0640420f00000000000300000045544806000000307844656164')
# utils.get_func_identifier(data)

