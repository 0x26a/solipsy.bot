# -- RUNTIME PARAMETERS --
SIMULATION_MODE = True
SERIALIZE_ATTEMPTS = 1
SWAP_ATTEMPTS = 1
UPDATE_TIME_LIM = 30 # seconds before giving up on trying to find the bought token in your wallet, must be coherent with the fees

# -- TRANSACTION SETTINGS --
MAX_FEE = 0 # in lamports
SOL_AMOUNT = 0  # in lamports

SLIPPAGE_IN = 2 * 100 # 2%
SLIPPAGE_OUT = 2 * 100 # 2% 

# -- RUGCHECK SETTINGS --
MIN_LIQUIDITY = 0 # in USDc
MIN_MARKETCAP = 0 # in USDc

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
