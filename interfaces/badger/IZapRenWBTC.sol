// SPDX-License-Identifier: MIT
pragma solidity >=0.5.0 <0.8.0;

interface IZapRenWBTC {
    function calcMint(address token, uint256 amount)
        external
        view
        returns (
            uint256 poolId,
            uint256 idx,
            uint256 bBTC,
            uint256 fee
        );

    function mint(
        address token,
        uint256 amount,
        uint256 poolId,
        uint256 idx,
        uint256 minOut
    ) external returns (uint256);
}
