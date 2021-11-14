import pytest
from conftest import MAX_UINT256


@pytest.fixture(autouse=True)
def ibbtc_vault_zap(IbbtcVaultZap, deployer):
    zap = IbbtcVaultZap.deploy({"from": deployer})
    zap.initialize(deployer, deployer, {"from": deployer})
    yield zap


@pytest.fixture(scope="session")
def bcrvIbbtc(Contract):
    yield Contract("0xaE96fF08771a109dc6650a1BdCa62F2d558E40af")


@pytest.fixture(scope="session")
def curve_ibbtc_zap(Contract):
    yield Contract("0xbba4b444FD10302251d9F5797E763b0d912286A1")


@pytest.fixture(autouse=True)
def set_token_approvals(deployer, ibbtc, wbtc, renbtc, sbtc, ibbtc_vault_zap):
    # Approvals
    ibbtc.approve(ibbtc_vault_zap, MAX_UINT256, {"from": deployer})
    renbtc.approve(ibbtc_vault_zap, MAX_UINT256, {"from": deployer})
    wbtc.approve(ibbtc_vault_zap, MAX_UINT256, {"from": deployer})
    sbtc.approve(ibbtc_vault_zap, MAX_UINT256, {"from": deployer})


@pytest.fixture(autouse=True)
def set_contract_approvals(
    ibbtc_guestlist,
    badger_sett_peak,
    bcrvRenbtc,
    # ibbtc_mint_zap,
    ibbtc_vault_zap,
    bcrvIbbtc,
    wibbtc,
    curve_ibbtc_zap,
):
    # ibbtc_mint_zap.approveContractAccess(
    #     ibbtc_vault_zap, {"from": ibbtc_mint_zap.governance()}
    # )
    ibbtc_guestlist.setGuests(
        [ibbtc_vault_zap], [True], {"from": ibbtc_guestlist.owner()}
    )
    badger_sett_peak.approveContractAccess(
        ibbtc_vault_zap, {"from": badger_sett_peak.owner()}
    )
    bcrvRenbtc.approveContractAccess(ibbtc_vault_zap, {"from": bcrvRenbtc.governance()})
    bcrvIbbtc.approveContractAccess(ibbtc_vault_zap, {"from": bcrvIbbtc.governance()})

    # Grant role to mint wibbtc
    role = wibbtc.APPROVED_ACCOUNT_ROLE()
    admin = wibbtc.getRoleMember(wibbtc.getRoleAdmin(role), 0)
    wibbtc.grantRole(role, curve_ibbtc_zap, {"from": admin})


# TODO: Add permissions tests and more balance checks


def test_deposit_flow(deployer, ibbtc, renbtc, wbtc, sbtc, bcrvIbbtc, ibbtc_vault_zap):
    # add ibbtc liquidity
    amounts = [
        ibbtc.balanceOf(deployer) // 10,
        renbtc.balanceOf(deployer) // 10,
        wbtc.balanceOf(deployer) // 10,
        sbtc.balanceOf(deployer) // 10,
    ]

    shares = bcrvIbbtc.balanceOf(deployer)
    ibbtc_vault_zap.deposit(amounts, 0, {"from": deployer})

    assert bcrvIbbtc.balanceOf(deployer) > shares
