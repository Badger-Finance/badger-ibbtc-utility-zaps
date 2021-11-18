// SPDX-License-Identifier: MIT
pragma solidity >=0.5.0 <0.8.0;

interface ICurveMeta {
    function get_virtual_price() external view returns (uint256);
}
