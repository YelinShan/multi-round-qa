import asyncio
import logging
import threading
from logging import Logger


def build_format(color):
    reset = "\x1b[0m"
    underline = "\x1b[3m"
    return (
        f"{color}[%(asctime)s] %(levelname)s:{reset} %(message)s "
        + f"{underline}(%(filename)s:%(lineno)d:%(name)s){reset}"
    )


class CustomFormatter(logging.Formatter):

    grey = "\x1b[1m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: build_format(grey),
        logging.INFO: build_format(green),
        logging.WARNING: build_format(yellow),
        logging.ERROR: build_format(red),
        logging.CRITICAL: build_format(bold_red),
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def init_logger(name: str, log_level=logging.DEBUG) -> Logger:
    logger = logging.getLogger(name)

    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)

    return logger


class AsyncLoopWrapper:
    _loop: asyncio.AbstractEventLoop = None
    _thread: threading.Thread = None
    _logger = init_logger("AsyncLoopWrapper")

    @classmethod
    def WaitLoop(cls):
        assert cls._loop is not None, "Loop is not started"

        async def wait_for_tasks():
            current_task = asyncio.current_task(cls._loop)
            tasks = [
                task
                for task in asyncio.all_tasks(cls._loop)
                if not task.done() and task is not current_task
            ]
            cls._logger.info(f"Waiting for {len(tasks)} tasks to finish")
            if tasks:
                # Use asyncio.wait with timeout to avoid hanging indefinitely
                try:
                    done, pending = await asyncio.wait(
                        tasks, timeout=5.0, return_when=asyncio.ALL_COMPLETED
                    )
                    if pending:
                        cls._logger.warning(
                            f"Timeout waiting for {len(pending)} tasks to complete. "
                            f"Cancelling remaining tasks."
                        )
                        for task in pending:
                            task.cancel()
                        # Wait a bit more for cancelled tasks to clean up
                        await asyncio.wait(pending, timeout=2.0)
                except Exception as e:
                    cls._logger.error(f"Error during task cleanup: {e}")
                    # Cancel all remaining tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()

        # Schedule the wait_for_tasks coroutine to be executed in the loop
        future = asyncio.run_coroutine_threadsafe(wait_for_tasks(), cls._loop)
        try:
            # Wait for wait_for_tasks to complete with a reasonable timeout
            future.result(timeout=3.0)  # Total timeout including cleanup
        except asyncio.TimeoutError:
            cls._logger.warning("Timeout waiting for async loop cleanup")
        except Exception as e:
            cls._logger.error(f"Error while waiting for tasks: {e}")

    @classmethod
    def StartLoop(cls):
        if cls._loop is not None:
            cls._logger.warning("Loop is already started")
            return

        if cls._loop is None:
            cls._loop = asyncio.new_event_loop()

        def run_loop():
            asyncio.set_event_loop(cls._loop)
            cls._logger.debug("Starting the asyncio loop")
            cls._loop.run_forever()

        cls._thread = threading.Thread(target=run_loop)
        cls._thread.start()

    @classmethod
    def StopLoop(cls):
        assert cls._loop is not None, "Loop is not started"
        assert cls._thread is not None, "Thread is not started"

        def stop_loop():
            cls._logger.debug("Stopping the loop!")
            cls._loop.stop()

        cls._logger.info("Waiting for remaining tasks to finish")
        cls.WaitLoop()

        cls._loop.call_soon_threadsafe(stop_loop)
        cls._thread.join()

    @classmethod
    def GetLoop(cls) -> asyncio.AbstractEventLoop:
        assert cls._loop is not None, "Loop is not started"
        return cls._loop

    @classmethod
    def GetOrStartLoop(cls) -> asyncio.AbstractEventLoop:
        if cls._loop is None:
            cls.StartLoop()
        return cls._loop
