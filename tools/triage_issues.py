#!/usr/bin/env python3

"""
Issue Triage System

Categorizes dimensional issues into:
- Auto-fixable: Simple dimensional fixes (widths, fonts, etc.)
- Needs designer input: Complex structural decisions, trade-offs

After 2 auto-fix attempts, generates specific questions for designer.
"""

import json
from typing import List, Dict, Any, Tuple


def categorize_issue(issue: Dict[str, Any], iteration_history: List[Dict] = None) -> str:
    """
    Categorize issue as auto-fixable or needs-designer-input

    Args:
        issue: Feedback item from DOM measurements
        iteration_history: List of previous iteration results (to see if stuck)

    Returns:
        'auto-fixable' or 'needs-designer-input'
    """

    category = issue.get('category', 'general')
    element = issue.get('element', '')
    issue_text = issue.get('issue', '').lower()

    # Check if this issue has been stuck across iterations
    is_stuck = False
    if iteration_history and len(iteration_history) >= 2:
        # If same issue appears in multiple iterations, it's stuck
        is_stuck = True

    # Auto-fixable patterns
    auto_fixable_patterns = [
        'width is',
        'font size is',
        'font-size is',
        'too wide',
        'too narrow',
    ]

    # Needs-designer-input patterns
    needs_input_patterns = [
        'element not found',
        'missing',
        'height is',  # Often structural (fixed vs auto)
        'line-height',
    ]

    # Check for auto-fixable
    for pattern in auto_fixable_patterns:
        if pattern in issue_text:
            # But if stuck after 2 attempts, needs input
            if is_stuck:
                return 'needs-designer-input'
            return 'auto-fixable'

    # Check for needs-designer-input
    for pattern in needs_input_patterns:
        if pattern in issue_text:
            return 'needs-designer-input'

    # Default: needs input if high priority or stuck
    if issue.get('priority') == 'high' or is_stuck:
        return 'needs-designer-input'

    return 'auto-fixable'


