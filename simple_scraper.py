name: Defense News Scraper

on:
  # Manual trigger
  workflow_dispatch:
    inputs:
      days_back:
        description: 'Number of days to look back'
        required: false
        default: '7'
        type: string
  
  # Scheduled run (every Monday at 9 AM UTC)
  schedule:
    - cron: '0 9 * * 1'

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        cache: 'pip'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: Create output directory
      run: mkdir -p output
      
    - name: Run scraper
      env:
        PYTHONUNBUFFERED: 1
      run: |
        # Set days back from input or default to 7
        DAYS_BACK="${{ github.event.inputs.days_back || '7' }}"
        
        # Run the scraper with error handling
        python simple_scraper.py --manual --days "$DAYS_BACK" || {
          echo "Scraper failed with exit code $?"
          echo "Checking for partial results..."
          ls -la *.md || echo "No markdown files found"
          exit 1
        }
        
    - name: List generated files
      run: |
        echo "All files in current directory:"
        ls -la
        echo "Looking for markdown files:"
        find . -name "*.md" -type f || echo "No .md files found"
        echo "Looking for log files:"
        find . -name "*.log" -type f || echo "No .log files found"
        
    - name: Upload artifacts
      if: always()  # Upload even if scraper partially failed
      uses: actions/upload-artifact@v4
      with:
        name: defense-news-report-${{ github.run_number }}
        path: |
          .
        include-hidden-files: true
        retention-days: 30
        
    - name: Commit and push results (optional)
      if: success()
      run: |
        # Configure git (replace with your details)
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        
        # Add generated files
        git add *.md || echo "No markdown files to add"
        
        # Check if there are changes to commit
        if git diff --staged --quiet; then
          echo "No changes to commit"
        else
          git commit -m "Auto-update: Defense news report $(date +'%Y-%m-%d %H:%M')"
          git push || echo "Push failed - check repository permissions"
        fi

  # Optional: Send notification on failure
  notify-failure:
    runs-on: ubuntu-latest
    needs: scrape
    if: failure()
    
    steps:
    - name: Notify failure
      run: |
        echo "Scraper job failed. Check the logs for details."
        echo "Run number: ${{ github.run_number }}"
        echo "Run ID: ${{ github.run_id }}"
