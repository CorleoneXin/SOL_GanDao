from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from spl.token.constants import TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
# from spl.token.constants import TOKEN_2022_PROGRAM_ID  # 使用 Token-2022 程序
from spl.token.instructions import transfer_checked, TransferCheckedParams
from spl.token.instructions import create_associated_token_account
from spl.token._layouts import MINT_LAYOUT
from solders.message import Message
from solders.transaction import Transaction

# 连接到网络
client = Client("https://api.devnet.solana.com")

# 设置账户

sender = Keypair.from_base58_string('qA6ZME5AnRKcskssUMvKCpfX5pYrpv5swBiCdvwYDPEYBi3F96ohPqDJmVuUjH8B1ApMpLQZSU9jLwDTsvk4s3z')
receiver = Pubkey.from_string("Dy6wpRQKq4JXxPmd7V1ikyTLLgrBRY4sBHmfpZzkdVuL")
receiver2 = Pubkey.from_string("BgQEgwo1mAp9K8Kmys4PUZ1VQqJ77GJaQXySyHc12NKZ")
receiver3 = Pubkey.from_string("7X6pDo2d4W2kbf1JxivgMhkWX5m43V2fVGDvMr2Ldqwc")
token_mint = Pubkey.from_string("Hf7UTUeFT9vvYiexvNiM17sDSfNknFpzxVgjTDZyH1yC")  # SPL代币的Mint地址
# token_mint = Pubkey.from_string("FYbGcucHF4wZtzzArxEKNogujjJohMRXyem7Bcmgbbk4")  # Token2022代币的Mint地址

# 查询代币余额
def get_token_balance(pubkey):
    try:
        balance = client.get_token_account_balance(pubkey)
        return float(balance.value.amount) / (10 ** balance.value.decimals)
    except Exception as e:
        return 0

def create_token_account_for_receiver(payer, recive,mint):
    from spl.token.instructions import get_associated_token_address
    ata = get_associated_token_address(recive, mint)
    # 检查账户是否存在
    res = client.get_account_info(ata)
    print(f"找到现有代币账户: {res}")
    if(res.value != None):
        sender_balance = get_token_balance(ata)
        print(f"发送方代币余额: {sender_balance}")
        print(f"找到现有代币账户: {ata}")
    else:
        print(f"创建新代币账户: {ata}")
        # 创建ATA指令
        create_ata_ix = create_associated_token_account(
            payer=payer.pubkey(),
            owner=recive,
            mint=mint
        )
        
        # 发送创建账户的交易
        msg = Message([create_ata_ix], payer.pubkey())
        recent_blockhash = client.get_latest_blockhash().value.blockhash
        tx = Transaction([payer], msg, recent_blockhash)
        result = client.send_transaction(tx)
        print("交易签名:", result.value)
        confirmation = client.confirm_transaction(result.value)
        print("交易确认状态:", confirmation)
            
    return ata

# 获取或创建发送方的代币账户
def get_or_create_token_account(wallet, mint):
    from spl.token.instructions import get_associated_token_address
    ata = get_associated_token_address(wallet.pubkey(), mint)
    
    try:
        # 检查账户是否存在
        res = client.get_account_info(ata)
        print(f"找到现有代币账户: {res}")
        sender_balance = get_token_balance(ata)
        print(f"发送方代币余额: {sender_balance}")
        print(f"找到现有代币账户: {ata}")
        return ata
    except Exception:
        print(f"创建新代币账户: {ata}")
        # 创建ATA指令
        create_ata_ix = create_associated_token_account(
            payer=wallet.pubkey(),
            owner=wallet.pubkey(),
            mint=mint
        )
        
        # 发送创建账户的交易
        msg = Message([create_ata_ix], wallet.pubkey())
        recent_blockhash = client.get_latest_blockhash().value.blockhash
        tx = Transaction([wallet], msg, recent_blockhash)
        result = client.send_transaction(tx)
        confirmation = client.confirm_transaction(result.value)
        print("交易确认状态:", confirmation)
        return ata



