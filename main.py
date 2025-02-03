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


class UpdateTimeout(Exception):
	pass
class SwapFailed(Exception):
	pass
class SerializationFailed(Exception):
	pass
class RugpullCheckFailed(Exception):
	pass

class Session:
	def __init__(self, amount,slippageIn,slippageOut,fee):
		self.fee = int(fee)
		self.keys = None
		self.token = None
		self.amount = int(amount)
		self.slippageIn = int(slippageIn)
		self.slippageOut = int(slippageOut)

	def startup(self,raw_key):
		if name == "nt":
			_ = system("cls") 
		else:
			_ = system("clear")
		init()
		self.keys = Keypair.from_bytes(base58.b58decode(raw_key))
		self.details()

	def details(self):
		print(BANNER)
		k = str(self.keys.pubkey())
		k = k.replace(k[len(k)-6:],"*"*6)
		print(col("\n\u25B8 slippage: ", Fore.CYAN) + f"{int(self.slippageIn / 100)}%, {int(self.slippageOut / 100)}%")
		print(col("\u25B8 amount: ", Fore.CYAN) + f"{self.amount / 10**9} SOL")
		print(col("\u25B8 wallet: ", Fore.CYAN) + f"{k}\n")

	def process(self):
		self.swap(self.transaction(_input=config.SOL_LP_MINT, _output=self.token.mint, buy=True))
		while True:
			try:
				data = requests.post(config.HELIUS_POST, json={
					"jsonrpc": "2.0", "id": 1,
				    "method": "getTokenAccountsByOwner",
					"params": [str(self.keys.pubkey()), {"mint": self.token.mint}, {"encoding":"jsonParsed"}]}).json()
				self.amount = int(data["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"])
				break
			except:
				time.sleep(1)
				pass
		print(f"press {col("[", Fore.CYAN)}ENTER{col("]", Fore.CYAN)} to sell {self.amount} {self.token.symbol}")
		input()
		self.swap(self.transaction(_input=self.token.mint,_output=config.SOL_LP_MINT, buy=False))

	def get_wallet_update(self):
		attempts = 0
		while attempts < settings.UPDATE_TIME_LIM:
			try:
				data = requests.post(config.HELIUS_POST, json={
					"jsonrpc": "2.0", "id": 1,
				    "method": "getTokenAccountsByOwner",
					"params": [str(self.keys.pubkey()), {"mint": self.token.mint}, {"encoding":"jsonParsed"}]}).json()
				self.amount = int(data["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"])
				break
			except:
				time.sleep(1)
				attempts += 1
		raise UpdateTimeout()

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

	def transaction(self,_input,_output, buy=True):
		attempts = 0
		serialized = None
		while attempts < settings.SERIALIZE_ATTEMPTS:
			try:
				quote = requests.get(f"https://api.jup.ag/swap/v1/quote?inputMint={_input}&outputMint={_output}&amount={self.amount}&slippageBps={self.slippageIn if buy else self.slippageOut}")
				quote = quote.json()
				r = requests.post("https://api.jup.ag/swap/v1/swap", 
					headers= {
    					'Content-Type': 'application/json'
    				},
					data=json.dumps({
					"quoteResponse" : quote,
					"userPublicKey" : str(self.keys.pubkey()),
					"prioritizationFeeLamports": {
						"priorityLevelWithMaxLamports": {
							"maxLamports": self.fee,
							"priorityLevel": "veryHigh"
						}
					}})
				)
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
				time.sleep(1)
				attempts += 1
		raise SerializationFailed()

class Token:
	def __init__(self, mint):
		self.mc = None
		self.flags = []
		self.name = None
		self.mint = mint
		self.symbol = None
		self.creator = None
		self.mintAuth = None
		self.liquidity = None
		self.freezeAuth = None
		print(msgok(f"({datetime.now()}) fetched mint {mint}"))

	def check(self):
		data = None
		print(msg(f"({datetime.now()}) analysing token..."))
		try:
			data = requests.get(f"{config.RGXYZ}/tokens/{self.mint}/report").json()
			data2 = requests.post(
			    config.HELIUS_POST,
			    headers={"Content-Type":"application/json"},
			    json={"jsonrpc":"2.0","id":"test","method":"getAsset","params":{"id":self.mint}}).json()
			self.creator = data["creator"]
			self.name = data["tokenMeta"]["name"]
			self.mintAuth = data["mintAuthority"]
			self.freezeAuth = data["freezeAuthority"]
			self.liquidity = round(data["totalMarketLiquidity"] * 100) / 100
			self.symbol = data2["result"]["token_info"]["symbol"]
			self.supply = data2["result"]["token_info"]["supply"]
			self.mc = round(data2["result"]["token_info"]["price_info"]["price_per_token"] * data2["result"]["token_info"]["supply"] / (10**(data2["result"]["token_info"]["decimals"])) * 100) / 100
		except:
			raise RugpullCheckFailed()
		try:
			if not settings.ALLOW["pump.fun"]:
				assert not self.mint.endswith("pump")
			assert self.freezeAuth == None
			assert self.mintAuth == None
			assert self.liquidity > settings.MIN_LIQUIDITY
			assert self.mc > settings.MIN_MARKETCAP
			for flag in data["risks"]:
				self.flags.append(flag["name"])
				assert settings.ALLOW[flag["name"]]
			return self.display(False)
		except:
			return self.display(True)

	def display(self, rugpull):
		print(f"\tname: {self.name}\n\tsymbol: {self.symbol}\n\tmarket cap: {self.mc}$\n\tliquidity: {self.liquidity}$\n\tmint: {self.mint}\n\tcreator: {self.creator}")
		for f in self.flags:
			print("\t\u25B8 "+f)
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
								if not sniper.token.check():
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
			int(round(settings.SOL_AMOUNT)), 
			settings.SLIPPAGE_IN,
			settings.SLIPPAGE_OUT, 
			settings.MAX_FEE
		)
		sniper.startup(secret.KEY)

		print("press "+col("[", Fore.CYAN)+"ENTER"+col("]", Fore.CYAN)+ " to reach RPC node")
		input()
		asyncio.run(rpc(sniper))
		print(msg("bot halted"))
	except:
		print()
		panic("bot halted")

main()