def generate_designer_question(issue: Dict[str, Any], attempt_history: List[str] = None) -> Dict[str, Any]:
    """
    Generate a specific question for the designer about a complex issue

    Args:
        issue: Feedback item from DOM measurements
        attempt_history: What we tried to fix it

    Returns:
        Question object with context, options, recommendation
    """

    element = issue.get('element', 'Unknown element')
    issue_text = issue.get('issue', '')
    category = issue.get('category', 'general')
    figma_id = issue.get('figma_id', '')

    # Build question based on issue type
    question = {
        'element': element,
        'figma_id': figma_id,
        'category': category,
        'issue': issue_text,
        'context': '',
        'question': '',
        'options': [],
        'recommendation': '',
        'priority': issue.get('priority', 'medium')
    }

    # MISSING ELEMENT
    if 'not found' in issue_text.lower() or category == 'missing_element':
        question['context'] = f"Complex UI component '{element}' exists in Figma but structure unclear from dimensions alone."
        question['question'] = f"What should be inside '{element}'? How should it be structured in HTML?"
        question['options'] = [
            {
                'id': 'describe',
                'label': 'Describe the structure',
                'description': 'I\'ll provide a description of what should be inside'
            },
            {
                'id': 'optional',
                'label': 'It\'s optional',
                'description': 'This element can be omitted from HTML version'
            },
            {
                'id': 'defer',
                'label': 'Add in next iteration',
                'description': 'Focus on other issues first, revisit this later'
            }
        ]
        question['recommendation'] = 'Recommend describing structure for best fidelity'

    # HEIGHT ISSUES (fixed vs flexible)
    elif 'height is' in issue_text.lower():
        actual_height = issue_text.split('is ')[1].split('px')[0] if 'is ' in issue_text else 'unknown'
        expected_height = issue_text.split('should be ')[1].split('px')[0] if 'should be ' in issue_text else 'unknown'

        question['context'] = f"Figma shows fixed height ({expected_height}px), but HTML naturally sizes to {actual_height}px based on content."
        question['question'] = f"Should '{element}' be fixed height or flexible?"
        question['options'] = [
            {
                'id': 'fixed',
                'label': f'Fixed at {expected_height}px',
                'description': 'Match Figma exactly (may crop content or add whitespace)'
            },
            {
                'id': 'flexible',
                'label': 'Flexible (auto)',
                'description': 'Let content determine height (web best practice)'
            },
            {
                'id': 'min-height',
                'label': f'Minimum {expected_height}px',
                'description': 'At least {expected_height}px, can grow if needed'
            }
        ]
        question['recommendation'] = 'Recommend flexible (auto) for web-native behavior'

        if attempt_history:
            question['context'] += f"\n\nAttempts made: {', '.join(attempt_history)}"

    # LINE-HEIGHT / TYPOGRAPHY
    elif 'line-height' in issue_text.lower() or ('height' in issue_text and 'font' in element.lower()):
        question['context'] = "Text height includes font-size + line-height. Figma uses exact heights, HTML needs readable line-height."
        question['question'] = f"For '{element}', what matters more?"
        question['options'] = [
            {
                'id': 'font-size',
                'label': 'Font-size accuracy',
                'description': 'Keep correct font-size, allow natural line-height (readable)'
            },
            {
                'id': 'total-height',
                'label': 'Total height accuracy',
                'description': 'Force exact total height (may look cramped with line-height:1)'
            },
            {
                'id': 'balanced',
                'label': 'Balanced approach',
                'description': 'Correct font-size with slightly reduced line-height (1.2-1.3)'
            }
        ]
        question['recommendation'] = 'Recommend font-size accuracy with natural line-height'

    # GENERIC/OTHER
    else:
        question['context'] = f"Issue with '{element}': {issue_text}"
        question['question'] = f"How should we resolve this?"
        question['options'] = [
            {
                'id': 'accept',
                'label': 'Accept current implementation',
                'description': 'HTML version is acceptable, prioritize other issues'
            },
            {
                'id': 'manual',
                'label': 'Needs manual fix',
                'description': 'I\'ll provide specific guidance on how to fix'
            },
            {
                'id': 'defer',
                'label': 'Defer for now',
                'description': 'Not critical, focus on higher priority issues'
            }
        ]
        question['recommendation'] = 'Recommend accepting if close enough'

    return question


def triage_issues(
    issues: List[Dict[str, Any]],
    iteration_count: int = 2,
    iteration_history: List[Dict] = None
) -> Dict[str, Any]:
    """
    Triage issues after plateau detected

    Args:
        issues: List of feedback items from DOM measurements
        iteration_count: Number of auto-fix iterations attempted
        iteration_history: History of previous iterations

    Returns:
        Triage report with categorized issues and designer questions
    """

    auto_fixable = []
    needs_designer_input = []

    # Categorize each issue
    for issue in issues:
        category = categorize_issue(issue, iteration_history)

        if category == 'auto-fixable':
            auto_fixable.append(issue)
        else:
            needs_designer_input.append(issue)

    # Generate questions for issues needing designer input
    designer_questions = []
    for issue in needs_designer_input:
        question = generate_designer_question(issue)
        designer_questions.append(question)

    # Build triage report
    triage_report = {
        'summary': {
            'iterations_attempted': iteration_count,
            'total_issues': len(issues),
            'auto_fixable': len(auto_fixable),
            'needs_designer_input': len(needs_designer_input),
            'plateau_detected': True
        },
        'auto_fixable_issues': auto_fixable,
        'designer_questions': designer_questions,
        'recommendations': [
            f"Auto-fixed {len(auto_fixable)} issues successfully" if auto_fixable else "All auto-fixable issues resolved",
            f"{len(needs_designer_input)} issues need designer input to proceed",
            "Review questions below and provide guidance",
            "After designer input, run additional improvement iterations"
        ]
    }

    return triage_report


