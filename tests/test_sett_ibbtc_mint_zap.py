import brownie
import pytest
from conftest import MAX_UINT256

SETTS = {
    "byvWbtc": {
        "contract": "0x4b92d19c11435614CD49Af1b589001b7c08cD4D5",
        "whale": "0x53461E4fddcC1385f1256Ae24ce3505Be664f249",
    },
    "bcrvSbtc": {
        "contract": "0xd04c48A53c111300aD41190D63681ed3dAd998eC",
        "whale": "0x81EEc27E8e98289732ac106632047896E6592604",
    },
    "bcrvTbtc": {
        "contract": "0xb9D076fDe463dbc9f915E5392F807315Bf940334",
        "whale": "0xEE9F84Af6a8251Eb5ffDe38c5F056bc72d3b3DD0",
    },
    "bcrvHbtc": {
        "contract": "0x8c76970747afd5398e958bDfadA4cf0B9FcA16c4",
        "whale": "0xbd9795a14035dBA41BccFC563329aA6b197A0cBB",
    },
    "bcrvBbtc": {
        "contract": "0x5Dce29e92b1b939F8E8C60DcF15BDE82A85be4a9",
        "whale": "0x433CFfFeA18b811017856e9659ada4e6B441312d",
    },
}

MAX_SLIPPAGE = 0.01


