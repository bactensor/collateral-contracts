// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

import {Collateral} from "../src/Collateral.sol";
import {CollateralTestBase} from "./CollateralTestBase.sol";

contract CollateralTest is CollateralTestBase {
    address constant DEPOSITOR1 = address(0x1001);
    address constant DEPOSITOR2 = address(0x1002);

    // used to test a case in which transfer in finalizeReclaim fails
    receive() external payable {
        revert();
    }

    function setUp() public override {
        // fund depositors
        payable(DEPOSITOR1).transfer(3 ether);
        payable(DEPOSITOR2).transfer(3 ether);
        super.setUp();
    }

    function test_constructor_ConfigSetProperly() public view {
        assertEq(collateral.NETUID(), NETUID);
        assertEq(collateral.TRUSTEE(), TRUSTEE);
        assertEq(collateral.MIN_COLLATERAL_INCREASE(), MIN_COLLATERAL_INCREASE);
        assertEq(collateral.DECISION_TIMEOUT(), DECISION_TIMEOUT);
    }

    function test_revert_constructor_RevertIfTrusteeIsZeroAddress() public {
        vm.expectRevert();
        new Collateral(NETUID, address(0), MIN_COLLATERAL_INCREASE, DECISION_TIMEOUT);
    }

    function test_revert_constructor_RevertIfMinCollateralIncreaseIsZero() public {
        vm.expectRevert();
        new Collateral(NETUID, TRUSTEE, 0, DECISION_TIMEOUT);
    }

    function test_revert_constructor_RevertIfDecisionTimeoutIsZero() public {
        vm.expectRevert();
        new Collateral(NETUID, TRUSTEE, MIN_COLLATERAL_INCREASE, 0);
    }

    function test_deposit() public {
        vm.startPrank(DEPOSITOR1);
        vm.expectEmit(true, false, false, true);
        emit Deposit(DEPOSITOR1, 1 ether);

        collateral.deposit{value: 1 ether}();
        assertEq(collateral.collaterals(DEPOSITOR1), 1 ether);
        assertEq(address(collateral).balance, 1 ether);

        vm.expectEmit(true, false, false, true);
        emit Deposit(DEPOSITOR1, 1 ether);

        collateral.deposit{value: 1 ether}();
        assertEq(collateral.collaterals(DEPOSITOR1), 2 ether);
        assertEq(address(collateral).balance, 2 ether);
    }

    function test_revert_deposit_CanNotDepositWhenCollateralLessThanMinCollateralIncrease() public {
        vm.expectRevert(InsufficientAmount.selector);
        collateral.deposit{value: 0.5 ether}();
    }

    function test_revert_CanNotDepositViaReceive() public {
        (bool success,) = address(collateral).call{value: 0.5 ether}("");
        assertFalse(success);
        assertEq(address(collateral).balance, 0);
    }

    function test_revert_CanNotDepositViaFallback() public {
        (bool success,) = address(collateral).call{value: 0.5 ether}(abi.encodeWithSignature("doesNotExist()", ""));
        assertFalse(success);
        assertEq(address(collateral).balance, 0);
    }

    function test_reclaim_CanStartReclaimProcess() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();
        uint256 expectedReclaimId = 1;

        vm.expectEmit(true, true, false, true);
        emit ReclaimProcessStarted(
            expectedReclaimId,
            DEPOSITOR1,
            1 ether,
            uint64(block.timestamp + DECISION_TIMEOUT),
            URL,
            URL_CONTENT_MD5_CHECKSUM
        );

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        // reclaim data is available in the contract
        verifyReclaim(expectedReclaimId, DEPOSITOR1, 1 ether, block.timestamp + DECISION_TIMEOUT);

        // depositor's funds are still locked
        assertEq(collateral.collaterals(DEPOSITOR1), 1 ether);
        assertEq(address(collateral).balance, 1 ether);
    }

    function test_reclaim_CanReclaimIfTotalReclaimAmountLessThanCollateral() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 2 ether}();

        for (uint256 i = 1; i < 3; ++i) {
            vm.expectEmit(true, true, false, true);
            emit ReclaimProcessStarted(
                i, DEPOSITOR1, 1 ether, uint64(block.timestamp + DECISION_TIMEOUT), URL, URL_CONTENT_MD5_CHECKSUM
            );

            collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

            // reclaim data is available in the contract
            verifyReclaim(i, DEPOSITOR1, 1 ether, block.timestamp + DECISION_TIMEOUT);
        }

        // depositor's funds are still locked
        assertEq(collateral.collaterals(DEPOSITOR1), 2 ether);
        assertEq(address(collateral).balance, 2 ether);
    }

    function test_reclaim_MultipleUsersCanStartReclaimProcess() public {
        vm.prank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();
        vm.prank(DEPOSITOR2);
        collateral.deposit{value: 1 ether}();

        vm.prank(DEPOSITOR1);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        vm.prank(DEPOSITOR2);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        uint256 expectedDenyTimeout = block.timestamp + DECISION_TIMEOUT;
        verifyReclaim(1, DEPOSITOR1, 1 ether, expectedDenyTimeout);
        verifyReclaim(2, DEPOSITOR2, 1 ether, expectedDenyTimeout);

        // all the funds are still locked
        assertEq(address(collateral).balance, 2 ether);
    }

    function test_reclaim_CanReclaimLessThanMinIncreaseIfItsTheWholeCollateral() public {
        vm.startPrank(DEPOSITOR1);
        uint256 reclaimRequestId = 1;
        collateral.deposit{value: 2.5 ether}();
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        // 1 request is finalized
        skip(DECISION_TIMEOUT + 1);
        collateral.finalizeReclaim(reclaimRequestId);

        uint256 nextReclaimId = 3;
        vm.expectEmit(true, true, false, true);
        emit ReclaimProcessStarted(
            nextReclaimId,
            DEPOSITOR1,
            0.5 ether,
            uint64(block.timestamp + DECISION_TIMEOUT),
            URL,
            URL_CONTENT_MD5_CHECKSUM
        );

        // 1 request is pending, we start another to withdraw all the remaining collateral
        collateral.reclaimCollateral(0.5 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        verifyReclaim(nextReclaimId, DEPOSITOR1, 0.5 ether, block.timestamp + DECISION_TIMEOUT);
    }

    function test_reclaim_CanReclaimAgainAfterDenial() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 2 ether}();
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        vm.stopPrank();
        vm.prank(TRUSTEE);
        collateral.denyReclaimRequest(1, URL, URL_CONTENT_MD5_CHECKSUM);

        skip(DECISION_TIMEOUT + 1);
        // first request is denied, the other succeeds
        // depositor is not credited for the denied request
        uint256 depositorBalanceBefore = DEPOSITOR1.balance;

        // the second request was not denied, so depositor is credited
        collateral.finalizeReclaim(2);
        uint256 depositorBalanceAfter = DEPOSITOR1.balance;
        assertEq(depositorBalanceAfter, depositorBalanceBefore + 1 ether);

        // bond can be reclaimed again
        vm.prank(DEPOSITOR1);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_revert_CanNotReclaimZero() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();

        vm.expectRevert(AmountZero.selector);
        collateral.reclaimCollateral(0, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_revert_reclaim_CanNotReclaimIfCollateralIsLessThanMinCollateralIncrease() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();

        vm.expectRevert(ReclaimAmountTooSmall.selector);
        collateral.reclaimCollateral(0.5 ether, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_revert_reclaim_CanNotReclaimMoreThanCollateral() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();

        vm.expectRevert(ReclaimAmountTooLarge.selector);
        collateral.reclaimCollateral(2 ether, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_revert_reclaim_CollateralUnderReclaimCanNotBeGreaterThanCollateral() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 3 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        // This reclaim pushes collateral under reclaim over total collateral
        vm.expectRevert(ReclaimAmountTooLarge.selector);
        collateral.reclaimCollateral(2 ether, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_finalizeReclaim() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        uint256 depositorBalanceBefore = DEPOSITOR1.balance;
        uint256 contractBalanceBefore = address(collateral).balance;

        vm.expectEmit(true, true, false, true);
        emit Reclaimed(1, DEPOSITOR1, 1 ether);
        collateral.finalizeReclaim(1);

        uint256 depositorBalanceAfter = DEPOSITOR1.balance;
        uint256 contractBalanceAfter = address(collateral).balance;
        assertEq(depositorBalanceAfter, depositorBalanceBefore + 1 ether);
        assertEq(contractBalanceAfter, contractBalanceBefore - 1 ether);

        // check that reclaim data is deleted after reclaim is finalized
        verifyReclaim(1, address(0), 0, 0);
    }

    function test_finalizeReclaim_CanBeCalledByAnyone() public {
        vm.prank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();

        vm.prank(DEPOSITOR1);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        uint256 depositorBalanceBefore = DEPOSITOR1.balance;
        uint256 contractBalanceBefore = address(collateral).balance;

        // not called by depositor
        collateral.finalizeReclaim(1);

        // but depositor is credited with reclaimed collateral
        uint256 depositorBalanceAfter = DEPOSITOR1.balance;
        uint256 contractBalanceAfter = address(collateral).balance;
        assertEq(depositorBalanceAfter, depositorBalanceBefore + 1 ether);
        assertEq(contractBalanceAfter, contractBalanceBefore - 1 ether);

        // check that reclaim data is deleted after reclaim is finalized
        verifyReclaim(1, address(0), 0, 0);
    }

    function test_finalizeReclaim_CanStartNewReclaimAfterFinalized() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 2 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        collateral.finalizeReclaim(1);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        // check that reclaim data is deleted after reclaim is finalized
        verifyReclaim(2, DEPOSITOR1, 1 ether, block.timestamp + DECISION_TIMEOUT);
    }

    function test_finalizeReclaim_DeletesReclaimRequestAndDoesNotReturnCollateralIfMinerGotCollateralSlashedBelowReclaimAmount(
    ) public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 2 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        vm.stopPrank();

        skip(DECISION_TIMEOUT + 1);
        vm.prank(TRUSTEE);
        collateral.slashCollateral(DEPOSITOR1, 1.5 ether, SLASH_REASON_URL, URL_CONTENT_MD5_CHECKSUM);

        vm.prank(DEPOSITOR1);

        // bond poster won't get the collateral back but the reclaim request will be deleted so he can start a new one
        uint256 bondPosterBalanceBefore = DEPOSITOR1.balance;
        uint256 contractBalanceBefore = address(collateral).balance;
        collateral.finalizeReclaim(1);
        uint256 bondPosterBalanceAfter = DEPOSITOR1.balance;
        uint256 contractBalanceAfter = address(collateral).balance;
        assertEq(bondPosterBalanceAfter, bondPosterBalanceBefore);
        assertEq(contractBalanceAfter, contractBalanceBefore);
    }

    function test_revert_finalizeReclaim_CanNotFinalizeUntilDenyTimeoutExpires() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 2 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        vm.expectRevert(BeforeDenyTimeout.selector);
        collateral.finalizeReclaim(1);
    }

    function test_revert_finalizeReclaim_CanNotFinalizeTheSameReclaimRequestMultipleTimes() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 2 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        collateral.finalizeReclaim(1);
        vm.expectRevert(ReclaimNotFound.selector);
        collateral.finalizeReclaim(1);
    }

    function test_revert_finalizeReclaim_CanNotFinalizeReclaimIfTransferFails() public {
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        vm.expectRevert(TransferFailed.selector);
        collateral.finalizeReclaim(1);
    }

    function test_denyReclaimRequest() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        vm.stopPrank();

        vm.prank(TRUSTEE);
        uint256 reclaimRequestId = 1;
        uint256 contractBalanceBefore = address(collateral).balance;

        vm.expectEmit(true, false, false, false);
        emit Denied(reclaimRequestId, URL, URL_CONTENT_MD5_CHECKSUM);
        collateral.denyReclaimRequest(reclaimRequestId, URL, URL_CONTENT_MD5_CHECKSUM);

        uint256 contractBalanceAfter = address(collateral).balance;
        // does not change contract balance
        assertEq(contractBalanceAfter, contractBalanceBefore);

        skip(DECISION_TIMEOUT + 1);
        vm.prank(DEPOSITOR1);
        vm.expectRevert(ReclaimNotFound.selector);
        collateral.finalizeReclaim(reclaimRequestId);
    }

    function test_revert_denyReclaimRequest_CanBeCalledOnlyByTrustee() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        vm.expectRevert(NotTrustee.selector);
        collateral.denyReclaimRequest(1, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_revert_denyReclaimRequest_CanNotBeCalledForFinalizedReclaimRequest() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);
        uint256 reclaimRequestId = 1;
        collateral.finalizeReclaim(reclaimRequestId);

        vm.stopPrank();
        vm.prank(TRUSTEE);
        vm.expectRevert(ReclaimNotFound.selector);
        collateral.denyReclaimRequest(reclaimRequestId, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_revert_denyReclaimRequest_CanNotBeCalledAfterDenyTimeoutExpires() public {
        vm.startPrank(DEPOSITOR1);
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        vm.stopPrank();
        vm.prank(TRUSTEE);
        vm.expectRevert(PastDenyTimeout.selector);
        collateral.denyReclaimRequest(1, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_slashCollateral() public {
        vm.prank(DEPOSITOR1);
        collateral.deposit{value: 2 ether}();

        uint256 bondPosterCollateralBeforeSlash = collateral.collaterals(DEPOSITOR1);
        uint256 contractBalanceBeforeSlash = address(collateral).balance;

        vm.prank(TRUSTEE);
        vm.expectEmit(true, false, false, true);
        emit Slashed(DEPOSITOR1, 1 ether, SLASH_REASON_URL, URL_CONTENT_MD5_CHECKSUM);
        collateral.slashCollateral(DEPOSITOR1, 1 ether, SLASH_REASON_URL, URL_CONTENT_MD5_CHECKSUM);

        uint256 bondPosterCollateralAfterSlash = collateral.collaterals(DEPOSITOR1);
        assertEq(bondPosterCollateralAfterSlash, bondPosterCollateralBeforeSlash - 1 ether);

        uint256 contractBalanceAfterSlash = address(collateral).balance;
        assertEq(contractBalanceAfterSlash, contractBalanceBeforeSlash - 1 ether);
    }

    function test_revert_slashCollateral_CanBeCalledOnlyByTrustee() public {
        vm.prank(DEPOSITOR1);
        collateral.deposit{value: 2 ether}();

        vm.expectRevert(NotTrustee.selector);
        collateral.slashCollateral(DEPOSITOR1, 1 ether, SLASH_REASON_URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_revert_slashCollateral_CanNotSlashZero() public {
        vm.prank(TRUSTEE);
        vm.expectRevert(AmountZero.selector);
        collateral.slashCollateral(DEPOSITOR1, 0, SLASH_REASON_URL, URL_CONTENT_MD5_CHECKSUM);
    }
}
