import concurrent.futures

import example.application


def test_get_application():

    def get_app():
        return next(example.application.get_application())

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=5
    ) as executor:

        futures = [
            executor.submit(get_app) for _ in range(10)
        ]

        results = [
            future.result() for future
            in concurrent.futures.as_completed(futures)
        ]

        assert len(futures) == len(results) == 10
        assert len(set(results)) == 1
        assert results[0] is not None