@pytest.fixture(scope="session")
def guardian(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def rando(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def ibbtc_mint_zap(Contract):
    yield Contract("0xe8E40093017A3A55B5c2BC3E9CA6a4d208c07734")


@pytest.fixture(autouse=True)
def sett_ibbtc_zap(SettToRenIbbtcZap, deployer, guardian):
    zap = SettToRenIbbtcZap.deploy({"from": deployer})
    zap.initialize(deployer, guardian, {"from": deployer})
    yield zap


@pytest.fixture(autouse=True)
def set_contract_approvals(
    ibbtc_mint_zap, sett_ibbtc_zap, bcrvRenbtc, badger_sett_peak, ibbtc_guestlist
):
    ibbtc_mint_zap.approveContractAccess(
        sett_ibbtc_zap, {"from": ibbtc_mint_zap.governance()}
    )
    bcrvRenbtc.approveContractAccess(ibbtc_mint_zap, {"from": bcrvRenbtc.governance()})
    badger_sett_peak.approveContractAccess(
        ibbtc_mint_zap, {"from": badger_sett_peak.owner()}
    )
    ibbtc_guestlist.setGuests(
        [ibbtc_mint_zap], [True], {"from": ibbtc_guestlist.owner()}
    )


@pytest.fixture()
def sett(web3, Contract, request, sett_ibbtc_zap, deployer):
    vault = Contract(request.param["contract"])

    # Get max 1 share from whale
    amount = min(10 ** vault.decimals(), vault.balanceOf(request.param["whale"]))
    vault.transfer(deployer, amount, {"from": request.param["whale"]})

    # Approve zap for contract access
    if web3.toChecksumAddress(vault.address) != web3.toChecksumAddress(
        SETTS["byvWbtc"]["contract"]
    ):
        vault.approveContractAccess(sett_ibbtc_zap, {"from": vault.governance()})
    # Approve zap to spend sett tokens
    vault.approve(sett_ibbtc_zap, MAX_UINT256, {"from": deployer})

    yield vault


def test_set_guardian(sett_ibbtc_zap, deployer, guardian, rando):
    with brownie.reverts("onlyGovernance"):
        sett_ibbtc_zap.setGuardian(rando, {"from": guardian})

    with brownie.reverts("onlyGovernanceOrGuardian"):
        sett_ibbtc_zap.pause({"from": rando})

    sett_ibbtc_zap.setGuardian(rando, {"from": deployer})

    assert sett_ibbtc_zap.guardian() == rando.address

    sett_ibbtc_zap.pause({"from": rando})


def test_set_goverannce(sett_ibbtc_zap, deployer, guardian, rando):
    with brownie.reverts("onlyGovernance"):
        sett_ibbtc_zap.setGovernance(rando, {"from": guardian})

    sett_ibbtc_zap.setGovernance(rando, {"from": deployer})

    assert sett_ibbtc_zap.governance() == rando.address

    sett_ibbtc_zap.pause({"from": rando})

    with brownie.reverts("onlyGovernance"):
        sett_ibbtc_zap.unpause({"from": deployer})


def test_pausing(deployer, sett_ibbtc_zap, guardian, rando):
    assert sett_ibbtc_zap.paused() == False

    with brownie.reverts("onlyGovernanceOrGuardian"):
        sett_ibbtc_zap.pause({"from": rando})

    sett_ibbtc_zap.pause({"from": guardian})

    assert sett_ibbtc_zap.paused()

    with brownie.reverts("onlyGovernance"):
        sett_ibbtc_zap.unpause({"from": guardian})

    with brownie.reverts():
        sett_ibbtc_zap.mint(SETTS["bcrvSbtc"]["contract"], 1, 0, {"from": deployer})

    sett_ibbtc_zap.unpause({"from": deployer})

    assert sett_ibbtc_zap.paused() == False


@pytest.mark.parametrize("sett", [(SETTS["bcrvSbtc"])], indirect=True)
def test_set_zap_config(sett_ibbtc_zap, sett, ibbtc, renbtc, deployer, rando):
    _, curve_pool, withdraw_token, withdraw_ix = sett_ibbtc_zap.zapConfigs(sett)

    with brownie.reverts("onlyGovernance"):
        sett_ibbtc_zap.setZapConfig(
            sett, curve_pool, withdraw_token, withdraw_ix, {"from": rando}
        )

    sett_ibbtc_zap.setZapConfigWithdrawToken(sett, renbtc, 0, {"from": deployer})

    balance_before = ibbtc.balanceOf(deployer)

    amount_in = sett.balanceOf(deployer)

    tx = sett_ibbtc_zap.mint(sett, amount_in, 0, {"from": deployer})
    amount_out = tx.return_value

    balance_after = ibbtc.balanceOf(deployer)

    assert balance_after - balance_before == amount_out

    print(f"In: {amount_in} | Out: {amount_out}")


@pytest.mark.parametrize(
    "sett",
    [
        {
            "contract": "0x55912D0Cf83B75c492E761932ABc4DB4a5CB1b17",
            "whale": "0xDe4288cbc81605E615e40aa0E171F74594671e53",
        },
    ],
    indirect=True,
)
def test_add_zap_config(sett, sett_ibbtc_zap, wbtc, ibbtc, deployer, rando):
    bcrvPbtc = {
        "pool": "0x11F419AdAbbFF8d595E7d5b223eee3863Bb3902C",
        "withdrawToken": wbtc,
        "withdrawTokenIdx": 2,
        "whale": "0xDe4288cbc81605E615e40aa0E171F74594671e53",
    }

    with brownie.reverts("onlyGovernance"):
        sett_ibbtc_zap.setZapConfig(
            sett,
            bcrvPbtc["pool"],
            bcrvPbtc["withdrawToken"],
            bcrvPbtc["withdrawTokenIdx"],
            {"from": rando},
        )

    sett_ibbtc_zap.setZapConfig(
        sett,
        bcrvPbtc["pool"],
        bcrvPbtc["withdrawToken"],
        bcrvPbtc["withdrawTokenIdx"],
        {"from": deployer},
    )

    balance_before = ibbtc.balanceOf(deployer)

    amount_in = sett.balanceOf(deployer)

    tx = sett_ibbtc_zap.mint(sett, amount_in, 0, {"from": deployer})
    amount_out = tx.return_value

    balance_after = ibbtc.balanceOf(deployer)

    assert balance_after - balance_before == amount_out

    print(f"In: {amount_in} | Out: {amount_out}")


@pytest.mark.parametrize("sett", SETTS.values(), indirect=True)
def test_zap_calc_mint(sett_ibbtc_zap, sett):
    assert sett_ibbtc_zap.calcMint(sett, 0) == 0

    amount_in = 10 ** sett.decimals()
    amount_out = sett_ibbtc_zap.calcMint(sett, amount_in)

    print(f"In: {amount_in} | Out: {amount_out}")

    assert amount_out > 0


@pytest.mark.parametrize("sett", SETTS.values(), indirect=True)
def test_zap_mint(deployer, ibbtc, sett_ibbtc_zap, sett):
    balance_before = ibbtc.balanceOf(deployer)

    amount_in = sett.balanceOf(deployer)

    amount_out_expected = sett_ibbtc_zap.calcMint(sett, amount_in, {"from": deployer})
    tx = sett_ibbtc_zap.mint(sett, amount_in, 0, {"from": deployer})
    amount_out = tx.return_value

    balance_after = ibbtc.balanceOf(deployer)

    assert balance_after - balance_before == amount_out

    print(f"In: {amount_in} | Out: {amount_out}")

    assert float(amount_out) == pytest.approx(amount_out_expected, rel=MAX_SLIPPAGE)
