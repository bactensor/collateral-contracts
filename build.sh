#!/bin/bash

# build the smart contract
forge build src/Collateral.sol

# store the ABI in a file
jq '.abi' out/Collateral.sol/Collateral.json >abi.json.temp

# check if the abi file changed
if [ -f abi.json ]; then
  diff -q abi.json abi.json.temp
  EXIT_CODE=$?
else
  EXIT_CODE=1
fi

mv abi.json.temp abi.json
exit $EXIT_CODE
