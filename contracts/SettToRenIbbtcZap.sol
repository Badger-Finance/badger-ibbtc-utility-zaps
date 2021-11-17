// SPDX-License-Identifier: MIT

pragma solidity ^0.6.12;

import "@openzeppelin-contracts-upgradeable/math/SafeMathUpgradeable.sol";
import "@openzeppelin-contracts-upgradeable/token/ERC20/IERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/token/ERC20/SafeERC20Upgradeable.sol";
import "@openzeppelin-contracts-upgradeable/utils/AddressUpgradeable.sol";
import "@openzeppelin-contracts-upgradeable/utils/PausableUpgradeable.sol";

import "../interfaces/badger/ISett.sol";
import "../interfaces/badger/IZapRenWBTC.sol";
import "../interfaces/curve/ICurveFi.sol";

contract SettToRenIbbtcZap is PausableUpgradeable {
    using SafeERC20Upgradeable for IERC20Upgradeable;
    using AddressUpgradeable for address;
    using SafeMathUpgradeable for uint256;

    address public guardian;
    address public governance;

    struct ZapConfig {
        IERC20Upgradeable token;
        ICurveFi curvePool;
        IERC20Upgradeable withdrawToken;
        int128 withdrawTokenIndex;
    }
    mapping(address => ZapConfig) public settZapConfigs;

    IERC20Upgradeable public constant WBTC =
        IERC20Upgradeable(0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599);
    IERC20Upgradeable public constant RENBTC =
        IERC20Upgradeable(0xEB4C2781e4ebA804CE9a9803C67d0893436bB27D);
    IERC20Upgradeable public constant IBBTC =
        IERC20Upgradeable(0xc4E15973E6fF2A35cC804c2CF9D2a1b817a8b40F);

    IZapRenWBTC public constant IBBTC_MINT_ZAP =
        IZapRenWBTC(0xe8E40093017A3A55B5c2BC3E9CA6a4d208c07734);

    ISett public constant RENCRV_SETT =
        ISett(0x6dEf55d2e18486B9dDfaA075bc4e4EE0B28c1545);
    address public constant WBTC_YEARN_SETT =
        0x4b92d19c11435614CD49Af1b589001b7c08cD4D5;

    uint256 public constant SETT_WITHDRAWAL_FEE = 10;
    uint256 public constant MAX_FEE = 10_000;

    event GovernanceUpdated(address indexed newGovernanceAddress);
    event GuardianshipTransferred(address indexed newGuardianAddress);

    function initialize(address _governance, address _guardian)
        public
        initializer
        whenNotPaused
    {
        require(_guardian != address(0)); // dev: 0 address
        require(_governance != address(0)); // dev: 0 address

        guardian = _guardian;
        governance = _governance;

        // Allow zap to mint ibbtc through wbtc/renbtc
        WBTC.safeApprove(address(IBBTC_MINT_ZAP), type(uint256).max);
        RENBTC.safeApprove(address(IBBTC_MINT_ZAP), type(uint256).max);

        // Add zap configs for setts
        _setZapConfig(
            WBTC_YEARN_SETT, // byvWBTC
            address(WBTC),
            address(0), // No curve pool
            address(WBTC),
            0 // No curve pool
        );
        _setZapConfig(
            0xd04c48A53c111300aD41190D63681ed3dAd998eC, // bcrvSBTC
            0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3, // sbtcCrv
            0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714, // sbtcCrv curve pool
            address(WBTC),
            1 // idx - renbtc: 0, wbtc: 1
        );
        _setZapConfig(
            0xb9D076fDe463dbc9f915E5392F807315Bf940334, // bcrvTBTC
            0x64eda51d3Ad40D56b9dFc5554E06F94e1Dd786Fd, // tbtcCrv
            0xaa82ca713D94bBA7A89CEAB55314F9EfFEdDc78c, // tbtcCrv zap
            address(WBTC),
            2 // idx - renbtc: 1, wbtc: 2
        );
        _setZapConfig(
            0x8c76970747afd5398e958bDfadA4cf0B9FcA16c4, // bcrvHBTC
            0xb19059ebb43466C323583928285a49f558E572Fd, // hbtcCrv
            0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F, // hbtcCrv curve pool
            address(WBTC),
            1 // idx - wbtc: 1
        );
        _setZapConfig(
            0x5Dce29e92b1b939F8E8C60DcF15BDE82A85be4a9, // bcrvBBTC
            0x410e3E86ef427e30B9235497143881f717d93c2A, // bbtcCrv
            0xC45b2EEe6e09cA176Ca3bB5f7eEe7C47bF93c756, // bbtcCrv zap
            address(WBTC),
            2 // idx - renbtc: 1, wbtc: 2
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

    function setZapConfig(
        address _sett,
        address _token,
        address _curvePool,
        address _withdrawToken,
        int128 _withdrawTokenIndex
    ) external {
        _onlyGovernance();
        _setZapConfig(
            _sett,
            _token,
            _curvePool,
            _withdrawToken,
            _withdrawTokenIndex
        );
    }

    function setZapConfigWithdrawToken(
        address _sett,
        address _withdrawToken,
        int128 _withdrawTokenIndex
    ) external {
        _onlyGovernance();

        require(address(settZapConfigs[_sett].token) != address(0));
        require(
            _withdrawToken == address(WBTC) || _withdrawToken == address(RENBTC)
        );

        settZapConfigs[_sett].withdrawToken = IERC20Upgradeable(_withdrawToken);
        settZapConfigs[_sett].withdrawTokenIndex = _withdrawTokenIndex;
    }

    /// ===== Internal Implementations =====

    function _setZapConfig(
        address _sett,
        address _token,
        address _curvePool,
        address _withdrawToken,
        int128 _withdrawTokenIndex
    ) internal {
        require(_sett != address(0));
        require(_token != address(0));
        require(
            _withdrawToken == address(WBTC) || _withdrawToken == address(RENBTC)
        );

        settZapConfigs[_sett] = ZapConfig({
            token: IERC20Upgradeable(_token),
            curvePool: ICurveFi(_curvePool),
            withdrawToken: IERC20Upgradeable(_withdrawToken),
            withdrawTokenIndex: _withdrawTokenIndex
        });
        if (_curvePool != address(0)) {
            IERC20Upgradeable(_token).safeApprove(_curvePool, 0);
            IERC20Upgradeable(_token).safeApprove(
                _curvePool,
                type(uint256).max
            );
        }
    }

    /// ===== Public Functions =====

    function calcMint(address _sett, uint256 _shares)
        public
        view
        returns (uint256)
    {
        ZapConfig memory zapConfig = settZapConfigs[_sett];

        // Check if valid sett
        require(address(zapConfig.token) != address(0));

        if (_shares == 0) {
            return 0;
        }

        // Get price per share
        uint256 pricePerShare;
        if (_sett == WBTC_YEARN_SETT) {
            // byvWBTC doesn't support getPricePerFullShare
            pricePerShare = IYearnSett(_sett).pricePerShare();
        } else {
            pricePerShare = ISett(_sett).getPricePerFullShare();
        }

        // Withdraw (0.1% withdrawal fee)
        uint256 underlyingAmount = _shares
            .mul(pricePerShare)
            .mul(MAX_FEE.sub(SETT_WITHDRAWAL_FEE))
            .div(MAX_FEE)
            .div(10**ISett(_sett).decimals());

        // Underlying of bvyWBTC is WBTC
        uint256 btcAmount = underlyingAmount;

        if (address(zapConfig.curvePool) != address(0)) {
            // Remove renBTC/WBTC from pool (0.04% fee + slippage)
            btcAmount = zapConfig.curvePool.calc_withdraw_one_coin(
                underlyingAmount,
                zapConfig.withdrawTokenIndex
            );
        }

        // Zap (calcMint)
        (, , uint256 ibbtcAmount, ) = IBBTC_MINT_ZAP.calcMint(
            address(zapConfig.withdrawToken),
            btcAmount
        );
        return ibbtcAmount;
    }

    function mint(
        address _sett,
        uint256 _shares,
        uint256 _minOut
    ) public whenNotPaused returns (uint256) {
        ZapConfig memory zapConfig = settZapConfigs[_sett];

        // Valid sett
        require(address(zapConfig.token) != address(0));
        // Non-zero shares
        require(_shares > 0, "No shares");
        // Ensure mint zap isn't block locked
        require(
            RENCRV_SETT.blockLock(address(IBBTC_MINT_ZAP)) < block.number,
            "blockLocked"
        );

        if (_sett != WBTC_YEARN_SETT) {
            // Not block locked by sett
            require(
                ISett(_sett).blockLock(address(this)) < block.number,
                "blockLocked"
            );
        }

        IERC20Upgradeable(_sett).safeTransferFrom(
            msg.sender,
            address(this),
            _shares
        );

        // Withdraw from sett
        ISett(_sett).withdraw(_shares);
        uint256 underlyingAmount = zapConfig.token.balanceOf(address(this));

        // Underlying of bvyWBTC is WBTC
        uint256 btcAmount = underlyingAmount;

        if (address(zapConfig.curvePool) != address(0)) {
            // Remove from pool
            zapConfig.curvePool.remove_liquidity_one_coin(
                underlyingAmount,
                zapConfig.withdrawTokenIndex,
                0 // minOut
            );
            btcAmount = zapConfig.withdrawToken.balanceOf(address(this));
        }

        // Use other zap to deposit
        uint256 ibbtcAmount = IBBTC_MINT_ZAP.mint(
            address(zapConfig.withdrawToken),
            btcAmount,
            0, // poolId - renCrv: 0
            address(zapConfig.withdrawToken) == address(RENBTC) ? 0 : 1, // idx - renbtc: 0, wbtc: 1
            _minOut
        );
        IBBTC.safeTransfer(msg.sender, ibbtcAmount);

        return ibbtcAmount;
    }
}
