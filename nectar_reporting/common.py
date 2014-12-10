

def with_retries(fn, *args, **kwargs):
    count = 0
    max_retries = kwargs.get("max_retries", 5)
    while True:
        try:
            return fn(*args, **kwargs)
        except:
            if count > max_retries:
                raise
            count += 1
