#!/bin/bash
# Check status of colleague meeting experiments

echo "======================================================================="
echo "🔍 EXPERIMENT STATUS CHECK"
echo "======================================================================="
echo ""

# Check if experiments directory exists
if [ -d "colleague_meeting_experiments" ]; then
    echo "✅ Experiment directory exists: colleague_meeting_experiments/"
    echo ""
    
    # Count total experiments
    total=$(find colleague_meeting_experiments -maxdepth 1 -type d | tail -n +2 | wc -l | tr -d ' ')
    echo "📁 Total experiment directories: $total"
    
    # Count completed experiments (those with results files)
    completed=$(find colleague_meeting_experiments -name "experiment_results.json" | wc -l | tr -d ' ')
    echo "✅ Completed experiments: $completed"
    
    # Calculate progress
    if [ "$total" -gt 0 ]; then
        progress=$((completed * 100 / total))
        echo "📊 Progress: $progress%"
    fi
    
    echo ""
    
    # Check if summary results exist
    if [ -f "results/data/colleague_meeting_results.json" ]; then
        echo "✅ Summary results file exists"
        echo "   File: results/data/colleague_meeting_results.json"
    else
        echo "⏳ Summary results file not yet created"
    fi
    
    echo ""
    
    # Check log file
    if [ -f "results/reports/colleague_meeting_experiments_log.txt" ]; then
        echo "📄 Log file exists"
        lines=$(wc -l < results/reports/colleague_meeting_experiments_log.txt | tr -d ' ')
        echo "   Lines: $lines"
        echo ""
        echo "Last 10 lines of log:"
        echo "---"
        tail -10 results/reports/colleague_meeting_experiments_log.txt
    else
        echo "⏳ Log file not yet created"
    fi
    
else
    echo "❌ Experiment directory not found"
    echo "   Please run: python run_colleague_meeting_experiments.py"
fi

echo ""
echo "======================================================================="




