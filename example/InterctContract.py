from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.message import Message
from solders.transaction import Transaction
from solders.instruction import AccountMeta, Instruction
import borsh_construct as borsh
import typing

sender = Keypair.from_base58_string('qA6ZME5AnRKcskssUMvKCpfX5pYrpv5swBiCdvwYDPEYBi3F96ohPqDJmVuUjH8B1ApMpLQZSU9jLwDTsvk4s3z')
token_mint = Pubkey.from_string("Hf7UTUeFT9vvYiexvNiM17sDSfNknFpzxVgjTDZyH1yC")  # SPL代币的Mint地址

program_id = Pubkey.from_string("HQW9FafmgcTLLQTjtMaET7ViNiSe5Bk2fEW5jetNivCv")
pda = Pubkey.from_string("EDwU2xaq5KuYRuBQiCfyipvqnHxZ8KC9UqDBLijdMwZJ")

class DepositNativeArgs(typing.TypedDict):
    amount: int
    target_chain: str
    target_addr: str


layout = borsh.CStruct(
    "amount" / borsh.U64, "target_chain" / borsh.String, "target_addr" / borsh.String
)


class DepositNativeAccounts(typing.TypedDict):
    from_: Pubkey
    pda: Pubkey

def deposit_native(
    args: DepositNativeArgs,
    accounts: DepositNativeAccounts,
    program_id: Pubkey = program_id,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["from_"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["pda"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\r\x9e\r\xdf_\xd5\x1c\x06"
    encoded_args = layout.build(
        {
            "amount": args["amount"],
            "target_chain": args["target_chain"],
            "target_addr": args["target_addr"],
        }
    )
    data = identifier + encoded_args
    print(data)
    return Instruction(program_id, data, keys)


def deposit():
    ix = deposit_native({
    "amount": 1000000,
    'target_chain':'ETH',
    'target_addr': '0xDead'
    }, {
    "from_": sender.pubkey(),
    "pda": pda,
    })

    ixns = [ix]
    msg = Message(ixns, sender.pubkey())
    client = Client("https://api.devnet.solana.com")

    recent_blockhash = client.get_latest_blockhash().value.blockhash
    print(recent_blockhash)
    # 创建并发送交易
    tx = Transaction([sender], msg, recent_blockhash)
    # 发送交易并打印结果
    result = client.send_transaction(tx)
    print("交易签名:", result.value)
    # 等待并确认交易
    confirmation = client.confirm_transaction(result.value)
    print("交易确认状态:", confirmation)
    
deposit()