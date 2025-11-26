#!/usr/bin/env bash
# Render build script

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install PDF generation dependencies
pip install reportlab matplotlib

# Database migrations
alembic upgrade head
