#!/bin/bash
# Detect which AI agent platform is running on this system.
# Outputs: "openclaw" | "hermes" | "unknown"

if [ -d "$HOME/.openclaw" ] && command -v openclaw &>/dev/null; then
  echo "openclaw"
elif [ -d "$HOME/.hermes" ] && command -v hermes &>/dev/null; then
  echo "hermes"
else
  echo "unknown"
fi
