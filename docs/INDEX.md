# Documentation Index

This directory contains all documentation for the mdk_mcp project.

## 📚 Quick Navigation

### For Users

**Start Here:**
1. **[../README.md](../README.md)** - Project overview, quick start, features
2. **[QUICK_START.md](QUICK_START.md)** - 5-minute getting started guide
3. **[INTERACTIVE_MODE.md](INTERACTIVE_MODE.md)** - Complete interactive mode guide

**Advanced Usage:**
- **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive user guide with all features

### For Developers

**Architecture & Integration:**
- **[../CLAUDE.md](../CLAUDE.md)** - Project overview and development guidelines
- **[AUTOGEN_INTEGRATION.md](AUTOGEN_INTEGRATION.md)** - AG2 integration details
- **[road_map.md](road_map.md)** - Development roadmap (6 phases)

**Deployment:**
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide (Docker + Kubernetes)

### Historical Documentation

**Archive:**
- **[archive/](archive/)** - Previous status reports, testing docs, and intermediate files

## 📖 Document Descriptions

### User Documentation

#### [QUICK_START.md](QUICK_START.md)
- **Purpose:** Get started in 5 minutes
- **Audience:** First-time users
- **Contents:**
  - Prerequisites and setup
  - Starting the system
  - Understanding the workflow
  - Example requests
  - Viewing results
  - Basic troubleshooting

#### [INTERACTIVE_MODE.md](INTERACTIVE_MODE.md)
- **Purpose:** Complete guide to interactive chat interface
- **Audience:** All users
- **Contents:**
  - How interactive mode works
  - Available commands
  - Example interactions
  - Real-time progress display
  - Viewing task logs
  - Tips for effective requests
  - Troubleshooting

#### [USER_GUIDE.md](USER_GUIDE.md)
- **Purpose:** Comprehensive reference for all features
- **Audience:** Regular users, advanced users
- **Contents:**
  - System architecture overview
  - Agent roles and capabilities
  - All interaction methods
  - Task log interpretation
  - Configuration options
  - Use cases and examples
  - Best practices

### Technical Documentation

#### [../CLAUDE.md](../CLAUDE.md)
- **Purpose:** Guide for Claude Code AI assistant when working with this codebase
- **Audience:** Developers, Claude Code
- **Contents:**
  - Project overview
  - Architecture summary
  - Key technologies
  - Development commands
  - Code structure patterns
  - Important design decisions
  - Common development tasks

#### [AUTOGEN_INTEGRATION.md](AUTOGEN_INTEGRATION.md)
- **Purpose:** Technical details of AG2 integration
- **Audience:** Developers
- **Contents:**
  - AG2 multi-agent system architecture
  - MCP bridge implementation
  - Tool integration patterns
  - Async/await patterns
  - Testing strategies

#### [DEPLOYMENT.md](DEPLOYMENT.md)
- **Purpose:** Production deployment guide
- **Audience:** DevOps, system administrators
- **Contents:**
  - Docker deployment
  - Kubernetes manifests
  - Environment configuration
  - Scaling considerations
  - Monitoring and logging
  - Security best practices

#### [road_map.md](road_map.md)
- **Purpose:** Development roadmap and timeline
- **Audience:** Developers, project managers
- **Contents:**
  - 6-phase implementation plan
  - Phase 1: Database Integration (current)
  - Phase 2: Sequence Processing
  - Phase 3: Alignment & Phylogenetics
  - Phase 4: Design & Primers
  - Phase 5: Validation & Literature
  - Phase 6: Export & Provenance
  - Timeline estimates

### Historical Documentation (Archive)

#### [archive/INTERACTION_REFERENCE.md](archive/INTERACTION_REFERENCE.md)
- Quick reference card (superseded by INTERACTIVE_MODE.md)

#### [archive/INTERACTIVE_QUICK_START.md](archive/INTERACTIVE_QUICK_START.md)
- Quick start for interactive mode (consolidated into INTERACTIVE_MODE.md)

#### [archive/TASK_LOGGING_SUMMARY.md](archive/TASK_LOGGING_SUMMARY.md)
- Task logging system summary (now covered in USER_GUIDE.md)

#### [archive/WEEK7_SUMMARY.md](archive/WEEK7_SUMMARY.md)
- Week 7 development summary (historical record)

#### [archive/TESTING_AUTOGEN.md](archive/TESTING_AUTOGEN.md)
- AutoGen testing guide (historical record)

#### [archive/PHASE1_STATUS.md](archive/PHASE1_STATUS.md)
- Phase 1 status report (see road_map.md for current status)

#### [archive/phase1-2-actions.md](archive/phase1-2-actions.md)
- Detailed action items for Phase 1-2 (historical record)

## 🗂️ Documentation by Topic

### Getting Started
- [../README.md](../README.md) - Overview and quick start
- [QUICK_START.md](QUICK_START.md) - 5-minute guide
- [INTERACTIVE_MODE.md](INTERACTIVE_MODE.md) - Interactive interface

### Using the System
- [INTERACTIVE_MODE.md](INTERACTIVE_MODE.md) - Chat interface guide
- [USER_GUIDE.md](USER_GUIDE.md) - Complete user reference

### Architecture & Design
- [../CLAUDE.md](../CLAUDE.md) - Project overview
- [AUTOGEN_INTEGRATION.md](AUTOGEN_INTEGRATION.md) - AG2 multi-agent system
- [road_map.md](road_map.md) - Development roadmap

### Deployment & Operations
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [USER_GUIDE.md](USER_GUIDE.md) - Configuration options

### Development
- [../CLAUDE.md](../CLAUDE.md) - Development guidelines
- [AUTOGEN_INTEGRATION.md](AUTOGEN_INTEGRATION.md) - Technical details
- [road_map.md](road_map.md) - Roadmap

## 📝 Documentation Standards

### File Naming
- **UPPERCASE.md** - Major documentation files
- **lowercase.md** - Technical/historical files
- Keep names descriptive and concise

### Content Structure
All documentation should include:
1. **Title and Purpose** - What this document covers
2. **Table of Contents** - For documents >2 pages
3. **Quick Start** - Getting started quickly
4. **Detailed Sections** - Comprehensive coverage
5. **Examples** - Real-world usage examples
6. **Troubleshooting** - Common issues and solutions
7. **See Also** - Links to related documentation

### Markdown Style
- Use **bold** for emphasis and UI elements
- Use `code` for commands, file names, and code snippets
- Use ```blocks for multi-line code
- Use tables for structured data
- Use emoji sparingly for visual markers (🚀 ✅ ❌ 🚧 📖 🔧)

## 🔄 Keeping Documentation Updated

### When to Update
- **README.md**: When adding major features or changing architecture
- **QUICK_START.md**: When changing startup procedure
- **INTERACTIVE_MODE.md**: When adding commands or changing interface
- **USER_GUIDE.md**: When adding features or changing behavior
- **AUTOGEN_INTEGRATION.md**: When upgrading AG2 or changing architecture
- **DEPLOYMENT.md**: When changing deployment procedures
- **road_map.md**: At the end of each phase or when priorities change

### Deprecation Process
1. Mark sections as **[DEPRECATED]** in original document
2. Move entire documents to `archive/` when fully superseded
3. Update links in remaining documents
4. Update this INDEX.md

## 📞 Documentation Feedback

If you find:
- **Errors or outdated information**: File an issue
- **Missing content**: Submit a pull request
- **Unclear sections**: Open a discussion

All documentation improvements are welcome!

---

**Document Version:** 1.0
**Last Updated:** 2025-10-01
**Status:** Current
