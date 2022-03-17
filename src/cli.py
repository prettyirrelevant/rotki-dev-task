import click
from eth_utils.address import is_address as is_valid_eth_address

from .utils import (
    add_address,
    fetch_currency_price,
    fetch_eth_transactions,
    get_addresses_by_chain,
    get_btc_balance,
    get_eth_balance,
    get_eth_token_balances,
    humanize_hash_or_addr,
    initialise_database,
    is_valid_btc_address,
)


@click.group()
def rotki():
    """
    Rotki Dev Task.

    Note: Run `python main.py setup` first.
    """


@rotki.command()
def setup():
    """This commands requests the user for BTC addresses and ETH addresses."""
    try:
        # Inititalise the db
        initialise_database()

        btc_input = click.prompt("Enter BTC addresses separated by a comma")
        btc_addresses = [addr.strip() for addr in btc_input.split(",")]
        for addr in btc_addresses:
            if not is_valid_btc_address(addr):
                click.secho("One or more of the BTC addresses provided are invalid!", fg="red")
                break

        eth_input = click.prompt("Enter ETH addresses separated by a comma")
        eth_addresses = [addr.strip() for addr in eth_input.split(",")]
        for addr in eth_addresses:
            if not is_valid_eth_address(addr):
                click.secho("One or more of the ETH addresses provided are invalid!", fg="red")
                break

        for addr in btc_addresses:
            add_address({"address": addr, "chain": "btc"})

        for addr in eth_addresses:
            add_address({"address": addr, "chain": "eth"})

        click.secho("BTC & ETH addresses saved to DB!", fg="green")
    except Exception:
        click.secho("Sorry, something wrong happened!", fg="red")


@rotki.command()
@click.option("-c", "--chain", type=click.Choice(["btc", "eth"]), required=True)
@click.option("-cur", "--currency", default="USD", show_default=True)
def balances(chain, currency):
    """This command returns either Ether & token balances for all ETH addresses stored or Bitcoin balances for all BTC addresses stored."""

    try:
        addresses = get_addresses_by_chain(chain)
        currency = currency.upper()

        if chain == "btc":
            click.secho(
                "{:11} | {:>20} | {:>20}".format(
                    "BTC Address", "Balance(BTC)", f"Balance({currency})"
                ),
                bold=True,
                fg="green",
            )
            click.secho("- " * 29)
            for addr in addresses:
                btc_balance = get_btc_balance(addr[1])

                print("{:11} |".format(humanize_hash_or_addr(addr[1])), end=" ")
                print("{:>20} |".format(btc_balance), end=" ")
                print("{:>20}".format(fetch_currency_price(chain, currency, btc_balance)))
        elif chain == "eth":
            click.secho(
                "{:11} | {:>20} | {:>20} | {:>10} | {:>15}".format(
                    "ETH Address",
                    "Ether Balance(ETH)",
                    f"Ether Balance({currency})",
                    "Token Name",
                    "Token Balance",
                ),
                bold=True,
                fg="green",
            )
            click.secho("- " * 45, fg="green", bold=True)
            for addr in addresses:
                eth_balance = get_eth_balance(addr[1])
                token_balances = get_eth_token_balances(addr[1])
                if token_balances:
                    for token in token_balances:
                        print("{:11} |".format(humanize_hash_or_addr(addr[1])), end=" ")
                        print("{:>20} |".format(eth_balance), end=" ")
                        print(
                            "{:>20} |".format(fetch_currency_price(chain, currency, eth_balance)),
                            end=" ",
                        )
                        print("{:>10} |".format(token["name"]), end=" ")
                        print("{:>15}".format(token["amount"]))
                else:
                    print("{:11} |".format(humanize_hash_or_addr(addr[1])), end=" ")
                    print("{:>20} |".format(eth_balance), end=" ")
                    print(
                        "{:>20} |".format(fetch_currency_price(chain, currency, eth_balance)),
                        end=" ",
                    )
                    print("{:>10} |".format("N/A"), end=" ")
                    print("{:>15}".format("N/A"))
    except Exception:
        click.secho("Sorry, something wrong happened!", fg="red")


@rotki.command()
def transactions():
    """This command returns transactions for all ETH addresses stored."""

    try:
        addresses = get_addresses_by_chain("eth")
        for addr in addresses:
            click.secho(f"Last 25 transactions for {addr[1]}", bold=True)
            transactions = fetch_eth_transactions(addr[1])
            click.secho(
                "{:2} | {:>11} | {:>11} | {:>11} | {:>13} | {:>20}".format(
                    "ID", "Txn Hash", "From", "To", "Txn Type", "Value(Wei)"
                ),
                bold=True,
                fg="green",
            )
            click.secho("- " * 43)
            for txn in transactions:
                print("{:2} |".format(txn[0]), end=" ")
                print("{:>11} |".format(humanize_hash_or_addr(txn[1])), end=" ")
                print("{:>11} |".format(humanize_hash_or_addr(txn[2])), end=" ")
                print("{:>11} |".format(humanize_hash_or_addr(txn[3])), end=" ")
                print("{:>13} |".format(txn[4]), end=" ")
                print("{:>20} |".format(txn[5]))
    except Exception:
        click.secho("Sorry, something wrong happened!", fg="red")


@rotki.command()
@click.option("-cur", "--currency", default="USD", show_default=True)
@click.pass_context
def all(ctx, currency):
    """This command performs all of the above commmands except `setup`."""

    try:
        ctx.invoke(balances, chain="btc", currency=currency)
        print("\n\n")
        ctx.invoke(balances, chain="eth", currency=currency)
        print("\n\n")
        ctx.invoke(transactions)
    except Exception:
        click.secho("Sorry, something wrong happened!", fg="red")
