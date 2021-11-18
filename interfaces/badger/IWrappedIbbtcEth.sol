// SPDX-License-Identifier: MIT
pragma solidity >=0.5.0 <0.8.0;

interface IWrappedIbbtcEth {
    function sharesToBalance(uint256 shares) external view returns (uint256);
}
