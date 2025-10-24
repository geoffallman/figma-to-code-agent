# Figma-to-Code Agent

Multi-agent AI system that automatically generates high-fidelity React code from Figma designs through iterative improvement.

## Status

**Phase 1: Proof of Concept** - Week 2 In Progress
**Last Updated:** October 24, 2025
**Progress:** 8/15 days complete (53%)

**Recent Milestone:** ✅ Image asset extraction pipeline complete

## Overview

This project demonstrates a builder/optimizer agent pattern:
- **Builder Agent:** Generates and refines React/Tailwind code from Figma
- **Evaluator Agent:** Objectively measures visual fidelity using pixel-diff + vision LLM
- **Orchestrator:** Manages iteration loops until 85%+ fidelity achieved

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Figma API token ([Get from Figma Settings](https://www.figma.com/settings))
- Anthropic API key

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Install Playwright browsers
npx playwright install
```

### Configuration

Create a `.env` file:
```
ANTHROPIC_API_KEY=your_api_key_here
FIGMA_API_TOKEN=your_figma_token_here
```

### Usage

Coming soon...

## Project Structure

```
figma-to-code-agent/
├── agents/          # Agent classes (Builder, Evaluator)
├── tools/           # Tool integrations (Figma MCP, Playwright, pixelmatch)
├── utils/           # Utilities (config, logging)
├── scripts/         # Standalone scripts for testing
├── output/          # Generated files
├── examples/        # Demo outputs
└── docs/            # Documentation
```

## Development

**Current Phase:** Phase 1 - Proof of Concept
**Timeline:** 3 weeks
**Goal:** Demonstrate single iteration loop improves code quality

See [implementation-plan-phase1.md](../claudesidian/01_Projects/Figma-to-Code%20Agent/implementation-plan-phase1.md) for detailed plan.

## License

MIT
