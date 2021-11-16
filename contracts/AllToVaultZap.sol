// SPDX-License-Identifier: MIT

pragma solidity ^0.6.12;

import "@openzeppelin-contracts-upgradeable/math/SafeMathUpgradeable.sol";
import "@openzeppelin-contracts-upgradeable/token/ERC20/IERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/token/ERC20/SafeERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/utils/AddressUpgradeable.sol";
import "@openzeppelin-contracts-upgradeable/utils/PausableUpgradeable.sol";

import "../interfaces/badger/ICurveZap.sol";
import "../interfaces/badger/ISett.sol";

contract AllToVaultZap is PausableUpgradeable {
    using SafeERC20Upgradeable for IERC20Upgradeable;
    using AddressUpgradeable for address;
    using SafeMathUpgradeable for uint256;

    address public guardian;
    address public governance;

    address public constant CURVE_IBBTC_METAPOOL =
        0xFbdCA68601f835b27790D98bbb8eC7f05FDEaA9B; // Ibbtc crv metapool
    ICurveZap public constant CURVE_IBBTC_DEPOSIT_ZAP =
        ICurveZap(0xbba4b444FD10302251d9F5797E763b0d912286A1); // Ibbtc crv deposit zap

    ISett public constant IBBTC_VAULT =
        ISett(0xaE96fF08771a109dc6650a1BdCa62F2d558E40af); // Ibbtc crv lp badger vault

    IERC20Upgradeable[] public ASSETS = [
        IERC20Upgradeable(0xc4E15973E6fF2A35cC804c2CF9D2a1b817a8b40F), // ibbtc
        IERC20Upgradeable(0xEB4C2781e4ebA804CE9a9803C67d0893436bB27D), // renbtc
        IERC20Upgradeable(0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599), // wbtc
        IERC20Upgradeable(0xfE18be6b3Bd88A2D2A7f928d00292E7a9963CfC6) // sbtc
    ];

    event GovernanceUpdated(address indexed newGovernanceAddress);
    event GuardianshipTransferred(address indexed newGuardianAddress);

    function initialize(address _guardian, address _governance)
        public
        initializer
        whenNotPaused
    {
        require(_guardian != address(0)); // dev: 0 address
        require(_governance != address(0)); // dev: 0 address

        guardian = _guardian;
        governance = _governance;

        // ibbtc, renbtc, wbtc, sbtc approvals for ibbtc curve zap
        for (uint256 i = 0; i < 4; i++) {
            ASSETS[i].safeApprove(address(CURVE_IBBTC_DEPOSIT_ZAP), type(uint256).max);
        }

        /// @dev approve the metapool tokens for vault to use
        /// @notice the address of metapool token is same as metapool address
        IERC20Upgradeable(CURVE_IBBTC_METAPOOL).safeApprove(
            address(IBBTC_VAULT),
            type(uint256).max
        );
    }

    /// ===== Modifiers =====

    function _onlyGovernance() internal view {
        require(msg.sender == governance, "onlyGovernance");
    }

    function _onlyGovernanceOrGuardian() internal view {
        require(
            msg.sender == governance || msg.sender == guardian,
            "onlyGovernanceOrGuardian"
        );
    }

    /// ===== Permissioned Actions: Governance or Guardian =====

    function pause() external {
        _onlyGovernanceOrGuardian();
        _pause();
    }

    /// ===== Permissioned Actions: Governance =====

    function unpause() external {
        _onlyGovernance();
        _unpause();
    }

    function setGuardian(address _guardian) external {
        _onlyGovernance();
        guardian = _guardian;
        emit GuardianshipTransferred(guardian);
    }

    function setGovernance(address _governance) external {
        _onlyGovernance();
        governance = _governance;
        emit GovernanceUpdated(governance);
    }

    /// ===== Public Functions =====

    function deposit(uint256[4] calldata _amounts, uint256 _minOut)
        public
        whenNotPaused
    {
        // Not block locked by setts
        require(
            IBBTC_VAULT.blockLock(address(this)) < block.number,
            "blockLocked"
        );

        for (uint256 i = 0; i < 4; i++) {
            if (_amounts[i] > 0) {
                ASSETS[i].safeTransferFrom(
                    msg.sender,
                    address(this),
                    _amounts[i]
                );
            }
        }

        // deposit into the crv by using ibbtc curve deposit zap
        uint256 vaultDepositAmount = CURVE_IBBTC_DEPOSIT_ZAP.add_liquidity(
            CURVE_IBBTC_METAPOOL,
            _amounts,
            0,
            address(this)
        );

        uint256 balanceBefore = IBBTC_VAULT.balanceOf(msg.sender);
        // deposit crv lp tokens into vault
        IBBTC_VAULT.depositFor(msg.sender, vaultDepositAmount);
        uint256 balanceAfter = IBBTC_VAULT.balanceOf(msg.sender);

        require(balanceAfter.sub(balanceBefore) >= _minOut, "Slippage Check");
    }
}
