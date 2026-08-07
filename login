#!/bin/sh
set -euo pipefail

# the agent-type code lives in work; _login is its hidden verb for this flow
exec "$(dirname "$0")/work" _login
