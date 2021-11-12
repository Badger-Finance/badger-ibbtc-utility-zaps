# TODO: Add permissions tests and more balance checks


def test_deposit_flow(
    deployer, ibbtc, renbtc, wbtc, sbtc, ibbtc_vault, ibbtc_vault_zap
):
    # add ibbtc liquidity
    amounts = [
        ibbtc.balanceOf(deployer) // 10,
        renbtc.balanceOf(deployer) // 10,
        wbtc.balanceOf(deployer) // 10,
        sbtc.balanceOf(deployer) // 10,
    ]

    shares = ibbtc_vault.balanceOf(deployer)
    ibbtc_vault_zap.deposit(amounts, {"from": deployer})
    assert ibbtc_vault.balanceOf(deployer) > shares
