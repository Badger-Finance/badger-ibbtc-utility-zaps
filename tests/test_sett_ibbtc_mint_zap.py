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
def ibbtc_mint_zap(Contract):
    yield Contract("0xe8E40093017A3A55B5c2BC3E9CA6a4d208c07734")


@pytest.fixture(autouse=True)
def sett_ibbtc_zap(SettToRenIbbtcZap, deployer):
    zap = SettToRenIbbtcZap.deploy({"from": deployer})
    zap.initialize(deployer, deployer, {"from": deployer})
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
def sett(Contract, request, deployer):
    vault = Contract(request.param["contract"])

    # Get max 1 share from whale
    amount = min(10 ** vault.decimals(), vault.balanceOf(request.param["whale"]))
    vault.transfer(deployer, amount, {"from": request.param["whale"]})

    yield vault


@pytest.fixture(autouse=True)
def set_zap_approvals(web3, sett, sett_ibbtc_zap, deployer):
    # Approve zap for contract access
    if web3.toChecksumAddress(sett.address) != web3.toChecksumAddress(
        SETTS["byvWbtc"]["contract"]
    ):
        sett.approveContractAccess(sett_ibbtc_zap, {"from": sett.governance()})
    # Approve zap to spend sett tokens
    sett.approve(sett_ibbtc_zap, MAX_UINT256, {"from": deployer})


# TODO: Add permissions tests and more balance checks


@pytest.mark.parametrize(
    "sett_idx, sett",
    [(v["idx"], v) for v in SETTS.values()],
    indirect=["sett"],
)
def test_zap_calc_mint(sett_ibbtc_zap, sett_idx, sett):
    assert sett_ibbtc_zap.calcMint(0, sett_idx) == 0
    assert sett_ibbtc_zap.calcMint(10 ** sett.decimals(), sett_idx) > 0


@pytest.mark.parametrize(
    "sett_idx, sett",
    [(v["idx"], v) for v in SETTS.values()],
    indirect=["sett"],
)
def test_zap_mint(deployer, ibbtc, sett_ibbtc_zap, sett_idx, sett):
    balance_before = ibbtc.balanceOf(deployer)

    sett_ibbtc_zap.mint(sett.balanceOf(deployer), sett_idx, 0, {"from": deployer})

    assert ibbtc.balanceOf(deployer) > balance_before
