$ErrorActionPreference = "Stop"
git checkout main
git branch -D hf-backend 2>$null
git checkout --orphan hf-backend
git rm -rf .
git checkout main -- backend src requirements.txt run_attack.py run_backend.py Dockerfile .env.example

$readmeContent = @"
---
title: Aegis-Red
emoji: 🛡️
colorFrom: red
colorTo: red
sdk: docker
app_port: 7860
---
# Aegis-Red Backend
"@
Set-Content -Path README.md -Value $readmeContent

git add README.md
git commit -m "Deploy to Hugging Face with updated Dockerfile"
git push huggingface hf-backend:main --force
git checkout main
git restore .