def format_triage_report_for_display(triage_report: Dict[str, Any]) -> str:
    """
    Format triage report as readable text for terminal/file

    Args:
        triage_report: Triage report from triage_issues()

    Returns:
        Formatted text report
    """

    summary = triage_report['summary']
    questions = triage_report['designer_questions']

    output = []
    output.append("=" * 70)
    output.append("🔍 ISSUE TRIAGE REPORT")
    output.append("=" * 70)
    output.append("")

    # Summary
    output.append(f"After {summary['iterations_attempted']} automatic improvement iterations:")
    output.append(f"  • Total issues: {summary['total_issues']}")
    output.append(f"  • Auto-fixable: {summary['auto_fixable']} ✅")
    output.append(f"  • Needs designer input: {summary['needs_designer_input']} ❓")
    output.append("")

    if summary['plateau_detected']:
        output.append("⚠️  PLATEAU DETECTED")
        output.append("   No improvement in last iteration - need designer input to proceed")
        output.append("")

    # Designer Questions
    if questions:
        output.append("=" * 70)
        output.append(f"❓ DESIGNER QUESTIONS ({len(questions)})")
        output.append("=" * 70)
        output.append("")

        for i, q in enumerate(questions, 1):
            priority_emoji = '🔴' if q['priority'] == 'high' else '🟡' if q['priority'] == 'medium' else '🟢'

            output.append(f"{i}. {priority_emoji} [{q['priority'].upper()}] {q['element']}")
            output.append(f"   Figma ID: {q['figma_id']}")
            output.append("")
            output.append(f"   📋 Context:")
            output.append(f"   {q['context']}")
            output.append("")
            output.append(f"   ❓ Question:")
            output.append(f"   {q['question']}")
            output.append("")
            output.append(f"   💡 Options:")

            for opt in q['options']:
                output.append(f"      [{opt['id'].upper()}] {opt['label']}")
                output.append(f"      → {opt['description']}")
                output.append("")

            output.append(f"   ✅ Recommendation: {q['recommendation']}")
            output.append("")
            output.append("-" * 70)
            output.append("")

    # Recommendations
    output.append("=" * 70)
    output.append("📌 NEXT STEPS")
    output.append("=" * 70)
    output.append("")

    for i, rec in enumerate(triage_report['recommendations'], 1):
        output.append(f"{i}. {rec}")

    output.append("")
    output.append("=" * 70)

    return "\n".join(output)


def save_triage_report(triage_report: Dict[str, Any], output_path: str):
    """
    Save triage report to JSON file

    Args:
        triage_report: Triage report from triage_issues()
        output_path: Path to save JSON file
    """

    with open(output_path, 'w') as f:
        json.dump(triage_report, f, indent=2)


def main():
    """Test the triage system with sample data"""

    # Sample issues (from our actual plateau)
    sample_issues = [
        {
            'priority': 'high',
            'category': 'dimension',
            'element': 'Brushed cashmere short-sleeve cardigan',
            'figma_id': '157:800',
            'issue': 'Height is 32px, should be 24.0px',
            'deviation': '33.3% too tall',
            'fix': 'Set height to 24.0px'
        },
        {
            'priority': 'high',
            'category': 'missing_element',
            'element': 'floating-selection-bar',
            'figma_id': '157:817',
            'issue': 'Element not found in DOM',
            'fix': 'Add container element matching Figma node 157:817'
        },
        {
            'priority': 'high',
            'category': 'dimension',
            'element': 'left column',
            'figma_id': '157:798',
            'issue': 'Height is 24px, should be 224.0px',
            'deviation': '89.3% too short',
            'fix': 'Set height to 224.0px'
        },
        {
            'priority': 'medium',
            'category': 'dimension',
            'element': 'Image1',
            'figma_id': '157:745',
            'issue': 'Width is 480px, should be 576.0px',
            'deviation': '16.7% too narrow',
            'fix': 'Set width to 576.0px'
        }
    ]

    # Run triage
    triage_report = triage_issues(sample_issues, iteration_count=2)

    # Print report
    print(format_triage_report_for_display(triage_report))

    # Save to file
    save_triage_report(triage_report, '/tmp/triage_report.json')
    print(f"\n💾 Saved triage report to: /tmp/triage_report.json")


if __name__ == '__main__':
    main()
