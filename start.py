import os
import sys

if __name__ == "__main__":
    # Optional: run startup check first
    try:
        import startup_check  # type: ignore
        rc = startup_check.main()
        if rc != 0:
            sys.exit(rc)
    except Exception as e:
        # Don't block start if startup_check isn't present
        print(f"Startup check skipped or failed: {e}")

    from uvicorn import run

    port_str = os.getenv("PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        # Fallback to 8080 if PORT isn't an int
        port = 8080

    run("app:app", host="0.0.0.0", port=port)
