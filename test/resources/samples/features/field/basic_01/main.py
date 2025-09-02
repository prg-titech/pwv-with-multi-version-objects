from log import Log

def main():
    log = Log()
    log.setlog("This is a log message.")
    print(log.log)

if __name__ == "__main__":
    main()
