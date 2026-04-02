#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "🚀 KIMVIWARE ORCHESTRATION - FULL SYSTEM STARTUP"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

KIMVIWARE_DIR=~/KIMVIWARE
VENV_PATH=$KIMVIWARE_DIR/venv_kimvieware

# Activate virtual environment
source $VENV_PATH/bin/activate

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo -e "${YELLOW}⚠️  tmux not found. Installing...${NC}"
    sudo apt install -y tmux
fi

# Kill existing tmux session
tmux kill-session -t kimviware 2>/dev/null

# Create new tmux session
echo -e "${BLUE}📺 Creating tmux session 'kimviware'${NC}"
tmux new-session -d -s kimviware

# Window 0: Dashboard
echo -e "${GREEN}✅ Starting Dashboard (Window 0)${NC}"
tmux rename-window -t kimviware:0 'Dashboard'
tmux send-keys -t kimviware:0 "cd $KIMVIWARE_DIR/kimvieware-orchestrator" C-m
tmux send-keys -t kimviware:0 "source $VENV_PATH/bin/activate" C-m
tmux send-keys -t kimviware:0 "echo '🌐 Starting Dashboard on http://localhost:8080'" C-m
tmux send-keys -t kimviware:0 "python -m uvicorn src.api.gateway:app --host 0.0.0.0 --port 8080 --reload" C-m

sleep 2

# Window 1: Phase 0 (Validation)
echo -e "${GREEN}✅ Starting Phase 0 Worker (Window 1)${NC}"
tmux new-window -t kimviware:1 -n 'Phase0'
tmux send-keys -t kimviware:1 "cd $KIMVIWARE_DIR/kimvieware-phase0-validator" C-m
tmux send-keys -t kimviware:1 "source $VENV_PATH/bin/activate" C-m
tmux send-keys -t kimviware:1 "echo '🔍 Starting Phase 0 - Validation Worker'" C-m
tmux send-keys -t kimviware:1 "python src/validator_service.py" C-m

sleep 1

# Window 2: Phase 1 (Extraction)
echo -e "${GREEN}✅ Starting Phase 1 Worker (Window 2)${NC}"
tmux new-window -t kimviware:2 -n 'Phase1'
tmux send-keys -t kimviware:2 "cd $KIMVIWARE_DIR/kimvieware-phase1-extractor" C-m
tmux send-keys -t kimviware:2 "source $VENV_PATH/bin/activate" C-m
tmux send-keys -t kimviware:2 "echo '📊 Starting Phase 1 - Extraction Worker'" C-m
tmux send-keys -t kimviware:2 "python src/worker.py" C-m

sleep 1

# Window 3: Phase 2 (SGATS)
echo -e "${GREEN}✅ Starting Phase 2 Worker (Window 3)${NC}"
tmux new-window -t kimviware:3 -n 'Phase2'
tmux send-keys -t kimviware:3 "cd $KIMVIWARE_DIR/kimvieware-phase2-sgats" C-m
tmux send-keys -t kimviware:3 "source $VENV_PATH/bin/activate" C-m
tmux send-keys -t kimviware:3 "echo '🎯 Starting Phase 2 - SGATS Worker'" C-m
tmux send-keys -t kimviware:3 "python src/sgats_service.py" C-m

sleep 1

# Window 4: Phase 3 (EvoPath-GA)
echo -e "${GREEN}✅ Starting Phase 3 Worker (Window 4)${NC}"
tmux new-window -t kimviware:4 -n 'Phase3'
tmux send-keys -t kimviware:4 "cd $KIMVIWARE_DIR/kimvieware-phase3-evopath" C-m
tmux send-keys -t kimviware:4 "source $VENV_PATH/bin/activate" C-m
tmux send-keys -t kimviware:4 "echo '🧬 Starting Phase 3 - EvoPath-GA Worker'" C-m
tmux send-keys -t kimviware:4 "python src/evopath_service.py" C-m

sleep 1

# Window 5: Monitoring
echo -e "${GREEN}✅ Creating Monitoring Window (Window 5)${NC}"
tmux new-window -t kimviware:5 -n 'Monitor'
tmux send-keys -t kimviware:5 "cd $KIMVIWARE_DIR" C-m
tmux send-keys -t kimviware:5 "source $VENV_PATH/bin/activate" C-m
tmux send-keys -t kimviware:5 "echo '📊 KIMVIWARE Monitoring'" C-m
tmux send-keys -t kimviware:5 "echo ''" C-m
tmux send-keys -t kimviware:5 "echo 'RabbitMQ Queues:'" C-m
tmux send-keys -t kimviware:5 "sudo rabbitmqctl list_queues" C-m

# Select Dashboard window
tmux select-window -t kimviware:0

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ ORCHESTRATION STARTED SUCCESSFULLY!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📺 Tmux Windows:"
echo "   0: Dashboard      (http://localhost:8080)"
echo "   1: Phase 0        (Validation)"
echo "   2: Phase 1        (Extraction)"
echo "   3: Phase 2        (SGATS)"
echo "   4: Phase 3        (EvoPath-GA)"
echo "   5: Monitoring"
echo ""
echo "🎮 Commands:"
echo "   tmux attach -t kimviware    # Attach to session"
echo "   Ctrl+B then 0-5             # Switch windows"
echo "   Ctrl+B then D               # Detach"
echo "   tmux kill-session -t kimviware  # Stop all"
echo ""
echo "🌐 Dashboard: http://localhost:8080"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Attaching to tmux session in 3 seconds..."
sleep 3

tmux attach -t kimviware
