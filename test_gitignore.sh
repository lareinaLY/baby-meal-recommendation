#!/bin/bash

# Test script to verify .gitignore is working correctly
# Run this in your project root directory

echo "🧪 Testing .gitignore configuration..."
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not a git repository. Run 'git init' first."
    exit 1
fi

# Check if .gitignore exists
if [ ! -f .gitignore ]; then
    echo "❌ .gitignore file not found!"
    exit 1
fi

echo "📋 .gitignore file found. Starting tests..."
echo ""

# Create test files if they don't exist
echo "📝 Creating test files..."
mkdir -p __pycache__ venv .idea
touch __pycache__/test.pyc
touch venv/test.txt
touch .env
touch .idea/workspace.xml
touch test.log
touch test.db
echo "SECRET_KEY=test123" > .env

# Counter for passed tests
passed=0
total=0

# Function to test if a file/directory is ignored
test_ignored() {
    local path=$1
    local should_ignore=$2
    total=$((total + 1))

    if git check-ignore -q "$path"; then
        if [ "$should_ignore" = "yes" ]; then
            echo "✅ $path is correctly ignored"
            passed=$((passed + 1))
        else
            echo "❌ $path should NOT be ignored but it is!"
        fi
    else
        if [ "$should_ignore" = "no" ]; then
            echo "✅ $path is correctly tracked"
            passed=$((passed + 1))
        else
            echo "❌ $path should be ignored but it's NOT!"
        fi
    fi
}

# Run tests
echo "🔍 Testing files that SHOULD be ignored:"
test_ignored ".env" "yes"
test_ignored "venv" "yes"
test_ignored "__pycache__" "yes"
test_ignored ".idea" "yes"
test_ignored "test.log" "yes"
test_ignored "test.db" "yes"
test_ignored "venv/test.txt" "yes"
test_ignored "__pycache__/test.pyc" "yes"

echo ""
echo "🔍 Testing files that should NOT be ignored:"
test_ignored ".gitignore" "no"
test_ignored "README.md" "no"

echo ""
echo "📊 Test Results: $passed/$total tests passed"
echo ""

if [ $passed -eq $total ]; then
    echo "🎉 All tests passed! Your .gitignore is configured correctly."
    echo ""
    echo "🧹 Cleaning up test files..."
    rm -rf __pycache__ venv/.venv .idea test.log test.db
    echo "✨ Cleanup complete!"
    exit 0
else
    echo "⚠️  Some tests failed. Please check your .gitignore file."
    echo ""
    echo "🔧 Common fixes:"
    echo "   - Make sure each pattern is on a new line"
    echo "   - Check for typos in patterns"
    echo "   - Ensure no extra spaces after patterns"
    echo ""
    echo "📁 Current .gitignore patterns:"
    cat .gitignore | grep -v "^#" | grep -v "^$"
    exit 1
fi