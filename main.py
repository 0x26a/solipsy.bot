import config
import secret
import settings
from style import *

import time
import traceback
from os import name, system
from datetime import datetime
from colorama import init, Fore, Back, Style

import json
import asyncio
import requests
from websockets.asyncio.client import connect

import base58
import base64
import solana
import solders
from solders.keypair import Keypair
from solders.signature import Signature

class SwapFailed(Exception):
	pass
class SerializationFailed(Exception):
	pass

class Session:
	def __init__(self, amount,slippageIn,slippageOut,fee):
		self.fee = fee
		self.keys = None
		self.token = None
		self.amount = amount
		self.slippageIn = slippageIn
		self.slippageOut = slippageOut
	def startup(self,raw_key):
		if name == "nt":
			_ = system("cls") 
		else:
			_ = system("clear")
		init()
		self.keys = Keypair.from_bytes(base58.b58decode(raw_key))
		self.details()
		print("press "+col("[", Fore.CYAN)+"ENTER"+col("]", Fore.CYAN)+ " to reach RPC node")
		input()

	def details(self):
		print(BANNER)
		print(col("\nslippage: ", Fore.CYAN) + f"{int(self.slippageIn / 100)}%, {int(self.slippageOut / 100)}%")
		print(col("amount: ", Fore.CYAN) + f"{self.amount / 10**9} SOL")
		print(col("wallet: ", Fore.CYAN) + f"{self.keys.pubkey()}\n")

	def process(self):
		self.swap(self.transactionOrder(_input=config.SOL_LP_MINT, _output=self.token.mint, buy=True))

		self.token.set_decimals()
		print(msg("please enter amount to swap back"))
		x = float(input("~"+col("# ", Fore.CYAN)))
		self.amount = int(x * (10**self.token.decimals))

		self.swap(self.transactionOrder(_input=self.token.mint,_output=config.SOL_LP_MINT, buy=False))

	def swap(self, tx):
		r = None
		attempts = 0
		while attempts < settings.SWAP_ATTEMPTS:
			try:
				tx_json = {
					"jsonrpc":"2.0",
					"id": 26,
					"method": "simulateTransaction" if settings.SIMULATION_MODE else "sendTransaction",
					"params" : [tx]
				}
				r = requests.post(config.HELIUS_POST,json=tx_json).json()
				print(msgok(f"({datetime.now()}) transaction: {r["result"]}"))
				print(msg(f"https://gmgn.ai/sol/token/{self.token.mint}\n"))
				return None
			except:
				panic(f"({datetime.now()}) transaction failed [{col(r["error"]["message"], Fore.YELLOW)}]")
				print(msg("trying again with additional slippage (+10%)..."))
				self.slippageOut = min(100 * 100, self.slippageOut + 10 * 100)
				self.slippageIn = min(100 * 100, self.slippageIn + 10 * 100)
				time.sleep(0.5)
				attempts += 1
		raise SwapFailed()

	def transactionOrder(self,_input,_output, buy=True):
		attempts = 0
		serialized = None
		while attempts < settings.SERIALIZE_ATTEMPTS:
			try:
				quote = requests.get(f"https://quote-api.jup.ag/v6/quote?inputMint={_input}&outputMint={_output}&amount={self.amount}&slippageBps={self.slippageIn if buy else self.slippageOut}")
				quote = quote.json()
				r = requests.post("https://quote-api.jup.ag/v6/swap",json={
					"quoteResponse" : quote,
					"userPublicKey" : str(self.keys.pubkey()),
					"prioritizationFeeLamports": {
						"priorityLevelWithMaxLamports": {
							"maxLamports": self.fee,
							"priorityLevel": "veryHigh"
						}
					}
				})
				serialized = r.json()
				swap_tx = serialized["swapTransaction"]
				raw_tx = solders.transaction.VersionedTransaction.from_bytes(base64.b64decode(swap_tx))
				signature = self.keys.sign_message(solders.message.to_bytes_versioned(raw_tx.message))
				signed_tx = solders.transaction.VersionedTransaction.populate(raw_tx.message, [signature])
				encoded_tx = base58.b58encode(bytes(signed_tx)).decode("utf-8")
				print(msgok("transaction order successfully signed"))
				return encoded_tx
			except:
				panic(f"({datetime.now()}) couldn't create signed transaction order [{col(serialized["error"], Fore.YELLOW)}]")
				time.sleep(8)
				attempts += 1
		raise SerializationFailed()

