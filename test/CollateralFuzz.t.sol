// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

import {CollateralTestBase} from "./CollateralTestBase.sol";

contract CollateralTest is CollateralTestBase {
    receive() external payable {}

    function testFuzz_deposit(uint256 amount) public {
        // leave some ether to cover gas fees
        vm.assume((amount >= MIN_COLLATERAL_INCREASE) && (amount < address(this).balance - 1 ether));
        vm.expectEmit(true, false, false, true);
        emit Deposit(address(this), amount);

        collateral.deposit{value: amount}();
        assertEq(collateral.collaterals(address(this)), amount);
        assertEq(address(collateral).balance, amount);
    }

    function testFuzz_reclaim(uint256 amount) public {
        vm.assume((amount >= MIN_COLLATERAL_INCREASE) && (amount < address(this).balance - 1 ether));

        collateral.deposit{value: amount}();

        vm.expectEmit(true, false, false, true);
        emit ReclaimProcessStarted(
            1, address(this), amount, uint64(block.timestamp) + DECISION_TIMEOUT, URL, URL_CONTENT_MD5_CHECKSUM
        );

        collateral.reclaimCollateral(amount, URL, URL_CONTENT_MD5_CHECKSUM);

        verifyReclaim(1, address(this), amount, block.timestamp + DECISION_TIMEOUT);
    }

    function testFuzz_revert_reclaim_ReclaimAmountTooLarge(uint256 amount, uint256 reclaimAmount) public {
        vm.assume((amount >= MIN_COLLATERAL_INCREASE) && (amount < address(this).balance - 1 ether));
        vm.assume(reclaimAmount > amount);
        collateral.deposit{value: amount}();

        vm.expectRevert(ReclaimAmountTooLarge.selector);
        collateral.reclaimCollateral(reclaimAmount, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function testFuzz_denyReclaimRequest(uint256 amount, uint64 decisionTimeout) public {
        vm.assume((amount >= MIN_COLLATERAL_INCREASE) && (amount < address(this).balance - 1 ether));
        vm.assume(decisionTimeout > 0 && decisionTimeout <= DECISION_TIMEOUT);

        collateral.deposit{value: amount}();
        collateral.reclaimCollateral(amount, URL, URL_CONTENT_MD5_CHECKSUM);

        skip(decisionTimeout);

        vm.expectEmit(true, false, false, true);
        emit Denied(1, URL, URL_CONTENT_MD5_CHECKSUM);

        vm.prank(TRUSTEE);
        collateral.denyReclaimRequest(1, URL, URL_CONTENT_MD5_CHECKSUM);

        // check that the reclaim request is denied
        // make sure finalizeReclaim can be called on the reclaim request
        skip(DECISION_TIMEOUT);
        vm.expectRevert(ReclaimNotFound.selector);
        collateral.finalizeReclaim(1);
    }

    function testFuzz_finalizeReclaim(uint256 amount, uint64 decisionTimeout) public {
        vm.assume((amount >= MIN_COLLATERAL_INCREASE) && (amount < address(this).balance - 1 ether));
        vm.assume(decisionTimeout > DECISION_TIMEOUT);

        collateral.deposit{value: amount}();
        collateral.reclaimCollateral(amount, URL, URL_CONTENT_MD5_CHECKSUM);

        skip(decisionTimeout);

        vm.expectEmit(true, false, false, true);
        emit Reclaimed(1, address(this), amount);

        uint256 balanceBefore = address(this).balance;
        collateral.finalizeReclaim(1);

        // check that the reclaim request can not be finalized again
        vm.expectRevert(ReclaimNotFound.selector);
        collateral.finalizeReclaim(1);

        assertEq(collateral.collaterals(address(this)), 0);
        assertEq(address(this).balance, balanceBefore + amount);
        assertEq(address(collateral).balance, 0);
    }

    function testFuzz_slash(uint256 amount) public {
        vm.assume((amount >= MIN_COLLATERAL_INCREASE) && (amount < address(this).balance / 2));

        collateral.deposit{value: 2 * amount}();

        vm.expectEmit(true, false, false, true);
        emit Slashed(address(this), amount, SLASH_REASON_URL, URL_CONTENT_MD5_CHECKSUM);

        vm.prank(TRUSTEE);
        collateral.slashCollateral(address(this), amount, SLASH_REASON_URL, URL_CONTENT_MD5_CHECKSUM);

        // slashes only amount and leaves the rest
        assertEq(collateral.collaterals(address(this)), amount);
        assertEq(address(collateral).balance, amount);
    }

    function testFuzz_revert_slash_SlashTooBig(uint256 amount) public {
        vm.assume((amount >= MIN_COLLATERAL_INCREASE) && (amount < address(this).balance / 2));

        collateral.deposit{value: 2 * amount}();

        vm.expectEmit(true, false, false, true);
        emit Slashed(address(this), amount, SLASH_REASON_URL, URL_CONTENT_MD5_CHECKSUM);

        vm.prank(TRUSTEE);
        collateral.slashCollateral(address(this), amount, SLASH_REASON_URL, URL_CONTENT_MD5_CHECKSUM);

        // slashes only amount and leaves the rest
        assertEq(collateral.collaterals(address(this)), amount);
        assertEq(address(collateral).balance, amount);
    }
}
