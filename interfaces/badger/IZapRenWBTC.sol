// SPDX-License-Identifier: MIT
pragma solidity >=0.5.0 <0.8.0;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IZapRenWBTC {
    function mint(IERC20 token, uint256 amount, uint256 poolId, uint256 idx, uint256 minOut) external returns (uint256);
    function calcMint(address token, uint256 amount) external view returns (uint256 poolId, uint256 idx, uint256 bBTC, uint256 fee);
}