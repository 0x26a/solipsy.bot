# -- RUNTIME PARAMETERS --
SIMULATION_MODE = False
SERIALIZE_ATTEMPTS = 1
SWAP_ATTEMPTS = 1

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

