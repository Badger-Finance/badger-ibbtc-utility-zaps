import brownie
import pytest
from conftest import MAX_UINT256

SETTS = {
    "byvWbtc": {
        "idx": 0,
        "contract": "0x4b92d19c11435614CD49Af1b589001b7c08cD4D5",
        "whale": "0x53461E4fddcC1385f1256Ae24ce3505Be664f249",
    },
    "bcrvSbtc": {
        "idx": 1,
        "contract": "0xd04c48A53c111300aD41190D63681ed3dAd998eC",
        "whale": "0x81EEc27E8e98289732ac106632047896E6592604",
    },
    "bcrvTbtc": {
        "idx": 2,
        "contract": "0xb9D076fDe463dbc9f915E5392F807315Bf940334",
        "whale": "0xEE9F84Af6a8251Eb5ffDe38c5F056bc72d3b3DD0",
    },
    "bcrvHbtc": {
        "idx": 3,
        "contract": "0x8c76970747afd5398e958bDfadA4cf0B9FcA16c4",
        "whale": "0xbd9795a14035dBA41BccFC563329aA6b197A0cBB",
    },
    "bcrvBbtc": {
        "idx": 4,
        "contract": "0x5Dce29e92b1b939F8E8C60DcF15BDE82A85be4a9",
        "whale": "0x433CFfFeA18b811017856e9659ada4e6B441312d",
    },
}


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


@pytest.fixture(scope="session")
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
        sett_ibbtc_zap.mint(1, 0, 0, {"from": deployer})

    sett_ibbtc_zap.unpause({"from": deployer})

    assert sett_ibbtc_zap.paused() == False


@pytest.mark.parametrize(
    "sett_idx, sett",
    [(SETTS["bcrvSbtc"]["idx"], SETTS["bcrvSbtc"])],
    indirect=["sett"],
)
def test_set_zap_config(sett_ibbtc_zap, sett, sett_idx, ibbtc, renbtc, deployer, rando):
    config = sett_ibbtc_zap.zapConfigs(sett_idx)
    sett_address, token, curve_pool, _, _ = config

    assert sett_address == sett.address

    with brownie.reverts("onlyGovernance"):
        sett_ibbtc_zap.setZapConfig(sett_idx, *config, {"from": rando})

    sett_ibbtc_zap.setZapConfig(
        sett_idx, sett, token, curve_pool, renbtc, 0, {"from": deployer}
    )

    balance_before = ibbtc.balanceOf(deployer)

    amount_in = sett.balanceOf(deployer)

    tx = sett_ibbtc_zap.mint(amount_in, sett_idx, 0, {"from": deployer})
    amount_out = tx.return_value

    balance_after = ibbtc.balanceOf(deployer)

    assert balance_after - balance_before == amount_out

    print(f"In: {amount_in} | Out: {amount_out}")


@pytest.mark.parametrize(
    "sett_idx, sett",
    [
        (
            5,
            {
                "contract": "0x55912D0Cf83B75c492E761932ABc4DB4a5CB1b17",
                "whale": "0xDe4288cbc81605E615e40aa0E171F74594671e53",
            },
        )
    ],
    indirect=["sett"],
)
def test_add_zap_config(sett_idx, sett, sett_ibbtc_zap, wbtc, ibbtc, deployer, rando):
    bcrvPbtc = {
        "token": "0xDE5331AC4B3630f94853Ff322B66407e0D6331E8",
        "pool": "0x11F419AdAbbFF8d595E7d5b223eee3863Bb3902C",
        "withdrawToken": wbtc,
        "withdrawTokenIdx": 2,
        "whale": "0xDe4288cbc81605E615e40aa0E171F74594671e53",
    }

    with brownie.reverts("onlyGovernance"):
        sett_ibbtc_zap.addZapConfig(
            sett,
            bcrvPbtc["token"],
            bcrvPbtc["pool"],
            bcrvPbtc["withdrawToken"],
            bcrvPbtc["withdrawTokenIdx"],
            {"from": rando},
        )

    sett_ibbtc_zap.addZapConfig(
        sett,
        bcrvPbtc["token"],
        bcrvPbtc["pool"],
        bcrvPbtc["withdrawToken"],
        bcrvPbtc["withdrawTokenIdx"],
        {"from": deployer},
    )

    balance_before = ibbtc.balanceOf(deployer)

    amount_in = sett.balanceOf(deployer)

    tx = sett_ibbtc_zap.mint(amount_in, sett_idx, 0, {"from": deployer})
    amount_out = tx.return_value

    balance_after = ibbtc.balanceOf(deployer)

    assert balance_after - balance_before == amount_out

    print(f"In: {amount_in} | Out: {amount_out}")


@pytest.mark.parametrize(
    "sett_idx, sett",
    [(v["idx"], v) for v in SETTS.values()],
    indirect=["sett"],
)
def test_zap_calc_mint(sett_ibbtc_zap, sett_idx, sett):
    assert sett_ibbtc_zap.calcMint(0, sett_idx) == 0

    amount_in = 10 ** sett.decimals()
    amount_out = sett_ibbtc_zap.calcMint(amount_in, sett_idx)

    print(f"In: {amount_in} | Out: {amount_out}")

    assert amount_out > 0


@pytest.mark.parametrize(
    "sett_idx, sett",
    [(v["idx"], v) for v in SETTS.values()],
    indirect=["sett"],
)
def test_zap_mint(deployer, ibbtc, sett_ibbtc_zap, sett_idx, sett):
    balance_before = ibbtc.balanceOf(deployer)

    amount_in = sett.balanceOf(deployer)

    tx = sett_ibbtc_zap.mint(amount_in, sett_idx, 0, {"from": deployer})
    amount_out = tx.return_value

    balance_after = ibbtc.balanceOf(deployer)

    assert balance_after - balance_before == amount_out

    print(f"In: {amount_in} | Out: {amount_out}")
