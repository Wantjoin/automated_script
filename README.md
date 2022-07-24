# automated_script

## crawler

### How to schedule a cron job to run crawler script?

Run `crontab -e` and add below script
```
0 0 * * * /root/miniconda3/bin/python /root/automated_script/crawler/crawl_shopee.py
```
## dashboard
Run `uvicorn main:app --host 0.0.0.0 --port 8050` to start the dashboard