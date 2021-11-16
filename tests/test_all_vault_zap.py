import pytest
from conftest import MAX_UINT256


@pytest.fixture(scope="session")
def bcrvIbbtc(Contract):
    yield Contract("0xaE96fF08771a109dc6650a1BdCa62F2d558E40af")


@pytest.fixture(scope="session")
def curve_ibbtc_pool(Contract):
    yield Contract("0xFbdCA68601f835b27790D98bbb8eC7f05FDEaA9B")


@pytest.fixture(scope="session")
def curve_ibbtc_zap(Contract):
    yield Contract("0xbba4b444FD10302251d9F5797E763b0d912286A1")


@pytest.fixture(autouse=True)
def all_vault_zap(AllToVaultZap, deployer):
    zap = AllToVaultZap.deploy({"from": deployer})
    zap.initialize(deployer, deployer, {"from": deployer})
    yield zap


@pytest.fixture(autouse=True)
def set_token_approvals(deployer, ibbtc, wbtc, renbtc, sbtc, all_vault_zap):
    # Approvals
    ibbtc.approve(all_vault_zap, MAX_UINT256, {"from": deployer})
    renbtc.approve(all_vault_zap, MAX_UINT256, {"from": deployer})
    wbtc.approve(all_vault_zap, MAX_UINT256, {"from": deployer})
    sbtc.approve(all_vault_zap, MAX_UINT256, {"from": deployer})


@pytest.fixture(autouse=True)
def set_contract_approvals(
    ibbtc_guestlist,
    badger_sett_peak,
    bcrvRenbtc,
    all_vault_zap,
    bcrvIbbtc,
    curve_ibbtc_zap,
    curve_ibbtc_pool,
):
    ibbtc_guestlist.setGuests(
        [all_vault_zap], [True], {"from": ibbtc_guestlist.owner()}
    )
    bcrvIbbtc.approveContractAccess(all_vault_zap, {"from": bcrvIbbtc.governance()})


# TODO: Add permissions tests and more balance checks


def test_deposit_flow(deployer, ibbtc, renbtc, wbtc, sbtc, bcrvIbbtc, all_vault_zap):
    # add ibbtc liquidity
    amounts = [
        ibbtc.balanceOf(deployer) // 10,
        renbtc.balanceOf(deployer) // 10,
        wbtc.balanceOf(deployer) // 10,
        sbtc.balanceOf(deployer) // 10,
    ]

    shares = bcrvIbbtc.balanceOf(deployer)
    all_vault_zap.deposit(amounts, 0, {"from": deployer})

    assert bcrvIbbtc.balanceOf(deployer) > shares
