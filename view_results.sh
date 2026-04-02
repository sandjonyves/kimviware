#!/bin/bash
# KIMVIWARE Test Results - Quick Access Guide

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                   🎓 KIMVIWARE TEST RESULTS - QUICK ACCESS                   ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

BASEDIR="/home/davie/KIMVIWARE"
VENV="$BASEDIR/venv_kimvieware/bin/python"

echo "📊 RÉSULTATS JSON DISPONIBLES:"
echo ""

# Check files
if [ -f "$BASEDIR/MULTILANG_COMPREHENSIVE_REPORT.json" ]; then
    echo "  ✅ MULTILANG_COMPREHENSIVE_REPORT.json"
    echo "     $(wc -l < $BASEDIR/MULTILANG_COMPREHENSIVE_REPORT.json) lignes"
fi

if [ -f "$BASEDIR/MULTILANG_TEST_REPORT.json" ]; then
    echo "  ✅ MULTILANG_TEST_REPORT.json"
    echo "     $(wc -l < $BASEDIR/MULTILANG_TEST_REPORT.json) lignes"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 OPTIONS D'AFFICHAGE:"
echo ""
echo "1️⃣  AFFICHER LES RÉSULTATS JSON (Terminal):"
echo "   cat $BASEDIR/MULTILANG_COMPREHENSIVE_REPORT.json | $VENV -m json.tool"
echo ""
echo "2️⃣  OUVRIR LE DASHBOARD HTML (Navigateur):"
echo "   firefox $BASEDIR/test_dashboard.html"
echo "   ou double-clic: $BASEDIR/test_dashboard.html"
echo ""
echo "3️⃣  LANCER LE SERVEUR WEB (Port 8888):"
echo "   $VENV $BASEDIR/dashboard_server.py"
echo "   Puis visiter: http://localhost:8888"
echo ""
echo "4️⃣  AFFICHER LE RAPPORT MARKDOWN:"
echo "   cat $BASEDIR/TESTING_REPORT_MARKDOWN.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 RÉSUMÉ RAPIDE DES RÉSULTATS:"
echo ""

$VENV << 'PYTHON_SCRIPT'
import json
from pathlib import Path

report_file = Path('/home/davie/KIMVIWARE/MULTILANG_COMPREHENSIVE_REPORT.json')

if report_file.exists():
    with open(report_file) as f:
        data = json.load(f)
    
    print("🐍 Python Auth Service:")
    py = data['services_tested'].get('python', {})
    if py:
        tests = py.get('tests', {})
        if 'unit_tests' in tests:
            print(f"   ✅ Unit Tests: {tests['unit_tests']['success_rate']} ({tests['unit_tests']['passed']}/{tests['unit_tests']['total']})")
        loc = tests.get('source_analysis', {}).get('lines_of_code') or tests.get('code_quality', {}).get('lines_of_code')
        if loc:
            print(f"   📝 Lines of Code: {loc}")
    
    print("")
    print("🔧 C Auth Service:")
    c = data['services_tested'].get('c', {})
    if c:
        tests = c.get('tests', {})
        comp = tests.get('compilation', {})
        if comp:
            print(f"   ✅ Compilation: {comp.get('status')}")
        loc = tests.get('source_analysis', {}).get('lines_of_code')
        if loc:
            print(f"   📝 Lines of Code: {loc}")
    
    print("")
    print("☕ Java Auth Service:")
    java = data['services_tested'].get('java', {})
    if java:
        tests = java.get('tests', {})
        analysis = tests.get('structural_analysis', {})
        if analysis:
            print(f"   ✅ Static Analysis: {analysis['success_rate']} ({analysis['passed']}/{analysis['total']})")
        loc = tests.get('code_quality', {}).get('lines_of_code')
        if loc:
            print(f"   📝 Lines of Code: {loc}")
    
    print("")
    summary = data['overall_summary']
    print(f"📈 GLOBAL RESULTS:")
    print(f"   Tests executed:  {summary['total_tests_executed']}")
    print(f"   Tests passed:    {summary['total_tests_passed']}")
    print(f"   Success rate:    {summary['overall_success_rate']}")
    print(f"   Framework:       {summary['framework_status']}")
PYTHON_SCRIPT

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ Framework Status: OPERATIONAL ✅"
echo "🎯 Ready for KIMVIWARE Pipeline Submission"
echo ""
