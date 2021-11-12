// SPDX-License-Identifier: MIT
pragma solidity >=0.5.0 <0.8.0;

interface IPeak {
    function portfolioValue() external view returns (uint256);
}

interface IBadgerSettPeak is IPeak {
    function mint(
        uint256 poolId,
        uint256 inAmount,
        bytes32[] calldata merkleProof
    ) external returns (uint256 outAmount);

    function calcMint(uint256 poolId, uint256 inAmount)
        external
        view
        returns (uint256 bBTC, uint256 fee);

    function redeem(uint256 poolId, uint256 inAmount)
        external
        returns (uint256 outAmount);

    function calcRedeem(uint256 poolId, uint256 bBtc)
        external
        view
        returns (
            uint256 sett,
            uint256 fee,
            uint256 max
        );
}
