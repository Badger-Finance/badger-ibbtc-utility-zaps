// SPDX-License-Identifier: MIT
pragma solidity >=0.5.0 <0.8.0;

interface ICurveFi {
    function add_liquidity(uint256[2] calldata amounts, uint256 min_mint_amount)
        external;

    function calc_token_amount(uint256[2] calldata amounts, bool isDeposit)
        external
        view
        returns (uint256);

    function remove_liquidity_one_coin(
        uint256 _token_amount,
        int128 i,
        uint256 min_amount
    ) external;

    function calc_withdraw_one_coin(uint256 _token_amount, int128 i)
        external
        view
        returns (uint256);
}
