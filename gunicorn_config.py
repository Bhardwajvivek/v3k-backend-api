def post_fork(server, worker):
    from app import start_background_scanner
    start_background_scanner()
