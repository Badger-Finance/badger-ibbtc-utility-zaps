// SPDX-License-Identifier: MIT

pragma solidity ^0.6.12;

import "@openzeppelin-contracts-upgradeable/token/ERC20/IERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/math/SafeMathUpgradeable.sol";
import "@openzeppelin-contracts-upgradeable/utils/AddressUpgradeable.sol";
import "@openzeppelin-contracts-upgradeable/token/ERC20/SafeERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/token/ERC20/ERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/utils/PausableUpgradeable.sol";

import "../interfaces/badger/ISett.sol";
import "../interfaces/badger/ICurveZap.sol";


contract BadgerVaultZap is PausableUpgradeable {
    
    using SafeERC20Upgradeable for IERC20Upgradeable;
    using AddressUpgradeable for address;
    using SafeMathUpgradeable for uint256;

    address public governance;
    address public constant CURVE_IBBTC_METAPOOL = 0xFbdCA68601f835b27790D98bbb8eC7f05FDEaA9B; // address of ibbtc crv metapool
    address public constant CURVE_IBBTC_DEPOSIT_ZAP = 0xbba4b444FD10302251d9F5797E763b0d912286A1; // address of ibbtc crv deposit zap
    address public constant VAULT = 0xaE96fF08771a109dc6650a1BdCa62F2d558E40af; // address of ibbtc crv lp badger vault
    
    address[] public ASSETS = [0xc4E15973E6fF2A35cC804c2CF9D2a1b817a8b40F /* ibbtc */, 0xEB4C2781e4ebA804CE9a9803C67d0893436bB27D /* renbtc */, 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599 /* wbtc */, 0xfE18be6b3Bd88A2D2A7f928d00292E7a9963CfC6 /* sbtc */];

    function initialize(address _governance) public {
        require(_governance != address(0)); // dev: 0 address
        governance = _governance;

        /// @dev approve the metapool tokens for vault to use
        /// @notice the address of metapool token is same as metapool address
        IERC20Upgradeable(CURVE_IBBTC_METAPOOL).safeApprove(VAULT, type(uint256).max);
    }

    /// ===== Modifiers =====

    function _onlyGovernance() internal view {
        require(msg.sender == governance, "onlyGovernance");
    }

    /// ===== Permissioned Actions: Governance =====

    function pause() external {
        _onlyGovernance();
        _pause();
    }

    function unpause() external {
        _onlyGovernance();
        _unpause();
    }

    /// ===== Public Functions =====

    function deposit(uint256[] memory _amounts) public whenNotPaused {
        
        uint256[] memory depositAmounts = new uint256[](4);

        for (int i=0; i<4; i++) {
            IERC20Upgradeable(ASSETS[i]).safeTransferFrom(msg.sender, address(this), _amounts[i]);
            depositAmounts[i] = _amount;
        }

        // deposit into the crv by using ibbtc curve deposit zap
        uint256 vaultDepositAmount = ICurveZap(CURVE_IBBTC_DEPOSIT_ZAP).add_liquidity(CURVE_IBBTC_METAPOOL, depositAmounts, 0, address(this));
        
        // deposit crv lp tokens into vault
        /// @notice For SettV4 depositFor _lockForBlock for receipient ie. msg.sender (patron) to this function ie. deposit
        /// therefore the zap will not be locked for the block and multiple tx's can happen in the same block
        ISett(VAULT).depositFor(msg.sender, vaultDepositAmount);

    }
 
}