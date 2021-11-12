import pytest

MAX_UINT256 = 2 ** 256 - 1


@pytest.fixture(scope="session")
def weth(interface):
    yield interface.ERC20("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")


@pytest.fixture(scope="session")
def wbtc(interface):
    yield interface.ERC20("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")


@pytest.fixture(scope="session")
def renbtc(interface):
    yield interface.ERC20("0xEB4C2781e4ebA804CE9a9803C67d0893436bB27D")


@pytest.fixture(scope="session")
def sbtc(interface):
    yield interface.ERC20("0xfE18be6b3Bd88A2D2A7f928d00292E7a9963CfC6")


@pytest.fixture(scope="session")
def ibbtc(Contract):
    yield Contract("0xc4E15973E6fF2A35cC804c2CF9D2a1b817a8b40F")


@pytest.fixture(scope="session")
def sbtc_pool(Contract):
    yield Contract("0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714")


@pytest.fixture(scope="session")
def router(Contract):
    yield Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")


@pytest.fixture(scope="session")
def deployer(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def ren_vault(Contract):
    yield Contract("0x6dEf55d2e18486B9dDfaA075bc4e4EE0B28c1545")


@pytest.fixture(scope="session")
def badger_sett_peak(Contract):
    yield Contract("0x41671BA1abcbA387b9b2B752c205e22e916BE6e3")


@pytest.fixture(scope="session")
def ibbtc_vault(Contract):
    yield Contract("0xaE96fF08771a109dc6650a1BdCa62F2d558E40af")


# @pytest.fixture(scope="session")
# def ibbtc_mint_zap(Contract):
#     yield Contract("0xe8E40093017A3A55B5c2BC3E9CA6a4d208c07734")


@pytest.fixture(scope="session")
def ibbtc_guestlist(Contract):
    yield Contract("0x1B4233242BeCfd8C1d517158406Bf0Ed19Be2AFe")


@pytest.fixture(autouse=True)
def ibbtc_vault_zap(IbbtcVaultZap, deployer):
    zap = IbbtcVaultZap.deploy({"from": deployer})
    zap.initialize(deployer, {"from": deployer})
    yield zap


@pytest.fixture(autouse=True)
def get_tokens(deployer, router, weth, ibbtc, wbtc, sbtc_pool):
    # Get ibbtc
    router.swapETHForExactTokens(
        10 ** ibbtc.decimals(),
        [weth, wbtc, ibbtc],
        deployer,
        MAX_UINT256,
        {"from": deployer, "value": deployer.balance()},
    )

    # Get wbtc
    router.swapETHForExactTokens(
        3 * 10 ** wbtc.decimals(),
        [weth, wbtc],
        deployer,
        MAX_UINT256,
        {"from": deployer, "value": deployer.balance()},
    )
    # Get renbtc, sbtc from curve sbtc pool
    wbtc.approve(sbtc_pool, MAX_UINT256, {"from": deployer})
    # renbtc
    sbtc_pool.exchange(1, 0, 10 ** wbtc.decimals(), 0, {"from": deployer})
    # sbtc
    sbtc_pool.exchange(1, 2, 10 ** wbtc.decimals(), 0, {"from": deployer})


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
    ren_vault,
    # ibbtc_mint_zap,
    ibbtc_vault_zap,
    ibbtc_vault,
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
    ren_vault.approveContractAccess(ibbtc_vault_zap, {"from": ren_vault.governance()})
    ibbtc_vault.approveContractAccess(
        ibbtc_vault_zap, {"from": ibbtc_vault.governance()}
    )


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass
