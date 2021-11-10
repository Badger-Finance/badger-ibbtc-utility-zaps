// SPDX-License-Identifier: MIT
pragma solidity >=0.5.0 <0.8.0;

interface ICurveZap {
    function add_liquidity(
        address _pool,
        uint256[] memory _deposit_amounts, // @notice 4 because we have ibbtc, renBTC, wBTC, sBTC
        uint256 _min_mint_amount,
        address _receiver
    ) external returns (uint256);
}