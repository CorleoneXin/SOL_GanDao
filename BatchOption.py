from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.message import Message
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer
from spl.token.constants import TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
# from spl.token.constants import TOKEN_2022_PROGRAM_ID  # 使用 Token-2022 程序
from spl.token.instructions import transfer_checked, TransferCheckedParams
from spl.token.instructions import create_associated_token_account
from spl.token._layouts import MINT_LAYOUT
from spl.token.instructions import get_associated_token_address

from modules import dbconnect


class BatchOption():
    db_account = None
    client = Client
    def __init__(self, db:str, url:str):
        db_name=f'db/{db}.db'
        self.db_account = dbconnect.DBSqlite(db_name)
        sql = f'CREATE TABLE BatchWallet (address CHAR(100) NOT NULL, privekey TEXT NOT NULL);'
        self.db_account.createTable(sql)
        
        self.client = Client(url)
        
    def get_addr_balance(self, addr:str):
        balance = self.client.get_balance(addr).value
        print(f'addr -{addr}- balance : {balance}')
        
    def get_token_info(self, mint):
        info = self.client.get_account_info(mint)
        owner = info.value.owner
        if owner == TOKEN_2022_PROGRAM_ID:
            print("Token-2022 代币")
        else:
            print("普通SPL 代币")
            data = MINT_LAYOUT.parse(info.value.data)
            res = {
                "supply": data.supply,
                "decimals": data.decimals,
                "mint_authority": data.mint_authority,
                "freeze_authority": data.freeze_authority
            }
            print(res)
        
    def _send_tx(self, sender: Keypair, ixns):
        msg = Message(ixns, sender.pubkey())
        recent_blockhash = self.client.get_latest_blockhash().value.blockhash
        tx = Transaction([sender], msg, recent_blockhash)
        result = self.client.send_transaction(tx)
        print("txid:", result.value)
        # confirmation = self.client.confirm_transaction(result.value)
        # print("tx receipt:", confirmation)
        
        
    def _get_token_decimals(self, mint_pubkey):
        mint_account = self.client.get_account_info(mint_pubkey)
        mint_data = MINT_LAYOUT.parse(mint_account.value.data)
        return mint_data.decimals

    def batch_transfer_sol(self, sender: Keypair, amount: int):
        sql_data = f"select * from BatchWallet"
        accounts = self.db_account.getData(sql_data)
        account_count  = len(accounts)
        ixns = []
        # 转帐指令打包到一起发送
        for index in range(0, account_count):
            addr = accounts[index][0]
            receiver = Pubkey.from_string(addr)
            tx1 = transfer(TransferParams(from_pubkey=sender.pubkey(), to_pubkey=receiver, lamports=amount))
            ixns.append(tx1)
            
        self._send_tx(sender, ixns)

    def batch_collection_spl(self, sender: Keypair, mint:Pubkey, amount: int):
        sql_data = f"select * from BatchWallet"
        accounts = self.db_account.getData(sql_data)
        account_count  = len(accounts)

        decimals = self._get_token_decimals(mint)
        master_ATA = get_associated_token_address(sender.pubkey(), mint)
        amount = amount * (10 ** decimals) 
        for index in range(0, account_count):
            # 获取db内的私钥，生成对应的keyPair
            privKey = accounts[index][1]
            account = Keypair.from_base58_string(privKey)
            # 获取ATA账户
            account_token_account = get_associated_token_address(account.pubkey(), mint)
            # 获取masterKey的ATA账户
            transfer_ix = transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=account_token_account,
                    mint=mint,
                    dest=master_ATA,
                    owner=account.pubkey(),
                    amount=amount,
                    decimals=decimals,
                    signers=[]
                )
            )            
            ixns = [transfer_ix]
            print(f'collection spl-{index}')
            self._send_tx(account, ixns)
    
    
    def batch_collection_byMaster_spl(self, sender: Keypair, mint:Pubkey, amount: int):
        sql_data = "select * from BatchWallet"
        accounts = self.db_account.getData(sql_data)
        account_count = len(accounts)

        decimals = self._get_token_decimals(mint)
        master_ATA = get_associated_token_address(sender.pubkey(), mint)
        amount = amount * (10 ** decimals)

        ix = []
        signers = [sender]
        for index in range(0, account_count):
            privKey = accounts[index][1]
            account = Keypair.from_base58_string(privKey)
            account_token_account = get_associated_token_address(account.pubkey(), mint)

            transfer_ix = transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=account_token_account,
                    mint=mint,
                    dest=master_ATA,
                    owner=account.pubkey(),
                    amount=amount,
                    decimals=decimals,
                    signers=[]
                )
            )
            ix.append(transfer_ix)
            signers.append(account)

        print('collection in one')
        # 创建消息
        message = Message(ix, sender.pubkey())            
        recent_blockhash = self.client.get_latest_blockhash().value.blockhash
        tx = Transaction(signers, message, recent_blockhash)
        tx.sign(signers, recent_blockhash)

        result = self.client.send_transaction(tx)
        print("txid:", result.value)
            
    def batch_transfer_spl(self, sender: Keypair, mint:Pubkey, amount: int):
        sql_data = f"select * from BatchWallet"
        accounts = self.db_account.getData(sql_data)
        account_count  = len(accounts)

        decimals = self._get_token_decimals(mint)
        master_ATA = get_associated_token_address(sender.pubkey(), mint)
        amount = amount * (10 ** decimals) 
        ixns = []
        for index in range(0, account_count):
            # 获取db内的私钥，生成对应的keyPair
            privKey = accounts[index][1]
            account = Keypair.from_base58_string(privKey)
            # 获取ATA账户
            account_token_account = get_associated_token_address(account.pubkey(), mint)            
            transfer_ix = transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=master_ATA,
                    mint=mint,
                    dest=account_token_account,
                    owner=sender.pubkey(),
                    amount=amount,
                    decimals=decimals,
                    signers=[]
                )
            )            
            ixns.append(transfer_ix)
            
        self._send_tx(sender, ixns)
    
    def batch_transfer_spl_2022(self, sender: Keypair, amount: int):
        pass
    
    # 为db的地址，批量生成ATA账户
    def batch_create_spl_ATA(self, sender: Keypair, mint: Pubkey):
        sql_data = f"select * from BatchWallet"
        accounts = self.db_account.getData(sql_data)
        account_count  = len(accounts)
        ixns = []
        # 转帐指令打包到一起发送
        for index in range(0, account_count):
            addr = accounts[index][0]
            addr = Pubkey.from_string(addr)
            # 创建ATA指令
            create_ata_ix = create_associated_token_account(
                payer=sender.pubkey(),
                owner=addr,
                mint=mint
            )
            ixns.append(create_ata_ix)
            
        self._send_tx(sender, ixns)
    
    def batch_create_spl_2022_ATA(self, sendre: Keypair):
        pass
    
    def batch_create_spl_ATA_transfer(slef, senfer: Keypair, amount: int):
        pass
    
    def batch_create_spl_2022_ATA_transfer(slef, senfer: Keypair, amount: int):
        pass