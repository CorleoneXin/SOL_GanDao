# from solana.rpc.api import Client
# from solana.transaction import Transaction
# from solders.system_program import TransferParams, transfer
# from solders.keypair import Keypair
# from solders.pubkey import Pubkey
# from solders.message import Message

from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.message import Message
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer

# Dyw8nZe4AgbXQ6R7dySEEsegLejBnVsuyMxdpQ7aj7cQ
sender = Keypair.from_base58_string('qA6ZME5AnRKcskssUMvKCpfX5pYrpv5swBiCdvwYDPEYBi3F96ohPqDJmVuUjH8B1ApMpLQZSU9jLwDTsvk4s3z')
receiver = Pubkey.from_string("Dy6wpRQKq4JXxPmd7V1ikyTLLgrBRY4sBHmfpZzkdVuL")
receiver2 = Pubkey.from_string("BgQEgwo1mAp9K8Kmys4PUZ1VQqJ77GJaQXySyHc12NKZ")

tx1 = transfer(TransferParams(from_pubkey=sender.pubkey(), to_pubkey=receiver, lamports=1000000))
tx2 = transfer(TransferParams(from_pubkey=sender.pubkey(), to_pubkey=receiver2, lamports=1000000))

ixns = [tx1, tx2]
msg = Message(ixns, sender.pubkey())
client = Client("https://api.devnet.solana.com")
# client.send_transaction(Transaction([sender], msg, client.get_latest_blockhash()).value.blockhash) # doctest: +SKIP

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
# 查询账户余额
sender_balance = client.get_balance(sender.pubkey()).value
receiver_balance = client.get_balance(receiver).value
receiver2_balance = client.get_balance(receiver2).value
print(f"发送方余额: {sender_balance} lamports")
print(f"接收方余额: {receiver_balance} lamports")
print(f"接收方2余额: {receiver2_balance} lamports")
