from solana.rpc.api import Client
# from solders.keypair import Keypair
# from solders.pubkey import Pubkey
# from solders.message import Message
# from solders.transaction import Transaction
# from solders.system_program import TransferParams, transfer
# from spl.token.constants import TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
# from spl.token.constants import TOKEN_2022_PROGRAM_ID  # 使用 Token-2022 程序
# from spl.token.instructions import transfer_checked, TransferCheckedParams
# from spl.token.instructions import create_associated_token_account
# from spl.token._layouts import MINT_LAYOUT
# from spl.token.instructions import get_associated_token_address

from modules import dbconnect
# from modules import Spl2022

# from pump_fun_py import pump_fun
# utils
import json
import time
from typing import Optional, Union
import requests
from construct import Padding, Struct, Int64ul, Flag
import struct
from solana.transaction import Signature
from solana.transaction import AccountMeta, Transaction
from solana.rpc.types import TokenAccountOpts, TxOpts
from spl.token.instructions import (
    create_associated_token_account, 
    get_associated_token_address, 
    close_account, 
    CloseAccountParams
)
from solders.keypair import Keypair #type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solders.instruction import Instruction  # type: ignore
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price  # type: ignore

import random

class BatchPumpOption():
    UNIT_BUDGET =  100_000
    UNIT_PRICE =  1_000_000

    # constant
    GLOBAL = Pubkey.from_string("4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf")
    # FEE_RECIPIENT = Pubkey.from_string("CebN5WGQ4jvEPvsVU4EoHEpgzq1VV7AbicfhtW4xC9iM") # Main-Beta
    FEE_RECIPIENT = Pubkey.from_string("68yFSZxzLWJXkxxRGydZ63C6mHx1NLEDWmwN9Lb5yySg") # Devnet
    SYSTEM_PROGRAM = Pubkey.from_string("11111111111111111111111111111111")
    TOKEN_PROGRAM = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
    ASSOC_TOKEN_ACC_PROG = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    RENT = Pubkey.from_string("SysvarRent111111111111111111111111111111111")
    EVENT_AUTHORITY = Pubkey.from_string("Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1")
    PUMP_FUN_PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
    SOL_DECIMAL = 10**9
    db_account = None
    client = Client
    def __init__(self, db:str, url:str):
        db_name=f'db/{db}.db'
        self.db_account = dbconnect.DBSqlite(db_name)
        sql = f'CREATE TABLE BatchWallet (address CHAR(100) NOT NULL, privekey TEXT NOT NULL);'
        self.db_account.createTable(sql)
        
        self.client = Client(url)
   
    def batch_buy_sell(self, sender: Keypair, mint: Pubkey, idx):
        sql_data = f"select * from BatchWallet"
        accounts = self.db_account.getData(sql_data)
        account_count  = len(accounts)
        
        # sol_in = 0.1
        # slippage = 25
        options = [0.003, 0.002, 0.001]
        for index in range(idx, account_count):
            addr = accounts[index][0]
            addr_priv = accounts[index][1]
            random_value = random.choice(options)
            print(f'{index}----buy----------{addr}')
            # # 可供选择的减值列表
            # # 随机选择一个值
            # self.buy(sender, addr_priv, mint, random_value, 25)
            # time.sleep(3)
            # print(f'{index}----sell--------{addr}')
            # self.sell(sender, addr_priv, mint, 100, 25, False)
            
            # self.atomic_buy_sell()
            # result = self.atomic_buy_sell(sender,addr_priv,mint,random_value, slippage=25, close_token_account=False)
            result = self.atomic_buy_sell(sender,addr_priv,mint,random_value, slippage=25, close_token_account=True)
            return

    #-------pump---------------
    def find_data(self, data: Union[dict, list], field: str) -> Optional[str]:
        if isinstance(data, dict):
            if field in data:
                return data[field]
            else:
                for value in data.values():
                    result = self.find_data(value, field)
                    if result is not None:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self.find_data(item, field)
                if result is not None:
                    return result
        return None

    def get_token_balance(self, addr:Pubkey, mint: Pubkey):
        try:
            account_token_account = get_associated_token_address(addr, mint)  
            balance = self.client.get_token_account_balance(account_token_account)
            balance = float(balance.value.amount) / (10 ** balance.value.decimals)
            print(f'addr -{addr}- spl balance : {balance}')
            # return float(balance.value.amount) / (10 ** balance.value.decimals)
            return float(balance)
            # return float(balance.value.amount)
        except Exception as e:
            return 0
        

    def confirm_txn(self, txn_sig: Signature, max_retries: int = 20, retry_interval: int = 3) -> bool:
        retries = 1
        
        while retries < max_retries:
            try:
                txn_res = self.client.get_transaction(txn_sig, encoding="json", commitment="confirmed", max_supported_transaction_version=0)
                txn_json = json.loads(txn_res.value.transaction.meta.to_json())
                
                if txn_json['err'] is None:
                    print("Transaction confirmed... try count:", retries)
                    return True
                
                print("Error: Transaction not confirmed. Retrying...")
                if txn_json['err']:
                    print("Transaction failed.")
                    return False
            except Exception as e:
                print("Awaiting confirmation... try count:", retries)
                retries += 1
                time.sleep(retry_interval)
        
        print("Max retries reached. Transaction confirmation failed.")
        return None

    def get_token_price(self, mint_str: str) -> float:
        try:
            coin_data = self.get_coin_data(mint_str)
            
            if not coin_data:
                print("Failed to retrieve coin data...")
                return None
            
            virtual_sol_reserves = coin_data['virtual_sol_reserves'] / 10**9
            virtual_token_reserves = coin_data['virtual_token_reserves'] / 10**6

            token_price = virtual_sol_reserves / virtual_token_reserves
            print(f"Token Price: {token_price:.20f} SOL")
            
            return token_price

        except Exception as e:
            print(f"Error calculating token price: {e}")
            return None


    def get_virtual_reserves(self, bonding_curve: Pubkey):
        bonding_curve_struct = Struct(
            Padding(8),
            "virtualTokenReserves" / Int64ul,
            "virtualSolReserves" / Int64ul,
            "realTokenReserves" / Int64ul,
            "realSolReserves" / Int64ul,
            "tokenTotalSupply" / Int64ul,
            "complete" / Flag
        )
        
        try:
            account_info = self.client.get_account_info(bonding_curve)
            data = account_info.value.data
            parsed_data = bonding_curve_struct.parse(data)
            return parsed_data
        except Exception:
            return None

    def derive_bonding_curve_accounts(self, mint_str: str):
        try:
            # print(f'mint_str{mint_str}')
            mint = Pubkey.from_string(mint_str)
            # print(f'bonding_curve{mint}')
            bonding_curve, _ = Pubkey.find_program_address(
                ["bonding-curve".encode(), bytes(mint)],
                self.PUMP_FUN_PROGRAM
            )
            # print(f'bonding_curve{bonding_curve}')
            associated_bonding_curve = get_associated_token_address(bonding_curve, mint)
            return bonding_curve, associated_bonding_curve
        except Exception:
            return None, None

    def get_coin_data(self, mint_str: str):
        bonding_curve, associated_bonding_curve = self.derive_bonding_curve_accounts(mint_str)
        if bonding_curve is None or associated_bonding_curve is None:
            return None

        virtual_reserves = self.get_virtual_reserves(bonding_curve)
        # print(f"virtual_reserves {virtual_reserves}")
        if virtual_reserves is None:
            return None

        try:
            virtual_token_reserves = int(virtual_reserves.virtualTokenReserves)
            virtual_sol_reserves = int(virtual_reserves.virtualSolReserves)
            token_total_supply = int(virtual_reserves.tokenTotalSupply)
            complete = bool(virtual_reserves.complete)
            
            return {
                "mint": mint_str,
                "bonding_curve": str(bonding_curve),
                "associated_bonding_curve": str(associated_bonding_curve),
                "virtual_token_reserves": virtual_token_reserves,
                "virtual_sol_reserves": virtual_sol_reserves,
                "token_total_supply": token_total_supply,
                "complete": complete
            }
        except Exception:
            return None

    #----pump------
    def buy(self, pyer_keypair, owner_key ,mint_str: str, sol_in: float = 0.01, slippage: int = 25) -> bool:
        try:
            print(f"Starting buy transaction for mint: {mint_str}")
            
            coin_data = self.get_coin_data(mint_str)
            # print("Coin data retrieved:", coin_data)
            status = coin_data.get('complete')
            print(status)
            if status == True:
                print("already complete")
                return False

            if not coin_data:
                print("Failed to retrieve coin data...")
                return
            
            # pyer_keypair = Keypair.from_base58_string(payer_key)
            owner_keypair = Keypair.from_base58_string(owner_key)
            owner = owner_keypair.pubkey()
            mint = Pubkey.from_string(mint_str)
            token_account, token_account_instructions = None, None

            try:
                account_data = self.client.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
                token_account = account_data.value[0].pubkey
                token_account_instructions = None
                print("Token account retrieved:", token_account)
            except:
                token_account = get_associated_token_address(owner, mint)
                token_account_instructions = create_associated_token_account(owner, owner, mint)
                print("Token account created:", token_account)

            print("Calculating transaction amounts...")
            virtual_sol_reserves = coin_data['virtual_sol_reserves']
            virtual_token_reserves = coin_data['virtual_token_reserves']
            sol_in_lamports = sol_in * self.SOL_DECIMAL
            amount = int(sol_in_lamports * virtual_token_reserves / virtual_sol_reserves)
            slippage_adjustment = 1 + (slippage / 100)
            sol_in_with_slippage = sol_in * slippage_adjustment
            max_sol_cost = int(sol_in_with_slippage * self.SOL_DECIMAL)  
            print(f"Amount: {amount} | Max Sol Cost: {max_sol_cost}")
            
            MINT = Pubkey.from_string(coin_data['mint'])
            BONDING_CURVE = Pubkey.from_string(coin_data['bonding_curve'])
            ASSOCIATED_BONDING_CURVE = Pubkey.from_string(coin_data['associated_bonding_curve'])
            ASSOCIATED_USER = token_account
            USER = owner

            print("Creating swap instructions...")
            keys = [
                AccountMeta(pubkey=self.GLOBAL, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.FEE_RECIPIENT, is_signer=False, is_writable=True),
                AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True),
                AccountMeta(pubkey=USER, is_signer=True, is_writable=True),
                AccountMeta(pubkey=self.SYSTEM_PROGRAM, is_signer=False, is_writable=False), 
                AccountMeta(pubkey=self.TOKEN_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.RENT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.EVENT_AUTHORITY, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.PUMP_FUN_PROGRAM, is_signer=False, is_writable=False)
            ]

            data = bytearray()
            data.extend(bytes.fromhex("66063d1201daebea"))
            data.extend(struct.pack('<Q', amount))
            data.extend(struct.pack('<Q', max_sol_cost))
            data = bytes(data)
            swap_instruction = Instruction(self.PUMP_FUN_PROGRAM, data, keys)

            print("Building transaction...")
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash
            txn = Transaction(recent_blockhash=recent_blockhash, fee_payer=owner)
            txn.add(set_compute_unit_price(self.UNIT_PRICE))
            txn.add(set_compute_unit_limit(self.UNIT_BUDGET))
            if token_account_instructions:
                txn.add(token_account_instructions)
            txn.add(swap_instruction)
            
            print("Signing and sending transaction...")
            txn.sign(owner_keypair)
            # txn_sig = client.send_transaction(txn, owner_keypair, opts=TxOpts(skip_preflight=True)).value
            txn_sig = self.client.send_legacy_transaction(txn, owner_keypair, opts=TxOpts(skip_preflight=True)).value
            print("Transaction Signature:", txn_sig)

            print("Confirming transaction...")
            confirmed = self.confirm_txn(txn_sig)
            print("Transaction confirmed:", confirmed)
            
            return confirmed

        except Exception as e:
            print("Error:", e)
            return None
        
    def sell(self, pyer_keypair, owner_key, mint_str: str, percentage: int = 100, slippage: int = 25, close_token_account: bool = True) -> bool:
        try:
            print(f"Starting sell transaction for mint: {mint_str}")
            
            if not (1 <= percentage <= 100):
                print("Percentage must be between 1 and 100.")
                return False
            
            coin_data = self.get_coin_data(mint_str)
            print("Coin data retrieved:", coin_data)
            if not coin_data:
                print("Failed to retrieve coin data...")
                return
            
            # pyer_keypair = Keypair.from_base58_string(payer_key)
            owner_keypair = Keypair.from_base58_string(owner_key)
            owner = owner_keypair.pubkey()
            mint = Pubkey.from_string(mint_str)
            token_account = get_associated_token_address(owner, mint)

            print("Calculating token price...")
            sol_decimal = 10**9
            token_decimal = 10**6
            virtual_sol_reserves = coin_data['virtual_sol_reserves'] / sol_decimal
            virtual_token_reserves = coin_data['virtual_token_reserves'] / token_decimal
            token_price = virtual_sol_reserves / virtual_token_reserves
            print(f"Token Price: {token_price:.20f} SOL")

            print("Retrieving token balance...")
            token_balance = self.get_token_balance(owner_keypair.pubkey(),mint)
            print("Token Balance:", token_balance)    
            if token_balance == 0:
                print("Token Balance is zero, nothing to sell")
                return
            
            print("Calculating transaction amounts...")
            token_balance = token_balance * (percentage / 100)
            amount = int(token_balance * token_decimal)     
            sol_out = float(token_balance) * float(token_price)
            slippage_adjustment = 1 - (slippage / 100)
            sol_out_with_slippage = sol_out * slippage_adjustment
            min_sol_output = int(sol_out_with_slippage * self.SOL_DECIMAL)
            print(f"Amount: {amount} | Minimum Sol Out: {min_sol_output}")
            
            MINT = Pubkey.from_string(coin_data['mint'])
            BONDING_CURVE = Pubkey.from_string(coin_data['bonding_curve'])
            ASSOCIATED_BONDING_CURVE = Pubkey.from_string(coin_data['associated_bonding_curve'])
            ASSOCIATED_USER = token_account
            USER = owner

            print("Creating swap instructions...")
            keys = [
                AccountMeta(pubkey=self.GLOBAL, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.FEE_RECIPIENT, is_signer=False, is_writable=True),
                AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True),
                AccountMeta(pubkey=USER, is_signer=True, is_writable=True),
                AccountMeta(pubkey=self.SYSTEM_PROGRAM, is_signer=False, is_writable=False), 
                AccountMeta(pubkey=self.ASSOC_TOKEN_ACC_PROG, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.TOKEN_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.EVENT_AUTHORITY, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.PUMP_FUN_PROGRAM, is_signer=False, is_writable=False)
            ]

            data = bytearray()
            data.extend(bytes.fromhex("33e685a4017f83ad"))
            data.extend(struct.pack('<Q', amount))
            data.extend(struct.pack('<Q', min_sol_output))
            data = bytes(data)
            swap_instruction = Instruction(self.PUMP_FUN_PROGRAM, data, keys)

            print("Building transaction...")
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash
            txn = Transaction(recent_blockhash=recent_blockhash, fee_payer=owner)
            txn.add(set_compute_unit_price(self.UNIT_PRICE))
            txn.add(set_compute_unit_limit(self.UNIT_BUDGET))
            txn.add(swap_instruction)
            
            if(close_token_account):
                if percentage == 100:
                    print("Preparing to close token account after swap...")
                    close_account_instructions = close_account(CloseAccountParams(self.TOKEN_PROGRAM, token_account, owner, owner))
                    txn.add(close_account_instructions)        

            print("Signing and sending transaction...")
            txn.sign(owner_keypair)
            # txn_sig = client.send_transaction(txn, owner_keypair, opts=TxOpts(skip_preflight=True)).value
            txn_sig = self.client.send_legacy_transaction(txn, owner_keypair, opts=TxOpts(skip_preflight=True)).value
            print("Transaction Signature:", txn_sig)

            print("Confirming transaction...")
            confirmed = self.confirm_txn(txn_sig)
            print("Transaction confirmed:", confirmed)
            
            return confirmed

        except Exception as e:
            print("Error:", e)
            return None
        
        
    def atomic_buy_sell_payer(self, pyer_keypair, owner_key, mint_str: str, sol_in: float = 0.01, slippage: int = 25, close_token_account: bool = True) -> bool:
        try:
            print(f"Starting atomic buy-sell transaction for mint: {mint_str}")
            
            # 获取代币数据
            coin_data = self.get_coin_data(mint_str)
            status = coin_data.get('complete')
            print(status)
            if status == True:
                print("already complete")
                return False

            if not coin_data:
                print("Failed to retrieve coin data...")
                return
            
            # 设置账户
            owner_keypair = Keypair.from_base58_string(owner_key)
            owner = owner_keypair.pubkey()
            pyer = pyer_keypair.pubkey()  # 添加 pyer 账户
            mint = Pubkey.from_string(mint_str)
            
            # 获取或创建代币账户
            try:
                account_data = self.client.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
                token_account = account_data.value[0].pubkey
                token_account_instructions = None
                print("Token account retrieved:", token_account)
            except:
                token_account = get_associated_token_address(owner, mint)
                # token_account_instructions = create_associated_token_account(owner, owner, mint)
                token_account_instructions = create_associated_token_account(pyer, owner, mint)
                print("Token account created:", token_account)

            # 计算买入金额
            print("Calculating buy amounts...")
            virtual_sol_reserves = coin_data['virtual_sol_reserves']
            virtual_token_reserves = coin_data['virtual_token_reserves']
            sol_in_lamports = sol_in * self.SOL_DECIMAL
            buy_amount = int(sol_in_lamports * virtual_token_reserves / virtual_sol_reserves)
            buy_slippage_adjustment = 1 + (slippage / 100)
            sol_in_with_slippage = sol_in * buy_slippage_adjustment
            max_sol_cost = int(sol_in_with_slippage * self.SOL_DECIMAL)
            print(f"Buy Amount: {buy_amount} | Max Sol Cost: {max_sol_cost}")

            # 计算卖出金额
            print("Calculating sell amounts...")
            token_price = virtual_sol_reserves / virtual_token_reserves
            sell_amount = buy_amount  # 卖出买入的相同数量
            sol_out = float(sell_amount) * token_price / self.SOL_DECIMAL
            sell_slippage_adjustment = 1 - (slippage / 100)
            min_sol_output = int(sol_out * sell_slippage_adjustment * self.SOL_DECIMAL)
            print(f"Sell Amount: {sell_amount} | Min Sol Output: {min_sol_output}")

            # 设置账户参数
            MINT = Pubkey.from_string(coin_data['mint'])
            BONDING_CURVE = Pubkey.from_string(coin_data['bonding_curve'])
            ASSOCIATED_BONDING_CURVE = Pubkey.from_string(coin_data['associated_bonding_curve'])
            ASSOCIATED_USER = token_account
            USER = owner

            # 创建买入指令
            buy_keys = [
                AccountMeta(pubkey=self.GLOBAL, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.FEE_RECIPIENT, is_signer=False, is_writable=True),
                AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True),
                AccountMeta(pubkey=USER, is_signer=True, is_writable=True),
                AccountMeta(pubkey=self.SYSTEM_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.TOKEN_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.RENT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.EVENT_AUTHORITY, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.PUMP_FUN_PROGRAM, is_signer=False, is_writable=False)
            ]

            buy_data = bytearray()
            buy_data.extend(bytes.fromhex("66063d1201daebea"))
            buy_data.extend(struct.pack('<Q', buy_amount))
            buy_data.extend(struct.pack('<Q', max_sol_cost))
            buy_instruction = Instruction(self.PUMP_FUN_PROGRAM, bytes(buy_data), buy_keys)

            # 创建卖出指令
            sell_keys = [
                AccountMeta(pubkey=self.GLOBAL, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.FEE_RECIPIENT, is_signer=False, is_writable=True),
                AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True),
                AccountMeta(pubkey=USER, is_signer=True, is_writable=True),
                AccountMeta(pubkey=self.SYSTEM_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.ASSOC_TOKEN_ACC_PROG, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.TOKEN_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.EVENT_AUTHORITY, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.PUMP_FUN_PROGRAM, is_signer=False, is_writable=False)
            ]

            sell_data = bytearray()
            sell_data.extend(bytes.fromhex("33e685a4017f83ad"))
            sell_data.extend(struct.pack('<Q', sell_amount))
            sell_data.extend(struct.pack('<Q', min_sol_output))
            sell_instruction = Instruction(self.PUMP_FUN_PROGRAM, bytes(sell_data), sell_keys)

            # 构建并发送交易
            print("Building atomic transaction...")
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash
            # txn = Transaction(recent_blockhash=recent_blockhash, fee_payer=owner)
            txn = Transaction(recent_blockhash=recent_blockhash, fee_payer=pyer)
            
            # 添加计算单元设置
            txn.add(set_compute_unit_price(self.UNIT_PRICE))
            txn.add(set_compute_unit_limit(self.UNIT_BUDGET))
            
            # 添加代币账户创建指令（如果需要）
            if token_account_instructions:
                txn.add(token_account_instructions)
            
            # 添加买入和卖出指令
            txn.add(buy_instruction)
            txn.add(sell_instruction)
            
            # 如果需要，添加关闭账户指令
            if close_token_account:
                print("Preparing to close token account after swap...")
                close_account_instructions = close_account(CloseAccountParams(
                    self.TOKEN_PROGRAM, token_account, owner, owner))
                txn.add(close_account_instructions)

            # 准备所有需要签名的账户
            signers = [pyer_keypair, owner_keypair]
            print("Signing and sending atomic transaction...")
            # 使用 sign_all 方法进行签名
            txn.sign(signers)
            # 发送交易
            txn_sig = self.client.send_legacy_transaction(txn, opts=TxOpts(skip_preflight=True)).value
            print("Transaction Signature:", txn_sig)
            # 确认交易
            print("Confirming atomic transaction...")
            confirmed = self.confirm_txn(txn_sig)
            print("Transaction confirmed:", confirmed)
            return confirmed
        except Exception as e:
            print("Error:", e)
            return None
            
    def atomic_buy_sell(self, pyer_keypair, owner_key, mint_str: str, sol_in: float = 0.01, slippage: int = 25, close_token_account: bool = True) -> bool:
        try:
            print(f"Starting atomic buy-sell transaction for mint: {mint_str}")
            
            # 获取代币数据
            coin_data = self.get_coin_data(mint_str)
            status = coin_data.get('complete')
            print(status)
            if status == True:
                print("already complete")
                return False

            if not coin_data:
                print("Failed to retrieve coin data...")
                return
            
            # 设置账户
            owner_keypair = Keypair.from_base58_string(owner_key)
            owner = owner_keypair.pubkey()
            mint = Pubkey.from_string(mint_str)
            
            # 获取或创建代币账户
            try:
                account_data = self.client.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
                token_account = account_data.value[0].pubkey
                token_account_instructions = None
                print("Token account retrieved:", token_account)
            except:
                token_account = get_associated_token_address(owner, mint)
                token_account_instructions = create_associated_token_account(owner, owner, mint)
                print("Token account created:", token_account)

            # 计算买入金额
            print("Calculating buy amounts...")
            virtual_sol_reserves = coin_data['virtual_sol_reserves']
            virtual_token_reserves = coin_data['virtual_token_reserves']
            sol_in_lamports = sol_in * self.SOL_DECIMAL
            buy_amount = int(sol_in_lamports * virtual_token_reserves / virtual_sol_reserves)
            buy_slippage_adjustment = 1 + (slippage / 100)
            sol_in_with_slippage = sol_in * buy_slippage_adjustment
            max_sol_cost = int(sol_in_with_slippage * self.SOL_DECIMAL)
            print(f"Buy Amount: {buy_amount} | Max Sol Cost: {max_sol_cost}")

            # 计算卖出金额
            print("Calculating sell amounts...")
            token_price = virtual_sol_reserves / virtual_token_reserves
            sell_amount = buy_amount  # 卖出买入的相同数量
            sol_out = float(sell_amount) * token_price / self.SOL_DECIMAL
            sell_slippage_adjustment = 1 - (slippage / 100)
            min_sol_output = int(sol_out * sell_slippage_adjustment * self.SOL_DECIMAL)
            print(f"Sell Amount: {sell_amount} | Min Sol Output: {min_sol_output}")

            # 设置账户参数
            MINT = Pubkey.from_string(coin_data['mint'])
            BONDING_CURVE = Pubkey.from_string(coin_data['bonding_curve'])
            ASSOCIATED_BONDING_CURVE = Pubkey.from_string(coin_data['associated_bonding_curve'])
            ASSOCIATED_USER = token_account
            USER = owner

            # 创建买入指令
            buy_keys = [
                AccountMeta(pubkey=self.GLOBAL, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.FEE_RECIPIENT, is_signer=False, is_writable=True),
                AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True),
                AccountMeta(pubkey=USER, is_signer=True, is_writable=True),
                AccountMeta(pubkey=self.SYSTEM_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.TOKEN_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.RENT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.EVENT_AUTHORITY, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.PUMP_FUN_PROGRAM, is_signer=False, is_writable=False)
            ]

            buy_data = bytearray()
            buy_data.extend(bytes.fromhex("66063d1201daebea"))
            buy_data.extend(struct.pack('<Q', buy_amount))
            buy_data.extend(struct.pack('<Q', max_sol_cost))
            buy_instruction = Instruction(self.PUMP_FUN_PROGRAM, bytes(buy_data), buy_keys)

            # 创建卖出指令
            sell_keys = [
                AccountMeta(pubkey=self.GLOBAL, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.FEE_RECIPIENT, is_signer=False, is_writable=True),
                AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True),
                AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True),
                AccountMeta(pubkey=USER, is_signer=True, is_writable=True),
                AccountMeta(pubkey=self.SYSTEM_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.ASSOC_TOKEN_ACC_PROG, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.TOKEN_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.EVENT_AUTHORITY, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.PUMP_FUN_PROGRAM, is_signer=False, is_writable=False)
            ]

            sell_data = bytearray()
            sell_data.extend(bytes.fromhex("33e685a4017f83ad"))
            sell_data.extend(struct.pack('<Q', sell_amount))
            sell_data.extend(struct.pack('<Q', min_sol_output))
            sell_instruction = Instruction(self.PUMP_FUN_PROGRAM, bytes(sell_data), sell_keys)

            # 构建并发送交易
            print("Building atomic transaction...")
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash
            txn = Transaction(recent_blockhash=recent_blockhash, fee_payer=owner)
            
            # 添加计算单元设置
            txn.add(set_compute_unit_price(self.UNIT_PRICE))
            txn.add(set_compute_unit_limit(self.UNIT_BUDGET * 2))
            
            # 添加代币账户创建指令（如果需要）
            if token_account_instructions:
                txn.add(token_account_instructions)
            
            # 添加买入和卖出指令
            txn.add(buy_instruction)
            txn.add(sell_instruction)
            
            # 如果需要，添加关闭账户指令
            if close_token_account:
                print("Preparing to close token account after swap...")
                close_account_instructions = close_account(CloseAccountParams(
                    self.TOKEN_PROGRAM, token_account, owner, owner))
                txn.add(close_account_instructions)

            # 签名并发送交易
            print("Signing and sending atomic transaction...")
            txn.sign(owner_keypair)
            txn_sig = self.client.send_legacy_transaction(txn, owner_keypair, opts=TxOpts(skip_preflight=True)).value
            print("Transaction Signature:", txn_sig)

            # 确认交易
            print("Confirming atomic transaction...")
            confirmed = self.confirm_txn(txn_sig)
            print("Transaction confirmed:", confirmed)
            
            return confirmed

        except Exception as e:
            print("Error:", e)
            return None