class Token:
	def __init__(self, mint):
		self.mc = None
		self.flags = []
		self.name = None
		self.mint = mint
		self.rugged = None
		self.creator = None
		self.decimals = None
		self.mintAuth = None
		self.liquidity = None
		self.freezeAuth = None
		print(msgok(f"({datetime.now()}) fetched mint {mint}"))

	def set_decimals(self):
		try:
			r = requests.post(
			    config.HELIUS_POST,
			    headers={"Content-Type":"application/json"},
			    json={"jsonrpc":"2.0","id":1,"method":"getTokenSupply","params":[self.mint]}
			).json()
			self.decimals = r["result"]["value"]["decimals"]
		except:
			panic(f"couldn't fetch {self.mint} decimals")
	def is_rugpull(self):
		print(msg(f"({datetime.now()}) analysing potential rugpull signs..."))
		data = requests.get(f"{config.RGXYZ}/tokens/{self.mint}/report").json()
		self.rugged = data["rugged"]
		self.creator = data["creator"]
		self.name = data["tokenMeta"]["name"]
		self.mintAuth = data["mintAuthority"]
		self.freezeAuth = data["freezeAuthority"]
		self.liquidity = data["totalMarketLiquidity"]
		try:
			if not settings.ALLOW["pump.fun"]:
				assert not self.mint.endswith("pump")
			assert not self.rugged
			assert self.freezeAuth == None
			assert self.mintAuth == None
			assert self.liquidity > settings.MIN_LIQUIDITY
			for flag in data["risks"]:
				self.flags.append(flag["name"])
				assert settings.ALLOW[flag["name"]]
			return self.display(False)
		except:
			return self.display(True)

	def display(self, rugpull):
		print("\trugged: "+str(self.rugged),
		"\n\tname: "+str(self.name),
		"\n\tliquidity: "+str(self.liquidity)+"$",
		"\n\tmint: "+str(self.mint),
		"\n\tcreator: "+str(self.creator))
		for f in self.flags:
			print("\t- "+f)
		print(msgno("the token triggered an unallowed flag") if rugpull else msgok("checks passed"))
		return rugpull

def logs_analysis(data):
	logs = data["params"]["result"]["value"]["logs"]
	signature = data["params"]["result"]["value"]["signature"]
	print("\r" + msg("parsing ") + signature, end='')
	if any(config.LP_CREATION in log for log in set(logs)):
		return signature
	return None

def fetch_mint(signature):
	print("\r"+msgok(f"\a({datetime.now()}) CREATE_POOL event at {signature}"))
	data = requests.post(config.HELIUS_FETCH, json={"transactions":[signature]}).json()
	try:
		instructions = data[0]["instructions"]
		assert len(instructions) > 0
		instruction = list(filter(lambda i: i["programId"] == config.RAYDIUM_ID, instructions))[0]
		if instruction["accounts"][8] == config.SOL_LP_MINT:
			return instruction["accounts"][9]
		else:
			return instruction["accounts"][8]
	except:
		panic("couldn't fetch mint")

async def rpc(sniper: Session):
	while True:
		try:
			async with connect(config.HELIUS_RPC) as ws:
					await ws.send(json.dumps({
  						"jsonrpc": "2.0",
 						"id": 1,
 						"method": "logsSubscribe",
						"params": [
							{
    	 							"mentions": [ config.RAYDIUM_ID ]
   							},
   							{
    	 							"commitment": "finalized"
   							}
  					]}))
					frep = await ws.recv()
					frepjson = json.loads(frep)
					print(msgok(f"subscribed to RPC logsSubscribe(), id={frepjson["result"]}"))
	
					while True:
						data = await ws.recv()
						data = json.loads(data)
						signature = logs_analysis(data)
						if signature != None:
							mint = fetch_mint(signature)
							if mint != None:
								sniper.token = Token(mint)
								if not sniper.token.is_rugpull():
									sniper.process()
									break
	
					await ws.close()
					break
		except:
			print()
			panic("connection terminated")
			time.sleep(1)

def main():
	try:
		sniper = Session(
			settings.SOL_AMOUNT, 
			settings.SLIPPAGE_IN,
			settings.SLIPPAGE_OUT, 
			settings.MAX_FEE
		)
		sniper.startup(secret.KEY)
		asyncio.run(rpc(sniper))
		print(msg("bot halted"))
	except:
		print()
		panic("bot halted")
main()