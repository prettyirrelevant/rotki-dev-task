# ROTKI DEVELOPER TASK
Rotki developer task

## Getting Started
- Clone the repository.
- Create a virtual environment.
```sh
$ python -m venv .venv
```
- Activate the virtual environment.
```sh
$ source .venv/bin/activate
```

- Install all the requirements needed to run the project.
```sh
$ pip install -r requirements.txt
```

- Start the CLI application.
```sh
$ python cli.py setup
```

- Get BTC balances(This takes approximately 5 seconds).
```sh
$ python cli.py balances --chain=btc --currency=ngn
```

- Get ETH balances and token balances(This takes approximately 40 seconds). `currency` can be one of `usd`, `eur`, `gpb`, `ngn`, `cad`, `chf`, etc.
```sh
$ python cli.py balances --chain=eth --currency=ngn
```

- Get ETH transactions of the inputted ETH addresses
```sh
$ python cli.py transactions
```

- Display all information
```sh
$ python cli.py all --currency=ngn
```

- Need help running one of the command?
```sh
$ python cli.py balances --help
```
## Features Implemented

- [x] detect the current BTC balances of the bitcoin addresses and display them when requested.
- [x] detect the current ETH and token balances of the ethereum addresses and display them when requested.
- [x] get the transactions of each ethereum address(save them on disk & scan them for token transfers and try to detect token swaps. Save them on disk.)
- [x] Display all the above when requested. Also show totals of balances across locations and breakdown of balance per asset per location.
- [ ] get the current balances of the kraken exchange and display them when requested.
- [ ] get the user's open orders and past trades of the kraken exchange, save them on disk and display them when requested.
## Services Used
- Infura Node API: This is used together with the Web3 library to get Ether balance & Token balances.
- EtherScan API: This is used to get transactions for the Ethereum blockchain.
- 4Byte Directory API: This is used to get the function name of a transaction input hash.
- Coincap API: This converts cryptocurrencies to their fiat equivalent.

## Libraries Used
- Web3.py: Used to interact with the Ethereum blockchain.
- Click: Used to create the terminal UI.
- Requests: Used to make external API requests.

## Things To Note
- Only the latest 25 transactions are returned for ETH transactions for a specific address.
- For the token balances of an ETH address, an `assets.json` which contains `contract address` and `decimals` of several tokens(70 tokens to be precise).
- To detect a swap & token transfer for ETH transactions, the first 8 hex characters(after removing the prefix `0x`) is used to get the function name. These characters are then sent the 4Byte Directory API and the name of the function is returned(`swapETHForExactTokens` represents "SWAP" while `transfer` represents a "TRANSFER"). All other contract calls are disregarded.