def handler(request, context):
    """
    ✅ Minimal Vercel-compatible Python function
    Used to confirm the Python runtime and routing work fine.
    """
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"message": "Hello from Vercel Python! 🚀"}'
    }
