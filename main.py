import os
from dotenv import load_dotenv

load_dotenv('.env')

DB_NAME = os.getenv("DB_NAME")
GERERATE_KEY_AMOUNT = os.getenv("GERERATE_KEY_AMOUNT")
RPC_URL = os.getenv("RPC_URL")
MASTER_ADDR = os.getenv("MASTER_ADDR")
MASTER_KEY = os.getenv("MASTER_KEY")
TRANSFER_AMOUNT = os.getenv("TRANSFER_AMOUNT")
CONTRACT_ADDR = os.getenv("CONTRACT_ADDR")
CONTRACT_ABI = os.getenv("CONTRACT_ABI")
TOKEN_MINT = os.getenv("TOKEN_MINT")

print(f'DB_NAME : {DB_NAME}')
print(f'GERERATE_KEY_AMOUNT : {GERERATE_KEY_AMOUNT}')
print(f'RPC_URL : {RPC_URL}')
# print(f'MASTER_KEY : {MASTER_KEY}')
print(f'MASTER_ADDR : {MASTER_ADDR}')
print(f'TRANSFER_AMOUNT : {TRANSFER_AMOUNT}')
print(f'CONTRACT_ADDR : {CONTRACT_ADDR}')
print(f'CONTRACT_ABI : {CONTRACT_ABI}')
print(f'TOKEN_MINT : {TOKEN_MINT}')


import GenerateKey
import BatchOption
from solders.keypair import Keypair
from solders.pubkey import Pubkey

cls = BatchOption.BatchOption(DB_NAME, RPC_URL)
sender = Keypair.from_base58_string(MASTER_KEY)
mint = Pubkey.from_string(TOKEN_MINT)

def gererateKey():
    # GenerateKey.GenerateKey(DB_NAME, int(GERERATE_KEY_AMOUNT))
    GenerateKey.showDB(DB_NAME, 0)

if __name__ == "__main__":
    # gererateKey()
    
    # 分发sol
    # cls.batch_transfer_sol(sender, 1000000)
    # 查询
    cls.get_addr_balance(sender.pubkey())
    # cls.get_token_balance(sender.pubkey(), mint)
    cls.get_token2022_balance(sender.pubkey(), mint)
    
    #----SPL-----
    # 创建代币ATA账户
    # cls.batch_create_spl_ATA(sender, mint)
    # 分发spl代币
    # cls.batch_transfer_spl(sender, mint, 10)
    # 归集代币
    # cls.batch_collection_spl(sender, mint, 5)
    # 由master支付费用进行归集
    # cls.batch_collection_byMaster_spl(sender, mint, 1)
    
    #---SPL2022----
    # 创建代币ATA账户
    # cls.batch_create_spl_2022_ATA(sender, mint)
    # 分发spl代币
    # cls.batch_transfer_spl_2022(sender, mint, 10)
    # 由master支付费用进行归集
    # cls.batch_collection_byMaster_spl2022(sender, mint, 1)
    pass