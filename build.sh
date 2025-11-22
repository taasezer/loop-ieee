#!/usr/bin/env bash
# Render build script

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Database migrations (if needed)
# alembic upgrade head
