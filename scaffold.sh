#!/bin/bash
# Run this once, from the parent folder where you want the project created.
# Usage: bash scaffold.sh

set -e

ROOT="Urbanroof-Assignment"

echo "Creating project structure at ./$ROOT ..."

# --- Backend ---
mkdir -p "$ROOT/backend/app/api"
mkdir -p "$ROOT/backend/app/core"
mkdir -p "$ROOT/backend/app/models"
mkdir -p "$ROOT/backend/app/utils"
mkdir -p "$ROOT/backend/storage/uploads"
mkdir -p "$ROOT/backend/storage/extracted_images"
mkdir -p "$ROOT/backend/storage/generated_reports"
mkdir -p "$ROOT/backend/tests/sample_data"

touch "$ROOT/backend/app/__init__.py"
touch "$ROOT/backend/app/main.py"
touch "$ROOT/backend/app/config.py"
touch "$ROOT/backend/app/api/__init__.py"
touch "$ROOT/backend/app/api/routes.py"
touch "$ROOT/backend/app/core/__init__.py"
touch "$ROOT/backend/app/core/pdf_extractor.py"
touch "$ROOT/backend/app/core/nlp_extractor.py"
touch "$ROOT/backend/app/core/merger.py"
touch "$ROOT/backend/app/core/ddr_builder.py"
touch "$ROOT/backend/app/core/pdf_generator.py"
touch "$ROOT/backend/app/models/__init__.py"
touch "$ROOT/backend/app/models/schemas.py"
touch "$ROOT/backend/app/utils/__init__.py"
touch "$ROOT/backend/app/utils/file_helpers.py"
touch "$ROOT/backend/app/utils/text_cleaning.py"
touch "$ROOT/backend/tests/__init__.py"
touch "$ROOT/backend/tests/test_pdf_extractor.py"
touch "$ROOT/backend/tests/test_merger.py"
touch "$ROOT/backend/requirements.txt"
touch "$ROOT/backend/.env.example"

# .gitkeep so empty storage folders survive git
touch "$ROOT/backend/storage/uploads/.gitkeep"
touch "$ROOT/backend/storage/extracted_images/.gitkeep"
touch "$ROOT/backend/storage/generated_reports/.gitkeep"

# --- Frontend (folders only — Vite will scaffold the rest via npm create) ---
mkdir -p "$ROOT/frontend/src/components"
mkdir -p "$ROOT/frontend/src/api"
mkdir -p "$ROOT/frontend/src/styles"
mkdir -p "$ROOT/frontend/public"

# --- Docs / root files ---
mkdir -p "$ROOT/docs"
touch "$ROOT/README.md"

cat > "$ROOT/.gitignore" <<'EOF'
# Python
__pycache__/
*.pyc
venv/
.env

# Node
node_modules/
dist/
.vite/

# Storage (generated/uploaded content)
backend/storage/uploads/*
backend/storage/extracted_images/*
backend/storage/generated_reports/*
!backend/storage/uploads/.gitkeep
!backend/storage/extracted_images/.gitkeep
!backend/storage/generated_reports/.gitkeep

# OS / Editor
.DS_Store
.vscode/
EOF

echo "Done. Structure created at ./$ROOT"
echo ""
echo "Next steps:"
echo "1. cd $ROOT/frontend && npm create vite@latest . -- --template react"
echo "2. cd $ROOT/backend && python -m venv venv && source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
