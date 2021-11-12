// SPDX-License-Identifier: MIT

pragma solidity ^0.6.12;

import "@openzeppelin-contracts-upgradeable/math/SafeMathUpgradeable.sol";
import "@openzeppelin-contracts-upgradeable/token/ERC20/IERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/token/ERC20/SafeERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/utils/AddressUpgradeable.sol";
import "@openzeppelin-contracts-upgradeable/utils/PausableUpgradeable.sol";

import "../interfaces/badger/ICurveZap.sol";
import {IBadgerSettPeak} from "../interfaces/badger/IPeak.sol";
import "../interfaces/badger/ISett.sol";
import "../interfaces/badger/IZapRenWBTC.sol";
import "../interfaces/curve/ICurveFi.sol";

contract SettToRenIbbtcZap is PausableUpgradeable {
    using SafeERC20Upgradeable for IERC20Upgradeable;
    using AddressUpgradeable for address;
    using SafeMathUpgradeable for uint256;

    address public governance;

    struct SettConfig {
        ISett sett;
        ICurveFi curvePool;
        IERC20Upgradeable lpToken;
        IERC20Upgradeable outputToken;
    }
    Sett[5] public pools;

    function initialize(address _governance) public {
        require(_governance != address(0)); // dev: 0 address
        governance = _governance;

        // TODO: Add sett configs and approvals
        // setts[0] = Sett({ });
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

    /// ===== Internal Implementations =====

    function _renZapToIbbtc(uint256[2] memory _amounts)
        internal
        returns (uint256)
    {
        CURVE_REN_POOL.add_liquidity(_amounts, 0);
        RENCRV_VAULT.deposit(RENCRV_TOKEN.balanceOf(address(this)));
        return
            SETT_PEAK.mint(
                0,
                RENCRV_VAULT.balanceOf(address(this)),
                new bytes32[](0)
            );
    }

    /// ===== Public Functions =====
    function calcMintOut(uint256 _shares, address _bTokenIdx) public view {
        // Withdraw (0.1% withdrawal fee)
        ISett sett = ISett(_bToken);
        uint256 crvLpAmount = _shares.mul(sett.balance()).div(
            sett.totalSupply()
        );

        // Remove from pool (calc_out)
        uint256 wbtcAmount = ICurveFi().calc_withdraw_one_coin(
            _token_amount,
            i
        );

        // Zap (calcMint)
        IIbbtcMintZap zap = IIbbtcMintZap(CURVE_IBBTC_DEPOSIT_ZAP);
        return zap.calcMint(crvLpAmount, wbtcAmount, new bytes32[](0));
    }

    function mint(
        uint256 _shares,
        uint256 _bTokenIdx,
        uint256 _minOut
    ) public whenNotPaused returns (uint256) {
        // TODO: Revert early on blockLock

        // Withdraw (0.1% withdrawal fee)
        ISett(_bToken).withdraw(_shares);

        // Remove from pool (use sett config)
        uint256 wbtcAmount = ICurveFi().withdraw_imbalance(_token_amount, i);

        // Use other zap to deposit (or copy logic here)
        IIbbtcMintZap zap = IIbbtcMintZap(CURVE_IBBTC_DEPOSIT_ZAP);
        uint256 ibbtcAmount = zap.mint(
            crvLpAmount,
            wbtcAmount,
            new bytes32[](0)
        );

        require(ibbtcAmount >= _minOut, "< minOut");
        ibbtc.safeTransfer(msg.sender, ibbtcAmount);

        return ibbtcAmount;
    }
}
