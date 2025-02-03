# Solipsy

An efficient Solana sniper bot written in python.


![Image](https://github.com/user-attachments/assets/e1e35513-207b-4f6a-8626-e2858a9277d6)

## Warnings
This code was written for learning purpose  and I do not encourage anyone to use it without `SIMULATION_MODE` turned on.

Your money, your problems.

## Runtime chronology
* The bot reaches HELIUS RPC node and looks for liquidity pool creation.
* The mint associated to the LP is fetched.
* The token is analyzed through rugcheck.xyz API and custom evaluation settings are applied.
* If the token doesn't trigger any unallowed flags, it is bought.
* Now you just have to press enter to exit your position.

## Settings 
You can chose to run in `SIMULATION_MODE`, allow `pump.fun` tokens and many other things in `settings.py`.

```python
# -- RUNTIME PARAMETERS --
SIMULATION_MODE = False
SERIALIZE_ATTEMPTS = 1
SWAP_ATTEMPTS = 1
UPDATE_TIME_LIM = 30

# -- TRANSACTION SETTINGS --
MAX_FEE = 0 # in lamports
SOL_AMOUNT = 0  # in lamports

SLIPPAGE_IN = 2 * 100 # 2%
SLIPPAGE_OUT = 2 * 100 # 2% 

# -- RUGCHECK SETTINGS --
MIN_LIQUIDITY = 0 # minimum total liquidity in USDc

ALLOW = {
	"pump.fun" : True,
	"High ownership" : True,
	"Low amount of LP Providers" : True,
	"High holder concentration" : True,
	"Mutable metadata" : True,
	"Large Amount of LP Unlocked" : True,
	"High holder correlation" : True,
	"Low Liquidity" : True,
	"Missing file metadata" : True,
	"Copycat token" : True,
	"Single holder ownership": True,
	"Top 10 holders high ownership": True
}
```
## Running the bot
You must enter your private key (base 58) and HELIUS API key in the `secret.py` file.

Then you can run `main.py`.

