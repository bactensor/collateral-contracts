// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

import {Test, console} from "forge-std/Test.sol";
import {Collateral} from "../src/Collateral.sol";

contract CollateralTest is Test {
    address constant TRUSTEE = address(0x1000);
    address constant BOND_POSTER1 = address(0x1001);
    address constant BOND_POSTER2 = address(0x1002);
    uint64 constant DECISION_TIMEOUT = 1 days;
    uint64 constant MIN_COLLATERAL_INCREASE = 1 ether;
    string constant URL = "https://reclaimreason.io";
    bytes16 constant URL_CONTENT_MD5_CHECKSUM = 0x12345678901234567890123456789012;

    Collateral public collateral;

    // this boilerplate code had to be copied from Collateral contract to be able to test events and errors
    // it's not possible to import events and errors from another contract
    event Deposit(address indexed account, uint256 amount);
    event ReclaimProcessStarted(
        uint256 indexed reclaimRequestId,
        address indexed account,
        uint256 amount,
        uint64 expirationTime,
        string url,
        bytes16 urlContentMd5Checksum
    );
    event Reclaimed(uint256 indexed reclaimRequestId, address indexed account, uint256 amount);
    event Denied(uint256 indexed reclaimRequestId);
    event Slashed(address indexed account, uint256 amount);

    error InvalidDepositMethod();
    error HasPendingReclaim();
    error InsufficientAmount();
    error InvalidReclaimAmount();
    error ReclaimNotFound();
    error NotAvailableYet();
    error TransferFailed();
    error PastDenyTimeout();
    error NotTrustee();

    function setUp() public {
        collateral = new Collateral(TRUSTEE, MIN_COLLATERAL_INCREASE, DECISION_TIMEOUT);
        // give trustee some ether to pay gas fees
        payable(TRUSTEE).transfer(3 ether);

        // fund bond posters
        payable(BOND_POSTER1).transfer(3 ether);
        payable(BOND_POSTER2).transfer(3 ether);
    }

    function test_deposit() public {
        vm.startPrank(BOND_POSTER1);
        vm.expectEmit(true, false, false, true);
        emit Deposit(BOND_POSTER1, 1 ether);

        collateral.deposit{value: 1 ether}();
        assertEq(collateral.collaterals(BOND_POSTER1), 1 ether);
        assertEq(address(collateral).balance, 1 ether);

        vm.expectEmit(true, false, false, true);
        emit Deposit(BOND_POSTER1, 1 ether);

        collateral.deposit{value: 1 ether}();
        assertEq(collateral.collaterals(BOND_POSTER1), 2 ether);
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
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 1 ether}();
        uint256 expectedReclaimId = 1;

        vm.expectEmit(true, true, false, true);
        emit ReclaimProcessStarted(
            expectedReclaimId,
            BOND_POSTER1,
            1 ether,
            uint64(block.timestamp + DECISION_TIMEOUT),
            URL,
            URL_CONTENT_MD5_CHECKSUM
        );

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        // reclaim data is available in the contract
        verifyReclaim(expectedReclaimId, BOND_POSTER1, 1 ether, block.timestamp + DECISION_TIMEOUT);

        // bond poster's funds are still locked
        assertEq(collateral.collaterals(BOND_POSTER1), 1 ether);
        assertEq(address(collateral).balance, 1 ether);
    }

    function test_reclaim_MultipleUsersCanStartReclaimProcess() public {
        vm.prank(BOND_POSTER1);
        collateral.deposit{value: 1 ether}();
        vm.prank(BOND_POSTER2);
        collateral.deposit{value: 1 ether}();

        vm.prank(BOND_POSTER1);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        vm.prank(BOND_POSTER2);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        uint256 expectedDenyTimeout = block.timestamp + DECISION_TIMEOUT;
        verifyReclaim(1, BOND_POSTER1, 1 ether, expectedDenyTimeout);
        verifyReclaim(2, BOND_POSTER2, 1 ether, expectedDenyTimeout);

        // all the funds are still locked
        assertEq(address(collateral).balance, 2 ether);
    }

    function test_reclaim_CanReclaimLessThanMinIncreaseIfItsTheWholeCollateral() public {
        vm.startPrank(BOND_POSTER1);
        uint256 reclaimRequestId = 1;
        collateral.deposit{value: 1.5 ether}();
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);
        collateral.finalizeReclaim(reclaimRequestId);

        uint256 nextReclaimId = 2;
        vm.expectEmit(true, true, false, true);
        emit ReclaimProcessStarted(
            nextReclaimId,
            BOND_POSTER1,
            0.5 ether,
            uint64(block.timestamp + DECISION_TIMEOUT),
            URL,
            URL_CONTENT_MD5_CHECKSUM
        );

        collateral.reclaimCollateral(0.5 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        verifyReclaim(nextReclaimId, BOND_POSTER1, 0.5 ether, block.timestamp + DECISION_TIMEOUT);
    }

    function test_revert_reclaim_CanNotReclaimIfCollateralIsLessThanMinCollateralIncrease() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 1 ether}();

        vm.expectRevert(InvalidReclaimAmount.selector);
        collateral.reclaimCollateral(0.5 ether, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_revert_reclaim_DoesNotAllowUserToStartConcurrentReclaims() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 2 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        vm.expectRevert(HasPendingReclaim.selector);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_revert_reclaim_CanNotReclaimMoreThanCollateral() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 1 ether}();

        vm.expectRevert(InsufficientAmount.selector);
        collateral.reclaimCollateral(2 ether, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_revert_reclaim_CanNotReclaimWwhenHasPendingReclaim() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 2 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        vm.expectRevert(HasPendingReclaim.selector);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
    }

    function test_finalizeReclaim() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        uint256 depositorBalanceBefore = BOND_POSTER1.balance;
        uint256 contractBalanceBefore = address(collateral).balance;

        vm.expectEmit(true, true, false, true);
        emit Reclaimed(1, BOND_POSTER1, 1 ether);
        collateral.finalizeReclaim(1);

        uint256 depositorBalanceAfter = BOND_POSTER1.balance;
        uint256 contractBalanceAfter = address(collateral).balance;
        assertEq(depositorBalanceAfter, depositorBalanceBefore + 1 ether);
        assertEq(contractBalanceAfter, contractBalanceBefore - 1 ether);

        // check that reclaim data is deleted after reclaim is finalized
        verifyReclaim(1, address(0), 0, 0);
    }

    function test_finalizeReclaim_CanStartNewReclaimAfterFinalized() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 2 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        collateral.finalizeReclaim(1);
        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        // check that reclaim data is deleted after reclaim is finalized
        verifyReclaim(2, BOND_POSTER1, 1 ether, block.timestamp + DECISION_TIMEOUT);
    }

    function test_finalizeReclaim_DeletesReclaimRequestAndDoesNotReturnCollateralIfMinerGotCollateralSlashedBelowReclaimAmount(
    ) public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 2 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        vm.stopPrank();

        skip(DECISION_TIMEOUT + 1);
        vm.prank(TRUSTEE);
        collateral.slashCollateral(BOND_POSTER1, 1.5 ether);

        vm.prank(BOND_POSTER1);

        // bond poster won't get the collateral back but the reclaim request will be deleted so he can start a new one
        uint256 bondPosterBalanceBefore = BOND_POSTER1.balance;
        uint256 contractBalanceBefore = address(collateral).balance;
        collateral.finalizeReclaim(1);
        uint256 bondPosterBalanceAfter = BOND_POSTER1.balance;
        uint256 contractBalanceAfter = address(collateral).balance;
        assertEq(bondPosterBalanceAfter, bondPosterBalanceBefore);
        assertEq(contractBalanceAfter, contractBalanceBefore);
    }

    function test_revert_finalizeReclaim_CanNotFinalizeUntilDenyTimeoutExpires() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 2 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);

        vm.expectRevert(NotAvailableYet.selector);
        collateral.finalizeReclaim(1);
    }

    function test_revert_finalizeReclaim_CanNotFinalizeTheSameReclaimRequestMultipleTimes() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 2 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        collateral.finalizeReclaim(1);
        vm.expectRevert(ReclaimNotFound.selector);
        collateral.finalizeReclaim(1);
    }

    function test_denyReclaimRequest() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        vm.stopPrank();

        vm.prank(TRUSTEE);
        uint256 reclaimRequestId = 1;
        uint256 contractBalanceBefore = address(collateral).balance;

        vm.expectEmit(true, false, false, false);
        emit Denied(reclaimRequestId);
        collateral.denyReclaimRequest(reclaimRequestId);

        uint256 contractBalanceAfter = address(collateral).balance;
        // does not change contract balance
        assertEq(contractBalanceAfter, contractBalanceBefore);

        skip(DECISION_TIMEOUT + 1);
        vm.prank(BOND_POSTER1);
        vm.expectRevert(ReclaimNotFound.selector);
        collateral.finalizeReclaim(reclaimRequestId);
    }

    function test_revert_denyReclaimRequest_CanBeCalledOnlyByTrustee() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        vm.expectRevert(NotTrustee.selector);
        collateral.denyReclaimRequest(1);
    }

    function test_revert_denyReclaimRequest_CanNotBeCalledForFinalizedReclaimRequest() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);
        uint256 reclaimRequestId = 1;
        collateral.finalizeReclaim(reclaimRequestId);

        vm.stopPrank();
        vm.prank(TRUSTEE);
        vm.expectRevert(ReclaimNotFound.selector);
        collateral.denyReclaimRequest(reclaimRequestId);
    }

    function test_revert_denyReclaimRequest_CanNotBeCalledAfterDenyTimeoutExpires() public {
        vm.startPrank(BOND_POSTER1);
        collateral.deposit{value: 1 ether}();

        collateral.reclaimCollateral(1 ether, URL, URL_CONTENT_MD5_CHECKSUM);
        skip(DECISION_TIMEOUT + 1);

        vm.stopPrank();
        vm.prank(TRUSTEE);
        vm.expectRevert(PastDenyTimeout.selector);
        collateral.denyReclaimRequest(1);
    }

    function test_slashCollateral() public {
        vm.prank(BOND_POSTER1);
        collateral.deposit{value: 2 ether}();

        uint256 bondPosterCollateralBeforeSlash = collateral.collaterals(BOND_POSTER1);
        uint256 contractBalanceBeforeSlash = address(collateral).balance;

        vm.prank(TRUSTEE);
        vm.expectEmit(true, false, false, true);
        emit Slashed(BOND_POSTER1, 1 ether);
        collateral.slashCollateral(BOND_POSTER1, 1 ether);

        uint256 bondPosterCollateralAfterSlash = collateral.collaterals(BOND_POSTER1);
        assertEq(bondPosterCollateralAfterSlash, bondPosterCollateralBeforeSlash - 1 ether);

        uint256 contractBalanceAfterSlash = address(collateral).balance;
        assertEq(contractBalanceAfterSlash, contractBalanceBeforeSlash - 1 ether);
    }

    function test_revert_slashCollateral_CanBeCalledOnlyByTrustee() public {
        vm.prank(BOND_POSTER1);
        collateral.deposit{value: 2 ether}();

        vm.expectRevert(NotTrustee.selector);
        collateral.slashCollateral(BOND_POSTER1, 1 ether);
    }

    function verifyReclaim(
        uint256 reclaimRequestId,
        address expectedAccount,
        uint256 expectedAmount,
        uint256 expectedExpirationTime
    ) private view {
        (address account, uint256 amount, uint256 expirationTime) = collateral.reclaims(reclaimRequestId);
        assertEq(account, expectedAccount);
        assertEq(amount, expectedAmount);
        assertEq(expirationTime, expectedExpirationTime);
    }
}
