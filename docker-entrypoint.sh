#!/bin/sh
export ENV=production
export SUPABASE_URL=$(echo aHR0cHM6Ly9hcXJycnhtbHFmZWNocmlwdWlnYS5hcC1ub3J0aGVhc3QtMi5zdXBhYmFzZS5jbw== | base64 -d)
export SUPABASE_KEY=$(echo c2JfcHVibGlzaGFibGVfVmVBd1F6ekhHU1YwNXNMN2VvN0VEUV93S0lla29JMA== | base64 -d)
export SUPABASE_SERVICE_KEY=$(echo c2Jfc2VjcmV0X18yM1JlZTZhc1c4UmEwWmZNUDd4VkFfLVhVVWlUTW8= | base64 -d)
export REDIS_URL=$(echo cmVkaXNzOi8vZGVmYXVsdDpnUUFBQUFBQUFndEJBQUlnY0RKaE5qQTBaRFUzTmpjMFlqZzBZMlkzWWpZelltVTBPR0kyTnpNMVlqZG1OQUBtYWdpY2FsLXBhcmFrZWV0LTEzMzk1My51cHN0YXNoLmlvOjYzNzk= | base64 -d)
export LEMONSQUEEZY_API_KEY=$(echo ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SmhkV1FpT2lKek5uZ3pRVzF3WlVaaVltVjRhVFJsVGxSMVlVdGpaM0pPQ0lzSW5OMVlpSTZJakkyT0RZNU1UazRJaXdpY205c1pTSTZJbUZrYldsdUlpd2laWGh3SWpveE56VTROelEzTWpBd2ZRLmpBM05qUTNOV1kxTlRVM05EbGpZVFpsT1RGbE5XRm1NbUpsTkRnME1URjk= | base64 -d)
export LEMONSQUEEZY_WEBHOOK_SECRET=$(echo ZGtfd2ViaG9va19zZWNyZXRfMjAyNF9zZWN1cmVfMzJjaGFycw== | base64 -d)
export LEMONSQUEEZY_STORE_ID=$(echo MTMxMTcyNA== | base64 -d)
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
