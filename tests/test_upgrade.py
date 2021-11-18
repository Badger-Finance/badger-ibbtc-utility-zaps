from brownie import *
import pytest


"""
Tests for the Upgrade from mainnet version to upgraded version
These tests must be run on mainnet-fork
"""


@pytest.fixture
def zap_proxy():
    yield Contract("0x87C3Ef099c6143e4687b060285bad201b9efa493")


@pytest.fixture
def proxy_admin():
    return Contract("0x7D0398D7D7432c47Dffc942Cd097B9eA3d88C385")


@pytest.fixture
def proxy_admin_owner():
    yield "0x86cbd0ce0c087b482782c181da8d191de18c8275"


@pytest.fixture(scope="session")
def bcrvIbbtc(Contract):
    yield Contract("0xaE96fF08771a109dc6650a1BdCa62F2d558E40af")


def test_upgrade(
    deployer,
    zap_proxy,
    proxy_admin,
    proxy_admin_owner,
    ibbtc,
    renbtc,
    wbtc,
    sbtc,
    bcrvIbbtc,
):
    new_zap_logic = IbbtcVaultZap.deploy({"from": deployer})

    ## Setting all variables, we'll use them later
    prev_gov = zap_proxy.governance()
    prev_guardian = zap_proxy.guardian()
    prev_CURVE_IBBTC_METAPOOL = zap_proxy.CURVE_IBBTC_METAPOOL()
    prev_CURVE_REN_POOL = zap_proxy.CURVE_REN_POOL()
    prev_RENCRV_TOKEN = zap_proxy.RENCRV_TOKEN()
    prev_RENCRV_VAULT = zap_proxy.RENCRV_VAULT()
    prev_SETT_PEAK = zap_proxy.SETT_PEAK()
    prev_IBBTC_VAULT = zap_proxy.IBBTC_VAULT()
    prev_IBBTC = zap_proxy.IBBTC()
    prev_RENBTC = zap_proxy.RENBTC()
    prev_WBTC = zap_proxy.WBTC()
    prev_SBTC = zap_proxy.SBTC()

    # Deploy new logic
    proxy_admin.upgrade(zap_proxy, new_zap_logic.address, {"from": proxy_admin_owner})

    gov = accounts.at(zap_proxy.governance(), force=True)

    ## Checking all variables are as expected
    assert prev_gov == zap_proxy.governance()
    assert prev_guardian == zap_proxy.guardian()
    assert prev_CURVE_IBBTC_METAPOOL == zap_proxy.CURVE_IBBTC_METAPOOL()
    assert prev_CURVE_REN_POOL == zap_proxy.CURVE_REN_POOL()
    assert prev_RENCRV_TOKEN == zap_proxy.RENCRV_TOKEN()
    assert prev_RENCRV_VAULT == zap_proxy.RENCRV_VAULT()
    assert prev_SETT_PEAK == zap_proxy.SETT_PEAK()
    assert prev_IBBTC_VAULT == zap_proxy.IBBTC_VAULT()
    assert prev_IBBTC == zap_proxy.IBBTC()
    assert prev_RENBTC == zap_proxy.RENBTC()
    assert prev_WBTC == zap_proxy.WBTC()
    assert prev_SBTC == zap_proxy.SBTC()

    # add ibbtc liquidity
    amounts = [
        ibbtc.balanceOf(deployer) // 10,
        renbtc.balanceOf(deployer) // 10,
        wbtc.balanceOf(deployer) // 10,
        sbtc.balanceOf(deployer) // 10,
    ]

    # test if calcMint works
    shares = bcrvIbbtc.balanceOf(deployer)

    minAmount = zap_proxy.calcMint(amounts, True)

    zap_proxy.deposit(amounts, minAmount * SLIPPAGE, True, {"from": deployer})

    assert bcrvIbbtc.balanceOf(deployer) - shares >= minAmount * SLIPPAGE
