import settings
import traceback
from colorama import Fore, Back, Style

BANNER = """
                ________
               /\\       \\
              /  \\       \\
             /    \\       \\
            /      \\_______\\   
            \\      /       /    LIQUIDITY POOL SNIPER BOT
          ___\\    /   ____/___      ON THE SOLANA BLOCKCHAIN
         /\\   \\  /   /\\       \\
        /  \\   \\/___/  \\       \\    """+(Back.GREEN + "SIMULATION MODE IS ON" if settings.SIMULATION_MODE else Back.RED + "SIMULATION MODE IS OFF")+ Style.RESET_ALL+"""
       /    \\       \\   \\       \\
      /      \\_______\\   \\_______\\
      \\      /       /   /       /
       \\    /       /   /       /
        \\  /       /\\  /       /
         \\/_______/  \\/_______/ 
"""

def col(x, color):
	return color + x + Style.RESET_ALL
def msg(x):
	return col("$ ", Fore.CYAN) + x
def msgok(x):
	return col("$ ", Fore.GREEN) + x
def msgno(x):
	return col("$ ", Fore.RED) + x
def panic(text):
    print(msgno(text+": ")+col(str(traceback.format_exc()), Fore.RED))