# 获取代币小数位数
def get_token_decimals(mint_pubkey):
    mint_account = client.get_account_info(mint_pubkey)
    mint_data = MINT_LAYOUT.parse(mint_account.value.data)
    return mint_data.decimals

# 获取代币信息
def get_token_info(mint):
    info = client.get_account_info(mint)
    owner = info.value.owner
    if owner == TOKEN_2022_PROGRAM_ID:
        print("这是一个 Token-2022 代币")
    else:
        print("这是一个普通的 SPL 代币")
        data = MINT_LAYOUT.parse(info.value.data)
        res = {
            "supply": data.supply,
            "decimals": data.decimals,
            "mint_authority": data.mint_authority,
            "freeze_authority": data.freeze_authority
        }
        print(res)
        
def createATA_transferSPL():
    from spl.token.instructions import get_associated_token_address
    sender_token_account = get_or_create_token_account(sender, token_mint)
    ata = get_associated_token_address(receiver3, token_mint)
    create_ata_ix = create_associated_token_account(
        payer=sender.pubkey(),
        owner=receiver3,
        mint=token_mint
    )
    
        # 创建转账指令
    decimals = get_token_decimals(token_mint)
    amount = 10 * (10 ** decimals)  # 转账1000个代币

    transfer_ix = transfer_checked(
        TransferCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=sender_token_account,
            mint=token_mint,
            dest=ata,
            owner=sender.pubkey(),
            amount=amount,
            decimals=decimals,
            signers=[]
        )
    )
    
    msg = Message([create_ata_ix, transfer_ix], sender.pubkey())
    recent_blockhash = client.get_latest_blockhash().value.blockhash
    tx = Transaction([sender], msg, recent_blockhash)

    result = client.send_transaction(tx)
    print(f"交易签名: {result.value}")
    confirmation = client.confirm_transaction(result.value)
    print("交易确认状态:", confirmation)

    sender_balance = get_token_balance(sender_token_account)
    receiver_balance = get_token_balance(ata)
    print(f"发送方代币余额: {sender_balance}")
    print(f"接收方代币余额: {receiver_balance}")
    
def TransferSPL():
    # 获取或创建代币账户
    sender_token_account = get_or_create_token_account(sender, token_mint)
    receiver_token_account = create_token_account_for_receiver(sender, receiver, token_mint)
    receiver2_token_account = create_token_account_for_receiver(sender, receiver2, token_mint)

    # 创建转账指令
    decimals = get_token_decimals(token_mint)
    amount = 10 * (10 ** decimals)  # 转账1000个代币

    transfer_ix = transfer_checked(
        TransferCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=sender_token_account,
            mint=token_mint,
            dest=receiver_token_account,
            owner=sender.pubkey(),
            amount=amount,
            decimals=decimals,
            signers=[]
        )
    )
    
    transfer_ix2 = transfer_checked(
        TransferCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=sender_token_account,
            mint=token_mint,
            dest=receiver2_token_account,
            owner=sender.pubkey(),
            amount=amount,
            decimals=decimals,
            signers=[]
        )
    )

    # 创建并发送交易
    msg = Message([transfer_ix, transfer_ix2], sender.pubkey())
    recent_blockhash = client.get_latest_blockhash().value.blockhash
    tx = Transaction([sender], msg, recent_blockhash)

    try:
        result = client.send_transaction(tx)
        print(f"交易签名: {result.value}")
        confirmation = client.confirm_transaction(result.value)
        print("交易确认状态:", confirmation)

        sender_balance = get_token_balance(sender_token_account)
        receiver_balance = get_token_balance(receiver_token_account)
        receiver2_balance = get_token_balance(receiver2_token_account)
        print(f"发送方代币余额: {sender_balance}")
        print(f"接收方代币余额: {receiver_balance}")
        print(f"接收方代币余额: {receiver2_balance}")
        
    except Exception as e:
        print(f"交易失败: {e}")
        
# get_token_info(token_mint)
# TransferSPL()

createATA_transferSPL()