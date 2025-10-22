from log import Log

def main():
    log = Log()
    log.log()
    with log.version_lock(2):
        log.log()
    log.log()

if __name__ == "__main__":
    main()
