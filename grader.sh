#!/bin/bash
set -e

# Sherlock Root Grader Orchestrator
# This script runs all sub-graders in the grader/ directory.

echo "===================================================="
echo "         SHERLOCK MIGRATED GRADER SUITE             "
echo "===================================================="

# 1. Grade Analysis (JSON Logic)
echo ""
bash grader/grade_analysis.sh

# 2. Grade Reports (Markdown Generation)
echo ""
bash grader/grade_reports.sh

# 3. Grade Docs (Project Documentation)
echo ""
bash grader/grade_docs.sh

echo ""
echo "===================================================="
echo "             GRADING COMPLETE                       "
echo "===================================================="
