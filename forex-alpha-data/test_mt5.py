import MetaTrader5 as mt5

path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
login = 5046678384      # mets ton login ici
password = "TkF@L7Ta"   # mets ton password ici
server = "MetaQuotes-Demo"  # mets ton server exact ici

if not mt5.initialize():
    print("Initialize failed", mt5.last_error())
    quit()

if not mt5.login(login, password, server):
    print("Login failed", mt5.last_error())
else:
    print("Login successful!")

mt5.shutdown()
