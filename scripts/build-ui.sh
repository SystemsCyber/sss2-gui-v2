#!/bin/bash
# Build UI and copy to app-ui/static/ui/

set -e

echo "Building Svelte UI..."
cd ui
npm run build

echo "Copying build output to app-ui/static/ui/..."
cd ..
rm -rf app-ui/static/ui/*
cp -r ui/dist/* app-ui/static/ui/

echo "Build complete! UI files are in app-ui/static/ui/"
