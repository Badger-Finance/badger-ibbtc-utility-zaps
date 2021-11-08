// SPDX-License-Identifier: MIT

pragma solidity ^0.6.12;

import "@openzeppelin-contracts-upgradeable/token/ERC20/IERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/math/SafeMathUpgradeable.sol";
import "@openzeppelin-contracts-upgradeable/utils/AddressUpgradeable.sol";
import "@openzeppelin-contracts-upgradeable/token/ERC20/SafeERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/token/ERC20/ERC20Upgradeable.sol";

import "../interfaces/badger/ISett.sol";


contract BadgeribbtcZap {
    
    using SafeERC20Upgradeable for IERC20Upgradeable;
    using AddressUpgradeable for address;
    using SafeMathUpgradeable for uint256;

    address public constant CURVE_IBBTC_METAPOOL = 0xBA12222222228d8Ba445958a75a0704d566BF2C8; // TODO: set address to ibbtc crv metapool
    address public constant CURVE_IBBTC_DEPOSIT_ZAP = 0xBA12222222228d8Ba445958a75a0704d566BF2C8; // TODO: set address to ibbtc crv deposit zap

    IVault vault = ISett(0xBA12222222228d8Ba445958a75a0704d566BF2C8); // TODO: set address to ibbtc crv lp badger vault
    IERC20Upgradeable public ibbtc = IERC20Upgradeable(0xc4E15973E6fF2A35cC804c2CF9D2a1b817a8b40F); // ibbtc token

    function deposit(uint256 _amount) {
        
        // before depositing approve the tokens for zap to use ... check that ?

        uint256 _before = ibbtc.balanceOf(address(this));
        token.safeTransferFrom(msg.sender, address(this), _amount);
        uint256 _after = ibbtc.balanceOf(address(this));

        require(_after - _before == _amount); // dev: _amount error

        // deposit ibbtc into the crv by using ibbtc curve deposit zap
        uint256[] memory _deposit_amounts = new uint256[](4);
        _deposit_amounts[0] = _amount;

        ZAP(CURVE_IBBTC_DEPOSIT_ZAP).add_liquidity(CURVE_IBBTC_METAPOOL, _deposit_amounts, 0); // change _min_mint_amount from 0
        
        // // approve tokens for vault to use
        // uint256 _vault_deposit_amount = lptoken.balanceOf(address(this));
        // // deposit crv lp tokens into vault
        // vault.depositFor(msg.sender, _vault_deposit_amount);

    }

}