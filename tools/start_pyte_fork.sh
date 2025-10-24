#!/bin/bash
# Quick start script for forking and patching pyte
# Run this to set up your pyte fork workspace

set -e  # Exit on error

echo "============================================================"
echo "PYTE FORK QUICK START"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}ERROR: Please run this from ActCLI-Bench root directory${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Clone pyte repository${NC}"
echo "Choose your fork location:"
echo "  A) Personal GitHub account"
echo "  B) llm-case-studies organization"
echo ""
read -p "Enter A or B: " choice

if [ "$choice" = "A" ] || [ "$choice" = "a" ]; then
    read -p "Enter your GitHub username: " github_user
    FORK_URL="https://github.com/$github_user/pyte.git"
elif [ "$choice" = "B" ] || [ "$choice" = "b" ]; then
    FORK_URL="https://github.com/llm-case-studies/pyte.git"
else
    echo -e "${RED}Invalid choice${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}→ Forking instructions:${NC}"
echo "  1. Go to: https://github.com/selectel/pyte"
echo "  2. Click 'Fork' button (top right)"
echo "  3. Choose destination as configured above"
echo "  4. Click 'Create fork'"
echo ""
read -p "Press ENTER after you've forked the repo..."

echo ""
echo -e "${YELLOW}Step 2: Clone your fork${NC}"
cd ~/Projects || mkdir -p ~/Projects && cd ~/Projects

if [ -d "pyte-fork" ]; then
    echo -e "${YELLOW}Directory pyte-fork already exists${NC}"
    read -p "Delete and re-clone? (y/n): " delete_choice
    if [ "$delete_choice" = "y" ]; then
        rm -rf pyte-fork
    else
        echo "Using existing clone"
        cd pyte-fork
    fi
fi

if [ ! -d "pyte-fork" ]; then
    echo "Cloning $FORK_URL..."
    git clone "$FORK_URL" pyte-fork
    cd pyte-fork
else
    cd pyte-fork
fi

echo ""
echo -e "${GREEN}✓ Cloned${NC}"

echo ""
echo -e "${YELLOW}Step 3: Add upstream remote${NC}"
if git remote | grep -q "^upstream$"; then
    echo "Upstream already configured"
else
    git remote add upstream https://github.com/selectel/pyte.git
    echo -e "${GREEN}✓ Added upstream remote${NC}"
fi

git remote -v

echo ""
echo -e "${YELLOW}Step 4: Create fix branch${NC}"
git fetch origin
git checkout main 2>/dev/null || git checkout master 2>/dev/null || echo "Already on main/master"

if git branch | grep -q "fix/cursor-tracking-ai-clis"; then
    echo "Branch already exists"
    git checkout fix/cursor-tracking-ai-clis
else
    git checkout -b fix/cursor-tracking-ai-clis
    echo -e "${GREEN}✓ Created branch: fix/cursor-tracking-ai-clis${NC}"
fi

echo ""
echo -e "${YELLOW}Step 5: Install pyte in development mode${NC}"
pip install -e .
echo -e "${GREEN}✓ Installed${NC}"

echo ""
echo -e "${YELLOW}Step 6: Run diagnostic test${NC}"
echo "This will show you the bug in action..."
echo ""

# Copy diagnostic script
cp ~/Projects/ActCLI-Bench/tools/diagnose_pyte_bug.py .
python3 diagnose_pyte_bug.py

echo ""
echo "============================================================"
echo "NEXT STEPS"
echo "============================================================"
echo ""
echo "Your pyte fork is ready at: $(pwd)"
echo ""
echo -e "${GREEN}What to do next:${NC}"
echo "  1. Review the diagnostic output above"
echo "  2. Identify which line shows the bug"
echo "  3. Look at pyte/screens.py to find the faulty method"
echo "  4. Make your fix"
echo "  5. Run: python3 diagnose_pyte_bug.py (should pass)"
echo "  6. Run: pytest tests/ (all tests should pass)"
echo "  7. Commit and push your changes"
echo ""
echo -e "${YELLOW}Detailed guide:${NC} ~/Projects/ActCLI-Bench/docs/PYTE_FORK_GUIDE.md"
echo ""
echo -e "${GREEN}Ready to fix the bug! 🚀${NC}"
