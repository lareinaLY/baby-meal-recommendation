#!/bin/bash

# Test script to verify .gitignore is working correctly
# Tests both backend and frontend ignore patterns

set -e  # Exit on any error

echo "🧪 Testing .gitignore configuration..."
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Test function
test_ignored() {
    local file=$1
    local description=$2
    
    # Create the file/directory if it doesn't exist
    if [[ $file == */ ]]; then
        # It's a directory
        mkdir -p "$file"
        touch "${file}test.txt"
    else
        # It's a file
        mkdir -p "$(dirname "$file")"
        echo "test" > "$file"
    fi
    
    # Check if git ignores it
    if git check-ignore -q "$file" || git check-ignore -q "${file}test.txt" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $description: $file"
    else
        echo -e "${RED}✗${NC} $description: $file (NOT IGNORED!)"
        FAILED=$((FAILED + 1))
    fi
}

echo ""
echo "📦 Testing Backend Patterns..."
echo "--------------------------------"

# Python patterns
test_ignored "backend/__pycache__/" "Python cache directory"
test_ignored "backend/test.pyc" "Python compiled file"
test_ignored "backend/.pytest_cache/" "Pytest cache"

# Virtual environment
test_ignored ".venv/" "Virtual environment"
test_ignored "venv/" "Virtual environment (alt)"
test_ignored "env/" "Virtual environment (alt2)"

# Environment files
test_ignored ".env" "Environment file"
test_ignored ".env.local" "Local environment file"
test_ignored "backend/.env.production" "Production environment file"

# Database files
test_ignored "backend/test.db" "SQLite database"
test_ignored "backend/test.sqlite3" "SQLite3 database"

echo ""
echo "🎨 Testing Frontend Patterns..."
echo "--------------------------------"

# Node modules
test_ignored "frontend/node_modules/" "Node modules directory"

# Build directories
test_ignored "frontend/dist/" "Frontend dist directory"
test_ignored "frontend/build/" "Frontend build directory"

# Logs
test_ignored "frontend/npm-debug.log" "NPM debug log"
test_ignored "frontend/yarn-error.log" "Yarn error log"

# Frontend environment
test_ignored "frontend/.env.local" "Frontend env file"

echo ""
echo "🖥️  Testing IDE & OS Patterns..."
echo "--------------------------------"

# IDE files
test_ignored ".vscode/" "VSCode directory"
test_ignored ".idea/" "IntelliJ directory"
test_ignored "test.swp" "Vim swap file"

# OS files
test_ignored ".DS_Store" "macOS metadata"
test_ignored "Thumbs.db" "Windows thumbnail cache"

echo ""
echo "📄 Testing Log Files..."
echo "--------------------------------"

test_ignored "backend/app.log" "Application log"
test_ignored "logs/" "Logs directory"
test_ignored "backend/debug.log" "Debug log"

echo ""
echo "========================================="

# Cleanup test files
echo ""
echo "🧹 Cleaning up test files..."

# Remove test files and directories
rm -rf backend/__pycache__ backend/.pytest_cache backend/test.pyc backend/test.db backend/test.sqlite3 backend/app.log backend/debug.log backend/.env.production
rm -rf frontend/node_modules frontend/dist frontend/build frontend/npm-debug.log frontend/yarn-error.log frontend/.env.local
rm -rf .venv venv env .env .env.local .vscode .idea test.swp .DS_Store Thumbs.db logs/
rm -rf test/ tmp/ temp/

echo "✓ Cleanup complete"

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}========================================="
    echo -e "✓ All tests passed! .gitignore is working correctly."
    echo -e "=====================================${NC}"
    exit 0
else
    echo -e "${RED}========================================="
    echo -e "✗ $FAILED test(s) failed!"
    echo -e "Please update your .gitignore file."
    echo -e "=====================================${NC}"
    exit 1
fi