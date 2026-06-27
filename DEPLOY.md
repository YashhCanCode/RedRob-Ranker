# Deploying the sandbox demo (Streamlit Community Cloud)

The challenge requires a public "sandbox" link where judges can run the ranker on
a small sample. `app.py` is that demo. Hosting it is free.

## Step 1 — Put this repo on GitHub
From inside this folder:

    git init
    git add .
    git commit -m "Redrob candidate ranker"
    git branch -M main
    git remote add origin https://github.com/<YOUR_USERNAME>/redrob-ranker.git
    git push -u origin main

(Create the empty `redrob-ranker` repo first at https://github.com/new — no README/.gitignore,
this repo already has them.)

## Step 2 — Deploy on Streamlit Community Cloud
1. Go to https://share.streamlit.io and sign in with GitHub (free).
2. Click **Create app -> Deploy a public app from GitHub**.
3. Fill in:
   - Repository: `<YOUR_USERNAME>/redrob-ranker`
   - Branch: `main`
   - Main file path: `app.py`
4. Click **Deploy**. First build takes ~2-3 min (it installs requirements.txt).
5. You'll get a public URL like `https://<something>.streamlit.app`.

## Step 3 — Record the link
Paste that URL into `submission_metadata.yaml` under `sandbox_link:`,
and your GitHub URL under `github_repo:`.

## Verifying it works
On the live page, tick "Use bundled 50-candidate sample" and click **Rank candidates**.
You should see a ranked table and a download button within a few seconds — that's
all the judges need to confirm.
